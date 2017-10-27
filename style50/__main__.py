from __future__ import print_function
from __future__ import division

import json
import signal
import sys
import traceback

import argparse
import termcolor

from . import Style50, Error, __version__

# require python 2.7+.
if sys.version_info < (2, 7):
    sys.exit("You have an old version of python. Install version 2.7 or higher.")


# Exit zero on Ctrl-C.
def handler(number, frame):
    sys.exit(1)


def excepthook(etype, value, tb):
    if etype is Error:
        termcolor.cprint(value.msg, "red", file=sys.stderr)
    else:
        termcolor.cprint("Sorry, something's wrong! "
                         "Let sysadmins@cs50.harvard.edu know!",
                         "red", file=sys.stderr)

    # Main might not have initialized args yet.
    try:
        verbose = main.args.verbose
    except AttributeError:
        verbose = True

    if verbose:
        traceback.print_exception(etype, value, tb)


# Set global exception handler.
sys.excepthook = excepthook


def main():
    # Listen for Ctrl-C.
    signal.signal(signal.SIGINT, handler)

    # Define command-line arguments.
    parser = argparse.ArgumentParser(prog="style50")
    parser.add_argument("file", metavar="FILE", nargs="+", help="file or directory to lint")
    parser.add_argument("-o", "--output", action="store", default="character",
                        choices=["character", "split", "unified", "score", "json"], metavar="MODE",
                        help="output mode, which can be character (default), split, unified, score, or json")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="print full tracebacks of errors")
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s {}".format(__version__))
    parser.add_argument("-E", "--extensions", action="version",
                        version=json.dumps(list(Style50.extension_map.keys())),
                        help="print supported file extensions (as JSON list) and exit")

    main.args = parser.parse_args()
    Style50(main.args.file, output=main.args.output).run()


# Necessary so `console_scripts` can extract the main function
if __name__ == "__main__":
    main()
