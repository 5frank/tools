#!/usr/bin/env python3
"""
ScriptLaunch - A CLI tool to run scripts from a centralized directory
"""
import os
import sys
import subprocess
from pathlib import Path


def get_script_base_path():
    """Get the base path for scripts from environment variable."""
    script_path = os.environ.get('SCRIPTLAUNCH_PATH')
    if not script_path:
        print("Error: SCRIPTLAUNCH_PATH environment variable not set", file=sys.stderr)
        sys.exit(1)

    path = Path(script_path).expanduser()
    if not path.exists():
        print(f"Error: Script path does not exist: {path}", file=sys.stderr)
        sys.exit(1)

    return path


def find_script(script_name, base_path):
    """Find the script file, trying common extensions."""
    # Try common script extensions in order
    extensions = ['.py', '.sh', '']  # Empty string for no extension

    for ext in extensions:
        script_file = base_path / f"{script_name}{ext}"
        if script_file.exists() and script_file.is_file():
            return script_file

    # If nothing found, show error
    print(f"Error: Script not found: {script_name}", file=sys.stderr)
    print(f"\nSearched in: {base_path}", file=sys.stderr)
    print(f"Tried extensions: .py, .sh, and no extension", file=sys.stderr)
    sys.exit(1)


def list_scripts(base_path, prefix=""):
    """List all available scripts for autocomplete."""
    scripts = set()  # Use set to avoid duplicates
    extensions = ['*.py', '*.sh']

    try:
        # Find scripts with common extensions
        for pattern in extensions:
            for item in base_path.rglob(pattern):
                if item.is_file():
                    # Get relative path without extension
                    rel_path = item.relative_to(base_path)
                    script_path = str(rel_path.with_suffix(''))

                    # Filter by prefix if provided
                    if prefix and not script_path.startswith(prefix):
                        continue

                    scripts.add(script_path)

        # Also find executable files without extensions
        for item in base_path.rglob("*"):
            if item.is_file() and item.suffix == '' and os.access(item, os.X_OK):
                rel_path = item.relative_to(base_path)
                script_path = str(rel_path)

                # Filter by prefix if provided
                if prefix and not script_path.startswith(prefix):
                    continue

                scripts.add(script_path)

    except Exception as e:
        print(f"Error listing scripts: {e}", file=sys.stderr)
        sys.exit(1)

    return sorted(scripts)


def run_script(script_file, args):
    """Execute the script with given arguments."""
    try:
        # Determine how to run the script based on extension
        if script_file.suffix == '.py':
            # Run Python scripts with the Python interpreter
            result = subprocess.run(
                [sys.executable, str(script_file)] + args,
                check=False
            )
        elif script_file.suffix == '.sh':
            # Run shell scripts with bash (works even without +x)
            result = subprocess.run(
                ['bash', str(script_file)] + args,
                check=False
            )
        else:
            # For other scripts, run directly if executable
            if not os.access(script_file, os.X_OK):
                print(f"Error: Script is not executable: {script_file}", file=sys.stderr)
                print(f"Try: chmod +x {script_file}", file=sys.stderr)
                sys.exit(1)

            result = subprocess.run(
                [str(script_file)] + args,
                check=False
            )
        sys.exit(result.returncode)
    except Exception as e:
        print(f"Error running script: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    # Handle --list command for bash completion (script name completion)
    if len(sys.argv) >= 2 and sys.argv[1] == "--list":
        base_path = get_script_base_path()
        prefix = sys.argv[2] if len(sys.argv) > 2 else ""
        scripts = list_scripts(base_path, prefix)
        for script in scripts:
            print(script)
        return

    # Simple argument handling - just take script name and pass everything else through
    if len(sys.argv) < 2:
        print("Usage: scriptlaunch <script_name> [args...]", file=sys.stderr)
        print("\nSet SCRIPTLAUNCH_PATH environment variable to your scripts directory", file=sys.stderr)
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]  # Everything else goes to the script

    # Execute the script
    base_path = get_script_base_path()
    script_file = find_script(script_name, base_path)

    run_script(script_file, script_args)


if __name__ == "__main__":
    main()
