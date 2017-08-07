from __future__ import print_function
from __future__ import division

from abc import ABCMeta, abstractmethod, abstractproperty
import errno
import difflib
import itertools
import json
import os
import subprocess
import sys
import tempfile

from backports.shutil_get_terminal_size import get_terminal_size
import icdiff
import six
import termcolor

COLUMNS = get_terminal_size((80, 0))[0]

class Style50(object):
    """
    Class which checks a list of files/directories for style.
    """
    extension_map = {}


    def __init__(self, paths, output="side-by-side"):
        # Creates a generator of all the files found recursively in `paths`
        self.files = itertools.chain.from_iterable(
                        [path] if not os.path.isdir(path)
                               else (os.path.join(root, file)
                                    for root, _, files in os.walk(path)
                                    for file in files)
                        for path in paths)

        # Set run function as apropriate for output mode
        if output == "side-by-side":
            self.run = self.run_diff
            self.diff = self.side_by_side
        elif output == "unified":
            self.run = self.run_diff
            self.diff = self.unified
        elif output == "raw":
            self.run = self.run_raw
        elif output == "json":
            self.run = self.run_json
        else:
            raise Error("invalid output type")


    def run_diff(self):
        """
        Run checks on self.files, printing diff of styled/unstyled output to stdout.
        """
        sep = "-" * COLUMNS
        for file in self.files:
            termcolor.cprint("{0}\n{1}\n{0}".format(sep, file), "blue")

            try:
                results = self._check(file)
            except Error as e:
                termcolor.cprint(e.msg, "yellow", file=sys.stderr)
                continue

            diff = self.diff(results.original, results.style(results.original))
            try:
                print(next(diff))
            except StopIteration:
                termcolor.cprint("no style errors found", "green")
            else:
                print(*diff, sep="\n")

            if results.comment_ratio < results.COMMENT_MIN:
                termcolor.cprint("Warning: It looks like you don't have very many comments; "
                                 "this may bring down your final score.", "yellow")

    def run_json(self):
        """
        Run checks on self.files, printing json object
        containing information relavent to the IDE plugin at the end.
        """
        checks = {}
        for file in self.files:
            try:
                results = self._check(file)
            except Error as e:
                termcolor.cprint(e.msg, "yellow", file=sys.stderr)
                continue

            checks[file] = {
                "comments": results.comment_ratio >= results.COMMENT_MIN,
                "styled": results.style(results.original)
            }

        json.dump(checks, sys.stdout)

    def run_raw(self):
        """
        Run checks on self.files, printing raw percentage to stdout.
        """
        diffs = 0
        lines = 0
        for file in self.files:

            try:
                results = self._check(file)
            except Error as e:
                termcolor.cprint(e.msg, "yellow", file=sys.stderr)
                continue

            diffs += results.diffs
            lines += results.lines

        try:
            print(1 - diffs / lines)
        except ZeroDivisionError:
            print(0)

    def _check(self, file):
        """
        Run apropriate check based on `file`'s extension and return it,
        otherwise raise an Error
        """
        _, extension = os.path.splitext(file)
        try:
            check = self.extension_map[extension]
            with open(file) as f:
                code = f.read()
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                raise Error("file \"{}\" not found".format(file))
            else:
                raise
        except KeyError:
            raise Error("unknown file type \"{}\", skipping...".format(file))
        else:
            return check(code)

    @staticmethod
    def side_by_side(old, new):
        return icdiff.ConsoleDiff(cols=COLUMNS).make_table(old.splitlines(), new.splitlines())

    @staticmethod
    def unified(old, new):
        for diff in difflib.ndiff(old.splitlines(), new.splitlines()):
            if diff[0] == " ":
                yield diff
            elif diff[0] == "?":
                continue
            else:
                yield termcolor.colored(diff, "red" if diff[0] == "-" else "green", attrs=["bold"])

class StyleMeta(ABCMeta):
    """
    Metaclass which defines an abstract class and adds each extension that the
    class supports to the global extension_map dictionary.
    """
    def __new__(mcls, name, bases, attrs):
        cls = ABCMeta.__new__(mcls, name, bases, attrs)
        try:
            for ext in attrs.get("extensions", []):
                Style50.extension_map[ext] = cls
        except TypeError:
            # if `extensions` property isn't iterable, skip it
            pass
        return cls

# Python 2 and 3 handle metaclasses incompatibly
@six.add_metaclass(StyleMeta)
class StyleCheck(object):
    """
    Abstact base class for all style checks. All children must define `extensions` and
    implement `style`
    """
    COMMENT_MIN = 0.1

    def __init__(self, code):
        self.original = code
        processed = self.preprocess(code)

        comments = self.count_comments(processed)

        self.comment_ratio = 1. if comments is None else comments / (processed.count("\n") + 1)
        styled = self.style(processed)
        styled_lines = styled.splitlines()

        # Count number of differences between styled and unstyled code
        self.diffs = sum(1 for d in difflib.ndiff(processed.splitlines(), styled_lines) if d[0] == "+")
        self.lines = len(styled_lines)
        self.score = 1 - self.diffs / self.lines

    def preprocess(self, code):
        """
        Remove blank lines from code, could be overriden in child class to do more
        """
        code_lines = [line for line in code.splitlines() if line.strip()]
        if not code_lines:
            raise Error("can't style check empty files")

        return "\n".join(code_lines)

    @staticmethod
    def run(command, input=None, exit=0, shell=False):
        """
        Run `command` passing it stdin from `input`, throwing a DependencyError if comand is not found.
        Throws Error if exit code of command is not `exit` (unless `exit` is None)
        """
        if isinstance(input, str):
            input = input.encode()

        stdin = {} if input is None else {"stdin": subprocess.PIPE}
        try:
            child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **stdin)
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                name = command.split(' ', 1)[0] if isinstance(command, str) else command[0]
                e = DependencyError(name)
            raise e

        stdout, _ = child.communicate(input=input)
        if exit is not None and child.returncode != exit:
            raise Error("failed to stylecheck code")
        return stdout.decode()

    def count_comments(self, code):
        """
        Returns number of coments in `code`. If not implemented by child, will not warn about comments
        """

    @abstractproperty
    def extensions(self):
        """
        List of file extensions that check should be run on
        """

    @abstractmethod
    def style(self, code):
        """
        Returns a styled version of `code`.
        """


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg


class DependencyError(Error):
    def __init__(self, dependency):
        self.msg = "style50 requires {}, but it does not seem to be installed".format(dependency)
        self.dependency = dependency
