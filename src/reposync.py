#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile


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

    def get_patch(self, last_common_commit_hash: str) -> str:
        args = ["git", "format-patch", f"{last_common_commit_hash}..HEAD", "--stdout"]
        patch = subprocess.check_output(args, text=True, cwd=self.path)
        return patch

    def apply_patch(self, patch_content) -> None:
        with tempfile.NamedTemporaryFile(
            "wt", encoding="utf-8", newline="\n", suffix=".patch"
        ) as file:
            file.write(patch_content)
            args = ["git", "am", os.path.realpath(file.name)]
            subprocess.check_call(args, text=True, cwd=self.path)

    def get_commits(self) -> list[Commit]:
        try:
            return self.commits
        except AttributeError:
            pass
        args = [
            "git",
            "log",
            "--full-history",
            "--pretty=format:%H %aI %cI %s",
            "--date-order",
            "--max-count=1000",
        ]
        log_lines = subprocess.check_output(args, text=True, cwd=self.path).splitlines()
        ret: list[Commit] = []
        for line in log_lines:
            ret.append(Commit(line))
        self.commits = ret
        return ret

    def get_last_common_commit(self, other) -> Commit:
        commit_set = set(self.get_commits())
        commits = sorted(commit_set.intersection(other.get_commits()))
        if not commits:
            raise ValueError("there is no common commit")
        last_common_commit = commits[-1]
        for commit in self.get_commits():
            if commit == last_common_commit:
                return commit
        raise ValueError("there is no common commit")

    def get_author(self) -> str:
        args = ["git", "config", "--list"]
        configs = subprocess.check_output(args, text=True, cwd=self.path).splitlines()
        username = ""
        email = ""
        for config in configs:
            key, val = config.split("=", 1)
            if key == "user.name":
                username = val
            elif key == "user.email":
                email = val
        if username and email:
            return f"{username} <{email}>"
        raise ValueError(f"user is not configured for repository: {self.path}")


def update_autor(patch: str, new_author: str) -> str:
    pattern = re.compile(r"(From: )(.+ <\S+>)(\nDate: )")
    ret = pattern.sub(rf"\1{new_author}\3", patch)
    return ret


def main() -> None:
    author = ""
    if len(sys.argv) >= 3:
        repos = [
            Repository(sys.argv[1]),
            Repository(sys.argv[2]),
        ]
        if len(sys.argv) >= 4:
            author = sys.argv[3]
    else:
        print("USAGE: reposync REPO1 REPO2 [AUTHOR]")
        sys.exit(1)

    common_commit = [
        repos[0].get_last_common_commit(repos[1]),
        repos[1].get_last_common_commit(repos[0]),
    ]
    patches = [
        repos[0].get_patch(common_commit[0].commit_hash),
        repos[1].get_patch(common_commit[1].commit_hash),
    ]
    if len(patches[0]) == 0 and len(patches[1]) == 0:
        raise ValueError(
            "one of the repositories needs the last common commit to be on HEAD"
        )
    if len(patches[0]) == 0:
        patch_idx = 1
    else:
        patch_idx = 0
    patch = patches[patch_idx]
    if author:
        if author == "y":
            author = repos[1 - patch_idx].get_author()
        patch = update_autor(patch, author)
    repos[1 - patch_idx].apply_patch(patch)


if __name__ == "__main__":
    main()
