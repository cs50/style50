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
    parser.add_argument("-o", "--output", action="store", default="character",
                        choices=["character", "split", "unified", "score", "json", "html"], metavar="MODE",
                        help="output mode, which can be character (default), split, unified, score, or json")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print full tracebacks of errors")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s {}".format(__version__))
    parser.add_argument("-E", "--extensions", action="version",
                        version=json.dumps(list(Style50.extension_map.keys())),
                        help="print supported file extensions (as JSON list) and exit")
    parser.add_argument("-i", "--ignore", action="append", metavar="PATTERN",
                        help="paths/patterns to be ignored")

    args = parser.parse_args()
    ignore = args.ignore or filter(None, os.getenv("STYLE50_IGNORE", "").split(","))
    Style50(args.output).run(args.file, ignore=ignore)



# Necessary so `console_scripts` can extract the main function
if __name__ == "__main__":
    main()
