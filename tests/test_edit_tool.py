import pytest
from pathlib import Path
from tools.edit import tool_function

@pytest.fixture
def sample_dir(tmp_path):
    d = tmp_path / "test_repo"
    d.mkdir()
    return d

def test_create_file(sample_dir):
    file_path = sample_dir / "hello.txt"
    result = tool_function(
        command="create",
        path=str(file_path),
        file_text="Hello world\n"
    )
    assert "File created successfully" in result
    assert file_path.exists()

def test_view_file(sample_dir):
    file_path = sample_dir / "hello.txt"
    file_path.write_text("Line 1\nLine 2\n")
    result = tool_function(
        command="view",
        path=str(file_path)
    )
    assert "Line 1" in result
    assert "Line 2" in result

def test_str_replace(sample_dir):
    file_path = sample_dir / "hello.txt"
    file_path.write_text("foo bar\nbaz\n")
    result = tool_function(
        command="str_replace",
        path=str(file_path),
        old_str="bar",
        new_str="BAR"
    )
    assert "Replaced 'bar'" in result
    content = file_path.read_text()
    assert "foo BAR" in content

def test_str_replace_multiple(sample_dir):
    file_path = sample_dir / "hello2.txt"
    file_path.write_text("xyz xyz\n")
    result = tool_function(
        command="str_replace",
        path=str(file_path),
        old_str="xyz",
        new_str="abc"
    )
    assert "Found multiple occurrences" in result
    content = file_path.read_text()
    assert "xyz xyz" in content  # unchanged
