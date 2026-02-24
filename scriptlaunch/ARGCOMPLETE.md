# Autocomplete with scriptlaunch

## How Completion Works

scriptlaunch has a smart bash completion system that works in two modes:

### 1. Script Name Completion (always works)
When you type the script name:
```bash
scriptlaunch my_scr<TAB>
```
The completion script lists all available scripts in `$SCRIPTLAUNCH_PATH`.

### 2. Script Argument Completion (requires argcomplete in your scripts)
When you type arguments after the script name:
```bash
scriptlaunch my_script --opt<TAB>
```
The completion script **delegates** to the target script's own argcomplete configuration!

## Making Your Scripts Support Autocomplete

To add autocomplete to your Python scripts, just use argcomplete:

```python
#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(description='My script')
    parser.add_argument('--input', help='Input file')
    parser.add_argument('--mode', choices=['fast', 'slow'])

    # Enable argcomplete - must come before parse_args()
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass  # Optional dependency

    args = parser.parse_args()
    # ... your code ...

if __name__ == '__main__':
    main()
```

That's it! When you run this via scriptlaunch, the completion will work automatically:

```bash
scriptlaunch my_script --<TAB>
# Shows: --input  --mode  --help

scriptlaunch my_script --mode <TAB>
# Shows: fast  slow
```

## Setup

### Install argcomplete (for your scripts)
```bash
pip install argcomplete
```

You don't need to register anything! The bash completion script that comes with scriptlaunch handles everything.

## Example

See `example_scripts/demo_argcomplete.py` for a working example:

```bash
# Install scriptlaunch
./install.sh

# Set up your scripts directory
export SCRIPTLAUNCH_PATH="$(pwd)/example_scripts"

# Try it out
scriptlaunch demo_argcomplete --<TAB>
# You'll see: --input  --output  --verbose  --mode  --help

scriptlaunch demo_argcomplete --mode <TAB>
# You'll see: fast  normal  thorough
```

## How It Works Internally

1. **Script name completion**: The bash completion script calls `scriptlaunch --list` to get available scripts
2. **Argument completion**: The bash completion script:
   - Finds the target script file
   - Checks if it contains "argcomplete" (simple heuristic)
   - If yes, invokes the script with argcomplete's special environment variables
   - The script's argcomplete provides completions
   - Falls back to file completion if no argcomplete found

This means scriptlaunch is **transparent** - your scripts work the same whether called directly or via scriptlaunch.

## Requirements

- Basic completion: Works with just bash (no dependencies)
- Advanced completion: Your scripts need `argcomplete` installed
- The completion delegation works for Python scripts (.py files)

## Bash Scripts

For bash scripts, you can also use bash's built-in completion features, but that requires more manual setup. Python with argcomplete is the recommended approach for complex scripts.
