## Tool preferences
- Always use `rg` instead of `grep` for all file searches
- Use `rg -l` instead of `grep -l` when only listing matching files
- Use `rg -n` for line numbers (it's on by default in rg, just be explicit)
- Never fall back to `grep` even if a pattern seems grep-specific — translate it to rg syntax
- Only if the `rg` fails and you can't find an option, then you can fallback to `grep`
