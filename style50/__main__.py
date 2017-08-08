from __future__ import print_function
from __future__ import division

import argparse
import signal
import sys

import termcolor

from . import Style50

# require python 2.7+
if sys.version_info < (2, 7):
    sys.exit("You have an old version of python. Install version 2.7 or higher.")


def handler(number, frame):
    sys.exit(1)


def main():
    # Listen for Ctrl-C.
    signal.signal(signal.SIGINT, handler)

    # Define command-line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="files/directories to lint", default=["."])
    parser.add_argument("-o", "--output", action="store", default="side-by-side",
                        choices=["side-by-side", "unified", "raw", "json"], metavar="MODE",
                        help="specify output mode")

    args = parser.parse_args()
    Style50(args.files, output=args.output).run()


# Necessary so `console_scripts` can extract the main function
if __name__ == "__main__":
    try:
        main()
    except Exception:
        termcolor.cprint("Sorry, something's wrong! "
                         "Let sysadmins@cs50.harvard.edu know!",
                         "red", file=sys.stderr)
        sys.exit(1)
