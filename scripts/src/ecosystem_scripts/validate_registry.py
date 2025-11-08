#!/usr/bin/env python
"""Valididate packages' meta.yaml and generate an output directory with json/images to be uploaded on github pages"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from importlib.resources import files
from logging import basicConfig, getLogger
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import httpx
import jsonschema
import yaml
from PIL import Image
from rich.logging import RichHandler
from rich.traceback import install

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Mapping
else:
    from collections.abc import Iterable

log = getLogger(__name__)

# Constants
HTTP_OK = 200
HTTP_NOT_FOUND = 404
IMAGE_SIZE = 512


class LinkChecker:
    """Track known links and validate URLs."""

    def __init__(self):
        self.known_links: set[str] = set()

    def check_and_register(self, url: str, context: str) -> None:
        """Check if URL is duplicate, validate it exists, and register it.

        Parameters
        ----------
        url
            The URL to check and register
        context
            Context information for error messages (e.g., file being validated)
        """
        if url in self.known_links:
            msg = f"{context}: Duplicate link: {url}"
            raise ValueError(msg)

        response = httpx.head(url, follow_redirects=True)
        if response.status_code != HTTP_OK:
            msg = f"URL {url} is not reachable (error {response.status_code}). "
            raise ValueError(msg)

        self.known_links.add(url)


class GitHubUserValidator:
    """Validate GitHub usernames against the GitHub API."""

    def __init__(self, github_token: str | None = None):
        self.github_token = github_token
        self.validated_users: set[str] = set()

    def validate_username(self, username: str, context: str) -> None:
        """Validate that a GitHub username exists.

        Parameters
        ----------
        username
            The GitHub username to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        # Skip if already validated
        if username in self.validated_users:
            return

        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        response = httpx.head(f"https://api.github.com/users/{username}", headers=headers, follow_redirects=True)

        if response.status_code == HTTP_NOT_FOUND:
            msg = f"{context}: GitHub user '{username}' does not exist"
            raise ValueError(msg)
        if response.status_code != HTTP_OK:
            msg = f"{context}: Failed to validate GitHub user '{username}' (error {response.status_code})"
            raise ValueError(msg)

        self.validated_users.add(username)
        log.info(f"Validated GitHub user: {username}")


class PyPIValidator:
    """Validate PyPI package names against the PyPI API."""

    def __init__(self):
        self.validated_packages: set[str] = set()

    def validate_package(self, package_name: str, context: str) -> None:
        """Validate that a PyPI package exists.

        Parameters
        ----------
        package_name
            The PyPI package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        # Skip if already validated
        if package_name in self.validated_packages:
            return

        response = httpx.head(f"https://pypi.org/pypi/{package_name}/json", follow_redirects=True)

        if response.status_code == HTTP_NOT_FOUND:
            msg = f"{context}: PyPI package '{package_name}' does not exist"
            raise ValueError(msg)
        if response.status_code != HTTP_OK:
            msg = f"{context}: Failed to validate PyPI package '{package_name}' (error {response.status_code})"
            raise ValueError(msg)

        self.validated_packages.add(package_name)
        log.info(f"Validated PyPI package: {package_name}")


class CondaValidator:
    """Validate Conda package identifiers against the Anaconda API."""

    def __init__(self):
        self.validated_packages: set[str] = set()

    def validate_package(self, package_spec: str, context: str) -> None:
        """Validate that a Conda package exists.

        Parameters
        ----------
        package_spec
            The Conda package specification (e.g., "conda-forge::scanpy")
        context
            Context information for error messages (e.g., file being validated)
        """
        # Skip if already validated
        if package_spec in self.validated_packages:
            return

        # Parse channel and package name
        if "::" not in package_spec:
            msg = f"{context}: Invalid Conda package spec '{package_spec}' (expected format: channel::package)"
            raise ValueError(msg)

        channel, package_name = package_spec.split("::", 1)

        # Check package exists on the channel
        response = httpx.head(
            f"https://api.anaconda.org/package/{channel}/{package_name}",
            follow_redirects=True,
        )

        if response.status_code == HTTP_NOT_FOUND:
            msg = f"{context}: Conda package '{package_spec}' does not exist"
            raise ValueError(msg)
        if response.status_code != HTTP_OK:
            msg = f"{context}: Failed to validate Conda package '{package_spec}' (error {response.status_code})"
            raise ValueError(msg)

        self.validated_packages.add(package_spec)
        log.info(f"Validated Conda package: {package_spec}")


class CRANValidator:
    """Validate CRAN package names against the CRAN API."""

    def __init__(self):
        self.validated_packages: set[str] = set()

    def validate_package(self, package_name: str, context: str) -> None:
        """Validate that a CRAN package exists.

        Parameters
        ----------
        package_name
            The CRAN package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        # Skip if already validated
        if package_name in self.validated_packages:
            return

        # CRAN packages can be checked via the packages database
        response = httpx.head(
            f"https://crandb.r-pkg.org/{package_name}",
            follow_redirects=True,
        )

        if response.status_code == HTTP_NOT_FOUND:
            msg = f"{context}: CRAN package '{package_name}' does not exist"
            raise ValueError(msg)
        if response.status_code != HTTP_OK:
            msg = f"{context}: Failed to validate CRAN package '{package_name}' (error {response.status_code})"
            raise ValueError(msg)

        self.validated_packages.add(package_name)
        log.info(f"Validated CRAN package: {package_name}")


