import os
import subprocess
from pathlib import Path
from typing import List, Optional


class GitService:
    """Simple Git utility service for creating branches and pushing code."""

    REPO_PATH = Path(os.getenv("GIT_REPO_PATH", Path(__file__).resolve().parents[2]))
    DEFAULT_REMOTE = os.getenv("GIT_REMOTE", "originby")

    @staticmethod
    def _run_git(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        if cwd is None:
            cwd = GitService.REPO_PATH

        return subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )

    @classmethod
    def check_repository(cls) -> None:
        result = cls._run_git(["rev-parse", "--is-inside-work-tree"])
        if result.returncode != 0 or result.stdout.strip() != "true":
            raise RuntimeError("Repository root is not a Git working tree.")

    @classmethod
    def create_or_switch_branch(cls, branch_name: str) -> str:
        # Check branch existence robustly using refs
        exists_check = cls._run_git(["show-ref", "--verify", f"refs/heads/{branch_name}"])

        if exists_check.returncode == 0:
            # branch exists locally; switch to it
            switch_result = cls._run_git(["switch", branch_name])
            if switch_result.returncode != 0:
                raise RuntimeError(f"Failed to switch to branch '{branch_name}': {switch_result.stderr.strip()}")
            return switch_result.stdout.strip() or f"Switched to existing branch '{branch_name}'"

        # branch does not exist locally; create it
        create_result = cls._run_git(["switch", "-c", branch_name])
        if create_result.returncode != 0:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {create_result.stderr.strip()}")
        return create_result.stdout.strip() or f"Created branch '{branch_name}'"

    @classmethod
    def stage_all(cls) -> str:
        result = cls._run_git(["add", "--all"])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to stage files: {result.stderr.strip()}")
        return result.stdout.strip() or "Staged all changes"

    @classmethod
    def commit_all(cls, commit_message: str) -> str:
        result = cls._run_git(["commit", "-m", commit_message])
        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            if "nothing to commit" in stderr.lower() or "nothing to commit" in stdout.lower():
                return "No changes to commit"
            raise RuntimeError(f"Failed to commit changes: {stderr or stdout}")
        return result.stdout.strip() or "Committed changes"

    @classmethod
    def push_branch(cls, branch_name: str, remote: Optional[str] = None) -> str:
        remote = remote or cls.DEFAULT_REMOTE
        result = cls._run_git(["push", "-u", remote, branch_name])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to push branch '{branch_name}' to remote '{remote}': {result.stderr.strip()}" )
        return result.stdout.strip() or f"Pushed branch '{branch_name}' to remote '{remote}'"

    @classmethod
    def get_status(cls) -> str:
        result = cls._run_git(["status", "--short"])
        if result.returncode != 0:
            raise RuntimeError(f"Failed to get git status: {result.stderr.strip()}")
        return result.stdout.strip()


# test
