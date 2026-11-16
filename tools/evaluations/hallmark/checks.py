"""Conservative checks of recorded evidence, not a model-based judge."""
import re
import json


def redact(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if re.search(r'credential|password|secret|bearer|(?:^|_)token$', k, re.I)
                else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        if value.lstrip().startswith(('{', '[')):
            try: return json.dumps(redact(json.loads(value)), ensure_ascii=False)
            except ValueError: pass
        value = re.sub(r'(https?://)[^\s/@]+:[^\s/@]+@', r'\1[REDACTED]@', value)
        return re.sub(r'(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+', r'\1[REDACTED]', value)
    return value


def changed_paths(before, after):
    return sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))


def unexpected_changes(before, after, allowed):
    return [p for p in changed_paths(before, after)
            if not any(p.startswith(a) if a.endswith('/') else p == a for a in allowed)]


def completed_commands(events):
    return [e['item'] for e in events if e.get('type') == 'item.completed'
            and e.get('item', {}).get('type') == 'command_execution']


def skill_read_commands(events, skill):
    pattern = re.compile(r'(?:Get-Content|\bcat\b|\bread_text\b|\bsed\b)', re.I)
    needle = skill + '/SKILL.md'
    return [item['command'] for item in completed_commands(events)
            if item.get('exit_code') == 0
            and needle.lower() in item.get('command', '').replace('\\', '/').lower()
            and re.search(r'(?m)^name:\s*' + re.escape(skill) + r'\s*$', item.get('aggregated_output', ''))
            and pattern.search(item.get('command', ''))]


def render_status(events):
    items = [i for i in completed_commands(events)
             if 'sloplint' in i.get('command', '') and '--render' in i.get('command', '')]
    if not items:
        return 'NOT_RUN'
    # A zero process exit is not proof that Chromium rendered successfully.
    return 'FAIL' if items[-1].get('exit_code') != 0 else 'NEEDS_REPORT_REVIEW'


def unapproved_product_turns(turns):
    return [n for n, turn in enumerate(turns, 1) if not turn['approved']
            and any(is_product_path(p) for p in turn['changed'])]


def is_product_path(path):
    parts = path.split('/')
    if parts[0].startswith('.') or parts[0] in ('docs', 'tests') or '.hallmark' in parts:
        return False
    return (path.startswith(('site/', 'src/', 'app/', 'web/', 'scripts/', 'assets/')) or
            path.endswith(('.html', '.css', '.js', '.ts', '.tsx', '.jsx', '.svg', '.py')) or
            path in ('package.json', 'package-lock.json'))


def changed_product_files(before, after):
    return [path for path in changed_paths(before, after) if is_product_path(path)]
