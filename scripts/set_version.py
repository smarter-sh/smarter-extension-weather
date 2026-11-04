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
"""The repository's ``pyproject.toml``."""
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
"""A semantic version, as semantic-release passes it: ``1.2.0``, or a pre-release such as ``1.2.0-beta.1``."""


def set_version(text: str, version: str) -> str:
    """
    Return pyproject.toml's text, with the ``[project]`` table's version set to ``version``.

    Only the first ``version`` line inside ``[project]`` changes, so a ``version`` key in another
    table, the formatting and the comments are kept.

    :param text: The text of ``pyproject.toml``.
    :param version: The new version, e.g. ``1.2.0``.
    :returns: The text, with the new version.
    :raises ValueError: when the text has no ``[project]`` table, or the table has no version.
    """
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
    """
    Set the version given on the command line in ``pyproject.toml``, and print it.

    Exits with a usage message, and changes nothing, when the argument isn't a semantic version.

    :raises ValueError: when ``pyproject.toml`` has no ``[project]`` table, or no version in it.
    """
    if len(sys.argv) != 2 or not SEMVER.match(sys.argv[1]):
        sys.exit("usage: python scripts/set_version.py <major>.<minor>.<patch>")
    version = sys.argv[1]
    text = set_version(PYPROJECT.read_text(encoding="utf-8"), version)
    assert tomllib.loads(text)["project"]["version"] == version  # nosec B101: a sanity check
    PYPROJECT.write_text(text, encoding="utf-8")
    print(f"version = {version}")


if __name__ == "__main__":
    main()
