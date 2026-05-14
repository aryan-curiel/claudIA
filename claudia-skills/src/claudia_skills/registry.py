import re
import tomllib
from pathlib import Path

from claudia_skills.models import Skill, SkillSource

# __file__ = claudia-skills/src/claudia_skills/registry.py
# parents[0] = claudia_skills/
# parents[1] = src/
# parents[2] = claudia-skills/
# parents[3] = claudIA/
_HERE = Path(__file__).resolve()
REPO_ROOT = _HERE.parents[3]
LOCAL_SKILLS_DIR = REPO_ROOT / "skills"
CATALOG_PATH = _HERE.parents[2] / "catalog.toml"
CACHE_ROOT = Path.home() / ".claudia" / "cache"

if not (REPO_ROOT / "skills").is_dir():
    raise RuntimeError(f"Expected skills/ at {REPO_ROOT} — is the script installed from the claudIA repo?")



def _parse_frontmatter(text: str) -> dict[str, str]:
    match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def discover_local_skills() -> list[Skill]:
    skills: list[Skill] = []
    if not LOCAL_SKILLS_DIR.is_dir():
        return skills
    for entry in sorted(LOCAL_SKILLS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            fm = _parse_frontmatter(skill_md.read_text())
        except OSError:
            continue
        name = fm.get("name", entry.name)
        description = fm.get("description", "")
        skills.append(
            Skill(
                name=name,
                description=description,
                source=SkillSource.LOCAL,
                source_path=entry,
            )
        )
    return skills


def load_remote_skills() -> list[Skill]:
    if not CATALOG_PATH.exists():
        return []
    try:
        data = tomllib.loads(CATALOG_PATH.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return []
    skills: list[Skill] = []
    for entry in data.get("remote", []):
        name = entry.get("name", "")
        if not name:
            continue
        repo = entry.get("repo", "")
        repo_path = entry.get("path", "")
        ref = entry.get("ref")
        repo_slug = repo.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
        source_path = CACHE_ROOT / repo_slug / repo_path
        skills.append(
            Skill(
                name=name,
                description=entry.get("description", ""),
                source=SkillSource.REMOTE,
                source_path=source_path,
                repo=repo,
                repo_path=repo_path,
                ref=ref,
            )
        )
    return skills


def all_skills() -> list[Skill]:
    local = discover_local_skills()
    remote = load_remote_skills()
    merged: dict[str, Skill] = {s.name: s for s in remote}
    for s in local:
        merged[s.name] = s
    local_names = {s.name for s in local}
    result = [s for s in merged.values() if s.name in local_names]
    result += [s for s in merged.values() if s.name not in local_names]
    return result
