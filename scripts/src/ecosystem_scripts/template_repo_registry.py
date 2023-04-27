import os

from github import Github


def main():
    g = Github(os.environ["GITHUB_TOKEN"])
    results = g.search_code("filename:.cruft.json 'https://github.com/scverse/cookiecutter-scverse'")
    for result in results:
        print(result)


if __name__ == "__main__":
    main()
