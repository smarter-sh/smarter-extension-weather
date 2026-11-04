---
name: smarter-extension-development
description: Start here for any change to a Smarter Extension repository (smarter-extension-<slug>, e.g. smarter-extension-weather, -calculator or -date-calculator) - its tools, their arguments and result models, the services they call, the settings and dependencies in pyproject.toml, the package docstring that is its documentation, its tests, workflows or release scripts. Gives the rules, the tool protocol, the layout, the files kept identical across the official extensions, and which narrower skill to load. Not for the platform's extension framework itself (smarter.apps.llmtool.extension in smarter-sh/smarter).
---

# Smarter Extension Development

A Smarter Extension is a small Python package that adds tools to the LLMs of a Smarter platform.
An administrator installs it from the signed registry (smarter-sh/extensions-registry), configures
its settings, and lists its slug in an LLMClient's `spec.extensions`. The platform imports the
package, offers each tool to the LLM as `ext_<slug>_<tool name>`, validates the LLM's arguments,
runs the tool, and returns its result.

The extension doesn't run on its own. It runs inside the platform, against the platform's code and
libraries, so a local checkout of smarter-sh/smarter, `../smarter`, and its running development
containers are part of this repository's toolchain.

## Repository map

| Path                    | What lives there                                                                  |
| ----------------------- | --------------------------------------------------------------------------------- |
| `pyproject.toml`        | `[project]` (name, version, dependencies) and `[tool.smarter]` (slug, tools, ...) |
| `<package>/__init__.py` | Only the module docstring: the extension's documentation, in reStructuredText     |
| `<package>/tools.py`    | The tools: `SmarterExtensionTool` subclasses, one per tool                        |
| `<package>/models.py`   | Pydantic models of the arguments and the result (weather; small ones in tools.py) |
| `<package>/services.py` | Calls to third-party services, kept out of the tools (weather)                    |
| `tests/test_tools.py`   | unittest tests that call the tools directly, services mocked                      |
| `scripts/`              | `set_version.py` and `package.py`, run by semantic-release. Standard library only |
| `release.config.js`     | semantic-release: versioning, CHANGELOG, archive, GitHub release                  |
| `.github/workflows/`    | `test.yml` (tests + Codecov against a checkout of Smarter), `release.yml`         |
| `skills/`, `CLAUDE.md`  | Agent Skills and agent instructions. Not part of the archive                      |

`pyproject.toml`'s `[tool.smarter]` names the slug, the package and the tools' classes. Read it
first.

## Non-negotiable rules

1. **Never execute git write commands.** "Write a git commit" means output the command text. See
   `smarter-extension-git-commits`.
2. **Never edit `version` in `pyproject.toml`, or `CHANGELOG.md`.** semantic-release owns both,
   on every push to `main`. A commit's type decides the release. See `smarter-extension-release`.
3. **Run the tests yourself**, in the `smarter-app` container, after any change. Never ask the
   user to. See `smarter-extension-testing`. The container holds live cloud credentials: tests
   mock every third-party service and never need a real API key.
4. **Import only what the platform installs.** An extension can't install libraries. Anything it
   imports must be in the standard library, in Smarter, or in
   `../smarter/smarter/requirements/base.txt`, and be declared in `dependencies`. A library the
   platform lacks is a change to Smarter first: say so rather than adding it.
5. **Relative imports inside the package** (`from .models import WeatherArguments`), never
   `from weather.models import ...`. The platform imports each installed version under a name of
   its own, so the package's own name isn't importable there. Tests are the exception: they
   import the package by name.
6. **The slug is permanent.** LLMClient manifests list it and platforms track updates by it. Never
   change `slug`, a tool's `name`, or remove a setting, without a major release (a
   `BREAKING CHANGE`), and say so before doing it.
7. **This repository is public.** No API keys, tokens, account ids or private hostnames, in code,
   tests or skills. Tests use placeholders such as `SecretStr("test-key")`.

## The tool protocol

A tool subclasses `smarter.apps.llmtool.extension.SmarterExtensionTool` and declares:

