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
import six
import termcolor


class StyleChecker(object):
    """
    Class which checks a list of files/directories for style.
    """
    extension_map = {}

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
            check = self.extension_map[extension]
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

class StyleMeta(ABCMeta):
    """
    Metaclass which defines an abstract class and adds each extension that the
    class supports to the global extension_map dictionary.
    """
    def __new__(mcls, name, bases, attrs):
        cls = ABCMeta.__new__(mcls, name, bases, attrs)
        try:
            for ext in attrs.get("extensions", []):
                StyleChecker.extension_map[ext] = cls
        except TypeError:
            # if `extensions` property isn't iterable, skip it
            pass
        return cls

# Python 2 and 3 handle metaclasses incompatibly
@six.add_metaclass(StyleMeta)
class StyleCheckBase(object):
    """
    Abstact base class for all style checks. All children must define `extensions` and
    implement `style`
    """
    COMMENT_MIN = 0.1

    def __init__(self, code, unified=False):
        self.code = code
        self.styled = self.style(code)

        # Run check.
        self.check(code)

        if unified:
            red, green, clear = u"\u001b[1;31m", u"\u001b[1;32m", u"\u001b[0m"
            self.diff_cmd = ["diff", "-d",
                              "--new-line-format={}+ %L{}".format(green,clear),
                              "--old-line-format={}- %L{}".format(red, clear),
                              "--unchanged-line-format=  %L"]
        else:
            self.diff_cmd = ["icdiff", "-W", "--no-headers"]

    def check(self, code):
        """
        Run checks on code.
        """
        processed = self.preprocess(code)

        comments = self.count_comments(processed)

        self.comment_ratio = 1. if comments is None else comments / (processed.count("\n") + 1)
        styled = self.style(processed)
        styled_lines = styled.splitlines()

        # Count number of differences between styled and unstyled code
        diffs = sum(1 for d in difflib.ndiff(processed.splitlines(), styled_lines) if d[0] == "+")
        self.diffs = diffs
        self.lines = len(styled_lines)

    def preprocess(self, code):
        """
        Remove blank lines from code, could be overriden in child class to do more
        """
        code_lines = [line for line in code.splitlines() if line.strip()]
        if not code_lines:
            raise Error("can't style check empty files")

        return "\n".join(code_lines)


    def print_results(self):
        """
        Print diff of styled vs unstyled output, warning about comments if applicable
        """
        diff = self.diff()
        if diff:
            print(diff)
        else:
            termcolor.cprint("no style errors found", "green")

        if self.comment_ratio < self.COMMENT_MIN:
            termcolor.cprint("Warning: It looks like you may not have very many comments. "
                             "This may bring down your final score.", "yellow")

    def jsonify(self):
        """
        Create json object out of check containing fields relavent to IDE plugin
        """
        return json.dumps(dict(comments=self.comment_ratio > self.COMMENT_MIN,
                               comment_ratio=self.comment_ratio,
                               styled=self.styled))


    #TODO: Figure out how not to have to write to disk
    def diff(self):
        """
        Return diff (as created by running self.diff_cmd) of original and styled code
        """
        with tempfile.NamedTemporaryFile(mode="w") as styled_file, \
                tempfile.NamedTemporaryFile(mode="w") as orig_file:

            orig_file.write(self.code)
            orig_file.flush()

            styled_file.write(self.styled)
            styled_file.flush()
            command = self.diff_cmd + [orig_file.name, styled_file.name]
            return self.run(command, exit=None).rstrip()

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
