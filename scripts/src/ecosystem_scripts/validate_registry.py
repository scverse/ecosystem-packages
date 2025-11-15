#!/usr/bin/env python
"""Validate packages' meta.yaml and generate an output directory with json/images to be uploaded on Github Pages"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, cast

import httpx
import jsonschema
import yaml
from PIL import Image

from ._logging import log, setup_logging

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from importlib.resources.abc import Traversable

    from .schema import ScverseEcosystemPackages  # pyright: ignore[reportMissingModuleSource]


# Constants
HERE = Path(__file__).parent
IMAGE_SIZE = 512


@dataclass
class ValidationError:
    msg: str


class ErrorList(list):
    """List of error messages. Ignores None objects, and logs an error when one gets added."""

    def append(self, object):  # noqa A002
        if object is None:
            return
        log.error(f"Validation error: {object}")
        return super().append(object)


class LinkChecker:
    """Track known links and validate URLs."""

    def __init__(self) -> None:
        self.known_links: set[str] = set()

    def check_and_register(self, url: str, context: str) -> None | ValidationError:
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
            return ValidationError(msg)

        response = httpx.head(url, follow_redirects=True)
        if response.status_code != httpx.codes.OK:
            msg = f"URL {url} is not reachable (error {response.status_code}). "
            return ValidationError(msg)

        self.known_links.add(url)


class GitHubUserValidator:
    """Validate GitHub usernames using the GitHub API."""

    def __init__(self, github_token: str | None = None) -> None:
        self.github_token = github_token
        self.validated_users: set[str] = set()

    def validate_usernames(self, usernames: Sequence[str], context: str) -> None | ValidationError:
        """Validate that a GitHub username exists.

        Parameters
        ----------
        username
            The GitHub username to validate
        context
            Context information for error messages (e.g., file being validated)
        """

        if not (unvalidated := list(set(usernames) - self.validated_users)):
            return

        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        q = "\n".join(f"user{i}: user(login: {json.dumps(name)}) {{ login }}" for i, name in enumerate(unvalidated))
        response = httpx.post("https://api.github.com/graphql", headers=headers, json={"query": f"query {{ {q} }}"})

        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate GitHub users {unvalidated!r} (error {response.status_code})"
            return ValidationError(msg)

        gql_response = response.json()
        if errors := gql_response.get("errors"):
            error_msgs = "\n".join(f"- {error['message']}" for error in errors)
            msg = f"{context}: Failed to validate GitHub users {unvalidated!r}:\n{error_msgs}"
            return ValidationError(msg)

        self.validated_users |= set(unvalidated)
        log.info(f"Validated GitHub users: {unvalidated!r}")


class PyPIValidator:
    """Validate PyPI package names against the PyPI API."""

    def __init__(self) -> None:
        self.validated_packages: set[str] = set()

    def validate_package(self, package_name: str, context: str) -> None | ValidationError:
        """Validate that a PyPI package exists.

        Parameters
        ----------
        package_name
            The PyPI package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_name in self.validated_packages:
            return

        response = httpx.head(f"https://pypi.org/pypi/{package_name}/json", follow_redirects=True)

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: PyPI package {package_name!r} does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate PyPI package {package_name!r} (error {response.status_code})"
            return ValidationError(msg)

        self.validated_packages.add(package_name)
        log.info(f"Validated PyPI package: {package_name}")


class CondaValidator:
    """Validate Conda package identifiers using the Anaconda API."""

    def __init__(self) -> None:
        self.validated_packages: set[str] = set()

    def validate_package(self, package_spec: str, context: str) -> None | ValidationError:
        """Validate that a Conda package exists.

        Parameters
        ----------
        package_spec
            The Conda package specification (e.g., "conda-forge::scanpy")
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_spec in self.validated_packages:
            return

        # Parse channel and package name
        if "::" not in package_spec:
            msg = f"{context}: Invalid Conda package spec {package_spec!r} (expected format: channel::package)"
            return ValidationError(msg)

        channel, package_name = package_spec.split("::", 1)

        # Check package exists on the channel
        response = httpx.head(
            f"https://api.anaconda.org/package/{channel}/{package_name}",
            follow_redirects=True,
        )

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: Conda package '{package_spec}' does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate Conda package '{package_spec}' (error {response.status_code})"
            return ValidationError(msg)

        self.validated_packages.add(package_spec)
        log.info(f"Validated Conda package: {package_spec}")


class CRANValidator:
    """Validate CRAN package names using the CRAN API."""

    def __init__(self) -> None:
        self.validated_packages: set[str] = set()

    def validate_package(self, package_name: str, context: str) -> None | ValidationError:
        """Validate that a CRAN package exists.

        Parameters
        ----------
        package_name
            The CRAN package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_name in self.validated_packages:
            return

        # CRAN packages can be checked via the packages database
        response = httpx.head(
            f"https://crandb.r-pkg.org/{package_name}",
            follow_redirects=True,
        )

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: CRAN package '{package_name}' does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate CRAN package '{package_name}' (error {response.status_code})"
            return ValidationError(msg)

        self.validated_packages.add(package_name)
        log.info(f"Validated CRAN package: {package_name}")


