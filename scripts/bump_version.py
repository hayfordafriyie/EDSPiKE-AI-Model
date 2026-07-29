from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT_FILE = ROOT / "src" / "__init__.py"
PYPROJECT = ROOT / "pyproject.toml"


def read_version() -> str:
    match = re.search(r'__version__\s*=\s*"([^"]+)"', INIT_FILE.read_text())
    if not match:
        raise RuntimeError("Could not find __version__ in src/__init__.py")
    return match.group(1)


def bump(version: str, part: str = "patch") -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def write_version(new_version: str):
    init_content = INIT_FILE.read_text()
    init_content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', init_content)
    INIT_FILE.write_text(init_content)

    pyproject_content = PYPROJECT.read_text()
    pyproject_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        pyproject_content,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(pyproject_content)


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--set":
        new = sys.argv[2]
        current = read_version()
        write_version(new)
        print(f"{current} -> {new}")
        return
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if part not in ("major", "minor", "patch"):
        print(f"Usage: bump_version.py [--set X.Y.Z | major|minor|patch]  (default: patch)")
        sys.exit(1)
    current = read_version()
    new = bump(current, part)
    write_version(new)
    print(f"{current} -> {new}")


if __name__ == "__main__":
    main()
