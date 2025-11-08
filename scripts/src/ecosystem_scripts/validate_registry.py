#!/usr/bin/env python
"""Valididate packages' meta.yaml and generate an output directory with json/images to be uploaded on github pages"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from importlib.resources import files
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

import httpx
import jsonschema
import yaml
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Mapping
else:
    from collections.abc import Iterable

# Constants
HTTP_OK = 200
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

        response = httpx.head(url)
        if response.status_code != HTTP_OK:
            msg = f"URL {url} is not reachable (error {response.status_code}). "
            raise ValueError(msg)

        self.known_links.add(url)


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


def validate_packages(schema_file: Path, registry_dir: Path) -> Generator[dict, None, None]:
    """Find all package `meta.yaml` files in the registry dir and yield package records."""
    schema = json.loads(schema_file.read_bytes())
    link_checker = LinkChecker()

    for tmp_meta_file in registry_dir.rglob("meta.yaml"):
        pkg_id = tmp_meta_file.parent.name
        with tmp_meta_file.open() as f:
            tmp_meta = yaml.load(f, yaml.SafeLoader)

        jsonschema.validate(tmp_meta, schema)

        # Check and register all links
        link_checker.check_and_register(tmp_meta["project_home"], pkg_id)
        link_checker.check_and_register(tmp_meta["documentation_home"], pkg_id)
        link_checker.check_and_register(tmp_meta["tutorials_home"], pkg_id)

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

    Structure:
    outdir
       - ecosystem.json  # contains package metadata
       - packagexxx/icon.svg  # original icon filenames under a folder for each package.
       - packageyyy/icon.png
    """
    if outdir:
        outdir.mkdir(parents=True)

    packages_rel = []
    for pkg in packages:
        img_srcpath = Path(pkg["logo"])
        img_localpath = Path(img_srcpath.parent.name) / img_srcpath.name
        pkg_rel = dict(pkg)
        pkg_rel["logo"] = str(img_localpath)
        packages_rel.append(pkg_rel)
        if outdir:
            img_outpath = outdir / img_localpath
            img_outpath.parent.mkdir()
            shutil.copy(img_srcpath, img_outpath)

    if outdir:
        with (outdir / "packages.json").open("w") as f:
            json.dump(packages_rel, f)
    else:
        json.dump(packages_rel, sys.stdout, indent=2)


def main(args: Iterable[str] | None = None) -> None:
    """Main entry point for the validate-registry command."""
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
        default=Path.cwd() / "packages",
        help="Path to the registry directory containing package meta.yaml files",
    )
    parser.add_argument("--outdir", type=Path, help="outdir that will contain the data to be uploaded on github pages")

    parsed_args = parser.parse_args(args)

    schema_file = files("ecosystem_scripts").joinpath("schema.json")

    packages = list(validate_packages(schema_file, parsed_args.registry_dir))
    make_output(packages, outdir=parsed_args.outdir)


if __name__ == "__main__":
    main()
