---
name: memory-review
description: Weekly memory review - show new [inferred] memories for Taylor to confirm, correct or delete, and keep MEMORY.md and USER.md tidy.
metadata: { "openclaw": { "emoji": "🧠" } }
---

# Memory review (Sunday 17:00, or on request)

Taylor must always be able to see, correct and delete what Jarvis remembers.

1. Find items added or changed in the last 7 days in `MEMORY.md`, `USER.md`
   and `DREAMS.md` (use `git log -p --since="7 days ago"` in the workspace
   if it is a git repo; otherwise compare against the `Last reviewed` date
   at the top of MEMORY.md).
2. List the **`[inferred]`** items first, numbered, one line each. Then give
   a count of new `[stated]` items.
   ```
   New things I've inferred (reply e.g. "keep 1, delete 2, fix 3: ..."):
   1. You revise better before 21:00 than after. [inferred]
   2. You usually leave for college at 08:20. [inferred]
   Plus 4 new stated facts. Say "show stated" to see them.
   ```
3. Apply the replies:
   - **keep**: change the tag to `[stated]` (Taylor confirmed it).
   - **fix**: rewrite the line, tag it `[stated]`.
   - **delete**: remove the line. If it came from dreaming, also run
     `openclaw memory forget` for that session if Taylor asks for full removal.
4. Update `Last reviewed: DD/MM/YYYY` at the top of MEMORY.md.

## Rules

- Never put behavioural patterns about Taylor into a cloud-hosted research
  sub-agent's context.
- Sensitive items (health, family, money): mention that they exist, but
  don't read them aloud on voice.
