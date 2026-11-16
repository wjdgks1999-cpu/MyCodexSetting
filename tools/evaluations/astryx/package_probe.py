"""Package and install only a disposable kit copy; never touch real dist."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

from common import REPO, command, save_new, snapshot


def main(root):
    base=root/'packaging'
    base.mkdir()
    source=base/'source'
    shutil.copytree(REPO/'kit',source/'kit')
    for name in ('README.md','CHANGELOG.md','docs/usage.md','tools/build_release.py'):
        dest=source/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(REPO/name,dest)
    skill=source/'kit/skills/astryx'
    shutil.copytree(REPO/'tools/evaluations/astryx/candidate',skill)
    shutil.copy2(root/'upstream/LICENSE',skill/'LICENSE')
    model=source/'kit/mycodex_lib/model.py'
    text=model.read_text(encoding='utf-8').replace("'context-compression')", "'context-compression', 'astryx')",1)
    text += "\nREQUIRED_ASSETS.add('.agents/skills/astryx/LICENSE')\n"
    model.write_text(text,encoding='utf-8')
    build=command([sys.executable,'-X','utf8','-B',source/'tools/build_release.py','--output',base/'release'],source,root/'evidence/package-build.json')
    if build['exit']!=0:
        raise RuntimeError(build['stderr'])
    archive_path,=list((base/'release').glob('*.zip'))
    extracted=base/'extracted'
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if not (extracted/name).resolve().is_relative_to(extracted.resolve()):
                raise ValueError('unsafe ZIP path')
        if archive.testzip() is not None:
            raise ValueError('corrupt ZIP')
        archive.extractall(extracted)
        assets=[n for n in archive.namelist() if '/kit/skills/astryx/' in n]
    release,=extracted.iterdir()
    rows=[]
    for mode in ('clean','existing','edited-collision','foreign-skill'):
        target=base/('zip-consumer' if mode=='clean' else mode)
        target.mkdir()
        (target/'PRD.md').write_text('# ZIP 소비자\nReact UI 호환성 시험. 제품 구현은 승인된 범위에서만 한다.\n',encoding='utf-8')
        preserved={}
        if mode=='existing':
            preserved={'AGENTS.md':b'# User rules\nRead .context/index.md. Keep custom rules.\n','.codex/config.toml':b'model = "user-choice"\n'}
        if mode=='foreign-skill':
            preserved={'.agents/skills/astryx/SKILL.md':b'---\nname: astryx\ndescription: Foreign skill\n---\nKEEP_FOREIGN\n'}
        for name,data in preserved.items():
            dest=target/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
        args=[sys.executable,'-X','utf8','-B',release/'kit/mycodex.py','init','--target',target,'--requirements','PRD.md']
        before=snapshot(target)
        dry=command(args,base,root/f'evidence/zip-{mode}-dry.json')
        dry_unchanged=before==snapshot(target)
        install=command(args+['--apply'],base,root/f'evidence/zip-{mode}-apply.json')
        after=snapshot(target)
        row={'mode':mode,'dry_exit':dry['exit'],'dry_unchanged':dry_unchanged,'install_exit':install['exit'],
             'user_files_preserved':all((target/p).read_bytes()==data for p,data in preserved.items())}
        if install['exit']==0:
            manifest=json.loads((target/'.mycodex/manifest.json').read_text(encoding='utf-8'))
            row['manifest_count']=len(manifest['files'])
            row['manifest_match']=all(hashlib.sha256((target/p).read_bytes()).hexdigest()==h for p,h in manifest['files'].items())
            repeat=command(args+['--apply'],base,root/f'evidence/zip-{mode}-repeat.json')
            row.update(repeat_exit=repeat['exit'],repeat_unchanged=after==snapshot(target))
            validation=command([sys.executable,'-X','utf8','-B',target/'.mycodex/mycodex.py','validate','--target',target,'--strict','--json'],base,root/f'evidence/zip-{mode}-validate.json')
            row['validation']=json.loads(validation['stdout'])
            if mode=='edited-collision':
                p=target/'.agents/skills/astryx/SKILL.md'
                with p.open('a',encoding='utf-8') as f:f.write('\nUSER_EDIT_KEEP\n')
                edited=snapshot(target)
                conflict=command(args+['--apply'],base,root/'evidence/zip-edited-conflict.json')
                row.update(edited_conflict_exit=conflict['exit'],edited_preserved=edited==snapshot(target))
        else:
            row['failed_install_preserved']=before==after
        rows.append(row)
    # Add process skills after the ZIP contract check for a fresh consumer CLI trial.
    shutil.copytree(REPO/'.agents/skills/superpowers',base/'zip-consumer/.agents/skills/superpowers')
    save_new(root/'evidence/packaging-results.json',{'zip_sha256':hashlib.sha256(archive_path.read_bytes()).hexdigest(),'astryx_assets':assets,'consumers':rows})
    print(json.dumps({'assets':assets,'consumers':rows},ensure_ascii=False),flush=True)
    shutil.copytree(REPO/'tests',source/'tests',ignore=shutil.ignore_patterns('__pycache__','evaluations'))
    test=command([sys.executable,'-X','utf8','-B','-m','unittest','discover','-s','tests','-v'],source,root/'evidence/candidate-product-tests.json',timeout=600)
    print(json.dumps({'candidate_suite_exit':test['exit'],'tail':test['stderr'][-1200:]},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
