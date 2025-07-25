from ast import Dict
import os
from pathlib import Path
import re
from typing import Set
from src.types.files import File, Repo, Function


async def find_readme(path: str) -> str | None:
    """
    Find the README file in a repository.
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.lower().startswith("readme"):
                file_path = Path(root) / file
                return str(file_path.relative_to(path))
    return None


async def build_repo_model(path: str) -> Repo:
    """
    Recursively analyze all files in a folder and find their dependencies.

    Args:
        path: Path to the folder to analyze

    Returns:
        Repo object with categorized files and their dependencies
    """
    if not os.path.exists(path):
        raise ValueError(f"Path does not exist: {path}")

    root_path = Path(path).resolve()
    files_map: Dict[str, File] = {}
    all_file_paths: Set[str] = set()
    directories: Set[str] = set()

    # First pass: collect all file paths
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not _should_exclude_directory(d)]
        
        # Check if current directory should be excluded
        current_dir = Path(root)
        relative_current_dir = current_dir.relative_to(root_path)
        if any(_should_exclude_directory(part) for part in relative_current_dir.parts):
            continue
            
        directories.update(dirs)
        for file in files:
            file_path = Path(root) / file
            if _should_include_file(file_path, root_path):
                relative_path = file_path.relative_to(root_path)
                all_file_paths.add(str(relative_path))

    # Second pass: analyze dependencies
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories  
        dirs[:] = [d for d in dirs if not _should_exclude_directory(d)]
        
        # Check if current directory should be excluded
        current_dir = Path(root)
        relative_current_dir = current_dir.relative_to(root_path)
        if any(_should_exclude_directory(part) for part in relative_current_dir.parts):
            continue
        
        for file in files:
            file_path = Path(root) / file
            if not _should_include_file(file_path, root_path):
                continue

            relative_path = str(file_path.relative_to(root_path))

            # Calculate number of lines
            line_count = 0
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
            except (UnicodeDecodeError, OSError):
                # If we can't read the file, set line count to 0
                line_count = 0

            # Initialize default values
            imports = []
            functions = []
            temp_dep_paths = []
            file_description = None

            # Analyze dependencies for Python and TypeScript files
            if file_path.suffix in [".py", ".ts", ".tsx"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    temp_dep_paths, imports, functions, file_description = (
                        await hydrate_files(
                            content, file_path, root_path, all_file_paths
                        )
                    )

                except (UnicodeDecodeError, OSError):
                    # Skip files that can't be read
                    pass

            # Create File object
            file_obj = File(
                name=relative_path,
                number_of_lines=line_count,
                imports=imports,
                functions=functions,
                description=file_description,
                local_path=str(file_path),
            )
            files_map[relative_path] = file_obj

            # Store temporary dependency paths for later resolution
            if temp_dep_paths:
                file_obj._temp_dep_paths = temp_dep_paths


    # Categorize files into readme, package, and regular files
    readme_files = []
    package_files = []
    regular_files = []

    for file_obj in files_map.values():
        file_name = Path(file_obj.name).name.lower()

        # Check if it's a README file
        if file_name.startswith("readme"):
            readme_files.append(file_obj)
        # Check if it's a package file
        elif file_name in [
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "poetry.lock",
        ]:
            package_files.append(file_obj)
        else:
            regular_files.append(file_obj)

    return Repo(
        readme=readme_files,
        files=regular_files,
        package_files=package_files,
        directories=directories,
    )


async def hydrate_files(
    content: str, file_path: Path, root_path: Path, all_files: Set[str]
) -> tuple[list[str], list[str], list[Function], str | None]:
    """
    Extract dependencies, imports, functions, and file description from file content.

    Args:
        content: File content as string
        file_path: Path to the current file
        root_path: Root path of the repository
        all_files: Set of all file paths in the repository

    Returns:
        Tuple of (dependencies, imports, functions, file_description)
    """
    dependencies = []
    imports = []
    functions = []
    file_description = None

    file_extension = file_path.suffix.lower()

    if file_extension == ".py":
        dependencies, imports, functions, file_description = await _extract_python_info(
            content, file_path, root_path, all_files
        )
    elif file_extension in [".ts", ".tsx", ".js"]:
        dependencies, imports, functions, file_description = (
            await _extract_typescript_info(content, file_path, root_path, all_files)
        )

    return dependencies, imports, functions, file_description


async def _extract_python_info(
    content: str, file_path: Path, root_path: Path, all_files: Set[str]
) -> tuple[list[str], list[str], list[Function], str | None]:
    """Extract dependencies, imports, functions, and file description from Python files."""
    dependencies = []
    imports = []
    functions = []
    file_description = None

    lines = content.split("\n")

    # Extract file description from top comments or docstring
    file_description = _extract_file_description(content, "python")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Extract imports
        if line.startswith("import ") or line.startswith("from "):
            imports.append(line)

            # Extract dependencies (local imports)
            if line.startswith("from "):
                # Handle "from .module import" or "from src.module import"
                match = re.match(r"from\s+([\w.]+)\s+import", line)
                if match:
                    module_path = match.group(1)
                    if module_path.startswith("."):
                        # Relative import
                        dep_path = _resolve_relative_import(
                            module_path, file_path, root_path, all_files
                        )
                        if dep_path:
                            dependencies.append(dep_path)
                    elif module_path.startswith("src"):
                        # Absolute import from src
                        dep_path = _resolve_absolute_import(
                            module_path, root_path, all_files
                        )
                        if dep_path:
                            dependencies.append(dep_path)
            elif line.startswith("import "):
                # Handle "import module"
                match = re.match(r"import\s+([\w.]+)", line)
                if match:
                    module_path = match.group(1)
                    if module_path.startswith("src"):
                        dep_path = _resolve_absolute_import(
                            module_path, root_path, all_files
                        )
                        if dep_path:
                            dependencies.append(dep_path)

        # Extract function definitions with detailed info
        func_match = re.match(r"(async\s+)?def\s+(\w+)\s*\(([^)]*)\):", line)
        if func_match:
            func_name = func_match.group(2)
            func_args = func_match.group(3)

            # Look for function docstring in the following lines
            func_description = None
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            if j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    # Extract docstring
                    quote_type = '"""' if next_line.startswith('"""') else "'''"
                    if next_line.count(quote_type) >= 2:
                        # Single line docstring
                        func_description = next_line.strip(quote_type).strip()
                    else:
                        # Multi-line docstring
                        docstring_lines = [next_line.lstrip(quote_type)]
                        k = j + 1
                        while k < len(lines) and not lines[k].strip().endswith(
                            quote_type
                        ):
                            docstring_lines.append(lines[k])
                            k += 1
                        if k < len(lines):
                            docstring_lines.append(lines[k].rstrip(quote_type))
                        func_description = "\n".join(docstring_lines).strip()

            functions.append(
                Function(
                    name=func_name, arguments=func_args, description=func_description
                )
            )

        i += 1

    return dependencies, imports, functions, file_description


async def _extract_typescript_info(
    content: str, file_path: Path, root_path: Path, all_files: Set[str]
) -> tuple[list[str], list[str], list[Function], str | None]:
    """Extract dependencies, imports, functions, and file description from TypeScript/JavaScript files."""
    dependencies = []
    imports = []
    functions = []
    file_description = None

    lines = content.split("\n")

    # Extract file description from top comments
    file_description = _extract_file_description(content, "typescript")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Extract imports
        if line.startswith("import "):
            imports.append(line)

            # Extract dependencies (local imports)
            match = re.match(r'import.*from\s+[\'"]([^\'"]+)[\'"]', line)
            if match:
                import_path = match.group(1)
                if import_path.startswith("."):
                    # Relative import
                    dep_path = _resolve_ts_relative_import(
                        import_path, file_path, root_path, all_files
                    )
                    if dep_path:
                        dependencies.append(dep_path)

        # Extract function definitions
        func_description = None

        # Look for JSDoc comments before function
        if line.startswith("/**"):
            jsdoc_lines = []
            j = i
            while j < len(lines):
                jsdoc_lines.append(lines[j])
                if lines[j].strip().endswith("*/"):
                    break
                j += 1
            if jsdoc_lines:
                func_description = "\n".join(jsdoc_lines).strip()
                i = j + 1
                if i < len(lines):
                    line = lines[i].strip()
                else:
                    continue

        # Function declarations
        func_match = re.match(
            r"(export\s+)?(async\s+)?function\s+(\w+)\s*\(([^)]*)\)", line
        )
        if func_match:
            func_name = func_match.group(3)
            func_args = func_match.group(4)
            functions.append(
                Function(
                    name=func_name, arguments=func_args, description=func_description
                )
            )

        # Arrow functions
        arrow_match = re.match(
            r"(export\s+)?const\s+(\w+)\s*=\s*(\(([^)]*)\)\s*=>|async\s*\(([^)]*)\)\s*=>)",
            line,
        )
        if arrow_match:
            func_name = arrow_match.group(2)
            func_args = arrow_match.group(4) or arrow_match.group(5) or ""
            functions.append(
                Function(
                    name=func_name, arguments=func_args, description=func_description
                )
            )

        # Method definitions in classes
        method_match = re.match(r"\s*(async\s+)?(\w+)\s*\(([^)]*)\)\s*{", line)
        if (
            method_match
            and not line.strip().startswith("if")
            and not line.strip().startswith("for")
            and not line.strip().startswith("while")
        ):
            func_name = method_match.group(2)
            func_args = method_match.group(3)
            functions.append(
                Function(
                    name=func_name, arguments=func_args, description=func_description
                )
            )

        i += 1

    return dependencies, imports, functions, file_description


def _resolve_relative_import(
    module_path: str, file_path: Path, root_path: Path, all_files: Set[str]
) -> str:
    """Resolve relative Python imports to actual file paths."""
    # Remove leading dots and convert to path
    relative_parts = module_path.lstrip(".").split(".")

    # Start from the directory containing the current file
    current_dir = file_path.parent

    # Go up one directory for each leading dot beyond the first
    dots = len(module_path) - len(module_path.lstrip("."))
    for _ in range(dots):
        current_dir = current_dir.parent

    # Build the potential file path
    target_path = current_dir
    for part in relative_parts:
        target_path = target_path / part

    # Try adding .py extension
    py_file = str((target_path.with_suffix(".py")).relative_to(root_path))
    if py_file in all_files:
        return py_file

    # Try __init__.py in directory
    init_file = str((target_path / "__init__.py").relative_to(root_path))
    if init_file in all_files:
        return init_file

    return None


def _resolve_absolute_import(
    module_path: str, root_path: Path, all_files: Set[str]
) -> str:
    """Resolve absolute Python imports to actual file paths."""
    parts = module_path.split(".")
    target_path = root_path

    for part in parts:
        target_path = target_path / part

    # Try adding .py extension
    py_file = str((target_path.with_suffix(".py")).relative_to(root_path))
    if py_file in all_files:
        return py_file

    # Try __init__.py in directory
    init_file = str((target_path / "__init__.py").relative_to(root_path))
    if init_file in all_files:
        return init_file

    return None


def _resolve_ts_relative_import(
    import_path: str, file_path: Path, root_path: Path, all_files: Set[str]
) -> str:
    """Resolve relative TypeScript imports to actual file paths."""
    # Start from the directory containing the current file
    current_dir = file_path.parent

    # Resolve the relative path
    target_path = (current_dir / import_path).resolve()

    # Try different extensions
    for ext in [".ts", ".tsx", ".js"]:
        potential_file = str((target_path.with_suffix(ext)).relative_to(root_path))
        if potential_file in all_files:
            return potential_file

    # Try index files
    for ext in [".ts", ".tsx", ".js"]:
        index_file = str((target_path / f"index{ext}").relative_to(root_path))
        if index_file in all_files:
            return index_file

    return None


def _extract_file_description(content: str, file_type: str) -> str | None:
    """
    Extract file description from top comments or docstrings.

    Args:
        content: File content as string
        file_type: Type of file ("python" or "typescript")

    Returns:
        File description string or None if not found
    """
    lines = content.split("\n")
    description_lines = []

    if file_type == "python":
        # Look for module docstring or top comments
        i = 0
        # Skip empty lines and imports at the top
        while i < len(lines):
            line = lines[i].strip()
            if (
                not line
                or line.startswith("#")
                or line.startswith("from ")
                or line.startswith("import ")
            ):
                if line.startswith("#"):
                    description_lines.append(line.lstrip("# "))
                i += 1
            else:
                break

        # Check for module docstring
        if i < len(lines) and lines[i].strip().startswith('"""'):
            quote_type = '"""'
            if lines[i].strip().count(quote_type) >= 2:
                # Single line docstring
                description_lines.append(lines[i].strip().strip(quote_type).strip())
            else:
                # Multi-line docstring
                docstring_lines = [lines[i].strip().lstrip(quote_type)]
                i += 1
                while i < len(lines) and not lines[i].strip().endswith(quote_type):
                    docstring_lines.append(lines[i].strip())
                    i += 1
                if i < len(lines):
                    docstring_lines.append(lines[i].strip().rstrip(quote_type))
                description_lines.extend(docstring_lines)

    elif file_type == "typescript":
        # Look for top comments
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            elif stripped.startswith("//"):
                description_lines.append(stripped.lstrip("/ "))
            elif stripped.startswith("/*"):
                # Multi-line comment
                if stripped.endswith("*/"):
                    # Single line /* comment */
                    description_lines.append(stripped.lstrip("/* ").rstrip(" */"))
                else:
                    # Start of multi-line comment
                    description_lines.append(stripped.lstrip("/* "))
                    break
            else:
                # Hit actual code, stop looking
                break

    if description_lines:
        return "\n".join(description_lines).strip()
    return None


