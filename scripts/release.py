"""Prepare a release PR.

Usage: ``mise run release <version>`` (e.g. ``mise run release 0.2.0``).
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MANIFEST_PATH = _REPO_ROOT / "custom_components" / "hamster_mcp" / "manifest.json"
_PYPROJECT_PATH = _REPO_ROOT / "pyproject.toml"
_REQUIREMENTS_TEMPLATE = (
    "hamster-mcp@git+https://github.com/altendky/hamster-mcp.git@{ref}"
)


def _update_versions(*, version: str, git_ref: str) -> None:
    """Update version in manifest.json, pyproject.toml, and regenerate uv.lock."""
    manifest = json.loads(_MANIFEST_PATH.read_text())
    manifest["version"] = version
    manifest["requirements"] = [_REQUIREMENTS_TEMPLATE.format(ref=git_ref)]
    _MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    pyproject_text = _PYPROJECT_PATH.read_text()
    pyproject_text, replacements = re.subn(
        r'^version = ".*"$',
        f'version = "{version}"',
        pyproject_text,
        count=1,
        flags=re.MULTILINE,
    )
    if replacements != 1:
        msg = "Failed to update version in pyproject.toml — regex matched nothing"
        raise RuntimeError(msg)
    _PYPROJECT_PATH.write_text(pyproject_text)

    subprocess.run(["uv", "lock"], check=True, cwd=_REPO_ROOT)


def main() -> None:
    """Prepare a release branch, commit version bump, and open a PR."""
    if len(sys.argv) != 2:
        sys.exit("Usage: mise run release <version>")

    version = sys.argv[1]

    if not re.match(r"^\d+\.\d+\.\d+$", version):
        sys.exit(f"Invalid version format: {version!r}. Expected X.Y.Z")

    tag = f"v{version}"

    # Safety checks
    branch_result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        check=True,
    )
    if branch_result.stdout.strip() != "main":
        sys.exit("Must be on 'main' branch to create a release")

    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    if status_result.stdout.strip():
        sys.exit("Working tree has uncommitted changes")

    subprocess.run(["git", "pull", "--ff-only"], check=True)
    subprocess.run(["git", "fetch", "--tags"], check=True)

    tag_check = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
    )
    if tag_check.returncode == 0:
        sys.exit(f"Error: tag {tag} already exists")

    branch = f"release/{tag}"

    subprocess.run(["git", "checkout", "-b", branch], check=True)
    _update_versions(version=version, git_ref=tag)
    subprocess.run(
        [
            "git",
            "add",
            str(_MANIFEST_PATH),
            str(_PYPROJECT_PATH),
            str(_REPO_ROOT / "uv.lock"),
        ],
        check=True,
    )
    subprocess.run(["git", "commit", "-m", f"Release {tag}"], check=True)
    subprocess.run(["git", "push", "-u", "origin", branch], check=True)
    subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--title",
            f"Release {tag}",
            "--body",
            f"Bump version to `{version}` and pin requirements to `@{tag}`.",
            "--label",
            "enqueue",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
