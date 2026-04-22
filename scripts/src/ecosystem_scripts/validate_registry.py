#!/usr/bin/env python
"""Validate packages' meta.yaml and generate an output directory with json/images to be uploaded on Github Pages"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
from dataclasses import KW_ONLY, dataclass, field
from importlib.resources import files
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, cast, override

import httpx
import jsonschema
import yaml
from httpx_limiter import (  # type: ignore[attr-defined]
    AbstractRateLimiterRepository,
    AsyncMultiRateLimitedTransport,
    Rate,
)
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter  # type: ignore[attr-defined]
from httpx_retries import Retry, RetryTransport
from PIL import Image

from ._logging import log, setup_logging

if TYPE_CHECKING:
    from collections.abc import Awaitable, Generator, Iterable, Mapping, Sequence
    from importlib.resources.abc import Traversable

    from .schema import ScverseEcosystemPackages  # pyright: ignore[reportMissingModuleSource]


# Constants
HERE = Path(__file__).parent
IMAGE_SIZE = 512


class ValidationError(Exception):
    pass


RE_RTD = re.compile(
    r"https?://(?P<domain>.*\.(?:readthedocs\.io|rtfd\.io|readthedocs-hosted\.com))/(?P<version>en/[^/]+)(?P<path>.*)"
)


@dataclass
class HTTPValidator[E = str]:
    """Validate HTTP URLs."""

    client: httpx.AsyncClient
    _: KW_ONLY
    validated: set[E] = field(default_factory=set)


@dataclass
class LinkChecker(HTTPValidator):
    """Track known links and validate URLs."""

    name: str

    async def __call__(self, url: str, context: str) -> None | ValidationError:
        """Check if URL is duplicate, validate it exists, and register it.

        Parameters
        ----------
        url
            The URL to check and register
        context
            Context information for error messages (e.g., file being validated)
        """
        if m := re.fullmatch(RE_RTD, url):
            new_url = f"https://{m['domain']}/" + (f"page{m['path']}" if m["path"].strip("/") else "")
            msg = (
                f"{self.name}:{context}: "
                f"Please use the default version in ReadTheDocs URLs instead of {m['version']!r}:\n"
                f"{url}\n->\n{new_url}"
            )
            return ValidationError(msg)
        if url in self.validated:
            msg = f"{self.name}:{context}: Duplicate link: {url}"
            return ValidationError(msg)

        try:
            response = await self.client.head(url)
        except Exception as e:
            msg = f"{self.name}:{context}: URL {url} is not reachable: {e}"
            return ValidationError(msg)

        if response.status_code != httpx.codes.OK:
            msg = f"{self.name}:{context}: URL {url} is not reachable (error {response.status_code}). "
            return ValidationError(msg)

        self.validated.add(url)
        log.info(f"Validated {self.name} URL for {context}: {url!r}")
        return None


@dataclass
class GitHubUserValidator(HTTPValidator):
    """Validate GitHub usernames using the GitHub API."""

    github_token: str | None = None

    async def __call__(self, usernames: Sequence[str], context: str) -> None | ValidationError:
        """Validate that a GitHub username exists.

        Parameters
        ----------
        username
            The GitHub username to validate
        context
            Context information for error messages (e.g., file being validated)
        """

        if not (unvalidated := list(set(usernames) - self.validated)):
            return None

        headers = {}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        q = "\n".join(f"user{i}: user(login: {json.dumps(name)}) {{ login }}" for i, name in enumerate(unvalidated))

        try:
            response = await self.client.post(
                "https://api.github.com/graphql", headers=headers, json={"query": f"query {{ {q} }}"}
            )
        except Exception as e:
            msg = f"{context}: Failed to validate GitHub users {unvalidated!r}: {e}"
            return ValidationError(msg)

        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate GitHub users {unvalidated!r} (error {response.status_code})"
            return ValidationError(msg)

        gql_response = response.json()
        if errors := gql_response.get("errors"):
            error_msgs = "\n".join(f"- {error['message']}" for error in errors)
            msg = f"{context}: Failed to validate GitHub users {unvalidated!r}:\n{error_msgs}"
            return ValidationError(msg)

        self.validated |= set(unvalidated)
        log.info(f"Validated GitHub users for {context}: {unvalidated!r}")
        return None


@dataclass
class PyPIValidator(HTTPValidator):
    """Validate PyPI package names against the PyPI API."""

    async def __call__(self, package_name: str, context: str) -> None | ValidationError:
        """Validate that a PyPI package exists.

        Parameters
        ----------
        package_name
            The PyPI package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_name in self.validated:
            return None

        try:
            response = await self.client.head(f"https://pypi.org/pypi/{package_name}/json")
        except Exception as e:
            msg = f"{context}: Failed to validate PyPI package {package_name!r}: {e}"
            return ValidationError(msg)

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: PyPI package {package_name!r} does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate PyPI package {package_name!r} (error {response.status_code})"
            return ValidationError(msg)

        self.validated.add(package_name)
        log.info(f"Validated PyPI package for {context}: {package_name}")
        return None