def _should_exclude_directory(dir_name: str) -> bool:
    """
    Check if a directory should be excluded from analysis.

    Args:
        dir_name: Name of the directory

    Returns:
        True if directory should be excluded, False otherwise
    """
    excluded_dirs = {
        "tests", "test", "example", "examples", ".venv", "venv", 
        ".git", ".vscode", "cypress", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", "dist", "build", ".tox"
    }
    return dir_name.lower() in excluded_dirs


def _should_include_file(file_path: Path, root_path: Path) -> bool:
    """
    Check if a file should be included in the analysis.

    Args:
        file_path: Path to the file
        root_path: Root path of the repository

    Returns:
        True if file should be included, False otherwise
    """
    # Check if file is in an excluded directory path
    relative_path = file_path.relative_to(root_path)
    path_parts = relative_path.parts
    
    # Check if any part of the path is an excluded directory
    excluded_dirs = {
        "tests", "test", "example", "examples", ".venv", "venv", 
        ".git", ".vscode", "cypress", "node_modules", "__pycache__",
        ".pytest_cache", ".mypy_cache", "dist", "build", ".tox"
    }
    
    for part in path_parts[:-1]:  # Exclude the filename itself
        if part.lower() in excluded_dirs:
            return False
    
    # Include files with specific extensions
    if file_path.suffix.lower() in [".py", ".ts", ".js", ".tsx", ".md", ".txt"]:
        return True

    if file_path.name.lower() in [
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "poetry.lock",
    ]:
        return True

    if file_path.name.startswith("test"):
        return False

    return False
