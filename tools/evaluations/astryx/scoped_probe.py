"""Compare scoped styling with the observed whole-page reset regression."""
import argparse
from pathlib import Path
import shutil
import subprocess

from common import save_new, snapshot


def main(root):
    source=root/'apps/vite-candidate'
    target=root/'apps/vite-scoped'
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('node_modules','dist','.git'))
    subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(target/'node_modules'),str(root/'runtime/node_modules')],check=True,capture_output=True)
    p=target/'src/App.jsx'
    text=p.read_text(encoding='utf-8')
    text=text.replace('return <Theme theme={neutralTheme} mode="light"><main','return <main').replace('</main></Theme>','</main>')
    for component in ('TextInput','Button'):
        import re
        text=re.sub(r'<'+component+r'\b[^\n]*?/>',lambda m:'<Theme theme={neutralTheme} mode="light">'+m[0]+'</Theme>',text)
    p.write_text(text,encoding='utf-8')
    css=target/'src/style.css'
    css.write_text(css.read_text(encoding='utf-8').replace("@import '@astryxdesign/core/reset.css';\n",'')+
                   '\nbody{font-size:16px;color:#17212b;font-family:Arial,sans-serif}\n',encoding='utf-8')
    save_new(root/'evidence/vite-scoped-source.json',snapshot(target))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
