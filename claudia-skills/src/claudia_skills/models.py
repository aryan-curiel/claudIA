from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class SkillSource(Enum):
    LOCAL = auto()
    REMOTE = auto()


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    source: SkillSource
    source_path: Path
    repo: str | None = None
    repo_path: str | None = None
    ref: str | None = None


@dataclass
class InstallResult:
    skill: Skill
    success: bool
    message: str
    already_existed: bool = False
