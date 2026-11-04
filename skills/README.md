# Agent Skills

This folder holds the [Agent Skills](https://agentskills.io/specification) for working on this
Smarter Extension with an AI coding agent such as Claude Code. Each skill is a folder with a
`SKILL.md`, and sometimes a `scripts/` folder. They are developer tooling, like the workflows: they
are not part of the extension's archive, and no platform loads them.

`.claude/skills` is a symlink to this folder, so Claude Code finds them. Other agents can be told
to read `skills/smarter-extension-development/SKILL.md` at the start of a session. `CLAUDE.md`, at
the repository's root, holds the few rules that apply to every task.

| Skill                           | Use it when                                                            |
| ------------------------------- | ---------------------------------------------------------------------- |
| `smarter-extension-development` | You're making any change. Start here.                                  |
| `smarter-extension-testing`     | You're writing or running the tests, coverage or `validate_extension`. |
| `smarter-extension-release`     | You need to know how, or whether, a change is released.                |
| `smarter-extension-git-commits` | You've been asked to write a commit message.                           |

These skills come from the extension template,
[smarter-sh/smarter-extension-cookiecutter](https://github.com/smarter-sh/smarter-extension-cookiecutter),
and are identical in every official extension repository (smarter-extension-weather, -calculator
and -date-calculator). They are modeled on the skills of
[smarter-sh/smarter](https://github.com/smarter-sh/smarter/tree/main/skills). Improve them in the
template, then copy them to the official extensions. Publishing a release to the registry is
covered by the skills of [smarter-sh/extensions-registry](https://github.com/smarter-sh/extensions-registry).

The tests' runner, `scripts/run-tests.sh`, is an ordinary shell script that you can run yourself
from the repository's root.

## Security

A skill is a set of instructions that an agent follows, often without asking. Review a change to
this folder with the same care as a change to a workflow:

- The Smarter development containers that the tests run in hold live cloud credentials. Keep the
  rule that tests mock every third-party service.
- Rules that forbid something (never run git write commands, never edit the version by hand) are
  there on purpose.
- Look for instructions unrelated to a skill's purpose, network calls in scripts, and text that
  tells an agent to skip confirmations or safety rules.
- This repository is public: no keys, tokens or private hostnames in a skill.
