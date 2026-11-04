---
name: smarter-extension-testing
description: Use when writing, fixing or running the tests of a Smarter Extension repository (smarter-extension-<slug>), raising its coverage, checking it with manage.py validate_extension, or when its Test workflow fails. Covers running the tests in the local Smarter development container with the bundled script, the testing helpers tool_context and call_tool, mocking third-party services, the test_definition check, coverage, and how CI runs the same tests against a sparse checkout of Smarter.
---

# Testing a Smarter Extension

The tests live in `tests/test_tools.py`. They call the tools directly, without installing the
extension, without a database and without an LLM. They import Smarter
(`smarter.apps.llmtool.extension`), so they run where Smarter's code and libraries are: the
`smarter-app` development container of the sibling checkout `../smarter`, or CI.

## Run them

From this repository's root:

```bash
scripts/run-tests.sh             # tests and a coverage report
scripts/run-tests.sh --validate  # also manage.py validate_extension
```

The script copies the working tree to `/tmp/<repository name>` in `smarter-app` (replacing its own
previous copy, and nothing else), and runs the same command CI runs: `coverage run -m unittest
discover -s tests -t .` with `PYTHONPATH` set to the copy and to Smarter's source. `--validate` then
checks the extension as the installer and the registry will: its `pyproject.toml`, its
compatibility, that it imports, and each tool's definition, which it prints exactly as the LLM will
see it.

Run it yourself after every change. Never ask the user to. Write a long log to your scratchpad and
read the summary from it.

- If `smarter-app` isn't running, start the environment from `../smarter` (`make run`, which
  never returns: run it in the background and wait for `curl localhost:9357/` to return 302). The
  smarter repository's `smarter-docker-environment` skill has the details.
- **No `../smarter` checkout?** The tests need a Smarter development environment: clone
  https://github.com/smarter-sh/smarter beside this repository and run its `make init` (it builds
  the containers; see its README). Until then, CI is the only place the tests run: say so in your
  summary rather than claiming they pass.
- `make test` (in extensions generated from the template) runs this script.
- `python manage.py test_extension <path>` in the container runs the same tests, without coverage.
  It's what the README tells people to use.
- Don't `docker cp` the repository yourself: it nests into an existing target and leaves files
  owned by root, which the next copy can't replace. The script uses `tar` and clears the target as
  root for that reason.

**The container holds live credentials** (a kubeconfig for the real EKS cluster, AWS and Route53).
An extension's tests don't need any of them, and must never reach a real service: mock every
third-party call. The platform's own secrets, such as a Google Maps key, are never used by these
tests.

## Write them

`smarter.apps.llmtool.extension.testing` has two helpers:

- `tool_context(slug, **settings)` builds a call's context with the settings the tool reads, e.g.
  `tool_context("weather", google_maps_api_key=SecretStr("test-key"), weather_api_url=API_URL)`.
  Build it once, at module level.
- `call_tool(ToolClass, arguments, context=None)` calls a tool as the platform does: it validates
  the arguments and returns invalid arguments, or an `ExtensionToolError`, as `{"error": ...}`.
  Unlike the platform, it lets any other exception propagate, so the test sees it.

Every tool's tests cover, as `tests/test_tools.py` in weather does:

- **the definition**: `self.assertEqual(Tool.problems(), [])` runs the checks the platform runs when
  it loads the extension, and `Tool.parameters()["required"]` catches an arguments model that makes
  the wrong fields required.
- **`cache_ttl`**: assert its value, with a docstring that says why caching is safe.
- **each result shape** the LLM can get, asserted on the returned JSON, not on internals.
- **each `ExtensionToolError`**: assert the exact message, since the LLM reads it.
- **invalid arguments**: a wrong enum value and missing required fields return `Invalid arguments`.
- **the services**, separately, with their clients mocked: success, each failure they translate,
  and edge cases of the response (weather mocks Open-Meteo's flatbuffers response with
  `MagicMock`s and NumPy arrays, in `open_meteo_response()`).

Mock where the name is looked up: `patch("weather.tools.geocode")` to replace a service in the
tool, `patch("weather.services.googlemaps.Client")` to replace the client inside the service.

Plain `unittest.TestCase`, one test module per source module once a package has several, and
nothing that needs the network, the database or Django settings.

## Coverage

The official extensions, and a freshly generated one, are at 100% (`coverage report -m` lists any
missing lines). Keep them there. CI uploads the report to Codecov, which the README's badge shows.

## How CI runs them

`.github/workflows/test.yml`, on every push to `main` and every pull request: a sparse checkout of
smarter-sh/smarter at `SMARTER_REF` (`main`) into `.smarter/`, `pip install` of Smarter's
`requirements/base.txt`, then the same `coverage run` as the script, on Python 3.14. A failure
that doesn't reproduce in the container is usually a difference between Smarter's `main` and the
local checkout's branch (often `alpha`), or a library version: compare `git -C ../smarter log
origin/main..HEAD` and the versions in `base.txt`.
