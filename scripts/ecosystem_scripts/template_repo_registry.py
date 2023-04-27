import os

from github import Github


def main():
    g = Github(os.environ["GITHUB_PAT"])
    g.search_code("filename:.cruft.json 'https://github.com/scverse/cookiecutter-scverse'")


if __name__ == "__main__":
    main()
