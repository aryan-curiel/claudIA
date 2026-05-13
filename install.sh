#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing claudIA config from $REPO_DIR..."

backup() {
  local target="$1"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    local backup="${target}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "  Backing up $target → $backup"
    mv "$target" "$backup"
  fi
}

link() {
  local src="$1"
  local dst="$2"
  backup "$dst"
  ln -sf "$src" "$dst"
  echo "  Linked: $dst → $src"
}

# CLAUDE.md
link "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"

# settings.json
link "$REPO_DIR/settings.json" "$CLAUDE_DIR/settings.json"

# Custom skills — link each skill dir into ~/.claude/skills/
mkdir -p "$CLAUDE_DIR/skills"
for skill_dir in "$REPO_DIR/skills"/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  link "$skill_dir" "$CLAUDE_DIR/skills/$skill_name"
done

echo ""
echo "Done. Edit files in $REPO_DIR, push to git, and run this script on any machine to sync."
