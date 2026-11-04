from dataclasses import dataclass
from pathlib import Path
from typing import Literal

KIT_VERSION = '0.1.0'
SCHEMA_VERSION = 1
OPTIONAL_KEYS = ('decisions', 'active-spec', 'active-plan', 'active-ledger', 'latest-handoff')
HANDOFF_SECTIONS = ('목표', '작성 시점', '관련 원본', '작업 상태', '검증', '다음 행동', '재확인 사항')
REQUIRED_ASSETS = {
    '.mycodex/mycodex.py', '.mycodex/context-policy.md',
    *('.mycodex/mycodex_lib/' + n + '.py' for n in ('__init__', 'model', 'paths', 'documents', 'validation', 'install', 'handoff')),
    *('.mycodex/templates/' + n + '.md' for n in ('AGENTS', 'index', 'decision', 'handoff')),
    *('.agents/skills/' + n + '/' + f for n in ('project-init', 'session-handoff') for f in ('SKILL.md', 'agents/openai.yaml')),
}


class InputError(ValueError):
    """An input failed a documented constraint; never include its contents."""


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Literal['error', 'warning']
    path: str
    message: str


@dataclass(frozen=True)
class DocRef:
    kind: str
    path: str
    purpose: str


@dataclass(frozen=True)
class IndexData:
    schema_version: int
    status: str
    references: tuple[DocRef, ...]


@dataclass(frozen=True)
class FileChange:
    path: str
    action: Literal['create', 'preserve', 'skip', 'conflict']
    content: bytes | None


@dataclass(frozen=True)
class InstallPlan:
    root: Path
    changes: tuple[FileChange, ...]
    findings: tuple[Finding, ...]
