#!/usr/bin/env bash
# Installation script for scriptlaunch

set -e

echo "Installing scriptlaunch..."

# Determine installation directory
INSTALL_DIR="${HOME}/.local/bin"
COMPLETION_DIR="${HOME}/.local/share/bash-completion/completions"

# Create directories if they don't exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$COMPLETION_DIR"

# Copy the main script
echo "Installing scriptlaunch to $INSTALL_DIR..."
cp scriptlaunch.py "$INSTALL_DIR/scriptlaunch"
chmod +x "$INSTALL_DIR/scriptlaunch"

# Create symlink for sl alias
echo "Creating symlink: sl -> scriptlaunch"
ln -sf "$INSTALL_DIR/scriptlaunch" "$INSTALL_DIR/sl"

# Copy the completion script
echo "Installing bash completion to $COMPLETION_DIR..."
cp scriptlaunch-completion.bash "$COMPLETION_DIR/scriptlaunch"

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Make sure $INSTALL_DIR is in your PATH"
echo "   Add this to your ~/.bashrc or ~/.bash_profile:"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "2. Set the SCRIPTLAUNCH_PATH environment variable"
echo "   Add this to your ~/.bashrc or ~/.bash_profile:"
echo "   export SCRIPTLAUNCH_PATH=\"/path/to/your/scripts\""
echo ""
echo "3. Reload your shell configuration:"
echo "   source ~/.bashrc"
echo ""
echo "Then you can use either:"
echo "  scriptlaunch <script_name>"
echo "  sl <script_name>          (short alias installed)"
echo ""
echo "Both commands have full autocomplete support!"
echo ""
echo "Optional - Autocomplete for script arguments:"
echo "  If your scripts use argcomplete, install it with:"
echo "  pip install argcomplete"
echo ""
echo "  Then scriptlaunch will automatically delegate completion to your scripts!"
echo "  See ARGCOMPLETE.md for details."
