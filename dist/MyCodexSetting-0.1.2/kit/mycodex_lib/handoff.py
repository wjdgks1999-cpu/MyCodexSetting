"""Record a verified-shape snapshot without overwriting history."""
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from .documents import handoff_sections, parse_index, update_index_reference
from .install import atomic_create, guarded_update
from .model import InputError
from .paths import checked_path, read_text
from .validation import link_findings, validate


class HandoffWriteError(OSError):
    def __init__(self, snapshot: Path | None):
        super().__init__('Handoff write failed; the latest pointer was not advanced.')
        self.snapshot = snapshot


def record_handoff(root: Path, draft: Path, *, now: datetime | None = None) -> Path:
    root = root.resolve()
    try:
        draft_name = draft.absolute().relative_to(root).as_posix()
    except ValueError:
        raise InputError('Draft must be inside the project.') from None
    source = checked_path(root, draft_name)
    content = read_text(source)
    handoff_sections(content)
    index = checked_path(root, '.context/index.md', for_write=True)
    before = index.read_bytes()
    index_text = before.decode('utf-8-sig')
    parse_index(index_text)
    errors = [f for f in validate(root) if f.severity == 'error']
    if errors:
        raise InputError('Fix structural validation errors before recording a handoff.')
    now = now or datetime.now().astimezone()
    if now.utcoffset() is None:
        raise InputError('Recording timestamp must include timezone.')
    folder = checked_path(root, '.context/handoffs', for_write=True)
    name = now.strftime('%Y-%m-%d-%H%M%S')
    relative = f'.context/handoffs/{name}.md'
    if link_findings(root, relative, content):
        raise InputError('Fix local snapshot links before recording.')
    folder.mkdir(parents=True, exist_ok=True)
    while True:
        output = checked_path(root, relative, for_write=True)
        updated = update_index_reference(index_text, 'latest-handoff', relative).encode('utf-8')
        try:
            atomic_create(output, content.encode('utf-8'))
            break
        except FileExistsError:
            relative = f'.context/handoffs/{name}-{uuid4().hex[:8]}.md'
        except OSError:
            raise HandoffWriteError(None) from None
    try:
        checked_path(root, '.context/index.md', for_write=True)
        guarded_update(index, updated, before)
    except InputError as error:
        raise InputError(str(error) + ' Snapshot retained at ' + relative) from None
    except OSError:
        raise HandoffWriteError(output) from None
    return output