- `name`: unique within the extension, letters, digits and underscores, at most 48 characters.
- `arguments_model`: a Pydantic model. Its JSON Schema is what the LLM is told the tool accepts,
  and the platform validates the LLM's arguments with it. Describe every field: the LLM reads the
  descriptions.
- the class docstring: the tool's description for the LLM. Say what it does and when to use it.
- `cache_ttl` (optional, default 0): seconds to cache results by arguments and settings. Set it
  only for a tool that changes nothing and whose result doesn't depend on who calls it, and give
  it a docstring that says why it is safe (see each tool's `cache_ttl` here).
- `call(self, arguments, context) -> JsonValue`: does the work. `arguments` is already
  validated. `context.settings.<name>` holds each setting (a `secret` is a `SecretStr`: call
  `get_secret_value()` only where it's used, and never log it). `context.logger` logs as
  `smarter_extensions.<slug>`.

Raise `ExtensionToolError` with a message written **for the LLM** ("Could not find Atlantis: no
such place") when the tool can't do what was asked. Any other exception is logged and the LLM is
told only that the tool failed. Catch a service's own exceptions in `services.py`, re-raise them
as the module's own error classes, and translate those in the tool (see `weather/services.py` and
`weather/tools.py`).

Return a result model's `model_dump(mode="json")`, not a hand-built dict, once the result has more
than a couple of fields. Put everything the LLM needs to interpret it in the result: units,
timezones, the location that was actually found.

Do setup when it's first needed, not at import time: the platform imports the package in every
process when it loads the extension, and an import that fails or blocks makes it fail to load.

The full protocol and the developer guide are in the Smarter repository:
`../smarter/docs/source/smarter-framework/extensions/` (`developer-guide.rst`, `testing.rst`,
`pyproject-reference.rst`, `lifecycle.rst`, `publishing.rst`), published at
https://docs.smarter.sh/en/latest/smarter-framework/smarter-extensions.html. The protocol's code is
`../smarter/smarter/smarter/apps/llmtool/extension/protocol.py`.

## Pattern first

The official extensions are the reference implementations. Before writing anything, read the
nearest one in full and copy its structure, naming, docstrings and error handling:

- **weather**: a tool with a secret setting, a URL setting, two third-party services, and a
  structured result (`models.py`, `services.py`, `tools.py`).
- **calculator**: a pure function behind one tool, with its own safe evaluator (`evaluator.py`).
- **date-calculator**: one tool with several operations chosen by an argument.

Use their local checkouts, `../smarter-extension-<slug>`, if they exist, or read them on GitHub:
https://github.com/smarter-sh/smarter-extension-weather (and -calculator, -date-calculator).

## Files that come from the template

New extensions are generated from smarter-sh/smarter-extension-cookiecutter. These files are
copied from it unchanged, and are identical in every official extension: `release.config.js`,
`package.json`, `.github/workflows/release.yml`, `.github/workflows/test.yml`,
`scripts/package.py`, `scripts/set_version.py`, `scripts/run-tests.sh`, and everything under
`skills/`.

- **In an official extension** (a `smarter-sh/smarter-extension-<slug>` repository), a change to
  one of them is made in the template and in every official extension, in the same piece of work.
  Check that they still agree, from the extension's root:

  ```bash
  T=../smarter-extension-cookiecutter/'{{cookiecutter.repository_name}}'
  for f in release.config.js package.json .github/workflows/release.yml .github/workflows/test.yml \
    scripts/package.py scripts/set_version.py scripts/run-tests.sh; do diff -q "$T/$f" "$f"; done; diff -rq "$T/skills" skills
  ```

- **In any other extension**, they are yours to change, but staying close to the template makes
  its improvements easy to adopt.

`CLAUDE.md` is the one agent file that differs per repository: it describes the extension, and
sets who authors commits.

## Compatibility with Smarter

- Never assume the local `../smarter` checkout is on `main`: it is often on `alpha`, ahead of the
  latest release. Code that works there may use framework features that released platforms
  don't have yet.
- `requires-smarter` is the range of Smarter versions the extension works with. If a change uses
  something new in the extension framework, raise its lower bound to the first release that has
  it, and say so.
- `test.yml` runs the tests against Smarter's `main` (`SMARTER_REF`). To test against unreleased
  framework changes on `alpha`, change `SMARTER_REF` in a branch, never on `main`.

## Code style

Smarter's standard: black and isort (profile black), line length 120, reStructuredText docstrings
(`:param:`, `:returns:`, `:raises:`).

**Docstrings.** Every module, class, function and method has one, tests included, and so does
every module-level constant (a string literal on the line after it). Sphinx renders them, as it
renders Smarter's:

```python
def search(query: str, api_url: str, api_key: str) -> list[JsonValue]:
    """
    Search the service.

    :param query: What to search for.
    :param api_url: The service's search api.
    :param api_key: The service's API key.
    :returns: The service's results.
    :raises ServiceError: If the request fails, or the response has no list of results.
    """
```

- The opening `"""` on its own line, then a **one-line summary ending with a period**, a blank
  line, and the body. pydocstringformatter mangles a summary that wraps.
- A body says why when it isn't obvious: why a limit exists, why caching is safe, what a test
  protects against.
- `:param <name>:` for every argument but `self` and `cls`; `:returns:` unless it returns None;
  `:raises <Error>: when ...` for each exception a caller handles, and `AssertionError` for a test.
  Types come from the annotations: no `:type:`.
- Two docstrings are read by the platform, not Sphinx, and hold no fields: the tool class's is
  the tool's description for the LLM, and `<package>/__init__.py`'s is the extension's
  documentation for administrators.

- **With a `.pre-commit-config.yaml`** (every extension generated from the template), the hooks
  are the lint standard, as in Smarter: black, flake8, isort, autoflake, bandit, codespell,
  pyupgrade, pydocstringformatter, Prettier, and commitlint on commit messages. Run them on the
  changed files: `git diff --name-only | xargs venv/bin/pre-commit run --files` (or `make lint`
  for every file). `make init` creates `venv/` and installs the hooks.
- **Without one** (the older official extensions), run black and isort from the Smarter
  checkout's virtual environment, on the files you changed only (the existing files don't all
  agree on isort's sections, and reformatting untouched files adds noise):

  ```bash
  git diff --name-only -- '*.py' | xargs ../smarter/venv/bin/black -l 120
  git diff --name-only -- '*.py' | xargs ../smarter/venv/bin/isort --profile black -l 120
  ```

The host shell may be zsh, which doesn't word-split `$FILES`. Use `xargs`, as above.

## Documentation

- `<package>/__init__.py`'s docstring is what the web console and the registry show
  administrators: what it does, each setting, each tool. Update it with any change to a setting or
  a tool's arguments.
- `README.md`: badges, install, develop, release. Keep it short.
- **weather is the worked example of Smarter's developer guide.** `developer-guide.rst` and
  `testing.rst` in `../smarter/docs/source/smarter-framework/extensions/` quote its files. When
  weather's `pyproject.toml`, `models.py`, `services.py`, `tools.py` or tests change in a way a
  reader would notice, say in your summary that those pages need the same change (it's a separate
  change in the smarter repository).

## Which skill to load

| Task                                                                 | Skill                                                    |
| -------------------------------------------------------------------- | -------------------------------------------------------- |
| Writing, running or fixing the tests; coverage; `validate_extension` | `smarter-extension-testing`                              |
| How a change gets released, version numbers, the GitHub release      | `smarter-extension-release`                              |
| Writing a commit message                                             | `smarter-extension-git-commits`                          |
| Publishing a release to the registry                                 | `extensions-registry-entry`, in `../extensions-registry` |

## Definition of done

- The change follows the nearest official extension's pattern.
- Tests cover it, and you ran them in the container (`smarter-extension-testing`), with coverage
  still at 100%, and `validate_extension` passes.
- The pre-commit hooks (or black and isort) pass on the changed files.
- The package docstring, `README.md` and the tool and field descriptions match the code.
- In an official extension, a file from the template changed in the template and every official
  extension, or not at all.
- Your summary says what changed, what you verified, what you skipped, and which commit type the
  change needs (it decides the release).
