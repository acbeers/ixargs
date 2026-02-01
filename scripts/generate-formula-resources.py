#!/usr/bin/env python3
"""
Generate Homebrew formula resource blocks for ixargs dependencies.
Run this after updating dependencies in pyproject.toml.

Usage:
    python scripts/generate-formula-resources.py
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def get_package_info(package_name: str, version: str = None) -> dict:
    """Get package info from PyPI."""
    import urllib.request
    
    url = f"https://pypi.org/pypi/{package_name}/json"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
    
    if version:
        # Get specific version
        releases = data.get("releases", {})
        if version not in releases:
            raise ValueError(f"Version {version} not found for {package_name}")
        release_files = releases[version]
    else:
        # Get latest version
        version = data["info"]["version"]
        release_files = data["urls"]
    
    # Find the source tarball
    for file in release_files:
        if file["packagetype"] == "sdist" and file["filename"].endswith(".tar.gz"):
            return {
                "name": package_name,
                "version": version,
                "url": file["url"],
                "sha256": file["digests"]["sha256"]
            }
    
    raise ValueError(f"No source tarball found for {package_name}")


def generate_resource_block(info: dict) -> str:
    """Generate a Homebrew resource block."""
    return f'''  resource "{info['name']}" do
    url "{info['url']}"
    sha256 "{info['sha256']}"
  end'''


def _sha256_from_hash_field(hash_value: str) -> str:
    # uv.lock stores hashes like "sha256:<hex>"
    if hash_value.startswith("sha256:"):
        return hash_value.removeprefix("sha256:")
    return hash_value


def _load_uv_lock(lock_path: Path) -> dict[str, Any]:
    try:
        import tomllib  # py>=3.11
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Python 3.11+ is required to parse uv.lock (needs tomllib)."
        ) from e

    return tomllib.loads(lock_path.read_text(encoding="utf-8"))


def _normalize_extra_list(dep: dict[str, Any]) -> list[str]:
    # uv.lock uses `extra = ["foo"]` for requested extras.
    extra = dep.get("extra")
    if extra is None:
        return []
    if isinstance(extra, str):
        return [extra]
    if isinstance(extra, list):
        return [str(x) for x in extra]
    return []


def _marker_allows_dependency(
    marker: str, *, target_sys_platform: str, target_python_version: str
) -> bool:
    """
    Minimal marker evaluator for the handful of markers we expect in uv.lock.
    Supports:
      - sys_platform ==/!= "<value>"
      - python_version ==/!=/>=/<=/>/< "<major.minor>"
      - `and` / `or` boolean composition

    Anything unknown defaults to True (include) to avoid silently dropping deps.
    """
    marker = marker.strip()
    if not marker:
        return True

    # very small recursive descent parser
    tokens: list[str] = []
    buf = ""
    i = 0
    while i < len(marker):
        ch = marker[i]
        if ch in "()":
            if buf.strip():
                tokens.append(buf.strip())
            tokens.append(ch)
            buf = ""
            i += 1
            continue
        if marker[i : i + 4] == " and":
            if buf.strip():
                tokens.append(buf.strip())
            tokens.append("and")
            buf = ""
            i += 4
            continue
        if marker[i : i + 3] == " or":
            if buf.strip():
                tokens.append(buf.strip())
            tokens.append("or")
            buf = ""
            i += 3
            continue
        buf += ch
        i += 1
    if buf.strip():
        tokens.append(buf.strip())

    def eval_atom(expr: str) -> bool:
        expr = expr.strip()
        # expected shape: <key> <op> "<value>"
        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in expr:
                left, right = expr.split(op, 1)
                left = left.strip()
                right = right.strip().strip('"').strip("'")

                if left == "sys_platform":
                    if op == "==":
                        return target_sys_platform == right
                    if op == "!=":
                        return target_sys_platform != right
                    return True

                if left == "python_version":

                    def ver_tuple(v: str) -> tuple[int, int]:
                        parts = v.split(".")
                        major = int(parts[0])
                        minor = int(parts[1]) if len(parts) > 1 else 0
                        return (major, minor)

                    tv = ver_tuple(target_python_version)
                    rv = ver_tuple(right)
                    if op == "==":
                        return tv == rv
                    if op == "!=":
                        return tv != rv
                    if op == ">=":
                        return tv >= rv
                    if op == "<=":
                        return tv <= rv
                    if op == ">":
                        return tv > rv
                    if op == "<":
                        return tv < rv
                    return True

                # unknown key -> include
                return True

        # unknown atom -> include
        return True

    def parse_expr(pos: int = 0) -> tuple[bool, int]:
        def parse_term(p: int) -> tuple[bool, int]:
            tok = tokens[p]
            if tok == "(":
                val, p2 = parse_expr(p + 1)
                if p2 < len(tokens) and tokens[p2] == ")":
                    return val, p2 + 1
                return val, p2
            return eval_atom(tok), p + 1

        lhs, p = parse_term(pos)
        while p < len(tokens) and tokens[p] == "and":
            rhs, p = parse_term(p + 1)
            lhs = lhs and rhs
        return lhs, p

    def parse_or(pos: int = 0) -> tuple[bool, int]:
        lhs, p = parse_expr(pos)
        while p < len(tokens) and tokens[p] == "or":
            rhs, p = parse_expr(p + 1)
            lhs = lhs or rhs
        return lhs, p

    try:
        val, _ = parse_or(0)
        return bool(val)
    except Exception:
        return True


def _generate_from_uv_lock(repo_root: Path) -> list[dict[str, str]]:
    """
    Generate dependency resources using uv.lock.

    Benefits:
      - Works offline
      - Exactly matches the locked versions + hashes
      - Avoids pip's build backend resolution (hatchling) entirely
    """
    lock_path = repo_root / "uv.lock"
    lock = _load_uv_lock(lock_path)

    packages: list[dict[str, Any]] = lock.get("package", [])
    by_name: dict[str, dict[str, Any]] = {p["name"]: p for p in packages if "name" in p}

    root = by_name.get("ixargs")
    if not root:
        raise RuntimeError("uv.lock does not contain a package entry for 'ixargs'.")

    target_sys_platform = "darwin"  # Homebrew formula targets macOS primarily
    target_python_version = "3.13"  # Formula depends on python@3.13

    requested_extras: dict[str, set[str]] = {}
    seen: set[str] = set()
    queue: list[str] = []

    def add_dep(dep: dict[str, Any]) -> None:
        name = dep.get("name")
        if not name or name == "ixargs":
            return
        marker = dep.get("marker")
        if marker and not _marker_allows_dependency(
            str(marker),
            target_sys_platform=target_sys_platform,
            target_python_version=target_python_version,
        ):
            return

        extras = _normalize_extra_list(dep)
        if extras:
            requested_extras.setdefault(name, set()).update(extras)
        if name not in seen:
            queue.append(name)

    for dep in root.get("dependencies", []) or []:
        add_dep(dep)

    resources: list[dict[str, str]] = []

    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)

        pkg = by_name.get(name)
        if not pkg:
            # If uv.lock doesn't include it, we can't provide a deterministic url/hash.
            continue

        for dep in pkg.get("dependencies", []) or []:
            add_dep(dep)

        opt = pkg.get("optional-dependencies") or {}
        for extra in sorted(requested_extras.get(name, set())):
            for dep in opt.get(extra, []) or []:
                add_dep(dep)

        sdist = pkg.get("sdist")
        if not sdist:
            continue
        url = sdist.get("url")
        hash_value = sdist.get("hash")
        if not url or not hash_value:
            continue

        resources.append(
            {
                "name": name,
                "version": str(pkg.get("version", "")),
                "url": str(url),
                "sha256": _sha256_from_hash_field(str(hash_value)),
            }
        )

    return sorted(resources, key=lambda r: r["name"].lower())


def main():
    repo_root = Path(__file__).parent.parent

    # Prefer uv.lock (deterministic + offline).
    uv_lock = repo_root / "uv.lock"
    if uv_lock.exists():
        infos = _generate_from_uv_lock(repo_root)
        print(f"Found {len(infos)} dependencies from uv.lock:\n")
        resources = []
        for info in infos:
            resources.append(generate_resource_block(info))
            suffix = f" {info['version']}" if info.get("version") else ""
            print(f"✓ {info['name']}{suffix}")
    else:
        # Fallback: resolve via pip and fetch hashes from PyPI (requires network).
        print("Installing ixargs to determine exact dependencies...")
        result = subprocess.run(
            ["pip", "install", "--dry-run", "--report", "-", "."],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )

        if result.returncode != 0:
            print("Error: Could not resolve dependencies", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

        report = json.loads(result.stdout)

        # Extract package names (excluding ixargs itself)
        packages = []
        for item in report["install"]:
            metadata = item["metadata"]
            name = metadata["name"]
            if name != "ixargs":
                packages.append((name, metadata["version"]))

        print(f"\nFound {len(packages)} dependencies:\n")

        # Generate resource blocks
        resources = []
        for name, version in sorted(packages):
            try:
                info = get_package_info(name, version)
                resources.append(generate_resource_block(info))
                print(f"✓ {name} {version}")
            except Exception as e:
                print(f"✗ {name}: {e}", file=sys.stderr)
    
    print("\n" + "="*60)
    print("Add these resource blocks to Formula/ixargs.rb:")
    print("="*60 + "\n")
    print("\n\n".join(resources))


if __name__ == "__main__":
    main()
