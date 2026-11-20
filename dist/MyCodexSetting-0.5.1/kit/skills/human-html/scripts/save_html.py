"""Save or check human-only HTML without returning its body to the caller."""
import argparse
from datetime import datetime
from html.parser import HTMLParser
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from uuid import uuid4


IGNORE_RULES = b'*\n!.gitignore\n!.ignore\n'


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.opened = set()
        self.closed = set()
        self.title = []
        self.in_title = False
        self.language = False
        self.charset = False
        self.viewport = False

    def handle_starttag(self, tag, attrs):
        self.opened.add(tag)
        attrs = dict(attrs)
        if tag == 'html':
            self.language = bool(attrs.get('lang'))
        if tag == 'title':
            self.in_title = True
        if tag == 'meta':
            self.charset |= (attrs.get('charset') or '').lower() in ('utf-8', 'utf8')
            self.viewport |= ((attrs.get('name') or '').lower() == 'viewport'
                              and 'width=device-width' in (attrs.get('content') or '').replace(' ', ''))

    def handle_endtag(self, tag):
        self.closed.add(tag)
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def validate_html(content: bytes) -> None:
    try:
        text = content.decode('utf-8-sig')
    except UnicodeError:
        raise ValueError('INVALID_ENCODING: provide UTF-8 HTML.') from None
    document = Document()
    try:
        document.feed(text)
        document.close()
    except (AssertionError, ValueError):
        raise ValueError('INVALID_HTML: malformed HTML declaration.') from None
    required = {'html', 'head', 'title', 'body'}
    if not (required <= document.opened and required <= document.closed
            and ''.join(document.title).strip() and document.language
            and document.charset and document.viewport):
        raise ValueError('INVALID_HTML: require html/lang, head, title, body, UTF-8 charset and viewport.')


def reject_reparse(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('UNSAFE_PATH: symlinks and junctions are not supported here.')


def output_folder(root: Path) -> Path:
    folder = root / '.human-docs'
    reject_reparse(folder)
    if folder.exists() and not folder.is_dir():
        raise ValueError('OUTPUT_CONFLICT: .human-docs must be a directory.')
    return folder


def prepare_ignores(folder: Path) -> None:
    # Preflight both files before creating either; preserve customized rules.
    for name in ('.gitignore', '.ignore'):
        path = folder / name
        reject_reparse(path)
        if path.exists() and (not path.is_file() or path.read_bytes().replace(b'\r\n', b'\n') != IGNORE_RULES):
            raise ValueError('IGNORE_CONFLICT: preserve and review the existing folder ignore file.')
    folder.mkdir(exist_ok=True)
    for name in ('.gitignore', '.ignore'):
        path = folder / name
        reject_reparse(path)
        try:
            with path.open('xb') as stream:
                stream.write(IGNORE_RULES)
        except FileExistsError:
            reject_reparse(path)
            if not path.is_file() or path.read_bytes().replace(b'\r\n', b'\n') != IGNORE_RULES:
                raise ValueError('IGNORE_CONFLICT: folder rules changed; no HTML was saved.') from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--name', help='Short topic using letters, numbers, underscores or hyphens.')
    mode.add_argument('--check', help='Check one .human-docs/*.html file without printing its body.')
    args = parser.parse_args(argv)
    try:
        root = Path(args.target).resolve(strict=True)
        if not root.is_dir():
            raise ValueError('INVALID_TARGET: provide a project directory.')
        folder = output_folder(root)
        if args.check is not None:
            parts = PurePosixPath(args.check.replace('\\', '/')).parts
            if (len(parts) != 2 or parts[0] != '.human-docs'
                    or not re.fullmatch(r'[\w.-]+\.html', parts[1])):
                raise ValueError('INVALID_PATH: check a direct .human-docs/*.html file only.')
            path = folder / parts[1]
            reject_reparse(path)
            validate_html(path.read_bytes())
            print('HTML structure checked; visual layout and factual accuracy need separate review.')
            return 0
        if not re.fullmatch(r'[\w-]{1,80}', args.name):
            raise ValueError('INVALID_NAME: use 1-80 letters, numbers, underscores or hyphens.')
        content = sys.stdin.buffer.read()
        validate_html(content)
        prepare_ignores(folder)
        while True:
            name = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            path = folder / f'{name}-{args.name}-{uuid4().hex[:8]}.html'
            try:
                with path.open('xb') as stream:
                    stream.write(content)
                break
            except FileExistsError:
                continue
        print(path.relative_to(root).as_posix())
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print('IO_ERROR: check the target, file types and permissions; success is not claimed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
