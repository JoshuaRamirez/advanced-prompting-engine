# Release

Create a GitHub release for the advanced-prompting-engine package. Run `/pre-release` first.

## Arguments
- `$ARGUMENTS` — optional: version (e.g., "0.5.0"). If omitted, reads current version from pyproject.toml.

## Steps

### 1. Pre-flight
- If `$ARGUMENTS` is provided, use it as the version. Otherwise read from `pyproject.toml`.
- Verify git working tree is clean (excluding untracked files)
- Run `python3 -m pytest tests/ -q` — any failure is a blocker
- Verify CHANGELOG.md has a `## [x.y.z]` section AND a `[x.y.z]:` comparison link for this version

If any check fails, STOP and report.

### 2. Version Bump (only if $ARGUMENTS provided and differs from current)
- Update version in `pyproject.toml`
- Update `__version__` in `src/advanced_prompting_engine/__init__.py`
- Update `version` in `.claude-plugin/plugin.json` (marketplace manifest)
- If CHANGELOG.md has no section for this version, generate one from `git log --oneline v{previous}..HEAD`
- Add comparison link: `[x.y.z]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v{previous}...v{new}`
- Commit: `git commit -am "v{version}: <brief summary>"`

### 3. Push
```bash
git push origin main
```

### 4. Tag
```bash
git tag -a "v{version}" -m "Release v{version}"
git push origin "v{version}"
```

### 5. Create GitHub Release
Extract the CHANGELOG section between `## [x.y.z]` and the next `## [` header. Save to a temp file. Then:
```bash
gh release create "v{version}" --title "v{version}" --notes-file /tmp/release_notes.txt --latest
```

### 6. Verify
```bash
gh release view "v{version}" --json tagName,url,createdAt
```
Report: version, tag, release URL, commit hash.

### 7. Post-release
- PyPI: the `publish.yml` workflow triggers on release creation — publishes via OIDC trusted publisher automatically
- Plugin marketplace: the `.claude-plugin/plugin.json` version was updated in step 2 and pushed in step 3 — the marketplace picks up the new version from the repo
- Remind: `pip install -e ".[dev]"` to update local install

### Version files checklist (4 locations)
1. `pyproject.toml` → `version`
2. `src/advanced_prompting_engine/__init__.py` → `__version__`
3. `.claude-plugin/plugin.json` → `version`
4. `CHANGELOG.md` → section header + comparison link