@dataclass
class CondaValidator(HTTPValidator):
    """Validate Conda package identifiers using the Anaconda API."""

    async def __call__(self, package_spec: str, context: str) -> None | ValidationError:
        """Validate that a Conda package exists.

        Parameters
        ----------
        package_spec
            The Conda package specification (e.g., "conda-forge::scanpy")
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_spec in self.validated:
            return None

        # Parse channel and package name
        if "::" not in package_spec:
            msg = f"{context}: Invalid Conda package spec {package_spec!r} (expected format: channel::package)"
            return ValidationError(msg)

        channel, package_name = package_spec.split("::", 1)

        # Check package exists on the channel
        try:
            response = await self.client.head(f"https://api.anaconda.org/package/{channel}/{package_name}")
        except Exception as e:
            msg = f"{context}: Failed to validate Conda package '{package_spec}': {e}"
            return ValidationError(msg)

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: Conda package '{package_spec}' does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate Conda package '{package_spec}' (error {response.status_code})"
            return ValidationError(msg)

        self.validated.add(package_spec)
        log.info(f"Validated Conda package for {context}: {package_spec}")
        return None


@dataclass
class CRANValidator(HTTPValidator):
    """Validate CRAN package names using the CRAN API."""

    async def __call__(self, package_name: str, context: str) -> None | ValidationError:
        """Validate that a CRAN package exists.

        Parameters
        ----------
        package_name
            The CRAN package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_name in self.validated:
            return None

        # CRAN packages can be checked via the packages database
        try:
            response = await self.client.head(f"https://crandb.r-pkg.org/{package_name}")
        except Exception as e:
            msg = f"{context}: Failed to validate CRAN package '{package_name}': {e}"
            return ValidationError(msg)

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: CRAN package '{package_name}' does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate CRAN package '{package_name}' (error {response.status_code})"
            return ValidationError(msg)

        self.validated.add(package_name)
        log.info(f"Validated CRAN package for {context}: {package_name}")
        return None


@dataclass
class BioconductorValidator(HTTPValidator):
    """Validate Bioconductor package names using the Bioconductor API."""

    async def __call__(self, package_name: str, context: str) -> None | ValidationError:
        """Validate that a Bioconductor package exists.

        Parameters
        ----------
        package_name
            The Bioconductor package name to validate
        context
            Context information for error messages (e.g., file being validated)
        """
        if package_name in self.validated:
            return None

        # Bioconductor packages can be checked via their web API
        try:
            response = await self.client.head(f"https://bioconductor.org/packages/{package_name}/")
        except Exception as e:
            msg = f"{context}: Failed to validate Bioconductor package '{package_name}': {e}"
            return ValidationError(msg)

        if response.status_code == httpx.codes.NOT_FOUND:
            msg = f"{context}: Bioconductor package '{package_name}' does not exist"
            return ValidationError(msg)
        if response.status_code != httpx.codes.OK:
            msg = f"{context}: Failed to validate Bioconductor package '{package_name}' (error {response.status_code})"
            return ValidationError(msg)

        self.validated.add(package_name)
        log.info(f"Validated Bioconductor package for {context}: {package_name}")
        return None


def check_image(img_path: Path) -> None:
    """Validates that the image exists and that it is either a SVG or fits into the 512x512 bounding box."""
    if not img_path.exists():
        msg = f"Image does not exist: {img_path}"
        raise ValidationError(msg)
    if img_path.suffix == ".svg":
        return None
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
        raise ValidationError(msg)
    return None


class DomainBasedRateLimiterRepository(AbstractRateLimiterRepository):
    """Apply different rate limits based on the domain being requested."""

    @override
    def get_identifier(self, request: httpx.Request) -> str:
        return request.url.host

    @override
    def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:
        return AiolimiterAsyncLimiter.create(Rate.create(magnitude=25))


