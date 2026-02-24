#!/usr/bin/env python3
"""
Example script demonstrating argcomplete integration with scriptlaunch.

When run via scriptlaunch, autocomplete will work for this script's arguments!

Try: scriptlaunch demo_argcomplete --<TAB>
"""
import argparse

# ARGCOMPLETE_OK marker (optional but recommended)

def main():
    parser = argparse.ArgumentParser(description='Demo script with argcomplete support')

    parser.add_argument(
        '--input', '-i',
        help='Input file path',
        required=False
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path',
        required=False
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--mode',
        choices=['fast', 'normal', 'thorough'],
        default='normal',
        help='Processing mode'
    )

    parser.add_argument(
        'files',
        nargs='*',
        help='Files to process'
    )

    # Enable argcomplete (this must come before parse_args)
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass  # argcomplete not installed, completion won't work

    args = parser.parse_args()

    # Demo output
    print(f"Running demo with:")
    print(f"  Input: {args.input}")
    print(f"  Output: {args.output}")
    print(f"  Verbose: {args.verbose}")
    print(f"  Mode: {args.mode}")
    print(f"  Files: {args.files}")


if __name__ == '__main__':
    main()
