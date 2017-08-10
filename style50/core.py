from __future__ import print_function
from __future__ import division

from abc import ABCMeta, abstractmethod, abstractproperty
import cgi
import errno
import difflib
import fcntl
import itertools
import json
import os
import re
import struct
import subprocess
import sys
from termios import TIOCGWINSZ

import icdiff
import six
import termcolor


def get_terminal_size(fallback=(80, 24)):
    """
    Return tuple containing columns and rows of controlling terminal, trying harder
    than shutil.get_terminal_size to find a tty before returning fallback.

    Theoretically, stdout, stderr, and stdin could all be different ttys which could
    cause us to get the wrong measurements (instead of using the fallback) but the much more
    common case is that IO is piped.
    """
    for stream in [sys.__stdout__, sys.__stderr__, sys.__stdin__]:
        try:
            # Make WINSIZE call to terminal
            data = fcntl.ioctl(stream.fileno(), TIOCGWINSZ, b"\x00\x00\00\x00")
        except (IOError, OSError):
            pass
        else:
            # Unpack two shorts from ioctl call
            lines, columns = struct.unpack("hh", data)
            break
    else:
        columns, lines = fallback

    return columns, lines


COLUMNS, LINES = get_terminal_size()


class Style50(object):
    """
    Class which checks a list of files/directories for style.
    """
    extension_map = {}

    def __init__(self, paths, output="character"):
        # Creates a generator of all the files found recursively in `paths`.
        self.files = itertools.chain.from_iterable(
            [path] if not os.path.isdir(path)
            else (os.path.join(root, file)
                  for root, _, files in os.walk(path)
                  for file in files)
            for path in paths)

        # Set run function as apropriate for output mode.
        if output == "raw":
            self.run = self.run_raw
        elif output == "json":
            self.run = self.run_json
        else:
            self.run = self.run_diff
            # Set diff function as needed
            if output == "character":
                self.diff = self.char_diff
            elif output == "side-by-side":
                self.diff = self.side_by_side
            elif output == "unified":
                self.diff = self.unified
            else:
                raise Error("invalid output type")

    def run_diff(self):
        """
        Run checks on self.files, printing diff of styled/unstyled output to stdout.
        """
        files = tuple(self.files)
        # Same header as more
        header, footer = (termcolor.colored("{0}\n{{}}\n{0}\n".format(
            ":" * 14), "cyan"), "\n") if len(files) > 1 else ("", "")

        first = True
        for file in files:
            if first:
                first = False
            else:
                print(footer, end="")

            print(header.format(file), end="")
            try:
                results = self._check(file)
            except Error as e:
                termcolor.cprint(e.msg, "yellow", file=sys.stderr)
                continue

            if results.diffs:
                print(*self.diff(results.original, results.styled), sep="",  end="")
            else:
                termcolor.cprint("no style errors found", "green")

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
                "diff": "<pre>{}</pre>".format("".join(self.html_diff(results.original, results.styled))),
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
            print(0.0)

    def _check(self, file):
        """
        Run apropriate check based on `file`'s extension and return it,
        otherwise raise an Error
        """
        _, extension = os.path.splitext(file)
        try:
            check = self.extension_map[extension[1:]]
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
        """
        Returns a generator yielding the side-by-side diff of `old` and `new`).
        """
        return (line + "\n" for line in icdiff.ConsoleDiff(cols=COLUMNS).make_table(old.splitlines(), new.splitlines()))

    @staticmethod
    def unified(old, new):
        """
        Returns a generator yielding a unified diff between `old` and `new`.
        """
        for diff in difflib.ndiff(old.splitlines(True), new.splitlines(True)):
            if diff[0] == " ":
                yield diff
            elif diff[0] == "?":
                continue
            else:
                yield termcolor.colored(diff, "red" if diff[0] == "-" else "green", attrs=["bold"])

    def html_diff(self, old, new):
        """
        Return HTML formatted character-based diff between old and new (used for IDE).
        """
        def fmt_html(content, dtype):
            content = cgi.escape(content, quote=True)
            return content if dtype == " " else "<{1}><{0}></{1}>".format(content, "ins" if dtype == "+" else "del")

        return self._char_diff(old, new, fmt_html)

    def char_diff(self, old, new):
        """
        Return color-coded character-based diff between `old` and `new`.
        """
        def fmt_color(content, dtype):
            return termcolor.colored(content, None, "on_green" if dtype == "+" else "on_red" if dtype == "-" else None)
        return self._char_diff(old, new, fmt_color)

    @staticmethod
    def _char_diff(old, new, fmt):
        """
        Returns a char-based diff between `old` and `new` where blocks are
        formatted by `fmt`.
        """
        differ = difflib.ndiff(old, new)
        # Type of difference.
        dtype = None
        # List diffs of same type.
        buffer = []
        while True:
            # Get next diff or None if we're at the end
            d = next(differ, (None,))
            if d[0] != dtype:
                yield fmt("".join(buffer), dtype)
                dtype = d[0]
                buffer = []

            if dtype is None:
                break

            # Show insertions/deletions of whitespace clearly
            ch = d[2] if dtype == " " else d[2].replace("\n", "\\n\n").replace("\t", "\\t")
            buffer.append(ch)