def check_image(img_path: Path) -> None | ValidationError:
    """Validates that the image exists and that it is either a SVG or fits into the 512x512 bounding box."""
    if not img_path.exists():
        msg = f"Image does not exist: {img_path}"
        return ValidationError(msg)
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
        return ValidationError(msg)


def validate_packages(
    schema_file: Traversable, registry_dir: Path, github_token: str | None = None
) -> tuple[dict, list]:
    """Find all package `meta.yaml` files in the registry dir and yield package records."""
    schema = json.loads(schema_file.read_bytes())

    # using different link checkers,
    # because each of them may point to the same URL and this wouldn't qualify as duplicate
    link_checker_home = LinkChecker()
    link_checker_docs = LinkChecker()
    link_checker_tutorials = LinkChecker()

    github_validator = GitHubUserValidator(github_token)
    pypi_validator = PyPIValidator()
    conda_validator = CondaValidator()
    cran_validator = CRANValidator()

    errors: dict[str, str] = defaultdict(ErrorList)
    package_metadata = []

    for tmp_meta_file in sorted(registry_dir.rglob("meta.yaml"), key=lambda x: x.parent.name):
        pkg_id = tmp_meta_file.parent.name
        pkg_errors = errors[pkg_id]
        log.info(f"Validating {pkg_id}")
        with tmp_meta_file.open() as f:
            tmp_meta = cast("ScverseEcosystemPackages", yaml.load(f, yaml.SafeLoader))

        try:
            jsonschema.validate(tmp_meta, schema)
        except jsonschema.ValidationError as e:
            pkg_errors.append(str(e))

        # Check and register all links
        pkg_errors.append(link_checker_home.check_and_register(tmp_meta["project_home"], pkg_id))
        pkg_errors.append(link_checker_docs.check_and_register(tmp_meta["documentation_home"], pkg_id))
        if url := tmp_meta.get("tutorials_home"):
            pkg_errors.append(link_checker_tutorials.check_and_register(url, pkg_id))

        # Validate GitHub usernames in contact field
        if usernames := tmp_meta.get("contact"):
            pkg_errors.append(github_validator.validate_usernames(usernames, pkg_id))

        # Validate install packages
        if install_info := tmp_meta.get("install"):
            if pypi_name := install_info.get("pypi"):
                pkg_errors.append(pypi_validator.validate_package(pypi_name, pkg_id))
            if conda_name := install_info.get("conda"):
                pkg_errors.append(conda_validator.validate_package(conda_name, pkg_id))
            if cran_name := install_info.get("cran"):
                pkg_errors.append(cran_validator.validate_package(cran_name, pkg_id))

        # Check logo (if available) and make path relative to root of registry
        if "logo" in tmp_meta:
            img_path = registry_dir / pkg_id / tmp_meta["logo"]
            pkg_errors.append(check_image(img_path))
            tmp_meta["logo"] = str(img_path)

        package_metadata.append(tmp_meta)

    return errors, package_metadata


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


class Args(argparse.Namespace):
    registry_dir: Path
    outdir: Path | None


def main(args: Sequence[str] | None = None) -> None:
    """Main entry point for the validate-registry command."""
    setup_logging()
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
        # HERE is <root>/scripts/src/ecosystem_scripts/, so go up 3 levels
        default=HERE.parent.parent.parent / "packages",
        help="Path to the registry directory containing package meta.yaml files",
    )
    parser.add_argument("--outdir", type=Path, help="outdir that will contain the data to be uploaded on github pages")

    parsed_args = parser.parse_args(args, Args())
    if not parsed_args.registry_dir.is_dir():
        msg = f"Invalid Registry directory: {parsed_args.registry_dir}"
        raise ValueError(msg)

    schema_file = files("ecosystem_scripts").joinpath("schema.json")
    github_token = os.environ.get("GITHUB_TOKEN")
    if parsed_args.outdir is not None:
        parsed_args.outdir.mkdir(parents=True)

    log.info("Starting validation")
    errors, packages = validate_packages(schema_file, parsed_args.registry_dir, github_token)

    if any(errors.values()):
        log.error("Validation error occured in at least one package. Exiting.")
        sys.exit(1)
    else:
        make_output(packages, outdir=parsed_args.outdir)


if __name__ == "__main__":
    main()
