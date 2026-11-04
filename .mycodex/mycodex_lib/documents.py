from datetime import datetime
from pathlib import Path
import re
from urllib.parse import unquote
from .model import DocRef, IndexData, InputError, OPTIONAL_KEYS, HANDOFF_SECTIONS


def parse_index(text: str) -> IndexData:
    text = text.lstrip('\ufeff')
    front = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not front:
        raise InputError('Index metadata is missing.')
    meta = {}
    for line in front[1].splitlines():
        if not line.strip():
            continue
        pair = line.split(':', 1)
        if len(pair) != 2 or pair[0] in meta:
            raise InputError('Invalid or duplicate index metadata.')
        meta[pair[0]] = pair[1].strip()
    if meta != {'schema_version': '1', 'status': meta.get('status')} or meta.get('status') not in ('needs-review', 'ready'):
        raise InputError('Unsupported index schema or status.')
    references = []
    section = ''
    for line in text[front.end():].splitlines():
        if line.startswith('## '):
            section = line[3:].strip()
        if section not in ('원본과 현재 작업', '추가 문서') or not line.startswith('|'):
            continue
        cells = [c.strip().strip('`') for c in line.strip().strip('|').split('|')]
        if not cells or cells[0] in ('key', 'path') or cells[0].startswith('-'):
            continue
        if section == '원본과 현재 작업':
            if len(cells) != 3 or cells[0] not in ('requirements', *OPTIONAL_KEYS):
                raise InputError('Invalid navigation row.')
            references.append(DocRef(*cells))
        else:
            if len(cells) != 2:
                raise InputError('Invalid topic document row.')
            references.append(DocRef('document', *cells))
    for key in OPTIONAL_KEYS:
        if len([r for r in references if r.kind == key]) != 1:
            raise InputError('Each optional navigation key must appear exactly once.')
    requirements = [r for r in references if r.kind == 'requirements']
    if not requirements or any(not r.path or r.path == 'none' for r in requirements):
        raise InputError('At least one requirements path is required.')
    if any(not r.path for r in references):
        raise InputError('Empty reference path; use none for optional keys.')
    return IndexData(1, meta['status'], tuple(references))


def render_index(data: IndexData) -> str:
    template = (Path(__file__).resolve().parents[1] / 'templates/index.md').read_text(encoding='utf-8')
    rows = '\n'.join(f'| {r.kind} | `{r.path}` | {r.purpose} |' for r in data.references if r.kind != 'document')
    text = template.replace('{{references}}', rows).replace('status: needs-review', 'status: ' + data.status)
    topics = '\n'.join(f'| `{r.path}` | {r.purpose} |' for r in data.references if r.kind == 'document')
    text = text.replace('## 초기화 확인 사항', topics + '\n\n## 초기화 확인 사항') if topics else text
    parse_index(text)
    return text


def update_index_reference(text: str, kind: str, path: str) -> str:
    if kind not in OPTIONAL_KEYS or any(c in path for c in '\r\n|`'):
        raise InputError('Invalid reference update.')
    parse_index(text)
    pattern = rf'(?m)^(\|[ \t]*{re.escape(kind)}[ \t]*\|[ \t]*`?)[^|`\r\n]+(`?[ \t]*\|[^\r\n]*)(\r?)$'
    changed, count = re.subn(pattern, lambda m: m[1] + path + m[2] + m[3], text)
    if count != 1:
        raise InputError('Reference row must be unique.')
    parse_index(changed)
    return changed


def local_links(text: str) -> tuple[str, ...]:
    text = re.sub(r'(?ms)^\s*(`{3,}|~{3,})[^\n]*\n.*?^\s*\1\s*$', '', text)
    text = re.sub(r'(`+).*?\1', '', text, flags=re.S)
    definitions = {}
    def definition(match):
        definitions[' '.join(match[1].lower().split())] = match[2].strip('<>')
        return ''
    text = re.sub(r'(?m)^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>]+>|\S+)[^\n]*$', definition, text)
    targets = []
    consumed = 0
    for match in re.finditer(r'!?\[([^\]\n]*)\]', text):
        if match.start() < consumed:
            continue
        end = match.end()
        value = None
        if text[end:end + 1] == '(':
            cursor, depth, chars = end + 1, 0, []
            while cursor < len(text) and text[cursor] in ' \t':
                cursor += 1
            if text[cursor:cursor + 1] == '<':
                closing = text.find('>', cursor + 1)
                if closing >= 0:
                    value = text[cursor + 1:closing]
            else:
                while cursor < len(text):
                    char = text[cursor]
                    if char == '\\' and cursor + 1 < len(text):
                        chars.append(text[cursor + 1])
                        cursor += 2
                        continue
                    if char == ')' and depth == 0:
                        value = ''.join(chars)
                        break
                    if char.isspace() and depth == 0:
                        value = ''.join(chars)
                        break
                    depth += (char == '(') - (char == ')')
                    chars.append(char)
                    cursor += 1
        else:
            ref = re.match(r'\[([^\]]*)\]', text[end:])
            label = (ref[1] if ref and ref[1] else match[1])
            value = definitions.get(' '.join(label.lower().split()))
            if ref:
                consumed = end + len(ref[0])
        if value:
            if re.match(r'^[A-Za-z][A-Za-z0-9+.-]+:', value) or value.startswith('//'):
                continue
            path = value.split('#', 1)[0].split('?', 1)[0]
            if path:
                targets.append(unquote(path))
    return tuple(targets)


def handoff_sections(text: str) -> dict[str, str]:
    parts = re.split(r'(?m)^## (.+)\s*$', text)
    sections = dict(zip(parts[1::2], parts[2::2]))
    if any(k not in sections or not sections[k].strip() for k in HANDOFF_SECTIONS) or '{{' in text:
        raise InputError('Handoff requires all populated sections.')
    try:
        moment = datetime.fromisoformat(sections['작성 시점'].strip())
        if moment.utcoffset() is None:
            raise ValueError
    except ValueError:
        raise InputError('Handoff timestamp requires ISO 8601 with timezone.') from None
    definitions = '\n'.join(re.findall(r'(?m)^ {0,3}\[[^\]]+\]:[^\n]+$', text))
    if not local_links(sections['관련 원본'] + '\n' + definitions):
        raise InputError('Handoff requires at least one local source link in the evidence section.')
    return sections
