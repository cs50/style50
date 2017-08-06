from __future__ import print_function
from __future__ import division

import argparse
import signal
import sys

from . import StyleChecker

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
    parser.add_argument("-r", "--raw", action="store_true")
    parser.add_argument("-u", "--unified", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")


    args = parser.parse_args()
    StyleChecker(args.files, raw=args.raw, unified=args.unified).run()

# Necessary so `console_scripts` can extract the main function
if __name__ == "__main__":
    main()
