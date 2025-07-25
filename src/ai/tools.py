from src.types.files import Repo


TOOLS = [
        {
            "type": "function",
            "function": {
                "strict": True,
                "name": "get_function_description",
                "description": "Get description of the function from a specific file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "function_name": {
                            "type": "string",
                            "description": "The name of the function to analyze",
                        },
                        "file_name": {
                            "type": "string",
                            "description": "The name of the file containing the function",
                        },
                    },
                    "required": ["function_name", "file_name"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "strict": True,
                "name": "get_file_description",
                "description": "Get the full content of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["file_path"],
                    "additionalProperties": False,
                },
            },
        },
    ]


async def get_file_description(file_path: str, repo: Repo) -> str:
    local_path = ""
    # TODO: we can do much better here
    for file in repo.files:
        if file.name == file_path:
            local_path = file.local_path

    if not local_path:
        print(f"Error: File {file_path} not found in repository")
        return f"Error: File {file_path} not found in repository"

    try:
        with open(local_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Check if file is too large (over 500 lines) and return a summary
        if len(lines) > 500:
            # Return first 200 lines and last 100 lines
            first_part = lines[:200]
            last_part = lines[-100:]
            return "".join(first_part) + "\n\n[... file truncated ...]\n\n" + "".join(last_part)
        else:
            return "\n".join(lines)
    except FileNotFoundError:
        print(f"Error: File {local_path} does not exist")
        return f"Error: File {local_path} does not exist"
    except PermissionError:
        print(f"Error: Permission denied reading file {local_path}")
        return f"Error: Permission denied reading file {local_path}"
    except Exception as e:
        print(f"Error reading file {local_path}: {str(e)}")
        return f"Error reading file {local_path}: {str(e)}"


async def get_function_description(file_name: str, function_name: str, repo: Repo) -> str:
    local_path = ""
    # TODO: we can do much better here
    for file in repo.files:
        if file.name == file_name:
            local_path = file.local_path

    if not local_path:
        print(f"Error: File {file_name} not found in repository")
        return f"Error: File {file_name} not found in repository"

    try:
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File {local_path} does not exist")
        return f"Error: File {local_path} does not exist"
    except PermissionError:
        print(f"Error: Permission denied reading file {local_path}")
        return f"Error: Permission denied reading file {local_path}"
    except Exception as e:
        print(f"Error reading file {local_path}: {str(e)}")
        return f"Error reading file {local_path}: {str(e)}"

    lines = content.split("\n")

    # Find the function definition
    for i, line in enumerate(lines):
        # Python function patterns
        python_patterns = [
            f"def {function_name}(",
            f"def {function_name} (",
            f"async def {function_name}(",
            f"async def {function_name} (",
        ]

        # TypeScript/JavaScript function patterns
        ts_js_patterns = [
            f"function {function_name}(",
            f"function {function_name} (",
            f"async function {function_name}(",
            f"async function {function_name} (",
            f"export function {function_name}(",
            f"export function {function_name} (",
            f"export async function {function_name}(",
            f"export async function {function_name} (",
            f"const {function_name} = (",
            f"const {function_name} = async (",
            f"export const {function_name} = (",
            f"export const {function_name} = async (",
            f"let {function_name} = (",
            f"var {function_name} = (",
            f"{function_name}(",  # Method in class or object
            f"{function_name} (",  # Method in class or object with space
            f"{function_name}: (",  # Object method definition
            f"{function_name}: async (",  # Async object method
        ]

        # Check all patterns
        all_patterns = python_patterns + ts_js_patterns

        for pattern in all_patterns:
            if pattern in line:
                # Return the function definition and next 100 lines
                end_index = min(
                    i + 101, len(lines)
                )  # +1 for the function line + 100 after
                return "\n".join(lines[i:end_index])

    return f"Function '{function_name}' not found in {file_name}"