@dataclass
class Checker:
    schema_file: Traversable
    registry_dir: Path
    _: KW_ONLY
    github_token: str | None = None

    def __post_init__(self) -> None:
        self.schema = json.loads(self.schema_file.read_bytes())

        # Create HTTP client with retry configuration using httpx_retries transport
        transport: httpx.AsyncBaseTransport = AsyncMultiRateLimitedTransport.create(
            repository=DomainBasedRateLimiterRepository()
        )
        transport = RetryTransport(transport, Retry(total=3, backoff_factor=2))
        self.client = httpx.AsyncClient(follow_redirects=True, timeout=30.0, transport=transport)

        # using different link checkers,
        # because each of them may point to the same URL and this wouldn't qualify as duplicate
        self.check_home = LinkChecker(self.client, name="home")
        self.check_docs = LinkChecker(self.client, name="docs")
        self.check_tutorial = LinkChecker(self.client, name="tutorial")

        self.check_gh_users = GitHubUserValidator(self.client, self.github_token)
        self.check_pypi = PyPIValidator(self.client)
        self.check_conda = CondaValidator(self.client)
        self.check_cran = CRANValidator(self.client)
        self.check_bioc = BioconductorValidator(self.client)

    async def validate_packages(self) -> tuple[Mapping[str, Sequence[Exception]], Sequence[ScverseEcosystemPackages]]:
        """Find all package `meta.yaml` files in the registry dir and yield package records."""

        errors: dict[str, list[ValidationError | jsonschema.ValidationError]] = {}
        package_metadata: list[ScverseEcosystemPackages] = []

        async with self.client:
            async for check in asyncio.as_completed(
                self.check_package(meta_path)
                for meta_path in sorted(self.registry_dir.rglob("meta.yaml"), key=lambda x: x.parent.name)
            ):
                pkg_id, tmp_meta, pkg_errors = await check
                errors[pkg_id] = pkg_errors
                package_metadata.append(tmp_meta)

        return errors, package_metadata

    async def check_package(
        self, meta_file: Path
    ) -> tuple[str, ScverseEcosystemPackages, list[ValidationError | jsonschema.ValidationError]]:
        pkg_id = meta_file.parent.name
        with meta_file.open() as f:
            tmp_meta = cast("ScverseEcosystemPackages", yaml.load(f, yaml.SafeLoader))

        pkg_errors: list[ValidationError | jsonschema.ValidationError] = []
        try:
            jsonschema.validate(tmp_meta, self.schema)
        except jsonschema.ValidationError as e:
            pkg_errors.append(e)

        # Check logo (if available) and make path relative to root of registry
        if "logo" in tmp_meta:
            img_path = self.registry_dir / pkg_id / tmp_meta["logo"]
            try:
                check_image(img_path)
            except ValidationError as e:
                pkg_errors.append(e)
            tmp_meta["logo"] = str(img_path)

        log.info(f"Validating {pkg_id}")
        async for check in asyncio.as_completed(self.http_checks(pkg_id, tmp_meta)):
            try:
                await check
            except ValidationError as e:
                pkg_errors.append(e)

        return pkg_id, tmp_meta, pkg_errors

    def http_checks(self, pkg_id: str, tmp_meta: ScverseEcosystemPackages) -> Generator[Awaitable[Exception | None]]:
        # Check and register all links
        yield self.check_home(tmp_meta["project_home"], pkg_id)
        yield self.check_docs(tmp_meta["documentation_home"], pkg_id)
        if url := tmp_meta.get("tutorials_home"):
            yield self.check_tutorial(url, pkg_id)

        # Validate GitHub usernames in contact field
        if usernames := tmp_meta.get("contact"):
            yield self.check_gh_users(usernames, pkg_id)

        # Validate install packages
        if install_info := tmp_meta.get("install"):
            if pypi_name := install_info.get("pypi"):
                yield self.check_pypi(pypi_name, pkg_id)
            if conda_name := install_info.get("conda"):
                yield self.check_conda(conda_name, pkg_id)
            if cran_name := install_info.get("cran"):
                yield self.check_cran(cran_name, pkg_id)
            if bioconductor_name := install_info.get("bioconductor"):
                yield self.check_bioc(bioconductor_name, pkg_id)


def make_output(
    packages: Iterable[ScverseEcosystemPackages],
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
    packages_rel: list[ScverseEcosystemPackages] = []
    for pkg in packages:
        pkg_rel = pkg.copy()
        if logo := pkg.get("logo"):
            img_srcpath = Path(logo)
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
    checker = Checker(schema_file, parsed_args.registry_dir, github_token=github_token)
    errors, packages = asyncio.run(checker.validate_packages())

    if any(errors.values()):
        log.error("Validation error occured in at least one package. Exiting.")
        sys.exit(1)
    else:
        make_output(packages, outdir=parsed_args.outdir)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
