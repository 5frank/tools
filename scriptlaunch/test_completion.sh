#!/usr/bin/env bash
# Quick test script to verify bash completion works
# Run this with: bash test_completion.sh

set -e

echo "Testing scriptlaunch completion..."
echo ""

# Source the completion script
source ./scriptlaunch-completion.bash

# Set up environment
export SCRIPTLAUNCH_PATH="$(pwd)/example_scripts"
export PATH="$(pwd):$PATH"

# Make scriptlaunch.py available as 'scriptlaunch' and 'sl'
ln -sf "$(pwd)/scriptlaunch.py" "$(pwd)/scriptlaunch" 2>/dev/null || true
ln -sf "$(pwd)/scriptlaunch.py" "$(pwd)/sl" 2>/dev/null || true
chmod +x "$(pwd)/scriptlaunch"
chmod +x "$(pwd)/sl"

echo "1. Testing script name completion:"
echo "   Simulating: scriptlaunch demo<TAB>"
COMP_WORDS=(scriptlaunch demo)
COMP_CWORD=1
COMP_LINE="scriptlaunch demo"
COMP_POINT=17
_scriptlaunch_complete
echo "   Completions: ${COMPREPLY[@]}"
echo ""

echo "2. Testing script argument completion:"
echo "   Simulating: scriptlaunch demo_argcomplete --<TAB>"
COMP_WORDS=(scriptlaunch demo_argcomplete --)
COMP_CWORD=2
COMP_LINE="scriptlaunch demo_argcomplete --"
COMP_POINT=32
_scriptlaunch_complete
echo "   Completions: ${COMPREPLY[@]}"
echo ""

if [[ "${COMPREPLY[@]}" == *"--help"* ]]; then
    echo "✓ SUCCESS! Argument completion is working!"
else
    echo "✗ FAILED: Argument completion not working"
    echo "  Make sure argcomplete is installed: pip install argcomplete"
fi
echo ""

echo "3. Testing 'sl' alias - script name completion:"
echo "   Simulating: sl demo<TAB>"
COMP_WORDS=(sl demo)
COMP_CWORD=1
COMP_LINE="sl demo"
COMP_POINT=7
_scriptlaunch_complete
echo "   Completions: ${COMPREPLY[@]}"
echo ""

echo "4. Testing 'sl' alias - argument completion:"
echo "   Simulating: sl demo_argcomplete --<TAB>"
COMP_WORDS=(sl demo_argcomplete --)
COMP_CWORD=2
COMP_LINE="sl demo_argcomplete --"
COMP_POINT=22
_scriptlaunch_complete
echo "   Completions: ${COMPREPLY[@]}"
echo ""

if [[ "${COMPREPLY[@]}" == *"--help"* ]]; then
    echo "✓ SUCCESS! 'sl' alias completion is working!"
else
    echo "✗ FAILED: 'sl' alias completion not working"
fi

# Cleanup
rm -f "$(pwd)/scriptlaunch" "$(pwd)/sl" 2>/dev/null || true
