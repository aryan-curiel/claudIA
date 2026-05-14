import subprocess
from pathlib import Path

from claudia_skills.models import InstallResult, Skill, SkillSource

CACHE_ROOT = Path.home() / ".claudia" / "cache"


def detect_target_dir(start: Path | None = None) -> Path:
    current = start or Path.cwd()
    while True:
        if (current / ".claude").is_dir():
            return current / ".claude" / "skills"
        parent = current.parent
        if parent == current:
            break
        current = parent
    return Path.home() / ".claude" / "skills"


def is_installed(skill: Skill, target_dir: Path) -> bool:
    link = target_dir / skill.name
    if not link.is_symlink():
        return False
    try:
        return link.resolve() == skill.source_path.resolve()
    except OSError:
        return False


def install_skill(skill: Skill, target_dir: Path, force: bool = False) -> InstallResult:
    try:
        if skill.source is SkillSource.REMOTE:
            resolved_src = _ensure_repo_cached(skill)
        else:
            resolved_src = skill.source_path
        return _symlink(skill, resolved_src, target_dir / skill.name, force)
    except Exception as exc:  # noqa: BLE001
        return InstallResult(skill=skill, success=False, message=str(exc))


def _ensure_repo_cached(skill: Skill) -> Path:
    assert skill.repo and skill.repo_path  # noqa: S101
    repo_slug = skill.repo.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    cache_dir = CACHE_ROOT / repo_slug
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    def _git(*args: str) -> None:
        result = subprocess.run(["git", *args], capture_output=True, text=True)  # noqa: S603, S607
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())

    if not (cache_dir / ".git").exists():
        clone_args = ["clone"]
        if skill.ref:
            clone_args += ["--branch", skill.ref, "--single-branch"]
        clone_args += [skill.repo, str(cache_dir)]
        _git(*clone_args)
    else:
        _git("-C", str(cache_dir), "fetch", "origin")
        if skill.ref:
            _git("-C", str(cache_dir), "checkout", skill.ref)
        else:
            _git("-C", str(cache_dir), "pull")

    source_path = cache_dir / skill.repo_path
    if not source_path.is_dir():
        raise RuntimeError(f"Path {skill.repo_path!r} not found in cloned repo")
    return source_path


def _symlink(skill: Skill, src: Path, dst: Path, force: bool = False) -> InstallResult:
    if dst.is_symlink():
        try:
            already_points_here = dst.resolve() == src.resolve()
        except OSError:
            already_points_here = False
        if already_points_here and not force:
            return InstallResult(skill=skill, success=True, message="already installed", already_existed=True)
        dst.unlink()
    elif dst.exists():
        return InstallResult(
            skill=skill,
            success=False,
            message=f"{dst} exists and is not a symlink — remove it manually",
        )
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(src)
    return InstallResult(skill=skill, success=True, message=f"linked → {src}")
