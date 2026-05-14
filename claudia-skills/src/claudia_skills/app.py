import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, Log, SelectionList
from textual.widgets.selection_list import Selection

from claudia_skills.installer import detect_target_dir, install_skill, is_installed
from claudia_skills.models import Skill, SkillSource
from claudia_skills.registry import all_skills

_SEP_PREFIX = "__sep__"


class SkillInstallerApp(App[None]):
    CSS = """
    Screen {
        background: $surface;
    }
    #target-label {
        margin: 1 2 0 2;
        color: $text-muted;
    }
    #skill-list {
        height: 1fr;
        border: round $primary;
        margin: 1;
    }
    #button-bar {
        height: 3;
        align: center middle;
        margin: 0 1;
    }
    #button-bar Button {
        margin: 0 1;
    }
    #log-panel {
        height: 10;
        border: round $accent;
        margin: 0 1 1 1;
        display: none;
    }
    #log-panel.visible {
        display: block;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+a", "select_all", "Select All"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._target_dir: Path = detect_target_dir()
        self._skills: list[Skill] = all_skills()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Label(f"Target: {self._target_dir}", id="target-label")
        yield Vertical(
            _build_selection_list(self._skills, self._target_dir),
            Horizontal(
                Button("Install Selected", id="btn-install", variant="primary"),
                Button("Cancel", id="btn-cancel", variant="default"),
                id="button-bar",
            ),
            Log(id="log-panel", max_lines=200),
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.exit()
        elif event.button.id == "btn-install":
            self._start_install()

    def action_select_all(self) -> None:
        self.query_one(SelectionList).select_all()

    def _start_install(self) -> None:
        selection: SelectionList = self.query_one(SelectionList)
        selected_names = [v for v in selection.selected if not str(v).startswith(_SEP_PREFIX)]
        if not selected_names:
            return
        self.query_one("#log-panel").add_class("visible")
        self.query_one("#btn-install").disabled = True
        self.run_worker(self._install_worker(selected_names), exclusive=True)

    async def _install_worker(self, names: list[str]) -> None:
        log: Log = self.query_one("#log-panel", Log)
        skill_map = {s.name: s for s in self._skills}
        self._target_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            skill = skill_map[name]
            log.write_line(f"  …  {name}")
            result = await asyncio.to_thread(install_skill, skill, self._target_dir)
            if result.already_existed:
                log.write_line(f"  ✓  {name} — already installed")
            elif result.success:
                log.write_line(f"  ✓  {name} — {result.message}")
            else:
                log.write_line(f"  ✗  {name} — {result.message}")
        log.write_line("Done.")
        self.query_one("#btn-install").disabled = False


def _build_selection_list(skills: list[Skill], target_dir: Path) -> SelectionList:
    local = [s for s in skills if s.source is SkillSource.LOCAL]
    remote = [s for s in skills if s.source is SkillSource.REMOTE]
    items: list[Selection] = []

    if local:
        items.append(Selection("── Local ─────────────────────────────", f"{_SEP_PREFIX}local", disabled=True))
        for skill in local:
            installed = is_installed(skill, target_dir)
            label = f"{'[installed] ' if installed else ''}{skill.name:<20} {skill.description}"
            items.append(Selection(label, skill.name, initial_state=installed))

    if remote:
        items.append(Selection("── Remote ────────────────────────────", f"{_SEP_PREFIX}remote", disabled=True))
        for skill in remote:
            installed = is_installed(skill, target_dir)
            label = f"{'[installed] ' if installed else ''}{skill.name:<20} {skill.description}"
            items.append(Selection(label, skill.name, initial_state=installed))

    return SelectionList(*items, id="skill-list")
