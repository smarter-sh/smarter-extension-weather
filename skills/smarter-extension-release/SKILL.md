---
name: smarter-extension-release
description: Use when a question or change concerns how a Smarter Extension repository (smarter-extension-<slug>) is versioned and released, e.g. "will this release?", "why didn't it release?", "release a new version", "retry the release", or when changing release.config.js, package.json, scripts/set_version.py, scripts/package.py or the Release workflow. Covers semantic-release on each push to main, which commit types release what, the release commit, tag, archive and sha256, checking that a release happened, and handing over to the extensions registry.
---

# Releasing a Smarter Extension

Releases are automatic. Every push to `main` runs `.github/workflows/release.yml`, which runs
semantic-release with `release.config.js`. Nobody bumps a version by hand.

## What releases what

semantic-release reads the conventional commits since the last `v*` tag:

| Commit                                                      | Release                |
| ----------------------------------------------------------- | ---------------------- |
| `feat:`                                                     | minor (0.2.0 to 0.3.0) |
| `fix:`, `perf:`                                             | patch (0.2.1 to 0.2.2) |
| `BREAKING CHANGE:` in the body, or `feat!:`                 | major                  |
| `docs`, `test`, `style`, `refactor`, `ci`, `build`, `chore` | nothing                |

So the commit type is a release decision. A change that the platform's users would notice (a tool's
behavior, its arguments, its result, a setting, a dependency pin) must be `fix`, `perf` or `feat`,
or it never reaches the registry. A change only to tests, CI, the README or `skills/` must not be,
or it releases an archive identical in behavior to the last one. When writing a commit, say which
release it will cause.

Breaking changes for an extension: renaming the slug or a tool, removing or renaming a setting or
an argument, making an optional argument required, changing the result's shape in a way that
breaks a prompt that relies on it, or raising `requires-smarter` past releases people still run.

## What a release does

In order (see the comments in `release.config.js`):

1. adds the release notes to `CHANGELOG.md`;
2. `scripts/set_version.py <version>` sets `version` in `pyproject.toml`, and
   `scripts/package.py dist` builds `dist/<slug>-<version>.zip` and its `.zip.sha256`. The archive
   holds `pyproject.toml`, the README, LICENSE and CHANGELOG, and the package, with fixed
   timestamps, so the same source always builds the same archive. It has the same contents as
   Smarter's `manage.py package_extension`, but needs only the standard library;
3. commits `CHANGELOG.md` and `pyproject.toml` as `chore(release): <version>` with
   semantic-release's skip tag, and tags it `v<version>`;
4. creates the GitHub release with the archive and its sha256 attached;
5. the workflow's summary prints the `archive_url` and `sha256` that the registry entry needs.

So `version` in `pyproject.toml` and `CHANGELOG.md` are written only by the release. Never edit them,
never write a `chore(release)` commit, and never tag. After a release, the user's checkout is one
commit behind `origin/main`: tell them to pull before their next change.

## The first release

With no `v*` tag yet, semantic-release makes the first release **1.0.0**, whatever the commit
types. To start at 0.x instead, the user tags the first commit `v0.0.0` and pushes the tag before
the first `feat` or `fix` reaches `main`; the next `feat` then releases 0.1.0. Hand them the
commands (`git tag v0.0.0 <first commit>` and `git push origin v0.0.0`), never run them.

The Release workflow needs **Read and write permissions** for `GITHUB_TOKEN` (Settings › Actions
› General › Workflow permissions), because it pushes the release commit and the tag. A branch
protection rule on `main` that forbids pushes blocks it too.

## Did it release?

```bash
git ls-remote --tags --refs origin 'v*' | sed 's|.*refs/tags/||' | sort -V | tail -3
gh release view --repo smarter-sh/<repository> --json tagName,assets   # if gh is authenticated
curl -sI https://github.com/smarter-sh/<repository>/releases/download/v<version>/<slug>-<version>.zip | head -1
```

If no new tag appeared after a push: the commits' types released nothing, or the workflow failed.
Check which (`gh run list --workflow release.yml --repo smarter-sh/<repository>`, or the Actions
tab) and say so. To retry a failed release, the workflow has a manual start
(`workflow_dispatch`); hand the user the command or the click, don't run it.

## After the release: the registry

A release reaches platforms only when its entry, `extensions/<slug>/<version>.yaml`, is merged to
smarter-sh/extensions-registry. That is a separate change in `../extensions-registry`: load its
`extensions-registry-entry` skill, which writes the entry from the release's public assets and
validates it (set `PUBLISHER` to the publisher's id for an extension that isn't smarter-sh's).
Several extensions released together go in one registry commit. A publisher other than
smarter-sh submits it as a pull request from a fork, and adds itself to `publishers.yaml` with
`badge: community` the first time (see the registry's README).

A released version is never changed. To fix one, release another.

## Changing the release machinery

`release.config.js`, `package.json`, `release.yml`, `scripts/set_version.py` and
`scripts/package.py` come from the cookiecutter template, and are identical in every official
extension: in an official extension, change the template and all of them (see
`smarter-extension-development`). `package.py` must stay standard-library only and reproducible,
and include the same files as `manage.py package_extension` in
`../smarter/smarter/smarter/apps/llmtool/extension/archive.py`. Check a change locally without
releasing:

```bash
python3 scripts/package.py /tmp/<slug>-dist && unzip -l /tmp/<slug>-dist/*.zip
```

Never run semantic-release locally, `npm publish`, `gh release create`, or `git tag`.
