import pytest
from tools.edit import tool_function
from tools.bash import tool_function as bash_tool

def test_bash_echo():
    cmd = "echo 'Hello'"
    output = bash_tool(command=cmd)
    assert "Hello" in output

def test_edit_unknown_command():
    result = tool_function(command="unknown", path="/some/path")
    assert "Unknown command" in result
