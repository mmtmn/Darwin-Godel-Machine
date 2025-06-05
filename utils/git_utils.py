import os
import subprocess
from typing import Optional

def init_repo(path: str):
    """
    Initialize a new git repository at 'path'.
    """
    subprocess.run(["git", "init", "."], cwd=path, check=True)

def commit_all(path: str, message: str):
    """
    Commit all changes in the repository at 'path' with a commit message.
    """
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=path, check=True)

def get_current_commit(path: str) -> str:
    """
    Return the current HEAD commit hash at 'path'.
    """
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True)
    if proc.returncode == 0:
        return proc.stdout.strip()
    return ""

def reset_to_commit(path: str, commit_hash: str):
    """
    Reset the repository at 'path' to a given commit hash.
    """
    if not commit_hash:
        return
    subprocess.run(["git", "reset", "--hard", commit_hash], cwd=path, check=True)

def diff_versus_commit(path: str, commit_hash: str) -> str:
    """
    Return the diff of the working directory vs the commit.
    """
    if not commit_hash:
        return ""
    proc = subprocess.run(["git", "diff", commit_hash], cwd=path, capture_output=True, text=True)
    return proc.stdout

def apply_patch(path: str, patch_str: str) -> bool:
    """
    Apply a patch string to the repo at 'path'.
    """
    if not patch_str.strip():
        return False
    p = subprocess.Popen(["git", "apply", "-"], cwd=path, stdin=subprocess.PIPE, text=True)
    p.communicate(input=patch_str)
    return p.wait() == 0
