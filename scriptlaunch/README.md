# ScriptLaunch

A simple CLI tool to run scripts (Python, Bash, and other executables) from a centralized directory with bash autocomplete support.

## Features

- Run scripts from anywhere using `scriptlaunch <script_name>` or the short alias `sl`
- Automatically finds scripts in subdirectories (e.g., `scriptlaunch foo/bar` runs `$SCRIPTLAUNCH_PATH/foo/bar.py`)
- Bash autocomplete for script names and script arguments (delegates to your scripts)
- Pass arguments through to your scripts transparently
- Supports Python, Bash, and other executable scripts

## Installation

1. Clone or download this repository
2. Run the installation script:
   ```bash
   cd script_launcher
   chmod +x install.sh
   ./install.sh
   ```

3. Add to your `~/.bashrc` or `~/.bash_profile`:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   export SCRIPTLAUNCH_PATH="/path/to/your/scripts"
   ```

   **Note:** The installer also creates `sl` as a short command (symlink to `scriptlaunch`).

4. Reload your shell:
   ```bash
   source ~/.bashrc
   ```

## Autocomplete for Script Arguments

scriptlaunch supports **delegating autocomplete to your scripts**! This means:

- **Script names** are auto-completed automatically
- **Script arguments** are auto-completed if your scripts use argcomplete

To enable argument completion in your Python scripts, add argcomplete:

```python
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--your-option', help='...')

    # Add this before parse_args()
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()
```

Then install argcomplete:
```bash
pip install argcomplete
```

Now when you use scriptlaunch, your script's options will autocomplete:
```bash
scriptlaunch your_script --<TAB>
# Shows all your script's options!
```

See `ARGCOMPLETE.md` for detailed documentation and `example_scripts/demo_argcomplete.py` for a working example.

## Usage

### Basic usage
```bash
scriptlaunch my_script
# Or use the short alias:
sl my_script
```

This will run `$SCRIPTLAUNCH_PATH/my_script.py`

### Nested scripts
```bash
scriptlaunch utils/backup
```

This will run `$SCRIPTLAUNCH_PATH/utils/backup.py`

### Passing arguments
```bash
scriptlaunch my_script arg1 arg2 --flag
```

All arguments after the script name are passed to the script.

### Autocomplete
Just type `scriptlaunch` (or `sl`) and press TAB to see all available scripts. Start typing a script name and press TAB to autocomplete.

**Note:** Autocomplete works for both `scriptlaunch` and the `sl` alias!

## Directory Structure

Example scripts directory:
```
$SCRIPTLAUNCH_PATH/
├── backup.py          # Python script
├── deploy.sh          # Bash script
├── utils/
│   ├── cleanup.py     # Python script
│   └── monitor.sh     # Bash script
└── dev/
    └── setup          # Executable script (no extension)
```

You can then run:
- `scriptlaunch backup` → runs backup.py
- `scriptlaunch deploy` → runs deploy.sh
- `scriptlaunch utils/cleanup` → runs utils/cleanup.py
- `scriptlaunch dev/setup` → runs dev/setup

The tool automatically detects script types and runs them appropriately:
- `.py` files: runs with Python
- `.sh` files: runs with Bash (doesn't need +x permission)
- Other executables: runs directly (requires +x permission)

## Requirements

- Python 3.6+
- Bash shell
- `argcomplete` (optional, only needed if your scripts want argument completion)

## License

MIT