def _check_image(img_path: Path) -> None:
    """Check that the image exists and that it is either SVG or fits into the 512x512 bounding box."""
    if not img_path.exists():
        msg = f"Image does not exist: {img_path}"
        raise ValueError(msg)
    if img_path.suffix == ".svg":
        return
    with Image.open(img_path) as img:
        width, height = img.size
    if not ((width == IMAGE_SIZE and height <= IMAGE_SIZE) or (width <= IMAGE_SIZE and height == IMAGE_SIZE)):
        msg = dedent(
            f"""\
            When validating {img_path}: Image must fit in a {IMAGE_SIZE}x{IMAGE_SIZE}px bounding box
            and one dimension must be exactly {IMAGE_SIZE} px.
            Actual dimensions (width, height): ({width}, ({height}))."
            """
        )
        raise ValueError(msg)


def validate_packages(
    schema_file: Path, registry_dir: Path, github_token: str | None = None
) -> Generator[dict, None, None]:
    """Find all package `meta.yaml` files in the registry dir and yield package records."""
    schema = json.loads(schema_file.read_bytes())

    # using different checkers, because each of them may point to the same URL and this wouldn't qualify as duplicate
    link_checker_home = LinkChecker()
    link_checker_docs = LinkChecker()
    link_checker_tutorials = LinkChecker()
    github_validator = GitHubUserValidator(github_token)
    pypi_validator = PyPIValidator()
    conda_validator = CondaValidator()
    cran_validator = CRANValidator()

    for tmp_meta_file in sorted(registry_dir.rglob("meta.yaml"), key=lambda x: x.parent.name):
        pkg_id = tmp_meta_file.parent.name
        log.info(f"Validating {pkg_id}")
        with tmp_meta_file.open() as f:
            tmp_meta = yaml.load(f, yaml.SafeLoader)

        jsonschema.validate(tmp_meta, schema)

        # Check and register all links
        link_checker_home.check_and_register(tmp_meta["project_home"], pkg_id)
        link_checker_docs.check_and_register(tmp_meta["documentation_home"], pkg_id)
        if "tutorials_home" in tmp_meta.keys():
            link_checker_tutorials.check_and_register(tmp_meta["tutorials_home"], pkg_id)

        # Validate GitHub usernames in contact field
        if "contact" in tmp_meta:
            for username in tmp_meta["contact"]:
                github_validator.validate_username(username, pkg_id)

        # Validate install packages
        if "install" in tmp_meta:
            install_info = tmp_meta["install"]
            if "pypi" in install_info:
                pypi_validator.validate_package(install_info["pypi"], pkg_id)
            if "conda" in install_info:
                conda_validator.validate_package(install_info["conda"], pkg_id)
            if "cran" in install_info:
                cran_validator.validate_package(install_info["cran"], pkg_id)

        # Check logo (if available) and make path relative to root of registry
        if "logo" in tmp_meta:
            img_path = registry_dir / pkg_id / tmp_meta["logo"]
            _check_image(img_path)
            tmp_meta["logo"] = str(img_path)

        yield tmp_meta


def make_output(
    packages: Iterable[Mapping[str, str | Iterable[str]]],
    *,
    outdir: Path | None = None,
) -> None:
    """Create the output directory.

    If outdir is not set, don't copy anything, just print the JSON to stdout

    Structure:
    outdir
       - ecosystem.json  # contains package metadata
       - packagexxx/icon.svg  # original icon filenames under a folder for each package.
       - packageyyy/icon.png
    """
    packages_rel = []
    for pkg in packages:
        pkg_rel = dict(pkg)
        if "logo" in pkg:
            img_srcpath = Path(pkg["logo"])
            img_localpath = Path(img_srcpath.parent.name) / img_srcpath.name
            pkg_rel["logo"] = str(img_localpath)
            if outdir:
                img_outpath = outdir / img_localpath
                img_outpath.parent.mkdir()
                shutil.copy(img_srcpath, img_outpath)
        packages_rel.append(pkg_rel)

    if outdir:
        with (outdir / "packages.json").open("w") as f:
            json.dump(packages_rel, f)
    else:
        json.dump(packages_rel, sys.stdout, indent=2)


def setup() -> None:
    """Set up logging and rich traceback."""
    basicConfig(level="INFO", handlers=[RichHandler()])
    install(show_locals=True)

    # Suppress httpx INFO logs to reduce verbosity
    getLogger("httpx").setLevel("WARNING")


def main(args: Iterable[str] | None = None) -> None:
    """Main entry point for the validate-registry command."""
    setup()
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="validate-registry",
        description=(
            "Validate packages' meta.yaml and generate an output directory "
            "with json/images to be uploaded on github pages."
        ),
    )
    parser.add_argument(
        "--registry-dir",
        type=Path,
        help="Path to the registry directory containing package meta.yaml files",
    )
    parser.add_argument("--outdir", type=Path, help="outdir that will contain the data to be uploaded on github pages")

    parsed_args = parser.parse_args(args)
    if not parsed_args.registry_dir.is_dir():
        msg = f"Invalid Registry directory: {parsed_args.registry_dir}"
        raise ValueError(msg)

    schema_file = files("ecosystem_scripts").joinpath("schema.json")
    github_token = os.environ.get("GITHUB_TOKEN")
    if parsed_args.outdir is not None:
        parsed_args.outdir.mkdir(parents=True)

    packages = list(validate_packages(schema_file, parsed_args.registry_dir, github_token))
    make_output(packages, outdir=parsed_args.outdir)


if __name__ == "__main__":
    main()
