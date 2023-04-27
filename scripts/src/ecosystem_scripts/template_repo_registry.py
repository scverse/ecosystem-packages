from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from pathlib import Path

from github import Github
from yaml import safe_dump, safe_load


def parse_repos(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    with path.open() as f:
        return set(safe_load(f))


def search_repos(github_token: str | None) -> set[str]:
    g = Github(github_token)
    files = g.search_code("filename:.cruft.json 'https://github.com/scverse/cookiecutter-scverse'")
    repos = {file.repository for file in files}
    return {r.url for r in repos}


def main(args: Iterable[str] | None = None) -> None:
    if args is None:
        args = sys.argv[1:]
    if len(args) != 1:
        sys.exit("Usage: register-template-repos template-repos.yml")
    path = Path(args[0])
    repos = parse_repos(path) | search_repos(os.environ["GITHUB_TOKEN"])
    if repos:
        with path.open("w") as f:
            safe_dump(sorted(repos), f)


if __name__ == "__main__":
    main()
