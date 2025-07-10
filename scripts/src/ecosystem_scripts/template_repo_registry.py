"""Maintenance script for updating list of repositories that use the
scverse template in template-repos.yml.

After installing this via `pip install ./scripts` from the repo root,
It is available as `register-template-repos`.

Call `register-template-repos template-repos.yml` to update the file.
Each entry marked with `skip: true` will not be served PRs.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from logging import basicConfig, getLogger
from pathlib import Path
from typing import NotRequired, TypedDict

from github import Github
from rich.logging import RichHandler
from rich.traceback import install
from yaml import safe_dump, safe_load

log = getLogger(__name__)


class Repo(TypedDict):
    url: str
    skip: NotRequired[bool]


def parse_repos(path: Path) -> list[Repo]:
    if not path.is_file():
        log.info(f"No existing file found at: {path}")
        return []
    with path.open() as f:
        repos = safe_load(f)
        log.info(f"Found {len(repos)} known repos in: {path}")
        return repos


def search_repos(github_token: str | None) -> set[str]:
    g = Github(github_token)
    files = g.search_code('filename:.cruft.json "https://github.com/scverse/cookiecutter-scverse"')
    repos = {file.repository for file in files}
    return {r.html_url for r in repos}


def merge_repos(known: Iterable[Repo], new: Iterable[str]) -> list[Repo]:
    repos = list(known)
    n_known = len(repos)
    known_urls = {repo["url"] for repo in repos}
    for repo_url in new:
        if repo_url not in known_urls:
            repos.append(Repo(url=repo_url))
    log.info(f"Found {len(repos) - n_known} new repos in search")
    return repos


def setup() -> None:
    basicConfig(level="INFO", handlers=[RichHandler()])
    install(show_locals=True)


def main(args: Iterable[str] | None = None) -> None:
    setup()
    if args is None:
        args = sys.argv[1:]
    if len(args) != 1:
        sys.exit("Usage: register-template-repos template-repos.yml")
    path = Path(args[0])
    repos = merge_repos(
        parse_repos(path),
        search_repos(os.environ["GITHUB_TOKEN"]),
    )
    if repos:
        with path.open("w") as f:
            safe_dump(sorted(repos, key=lambda r: r["url"]), f, sort_keys=False)


if __name__ == "__main__":
    main()
