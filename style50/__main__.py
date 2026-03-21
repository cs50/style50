import json
import os
import signal
import sys
import traceback

import argparse
import termcolor

from . import Style50, Error, __version__, renderer

def excepthook(etype, value, tb):
    if isinstance(value, Error):
        termcolor.cprint(value.msg, "red", file=sys.stderr)
    elif isinstance(value, KeyboardInterrupt):
        sys.exit(1)
    else:
        termcolor.cprint("Sorry, something's wrong! "
                         "Let sysadmins@cs50.harvard.edu know!",
                         "red", file=sys.stderr)

    if excepthook.verbose:
        traceback.print_exception(etype, value, tb)

# Set global exception handler.
sys.excepthook = excepthook
excepthook.verbose = True


def main():
    # Define command-line arguments.
    parser = argparse.ArgumentParser(prog="style50")
    parser.add_argument("file", metavar="FILE", nargs="+", help="file or directory to lint")
    parser.add_argument("-o", "--output", action="store", default=None,
                        choices=["character", "split", "unified", "score", "json", "html", "format"], metavar="MODE",
                        help="output mode, which can be character (default), split, unified, score, json, html, or format")
    parser.add_argument("-y", "--side-by-side", action="store_true",
                        help="show side-by-side diff (equivalent to -o split)")
    parser.add_argument("-i", "--in-place", action="store_true",
                        help="rewrite files in place with style50 formatting")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print full tracebacks of errors")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s {}".format(__version__))
    parser.add_argument("-E", "--extensions", action="version",
                        version=json.dumps(list(Style50.extension_map.keys())),
                        help="print supported file extensions (as JSON list) and exit")
    parser.add_argument("--ignore", action="append", metavar="PATTERN",
                        help="paths/patterns to be ignored")
    parser.add_argument("--clang-format-style", metavar="STYLE",
                        help="clang-format style string or file:// URI (overrides default CS50 config)")

    args = parser.parse_args()
    ignore = args.ignore or list(filter(None, os.getenv("STYLE50_IGNORE", "").split(",")))

    if args.in_place and args.side_by_side:
        sys.exit("--in-place cannot be combined with --side-by-side")

    if args.in_place and args.output is not None:
        sys.exit("--in-place cannot be combined with --output")

    output = args.output or "character"

    if args.side_by_side:
        output = "split"

    if args.in_place:
        _, failures = Style50("format", clang_format_style=args.clang_format_style).format_files_in_place(args.file, ignore=ignore)
        if failures:
            sys.exit(1)
        return

    if output == "format":
        if len(args.file) != 1:
            sys.exit("format mode requires exactly one file")
        sys.stdout.write(Style50("format", clang_format_style=args.clang_format_style).format_file(args.file[0]))
        return

    Style50(output, clang_format_style=args.clang_format_style).run(args.file, ignore=ignore)



# Necessary so `console_scripts` can extract the main function
if __name__ == "__main__":
    main()
