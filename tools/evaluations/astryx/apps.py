"""Construct matched browser fixtures; synthetic data, no external service."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from common import command, save_new, snapshot

APP = ''''use client';
import React, {useState} from 'react';
__IMPORTS__
const rows = [{id:1, title:'하천 수질 자료', category:'water'}, {id:2, title:'대중교통 자료', category:'transport'}];
export default function App(){
 const [q,setQ]=useState(''),[query,setQuery]=useState(''),[category,setCategory]=useState('all');
 const [email,setEmail]=useState(''),[status,setStatus]=useState(''),[enters,setEnters]=useState(0),[count,setCount]=useState(0);
 const results=rows.filter(r=>r.title.includes(query)&&(category==='all'||r.category===category));
 return __WRAP_START__<main className="page mx-auto" data-fixture="public-data">
 <header><svg role="img" aria-label="공공데이터 길잡이 로고" width="40" height="40" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="#6d28d9"/></svg><h1>공공데이터 길잡이</h1></header>
 <p className="brand" id="brand">자료 · 검색</p><p>공개 자료의 출처와 기준일을 확인하세요.</p>
 <form id="search-form" onSubmit={e=>{e.preventDefault();setQuery(q);setCount(x=>x+1)}}>
 __SEARCH__
 __BUTTON__
 <label htmlFor="category">분야</label><select id="category" value={category} onChange={e=>setCategory(e.target.value)}><option value="all">전체</option><option value="water">물</option><option value="transport">교통</option></select>
 </form><p>검색 실행 <output id="submit-count">{count}</output>회</p>
 <ul id="results">{results.map(r=><li key={r.id}>{r.title}</li>)}</ul>
 <form id="contact" onSubmit={e=>{e.preventDefault();setStatus('입력 형식 확인: 전송하지 않았습니다.')}}>
 <label htmlFor="email">문의 이메일</label><input id="email" type="email" required value={email} onChange={e=>setEmail(e.target.value)}/><button type="submit">입력 확인</button><output id="status" aria-live="polite">{status}</output></form>
 <section aria-label="한국어 입력 검증"><h2>한글 조합과 Enter</h2>__IME__<output id="enter-count">{enters}</output></section>
 <p id="tailwind-canary" className="font-bold text-[rgb(109,40,217)]">아주 긴 한국어 안내 문구도 좁은 화면에서 빠짐없이 읽을 수 있어야 합니다. 자료의 출처와 기준일을 다시 확인하세요.</p>
 </main>__WRAP_END__;
}
'''
CSS = ':root{--brand:#6d28d9;color:#17212b;background:#fff;font-family:Arial,sans-serif}*{box-sizing:border-box}.page{max-width:960px;margin:0 auto;padding:24px}header{display:flex;align-items:center;gap:12px;flex-wrap:wrap}h1{font-size:28px;font-weight:700}.brand{color:var(--brand);font-weight:bold}form{display:flex;gap:12px;align-items:end;flex-wrap:wrap;margin:24px 0}input,button,select{max-width:100%;padding:10px}button:not(.astryx-button){background:#6d28d9;color:#fff}section{margin:24px 0}input:focus-visible,select:focus-visible,button:focus-visible{outline:3px solid #08754f;outline-offset:2px}p{overflow-wrap:anywhere}ul{padding:20px}h2{font-size:20px}@media(max-width:480px){.page{padding:12px}form{align-items:stretch}form>input{width:100%}}'
NATIVE_SEARCH = '<label htmlFor="q">자료 검색</label><input id="q" type="search" value={q} onChange={e=>setQ(e.target.value)}/>'
NATIVE_IME = '<label htmlFor="ime">한국어 조합 확인</label><input id="ime" value={email} onChange={e=>setEmail(e.target.value)} onKeyDown={e=>{if(e.key===\'Enter\'&&!e.nativeEvent.isComposing&&e.keyCode!==229)setEnters(x=>x+1)}}/>'


def app_source(candidate):
    return (APP.replace('__IMPORTS__', "import {Button} from '@astryxdesign/core/Button';\nimport {TextInput} from '@astryxdesign/core/TextInput';\nimport {Theme} from '@astryxdesign/core/theme';\nimport {neutralTheme} from '@astryxdesign/theme-neutral/built';" if candidate else '')
        .replace('__WRAP_START__', '<Theme theme={neutralTheme} mode="light">' if candidate else '')
        .replace('__WRAP_END__', '</Theme>' if candidate else '')
        .replace('__SEARCH__', '<TextInput type="search" label="자료 검색" value={q} onChange={setQ}/>' if candidate else NATIVE_SEARCH)
        .replace('__BUTTON__', '<Button id="search" label="검색" type="submit" variant="primary"/>' if candidate else '<button id="search" type="submit">검색</button>')
        .replace('__IME__', '<TextInput label="한국어 조합 확인" value={email} onChange={setEmail} onEnter={()=>setEnters(x=>x+1)}/>' if candidate else NATIVE_IME))


def main(root):
    runtime = root / 'runtime'
    for framework in ('vite', 'next'):
        for variant in ('baseline', 'candidate'):
            candidate = variant == 'candidate'
            target = root / 'apps' / f'{framework}-{variant}'
            target.mkdir(parents=True)
            subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(target / 'node_modules'), str(runtime / 'node_modules')], check=True, capture_output=True)
            source_dir = target / ('src' if framework == 'vite' else 'app')
            source_dir.mkdir()
            data = json.loads((runtime / 'package.json').read_text(encoding='utf-8'))
            data['name'] = f'astryx-{framework}-{variant}'
            data['scripts'] = {'build': 'vite build', 'dev': 'vite --host 127.0.0.1'} if framework == 'vite' else {'build': 'next build --webpack', 'dev': 'next dev --webpack --hostname 127.0.0.1'}
            save_new(target / 'package.json', data)
            shutil.copy2(runtime / 'package-lock.json', target / 'package-lock.json')
            (source_dir / ('App.jsx' if framework == 'vite' else 'page.jsx')).write_text(app_source(candidate), encoding='utf-8')
            imports = "@import '@astryxdesign/core/reset.css';\n@import '@astryxdesign/core/astryx.css';\n@import '@astryxdesign/theme-neutral/theme.css';\n" if candidate else ''
            if framework == 'next':
                imports = ("@layer reset, theme, base, astryx-base, astryx-theme, components, utilities;\n" if candidate else '') + "@import 'tailwindcss';\n" + imports
                (target / 'postcss.config.mjs').write_text("export default {plugins:{'@tailwindcss/postcss':{}}};\n", encoding='utf-8')
                (target / 'next.config.mjs').write_text("export default {experimental:{cpus:2},devIndicators:false};\n", encoding='utf-8')
                (source_dir / 'layout.jsx').write_text("import React from 'react';\nimport './globals.css';\nexport const metadata={title:'공공데이터 길잡이',icons:{icon:'data:,'}};\nexport default function Layout({children}){return <html lang=\"ko\"><body>{children}</body></html>}\n", encoding='utf-8')
                (source_dir / 'globals.css').write_text(imports + CSS, encoding='utf-8')
            else:
                (source_dir / 'style.css').write_text(imports + CSS, encoding='utf-8')
                (source_dir / 'main.jsx').write_text("import React from 'react';\nimport {createRoot} from 'react-dom/client';\nimport App from './App';\nimport './style.css';\ncreateRoot(document.getElementById('root')).render(<App/>);\n", encoding='utf-8')
                (target / 'index.html').write_text('<!doctype html><html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>공공데이터 길잡이</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>', encoding='utf-8')
            save_new(root / f'evidence/{framework}-{variant}-source.json', snapshot(target))
    print('Created four matched React fixtures.')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    main(p.parse_args().root)
