import pytest
import re

def is_patch_valid(patch_str: str):
    """
    Parse a patch to see if it edits at least one non-test file.
    Return (bool, reason).
    """
    patch_str = patch_str.strip()
    if not patch_str:
        return (False, "Empty patch")

    diff_header_pattern = re.compile(r'^\+\+\+ b/(.+)$', re.MULTILINE)
    matches = diff_header_pattern.findall(patch_str)
    if not matches:
        return (False, "No files modified")

    # check for non-test
    # e.g. "tests/" is test path
    non_test_modified = False
    for m in matches:
        if not (m.startswith("tests/") or m.endswith("_test.py") or "test_" in m):
            non_test_modified = True
            break

    if not non_test_modified:
        return (False, "Only test files were modified")

    return (True, "Valid patch with source file modifications")


def test_empty_patch():
    valid, reason = is_patch_valid("")
    assert valid is False
    assert reason == "Empty patch"

def test_no_files_modified():
    patch = "diff --git a/foo b/foo\n"
    valid, reason = is_patch_valid(patch)
    assert valid is False
    assert reason == "No files modified"

def test_test_only():
    patch = """
diff --git a/tests/test_something.py b/tests/test_something.py
index abc123..def456 100644
--- a/tests/test_something.py
+++ b/tests/test_something.py
"""
    valid, reason = is_patch_valid(patch)
    assert valid is False
    assert reason == "Only test files were modified"

def test_valid_patch():
    patch = """
diff --git a/foo.py b/foo.py
index abc123..def456 100644
--- a/foo.py
+++ b/foo.py
+print("Hello")
"""
    valid, reason = is_patch_valid(patch)
    assert valid is True
    assert reason.startswith("Valid patch")
