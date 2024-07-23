#!/usr/bin/env python3
import os
import subprocess
import sys


class Commit:
    author_date: str
    commit_date: str
    commit_hash: str
    message: str

    def __init__(self, log_line: str) -> None:
        self.commit_hash, self.author_date, self.commit_date, self.message = (
            log_line.split(" ", maxsplit=3)
        )

    def __repr__(self) -> str:
        return f"Commit({self.commit_hash} {self.author_date} {self.commit_date} {self.message})"

    def __eq__(self, value) -> bool:
        try:
            return (
                self.message == value.message and self.author_date == value.author_date
            )
        except AttributeError:
            return False

    def __ne__(self, value: object) -> bool:
        return self != value

    def __hash__(self) -> int:
        return hash((self.message, self.author_date))

    def __lt__(self, value) -> bool:
        try:
            return self.author_date < value.author_date
        except AttributeError:
            return False


class Repository:
    path: str
    commits: list[Commit]

    def __init__(self, path: str) -> None:
        self.path = os.path.realpath(os.path.expanduser(path))
        if not os.path.isdir(self.path):
            raise ValueError(f"repository path is no directory: {self.path}")
        if not os.path.isdir(os.path.join(self.path, ".git")):
            raise ValueError(
                f"repository path is valid git repository root: {self.path}"
            )

    def get_diff(self, last_common_commit: str):
        cmd = f"git format-patch {last_common_commit}..HEAD --stdout > commits.patch"

    def get_commits(self) -> list[Commit]:
        try:
            return self.commits
        except AttributeError:
            pass
        ret: list[Commit] = []
        log_lines = subprocess.check_output(
            [
                "git",
                "log",
                "--full-history",
                "--pretty=format:%H %aI %cI %s",
                "--date-order",
                "--max-count=1000",
            ],
            text=True,
            cwd=self.path,
        ).splitlines()
        for line in log_lines:
            ret.append(Commit(line))
        self.commits = ret
        return ret

    def get_last_common_commit(self, other) -> Commit:
        commit_set = set(self.get_commits())
        commits = sorted(commit_set.intersection(other.get_commits()))
        if not commits:
            raise ValueError("there is no common commit")
        return commits[-1]


def main() -> None:
    if len(sys.argv) == 3:
        repos = [
            Repository(sys.argv[1]),
            Repository(sys.argv[2]),
        ]
    else:
        return

    common_commit = [
        repos[0].get_last_common_commit(repos[1]),
        repos[1].get_last_common_commit(repos[0]),
    ]
    print(common_commit)


if __name__ == "__main__":
    main()
