---
name: import-skills
description: Discover skills in a GitHub repo, let the user pick which ones to include, and register them in catalog.toml.
---

# Import Skills from GitHub

Browse a remote GitHub repository for skills, select which ones to add, and register them in `catalog.toml` so `claudia` can install them.

## Invocation

```
/import-skills <github-url> [ref]
```

- `<github-url>` — HTTPS URL to a GitHub repository (e.g. `https://github.com/owner/repo`)
- `[ref]` — optional branch, tag, or commit SHA (omits `ref` from catalog if not supplied, tracking default branch)

---

## Step 1 — Parse the URL

Extract `owner` and `repo` from the URL. Normalize by stripping trailing slashes and `.git`.

Examples:
- `https://github.com/acme/claude-skills` → owner=`acme`, repo=`claude-skills`
- `https://github.com/acme/claude-skills.git` → same
- `https://github.com/acme/claude-skills/tree/main` → owner=`acme`, repo=`claude-skills`, ref=`main` (use as default ref if none was passed)

If the URL is not a `github.com` URL, tell the user only GitHub is supported and stop.

---

## Step 2 — List all files in the repo tree via GitHub API

Fetch the full recursive tree:

```
GET https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1
```

Use `ref` from the URL or the argument, defaulting to `HEAD` if neither is present.

Use WebFetch to call this URL. The response is JSON with a `tree` array. Each entry has a `path` and `type` (`blob` or `tree`).

Filter for entries where `type == "blob"` and the path ends with `SKILL.md` (case-sensitive). These are the candidate skills.

If the API returns `"truncated": true`, note it to the user — very large repos may be incomplete.

If the tree is empty or no `SKILL.md` files are found, report that to the user and stop.

---

## Step 3 — Fetch and parse each SKILL.md

For each candidate path, fetch the raw file content:

```
GET https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path_to_SKILL.md}
```

Parse the YAML frontmatter block at the top of the file (between `---` markers):

```
---
name: skill-name
description: Human-readable description
---
```

Extract:
- `name` — skill identifier (fall back to the directory name if missing)
- `description` — one-line description (fall back to empty string if missing)

The skill's **directory path** within the repo is the parent directory of the `SKILL.md` file (e.g. if `SKILL.md` is at `skills/my-skill/SKILL.md`, the path is `skills/my-skill`).

---

## Step 4 — Show discovered skills and ask the user to choose

Present a numbered list of discovered skills in this format:

```
Found N skill(s) in https://github.com/{owner}/{repo}:

  1. skill-name — Description from frontmatter
     path: skills/skill-name

  2. another-skill — Another description
     path: tools/another-skill

  ...

Which skills do you want to add to catalog.toml?
Enter numbers separated by commas (e.g. 1,3), "all" to add all, or "none" to cancel:
```

Wait for the user's response before proceeding.

---

## Step 5 — Check for conflicts with existing catalog entries

Read `claudia-skills/catalog.toml` from the claudIA repo root. Look for existing `[[remote]]` entries with the same `name` as any selected skill.

If a conflict exists:
- Tell the user: `"Skill 'X' is already in catalog.toml (from {existing_repo}). Overwrite? [y/N]"`
- Only overwrite if the user confirms.

---

## Step 6 — Write selected skills to catalog.toml

For each selected skill (after conflict resolution), append a `[[remote]]` block to `claudia-skills/catalog.toml`:

```toml
[[remote]]
name = "{name}"
description = "{description}"
repo = "https://github.com/{owner}/{repo}"
path = "{skill_dir_path}"
ref = "{ref}"   # omit this line entirely if no ref was specified
```

Locate `catalog.toml` by walking up from the current directory to find the claudIA repo root (the directory that contains both `skills/` and `claudia-skills/`). If not found, fall back to writing relative to the git repo root.

After writing, show a summary:

```
Added to catalog.toml:
  ✓ skill-name  (https://github.com/owner/repo / skills/skill-name)
  ✓ another-skill  (https://github.com/owner/repo / tools/another-skill)

Run `claudia` to install them.
```

---

## Notes

- Do not clone the repo. Use the GitHub API and raw content URLs only.
- Do not install skills — only register them in catalog.toml. The user runs `claudia` to install.
- Preserve all existing content in catalog.toml exactly. Only append new `[[remote]]` blocks.
- If a skill dir path is the repo root (i.e. `SKILL.md` is at the root), use `"."` as the path.
