from __future__ import print_function
from __future__ import division

import errno
import itertools
import os
import sys

from backports.shutil_get_terminal_size import get_terminal_size
import termcolor

from .checks import extensions, Error

class StyleChecker(object):
    """
    Class which checks a list of files/directories for style.
    """
    def __init__(self, paths, raw=False, unified=False):
        # Creates a generator of all the files found recursively in `paths`
        self.files = itertools.chain.from_iterable(
                        [path] if not os.path.isdir(path)
                               else (os.path.join(root, file)
                                    for root, _, files in os.walk(path)
                                    for file in files)
                        for path in paths)
        self.raw = raw
        self.unified = unified

    def run(self):
        """
        Run the style checker on the paths it was initialized with
        """
        sep = "-" * get_terminal_size((80, 0))[0]
        diffs = 0
        lines = 0
        for file in self.files:
            if not self.raw:
                # Print diff header
                termcolor.cprint(sep, "blue")
                termcolor.cprint(file, "blue")
                termcolor.cprint(sep, "blue")

            results = self._check(file)

            if results:
                if not self.raw:
                    results.print_results()
                diffs += results.diffs
                lines += results.lines

        if self.raw:
            try:
                print(1 - diffs / lines)
            except ZeroDivisionError:
                print(0)

    def _check(self, file):
        """
        Run apropriate check based on `file`'s extension and return it, writing to stderr if `file`
        does not exist or if extension is unsupported
        """
        _, extension = os.path.splitext(file)
        try:
            check = extensions[extension]
            with open(file) as f:
                code = f.read()
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                termcolor.cprint("file \"{}\" not found".format(file), "yellow", file=sys.stderr, end="")
            else:
                raise
        except KeyError:
            termcolor.cprint("unknown file type \"{}\", skipping...".format(file), "yellow", file=sys.stderr, end="")
        else:
            try:
                return check(code, unified=self.unified)
            except Error as e:
                termcolor.cprint(e.msg, "yellow", file=sys.stderr)
        finally:
            sys.stderr.flush()

