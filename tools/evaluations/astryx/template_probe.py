"""Exercise real library-page scaffolding and overwrite protection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from common import command, save_new


def main(root):
    target=root/'apps/template-library'
    target.mkdir()
    (target/'src').mkdir()
    dependencies=json.loads((root/'runtime/package.json').read_text(encoding='utf-8'))['dependencies']
    dependencies={k:v for k,v in dependencies.items() if k in ('react','react-dom','vite','@stylexjs/stylex','@astryxdesign/core','@astryxdesign/cli','@astryxdesign/theme-neutral')}
    dependencies['@heroicons/react']='2.2.0'
    save_new(target/'package.json',{'name':'astryx-template-fixture','version':'0.0.0','private':True,'dependencies':dependencies,'scripts':{'build':'vite build'}})
    env=os.environ.copy();env['npm_config_cache']=str(root/'npm-cache')
    install=command([shutil.which('npm.cmd'),'install','--no-audit','--no-fund'],target,root/'evidence/template-install.json',timeout=600,env=env)
    if install['exit']!=0:raise RuntimeError(install['stderr'])
    cli=target/'node_modules/.bin/astryx.cmd'
    recommend=command([cli,'build','public data directory with search filters and cards'],target,root/'evidence/template-recommend.json')
    scaffold=command([cli,'template','library','--type','page','src/Library.tsx'],target,root/'evidence/template-scaffold.json')
    p=target/'src/Library.tsx'
    original=p.read_bytes()
    repeat=command([cli,'template','library','--type','page','src/Library.tsx'],target,root/'evidence/template-repeat.json')
    preserved=p.read_bytes()==original
    save_new(root/'evidence/template-results.json',{'install_exit':install['exit'],'recommend_exit':recommend['exit'],'scaffold_exit':scaffold['exit'],
        'repeat_exit':repeat['exit'],'existing_file_preserved':preserved,'original_sha256':hashlib.sha256(original).hexdigest()})
    # Standalone Vite host: add the React namespace for the classic JSX runtime.
    p.write_text("import React from 'react';\n"+original.decode('utf-8'),encoding='utf-8')
    (target/'src/main.jsx').write_text("import React from 'react';\nimport {createRoot} from 'react-dom/client';\nimport {Theme} from '@astryxdesign/core/theme';\nimport {neutralTheme} from '@astryxdesign/theme-neutral/built';\nimport Library from './Library';\nimport '@astryxdesign/core/reset.css';\nimport '@astryxdesign/core/astryx.css';\nimport '@astryxdesign/theme-neutral/theme.css';\ncreateRoot(document.getElementById('root')).render(<Theme theme={neutralTheme} mode=\"light\"><Library/></Theme>);\n",encoding='utf-8')
    (target/'index.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>Astryx template fixture</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>',encoding='utf-8')
    build=command([shutil.which('npm.cmd'),'run','build'],target,root/'evidence/template-build.json',timeout=300,env=env)
    print(json.dumps({'install':install['exit'],'scaffold':scaffold['exit'],'repeat':repeat['exit'],'preserved':preserved,
                      'build':build['exit'],'build_tail':build['stdout'][-1000:]+build['stderr'][-1500:]},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
