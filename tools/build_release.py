"""Build the versioned consumer folder and ZIP from the install asset allowlist."""
import argparse
import io
import json
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'kit'))

from mycodex_lib.install import _source, atomic_create
from mycodex_lib.model import KIT_VERSION, REQUIRED_ASSETS
from mycodex_lib.paths import is_reparse, read_asset


def release_files() -> dict[str, bytes]:
    manual = (ROOT / 'README.md').read_text(encoding='utf-8')
    if manual.count('<!-- source-only:start -->') != 1 or manual.count('<!-- source-only:end -->') != 1:
        raise ValueError('README must have exactly one source-only block.')
    manual = re.sub(r'(?ms)^<!-- source-only:start -->\n.*?^<!-- source-only:end -->\n\n?', '', manual)
    if '<!-- source-only:' in manual:
        raise ValueError('README source-only block is malformed.')
    files = {'README.md': manual.encode('utf-8'), 'CHANGELOG.md': read_asset(ROOT / 'CHANGELOG.md')}
    for destination in sorted(REQUIRED_ASSETS):
        source = _source(ROOT / 'kit', destination)
        files['kit/' + source.relative_to(ROOT / 'kit').as_posix()] = read_asset(source)
    return files


def archive_bytes(name: str, files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, content in sorted(files.items()):
            info = ZipInfo(name + '/' + relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content, compresslevel=9)
    return buffer.getvalue()


def folder_matches(folder: Path, files: dict[str, bytes]) -> bool:
    if is_reparse(folder) or not folder.is_dir():
        return False
    directories = {parent.as_posix() for name in files for parent in Path(name).parents if parent != Path('.')}
    found = {}
    for path in folder.rglob('*'):
        relative = path.relative_to(folder).as_posix()
        if is_reparse(path):
            return False
        if path.is_dir():
            if relative not in directories:
                return False
        elif path.is_file():
            found[relative] = path.read_bytes()
        else:
            return False
    return found == files


def build_release(output: Path) -> dict[str, str | int]:
    files = release_files()
    name = f'MyCodexSetting-{KIT_VERSION}'
    zipped = archive_bytes(name, files)
    output = output.resolve()
    folder, archive = output / name, output / (name + '.zip')
    if (folder.exists() or is_reparse(folder)) and not folder_matches(folder, files):
        raise ValueError('RELEASE_CONFLICT: existing version folder differs; review it without overwriting.')
    if archive.exists() or is_reparse(archive):
        if is_reparse(archive) or not archive.is_file() or archive.read_bytes() != zipped:
            raise ValueError('RELEASE_CONFLICT: existing version ZIP differs; review it without overwriting.')
    output.mkdir(parents=True, exist_ok=True)
    if not folder.exists():
        with TemporaryDirectory(prefix='.mycodex-release-', dir=output) as temporary:
            staged = Path(temporary) / name
            staged.mkdir()
            for relative, content in files.items():
                path = staged / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            if folder.exists() or is_reparse(folder):
                raise ValueError('RELEASE_CONFLICT: destination appeared during staging; retry after review.')
            os.rename(staged, folder)
    if not archive.exists():
        atomic_create(archive, zipped)
    return {'version': KIT_VERSION, 'folder': str(folder), 'archive': str(archive), 'files': len(files)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    try:
        print(json.dumps(build_release(args.output), ensure_ascii=True))
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    except OSError:
        print('RELEASE_IO_ERROR: check output paths and permissions; success is not claimed.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
