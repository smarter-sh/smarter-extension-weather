---
name: smarter-extension-git-commits
description: Use whenever the user asks you to "write a git commit" (or a commit message, or the git add) in a Smarter Extension repository (smarter-extension-<slug>). Covers the never-execute rule, authorship, the multiple -m command format, choosing the conventional-commit type (which decides whether and how semantic-release releases the extension), the 72-character header, and how thorough the body must be.
---

# Smarter Extension Git Commits

## The rule: write, never execute

"Write a git commit", in any wording or tone, means **output the command as text**. It never
means run it. Frustrated or emphatic phrasing still asks for the command text.

- Never execute `git commit`, `git add`, `git reset`, `git restore --staged`, `git push`,
  `git tag`, `git stash`, or any other git command that writes. The user stages, commits and
  pushes.
- Read-only commands (`git status`, `git diff`, `git log`) are fine for working out what changed.
- Don't volunteer commit messages. Write one only when asked.

## Authorship

The repository's `CLAUDE.md` says who the author is and who the co-author is, in its
"Commit authorship" section. Follow it exactly. If it says nothing, the user is the author (no
`--author`), and the last `-m` is `Co-authored-by: Claude <noreply@anthropic.com>`.

## Command format

Exactly one `git commit` command in one code block, here with you as the author:

```console
git commit --author="Claude <noreply@anthropic.com>" \
  -m "<type>: <subject>" \
  -m "<body paragraph>" \
  -m "<body paragraph or bullet list>" \
  -m "Co-authored-by: <the co-author from CLAUDE.md>"
```

- One `-m` per paragraph. A bullet list goes in a single `-m`, with real newlines between bullets.
- No heredoc, no `-F`, and no `git add` in the same block. When the user asks for the `git add`
  too, write it as a separate block that lists the paths explicitly.
- Avoid backticks, `$` and `!` inside the double quotes. The user's shell is zsh, where `!` in
  double quotes is history expansion and aborts the whole command. Reword instead.
- **Never write a CI skip instruction anywhere in the message**, not even to describe one
  (`[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `skip-checks: true`). GitHub would then
  start no workflow for the push: no tests, and **no release**. Write "semantic-release's skip tag"
  instead.

## Type: it decides the release

semantic-release releases from every push to `main` (see `smarter-extension-release`):

| Type                                                        | Release |
| ----------------------------------------------------------- | ------- |
| `feat`                                                      | minor   |
| `fix`, `perf`                                               | patch   |
| `BREAKING CHANGE:` paragraph in the body                    | major   |
| `docs`, `test`, `style`, `refactor`, `ci`, `build`, `chore` | none    |

- `feat` is for a new tool, a new setting, or a new capability of a tool that administrators or
  LLMs would see as new. It's rare. When in doubt, it is `fix`.
- `fix` covers defects and shortcomings of what exists, including a dependency pin that breaks
  installs, and better error messages for the LLM.
- `perf` is for speed and caching (e.g. adding `cache_ttl`).
- A change only to tests, CI, the README or `skills/` is `test`, `ci`, `docs` or `chore`, and
  releases nothing. That's the point: don't make it `fix` to force a release.
- A change that must reach platforms needs a releasing type. If it would otherwise be `refactor`,
  ask whether the user wants a release.
- `chore(release): ...` belongs to semantic-release. Never write it.
- Say in your reply which release the commit will cause, e.g. "this will release 0.2.3".

**Scope** is usually omitted: the repository is the extension. Use one only to name a part of it,
e.g. `fix(services): ...` or `ci(release): ...`. Don't use another extension's name.

**Header length**: the whole header, type included, is 72 characters or fewer (the commitlint hook,
where `.pre-commit-config.yaml` installs it, rejects a longer one). Measure it; don't count by eye:

```console
printf %s "perf: cache forecasts for an hour" | wc -c
```

**Subject**: imperative mood, lower case, no trailing period. It becomes the CHANGELOG line and the
GitHub release note, so write it for the extension's users.

## Body

Write for a reader with no context.

- Start with the problem or motivation: what was wrong or missing, and how it showed up (for a
  tool, often what the LLM or the administrator saw).
- Then one bullet per change, naming files, classes, settings and tool arguments precisely, with
  the reason for each non-obvious choice.
- Cover the tests: what's new, and what they prove.
- End with the status: coverage, anything skipped, and follow-ups, e.g. the registry entry after
  the release, or a matching change to the other official extensions or to Smarter's docs.

## Before writing

1. Run `git status` and `git diff --stat` (and `git diff` where unclear), so the message describes
   the working tree, not your memory of it.
2. Leave out files that don't belong to the change.
3. Measure the header with `wc -c`.
4. Start the response with a one-line `Written for:` audience note.
