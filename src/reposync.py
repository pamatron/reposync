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

    def __hash__(self) -> int:
        return hash((self.commit_hash, self.author_date))


class Repository:
    path: str

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

    def list_commits(self) -> list[Commit]:
        ret: list[Commit] = []
        log_lines = subprocess.check_output(
            [
                "git",
                "log",
                "--full-history",
                "--pretty=format:%H %aI %cI %s",
                "--date-order",
                "--max-count=100",
            ],
            text=True,
            cwd=self.path,
        ).splitlines()
        for line in log_lines:
            ret.append(Commit(line))
            # print(ret[-1])
        return ret


def main() -> None:
    print(sys.argv)
    if len(sys.argv) == 3:
        repos = [
            Repository(sys.argv[1]),
            Repository(sys.argv[2]),
        ]
    else:
        return

    for repo in repos:
        repo.list_commits()


if __name__ == "__main__":
    main()
