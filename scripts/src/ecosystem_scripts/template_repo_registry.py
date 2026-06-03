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
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

from github import Github, GithubException, UnknownObjectException
from yaml import safe_dump, safe_load

from ._logging import log, setup_logging

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class Repo(TypedDict):
    url: str
    skip: NotRequired[bool]


def parse_repos(path: Path) -> list[Repo]:
    if not path.is_file():
        log.info(f"No existing file found at: {path}")
        return []
    with path.open() as f:
        repos = cast("list[Repo]", safe_load(f))
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


def filter_repos(repos: list[Repo], github_token: str | None) -> list[Repo]:
    """Filter repositories based on their GitHub status.

    Removes archived repositories, non-existent repositories, and repositories
    that no longer have .cruft.json in their root. Updates URLs for moved repositories.

    Parameters
    ----------
    repos
        List of repositories to filter
    github_token
        GitHub API token for authentication

    Returns
    -------
        Filtered list of repositories
    """
    g = Github(github_token)
    filtered_repos = []
    known_urls = {repo["url"] for repo in repos}

    for repo in repos:
        url = repo["url"]
        github_url_prefix = "https://github.com/"
        if not url.startswith(github_url_prefix):
            raise AssertionError
        repo_name = url.replace(github_url_prefix, "")
        log.info(f"Checking repo {repo_name}")

        try:
            gh_repo = g.get_repo(repo_name)
        except (GithubException, UnknownObjectException) as e:
            # Repo doesn't exist or other error
            log.info(f"Removing non-existent or inaccessible repo: {repo_name} ({e})")
            continue

        # Check if repo is archived
        if gh_repo.archived:
            log.info(f"Removing archived repo: {repo_name}")
            continue

        # Check if repo has been moved/renamed
        if gh_repo.html_url != url:
            log.info(f"Repo moved: {url} -> {gh_repo.html_url}")
            if gh_repo.html_url in known_urls:
                # duplicate already exists
                continue
            repo["url"] = gh_repo.html_url

        # Check if .cruft.json exists in root
        try:
            gh_repo.get_contents(".cruft.json")
        except UnknownObjectException:
            log.info(f"Removing repo without .cruft.json: {repo_name}")
            continue

        filtered_repos.append(repo)

    return filtered_repos


def main(args: Sequence[str] | None = None) -> None:
    setup_logging()
    if args is None:
        args = sys.argv[1:]
    if len(args) != 1:
        sys.exit("Usage: register-template-repos template-repos.yml")
    path = Path(args[0])
    github_token = os.environ["GITHUB_TOKEN"]
    repos = merge_repos(
        parse_repos(path),
        search_repos(github_token),
    )
    repos = filter_repos(repos, github_token)
    if repos:
        with path.open("w") as f:
            safe_dump(sorted(repos, key=lambda r: r["url"]), f, sort_keys=False)


if __name__ == "__main__":
    main()
