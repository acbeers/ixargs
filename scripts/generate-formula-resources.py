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


def main():
    # Get dependencies from a fresh pip install
    print("Installing ixargs to determine exact dependencies...")
    result = subprocess.run(
        ["pip", "install", "--dry-run", "--report", "-", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
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
