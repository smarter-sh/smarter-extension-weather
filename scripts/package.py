"""
Build this Smarter Extension's archive, <slug>-<version>.zip, and print its sha256, which it also
writes to <slug>-<version>.zip.sha256, in the format of sha256sum.

It includes what ``manage.py package_extension`` includes: pyproject.toml, the README, LICENSE and
CHANGELOG, and the package, without caches, with every file's timestamp fixed, so that the same
source always builds the same archive. It needs only the Python standard library, so that CI can
run it without Smarter.
"""

import hashlib
import io
import os
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPTIONAL_ROOT_FILES = ("README.md", "README.rst", "LICENSE", "LICENSE.md", "LICENSE.txt", "CHANGELOG.md")
EXCLUDED_DIRECTORIES = {
    "__pycache__",
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
}
ZIP_TIMESTAMP = (2000, 1, 1, 0, 0, 0)


def main() -> None:
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    slug, package = manifest["tool"]["smarter"]["slug"], manifest["tool"]["smarter"]["package"]
    version = manifest["project"]["version"]
    files = [ROOT / "pyproject.toml"] + [ROOT / name for name in OPTIONAL_ROOT_FILES if (ROOT / name).is_file()]
    for directory, subdirectories, filenames in os.walk(ROOT / package):
        subdirectories[:] = sorted(d for d in subdirectories if d not in EXCLUDED_DIRECTORIES)
        files += [
            Path(directory) / name
            for name in sorted(filenames)
            if not name.startswith(".") and Path(name).suffix not in (".pyc", ".pyo")
        ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=ZIP_TIMESTAMP)
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{slug}-{version}.zip"
    target.write_bytes(buffer.getvalue())
    sha256 = hashlib.sha256(buffer.getvalue()).hexdigest()
    Path(f"{target}.sha256").write_text(f"{sha256}  {target.name}\n", encoding="utf-8")
    print(target)
    print(sha256)


if __name__ == "__main__":
    main()
