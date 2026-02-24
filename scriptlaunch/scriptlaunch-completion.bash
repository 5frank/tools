#!/usr/bin/env bash
# Bash completion script for scriptlaunch
# This completes script names for the first argument,
# then delegates completion to the target script if it supports argcomplete

_scriptlaunch_complete() {
    local cur prev script_name script_file cmd_name
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    cmd_name="${COMP_WORDS[0]}"  # Either 'scriptlaunch' or 'sl'

    # Check if SCRIPTLAUNCH_PATH is set
    if [[ -z "$SCRIPTLAUNCH_PATH" ]]; then
        return 0
    fi

    # Complete the first argument (script name)
    if [[ ${COMP_CWORD} -eq 1 ]]; then
        local scripts
        scripts=$("$cmd_name" --list "$cur" 2>/dev/null)

        if [[ $? -eq 0 ]]; then
            COMPREPLY=( $(compgen -W "${scripts}" -- "${cur}") )
        fi
        return 0
    fi

    # For subsequent arguments, delegate to the actual script
    script_name="${COMP_WORDS[1]}"

    # Find the actual script file
    for ext in .py .sh ""; do
        script_file="$SCRIPTLAUNCH_PATH/${script_name}${ext}"
        if [[ -f "$script_file" ]]; then
            break
        fi
    done

    if [[ ! -f "$script_file" ]]; then
        # Script not found, use default file completion
        COMPREPLY=( $(compgen -f -- "$cur") )
        return 0
    fi

    # Check if it's a Python script with argcomplete support
    if [[ "$script_file" == *.py ]] && grep -q "argcomplete" "$script_file" 2>/dev/null; then
        # Invoke the script with argcomplete's completion protocol
        # We need to make it look like the script is being called directly

        # Build the modified command line (remove command name from the beginning)
        local modified_comp_line="${COMP_LINE#$cmd_name }"
        local cmd_length=$((${#cmd_name} + 1))  # +1 for the space
        local modified_comp_point=$((COMP_POINT - cmd_length))

        # Set up environment for argcomplete
        local IFS=$'\013'
        local completions
        completions=$(
            COMP_LINE="$modified_comp_line" \
            COMP_POINT="$modified_comp_point" \
            COMP_TYPE="$COMP_TYPE" \
            _ARGCOMPLETE=1 \
            _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \
            _ARGCOMPLETE_IFS=$'\013' \
            python3 "$script_file" 8>&1 9>&2 2>/dev/null
        )

        if [[ $? -eq 0 && -n "$completions" ]]; then
            COMPREPLY=( $completions )
            return 0
        fi
    fi

    # Default: use file completion for any script arguments
    COMPREPLY=( $(compgen -f -- "$cur") )
    return 0
}

# Register the completion function for both scriptlaunch and sl alias
complete -F _scriptlaunch_complete scriptlaunch
complete -F _scriptlaunch_complete sl
