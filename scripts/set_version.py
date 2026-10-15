"""
Set this Smarter Extension's version, the ``version`` of pyproject.toml's ``[project]`` table.

semantic-release runs it before it builds the archive: see release.config.js. Only the version's
line changes, so the file's formatting and comments are kept.

    python scripts/set_version.py 1.2.0
"""

import re
import sys
import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


def set_version(text: str, version: str) -> str:
    """Return pyproject.toml's text, with the [project] table's version set to ``version``."""
    project = re.search(r"^\[project\]\s*$(.*?)(?=^\[|\Z)", text, flags=re.MULTILINE | re.DOTALL)
    if project is None:
        raise ValueError("pyproject.toml has no [project] table")
    body, count = re.subn(
        r'^(version\s*=\s*)"[^"]*"', rf'\g<1>"{version}"', project.group(1), count=1, flags=re.MULTILINE
    )
    if count != 1:
        raise ValueError("pyproject.toml's [project] table has no version")
    return text[: project.start(1)] + body + text[project.end(1) :]


def main() -> None:
    if len(sys.argv) != 2 or not SEMVER.match(sys.argv[1]):
        sys.exit("usage: python scripts/set_version.py <major>.<minor>.<patch>")
    version = sys.argv[1]
    text = set_version(PYPROJECT.read_text(encoding="utf-8"), version)
    assert tomllib.loads(text)["project"]["version"] == version  # nosec B101: a sanity check
    PYPROJECT.write_text(text, encoding="utf-8")
    print(f"version = {version}")


if __name__ == "__main__":
    main()
