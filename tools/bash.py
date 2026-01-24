import subprocess
from typing import Optional


def tool_info():
    return {
        "name": "bash",
        "description": (
            "Execute a shell command and return its output.\n"
            "* `command`: the shell command to run.\n"
            "* `timeout`: optional timeout in seconds.\n"
            "* `cwd`: optional working directory.\n"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute."
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional timeout in seconds."
                },
                "cwd": {
                    "type": "string",
                    "description": "Optional working directory."
                }
            },
            "required": ["command"]
        }
    }


def _format_output(stdout: str, stderr: str) -> str:
    if stderr:
        return f"{stdout}\n{stderr}".strip()
    return stdout.strip()


def tool_function(**kwargs) -> str:
    command = kwargs.get("command")
    timeout = kwargs.get("timeout")
    cwd = kwargs.get("cwd")

    if not command:
        return "Error: Missing 'command'."

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        if proc.returncode != 0:
            output = _format_output(proc.stdout, proc.stderr)
            return f"Error: Command failed with exit code {proc.returncode}.\n{output}".strip()
        return _format_output(proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired as exc:
        output = _format_output(exc.stdout or "", exc.stderr or "")
        return f"Error: Command timed out after {timeout} seconds.\n{output}".strip()
    except Exception as exc:
        return f"Error: {exc}"