class StyleMeta(ABCMeta):
    """
    Metaclass which defines an abstract class and adds each extension that the
    class supports to the Style50's extension_map
    """
    def __new__(mcls, name, bases, attrs):
        cls = ABCMeta.__new__(mcls, name, bases, attrs)
        try:
            # Register class as the check for each of its extensions.
            for ext in attrs.get("extensions", []):
                Style50.extension_map[ext] = cls
        except TypeError:
            # If `extensions` property isn't iterable, skip it.
            pass
        return cls


@six.add_metaclass(StyleMeta)
class StyleCheck(object):
    """
    Abstact base class for all style checks. All children must define `extensions` and
    implement `style`.
    """

    # Warn if fewer than 10% of code is comments.
    COMMENT_MIN = 0.10

    def __init__(self, code):
        self.original = code
        comments = self.count_comments(code)

        try:
            # Avoid warning about comments if we don't knowhow to count them.
            self.comment_ratio = 1. if comments is None else comments / self.count_lines(code)
        except ZeroDivisionError:
            raise Error("file is empty")

        self.styled = self.style(code)

        # Count number of differences between styled and unstyled code (average of added and removed lines).
        self.diffs = sum(d[0] == "+" or d[0] == "-"
                         for d in difflib.ndiff(code.splitlines(True), self.styled.splitlines(True))) / 2

        self.lines = self.count_lines(self.styled)
        self.score = 1 - self.diffs / self.lines

    def count_lines(self, code):
        """
        Count lines of code (by default ignores empty lines, but child could override to do more).
        """
        return sum(bool(line.strip()) for line in code.splitlines())

    @staticmethod
    def run(command, input=None, exit=0, shell=False):
        """
        Run `command` passing it stdin from `input`, throwing a DependencyError if comand is not found.
        Throws Error if exit code of command is not `exit` (unless `exit` is None).
        """
        if isinstance(input, str):
            input = input.encode()

        # Only pipe stdin if we have input to pipe.
        stdin = {} if input is None else {"stdin": subprocess.PIPE}
        try:
            child = subprocess.Popen(command, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, **stdin)
        except (OSError, IOError) as e:
            if e.errno == errno.ENOENT:
                # Extract name of command.
                name = command.split(' ', 1)[0] if isinstance(command, str) else command[0]
                e = DependencyError(name)
            raise e

        stdout, _ = child.communicate(input=input)
        if exit is not None and child.returncode != exit:
            raise Error("failed to stylecheck code")
        return stdout.decode()

    def count_comments(self, code):
        """
        Returns number of coments in `code`. If not implemented by child, will not warn about comments.
        """

    @abstractproperty
    def extensions(self):
        """
        List of file extensions that check should be run on.
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
