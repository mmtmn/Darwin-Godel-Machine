import os
from pathlib import Path
from typing import Optional, List

def tool_info():
    return {
        "name": "editor",
        "description": (
            "A custom editing tool for viewing, creating, and editing files.\n"
            "* `view`: see file contents (with optional line-range) or directory listing.\n"
            "* `create`: create a new file.\n"
            "* `str_replace`: replace a unique occurrence of one string with another.\n"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["view", "create", "str_replace"],
                    "description": "Which operation to perform."
                },
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                },
                "file_text": {
                    "type": "string",
                    "description": "Used when creating a new file."
                },
                "view_range": {
                    "type": "array",
                    "description": "Optional [start_line, end_line] for partial view.",
                    "items": {"type": "integer"},
                    "minItems": 2,
                    "maxItems": 2
                },
                "old_str": {
                    "type": "string",
                    "description": "Used in `str_replace` to find text to replace."
                },
                "new_str": {
                    "type": "string",
                    "description": "Used in `str_replace` for the replacement."
                }
            },
            "required": ["command", "path"]
        }
    }

def validate_path(path: str, command: str) -> Path:
    path_obj = Path(path)
    if command == "view":
        if not path_obj.exists():
            raise ValueError(f"{path} does not exist.")
    elif command == "create":
        if path_obj.exists():
            raise ValueError(f"Cannot create file, path {path} already exists.")
    elif command == "str_replace":
        if not path_obj.is_file():
            raise ValueError(f"{path} is not a valid file for str_replace.")
    return path_obj

def read_file(path: Path) -> str:
    try:
        return path.read_text()
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")

def write_file(path: Path, content: str):
    try:
        path.write_text(content)
    except Exception as e:
        raise ValueError(f"Failed to write file: {e}")

def view_path(path_obj: Path, view_range: Optional[List[int]] = None) -> str:
    if path_obj.is_dir():
        # list directory contents up to 1 level
        items = sorted([p.name for p in path_obj.iterdir() if not p.name.startswith(".")])
        return "\n".join(items)
    else:
        content = read_file(path_obj)
        lines = content.splitlines()
        if view_range:
            start, end = view_range
            if start < 1: 
                raise ValueError("Start line must be >= 1.")
            if end < start:
                raise ValueError("End line must be >= start line.")
            sublines = lines[start-1:end] if end <= len(lines) else lines[start-1:]
            result = []
            for i, line_text in enumerate(sublines, start):
                result.append(f"{i}\t{line_text}")
            return "\n".join(result)
        else:
            result = []
            for i, line_text in enumerate(lines, 1):
                result.append(f"{i}\t{line_text}")
            return "\n".join(result)

def str_replace_in_file(path: Path, old_str: str, new_str: str) -> str:
    content = read_file(path)
    count_occ = content.count(old_str)
    if count_occ == 0:
        return f"Error: Could not find '{old_str}' in {path}"
    if count_occ > 1:
        return f"Error: Found multiple occurrences of '{old_str}' in {path}"
    new_content = content.replace(old_str, new_str)
    write_file(path, new_content)
    return f"Replaced '{old_str}' with '{new_str}' in {path}"

def tool_function(**kwargs) -> str:
    command = kwargs.get("command")
    path = kwargs.get("path")
    path_obj = validate_path(path, command)

    if command == "view":
        vr = kwargs.get("view_range")
        try:
            return view_path(path_obj, vr)
        except Exception as e:
            return f"Error: {e}"

    elif command == "create":
        file_text = kwargs.get("file_text")
        if not file_text:
            return "Error: Missing 'file_text' for create."
        try:
            write_file(path_obj, file_text)
            return f"File created successfully at {path_obj}"
        except Exception as e:
            return f"Error: {e}"

    elif command == "str_replace":
        old_str = kwargs.get("old_str")
        new_str = kwargs.get("new_str")
        if not old_str or not new_str:
            return "Error: Missing old_str or new_str"
        return str_replace_in_file(path_obj, old_str, new_str)

    return f"Error: Unknown command {command}"
