# claudIA

Personal Claude Code configuration and custom skills.

## What's here

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Global Claude instructions (tool preferences, behaviors) |
| `settings.json` | Claude Code settings — hooks, plugins, marketplaces |
| `skills/` | Custom Claude skills |
| `install.sh` | Sets up symlinks from `~/.claude/` to this repo |

## Setup on a new machine

```bash
git clone https://github.com/aryan-curiel/claudIA.git ~/Development/Projects/claudIA
cd ~/Development/Projects/claudIA
chmod +x install.sh
./install.sh
```

`install.sh` symlinks `CLAUDE.md`, `settings.json`, and every dir inside `skills/` into `~/.claude/`. Existing files are backed up with a timestamp before being replaced.

## Adding a custom skill

```bash
mkdir skills/my-skill
# Create skills/my-skill/SKILL.md with the skill definition
./install.sh   # links it into ~/.claude/skills/my-skill
```

Claude Code picks up skills in `~/.claude/skills/` automatically.

## Workflow

Edit files here → commit & push → on another machine: `git pull && ./install.sh`.
