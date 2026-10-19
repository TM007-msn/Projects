# 13 · Files, notes and your PC (Phase 3)

**What:** permission-controlled access to local files, Obsidian notes, and selected PC capabilities.
**Priority:** local files 9/10, notes/Obsidian 7/10, PC control 7/10. These sit in Phase 3 because the accountability loop and voice deliver more value first.

## Obsidian

OpenClaw bundles an **`obsidian`** skill, and `openclaw wiki` has Obsidian helpers.

1. Sync your vault to the OptiPlex. Syncthing is free and self-hosted: install it on both machines and share only the vault folder.
2. Point the skill at that folder (see `openclaw skills info obsidian` for its config key) and add the path to `AGENTS.md` → Tools.
3. Rules for `AGENTS.md`:
   - Jarvis may **create** notes in `Jarvis/` inside the vault and **append** to daily notes.
   - Editing or deleting your existing notes needs approval.
   - Research results can be copied into `Jarvis/Research/` when you ask ("save that to Obsidian").

## Files on the OptiPlex

- The workspace (`~/.openclaw/workspace`) is Jarvis's home. Everything there is fair game.
- For other folders (e.g. a synced `~/College` directory), list them in `AGENTS.md` → Tools as **read-only**, unless you say otherwise.
- The workspace is the default working directory, **not a sandbox**. Exec approvals (Telegram buttons) are what stop destructive commands. Keep `tools.exec` approval mode on its default, which asks for anything not allowlisted.

## Your Windows PC as a node

OpenClaw's **node host** lets the Gateway run selected commands on another machine, each one approval-gated.

```powershell
# On the PC (Node 24+):
npm i -g openclaw
openclaw node install      # pairs with the Gateway over Tailscale; approve the pairing on the OptiPlex
```

Then on the OptiPlex: `openclaw nodes list` / `openclaw devices`. Useful, safe starters:
- "Is my PC on?", "What's taking up space on D:?"
- open a file or URL on the PC
- run a specific script you've allowlisted (e.g. a backup)

Keep **computer-use / screen control** off until there's a clear need. It's the highest-risk capability.

## Coding tools

The bundled `coding-agent` / `github` skills work, but they're priority 6. Use Claude Code directly for coding, and only give Jarvis read access to repos for status questions ("did CI pass on my NEA repo?").

## Verify

- [ ] "Save that to Obsidian" → the note appears in `Jarvis/` and syncs to your PC
- [ ] "Delete my Economics notes" → it asks for approval, and declining leaves the files alone
- [ ] "Is my PC on?" answers correctly
