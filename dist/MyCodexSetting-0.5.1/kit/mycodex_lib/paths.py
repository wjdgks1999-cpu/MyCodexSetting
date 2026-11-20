from pathlib import Path, PureWindowsPath
import re
import stat
from urllib.parse import unquote
from .model import InputError


def resolve_root(target: str) -> Path:
    path = Path(target).resolve(strict=True)
    if not path.is_dir():
        raise InputError('Target must be an existing directory.')
    return path


def is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)


def checked_path(root: Path, relative: str, *, for_write: bool = False) -> Path:
    if not isinstance(relative, str) or not relative:
        raise InputError('Expected a nonempty relative path.')
    name = unquote(relative).replace('\\', '/')
    win = PureWindowsPath(name)
    if win.drive or win.root or name.startswith('/') or any(ord(c) < 32 for c in name):
        raise InputError('Absolute or control-character paths are not allowed.')
    parts = name.split('/')
    for part in parts:
        if any(c in part for c in ':*?<>|') or (part not in ('.', '..', '') and part.rstrip(' .') != part):
            raise InputError('Unsupported path component.')
        if re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part):
            raise InputError('Reserved device path.')
    lexical = root.joinpath(*parts)
    try:
        resolved = lexical.resolve()
        resolved.relative_to(root.resolve())
    except (ValueError, RuntimeError):
        raise InputError('Path must remain inside the project root.') from None
    if for_write:
        cursor = root
        for part in parts:
            cursor = cursor / part
            if is_reparse(cursor):
                raise InputError('Writing through a symlink or junction is not supported.')
        return lexical
    return resolved


def read_asset(path: Path) -> bytes:
    """Read a kit text asset independently of Git's LF/CRLF conversion."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8-sig')
    except UnicodeError:
        raise InputError('Document must be UTF-8 text.') from None
