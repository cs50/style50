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

    Theoretically, stdout, stderr, and stdin could all be different ttys that could
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

    # Dict which maps file extensions to check classes
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
        if output == "score":
            self.run = self.run_score
        elif output == "json":
            self.run = self.run_json
        else:
            self.run = self.run_diff
            # Set diff function as needed
            if output == "character":
                self.diff = self.char_diff
            elif output == "split":
                self.diff = self.split_diff
            elif output == "unified":
                self.diff = self.unified
            else:
                raise Error("invalid output type")

    def run_diff(self):
        """
        Run checks on self.files, printing diff of styled/unstyled output to stdout.
        """
        files = tuple(self.files)
        # Use same header as more.
        header, footer = (termcolor.colored("{0}\n{{}}\n{0}\n".format(
            ":" * 14), "cyan"), "\n") if len(files) > 1 else ("", "")

        first = True
        for file in files:
            # Only print footer after first file has been printed
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

            # Display results
            if results.diffs:
                print(*self.diff(results.original, results.styled), sep="\n")
                if results.comment_ratio < results.COMMENT_MIN:
                    termcolor.cprint("And consider adding more comments!", "yellow")
            else:
                termcolor.cprint("Looks good!", "green")
                if results.comment_ratio < results.COMMENT_MIN:
                    termcolor.cprint("But consider adding more comments!", "yellow")

    def run_json(self):
        """
        Run checks on self.files, printing json object
        containing information relavent to the CS50 IDE plugin at the end.
        """
        checks = {}
        for file in self.files:
            try:
                results = self._check(file)
            except Error as e:
                checks[file] = {
                    "error": e.msg
                }
            else:
                checks[file] = {
                    "score": results.score,
                    "comments": results.comment_ratio >= results.COMMENT_MIN,
                    "diff": "<pre>{}</pre>".format("\n".join(self.html_diff(results.original, results.styled))),
                }

        json.dump(checks, sys.stdout)

    def run_score(self):
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
    def split_diff(old, new):
        """
        Returns a generator yielding the side-by-side diff of `old` and `new`).
        """
        return map(lambda l: l.rstrip(),
                   icdiff.ConsoleDiff(cols=COLUMNS).make_table(old.splitlines(), new.splitlines()))

    @staticmethod
    def unified(old, new):
        """
        Returns a generator yielding a unified diff between `old` and `new`.
        """
        for diff in difflib.ndiff(old.splitlines(), new.splitlines()):
            if diff[0] == " ":
                yield diff
            elif diff[0] == "?":
                continue
            else:
                yield termcolor.colored(diff, "red" if diff[0] == "-" else "green", attrs=["bold"])

    def html_diff(self, old, new):
        """
        Return HTML formatted character-based diff between old and new (used for CS50 IDE).
        """
        def html_transition(old_type, new_type):
            tags = []
            for tag in [("/", old_type), ("", new_type)]:
                if tag[1] not in ["+", "-"]:
                    continue
                tags.append("<{}{}>".format(tag[0], "ins" if tag[1] == "+" else "del"))
            return "".join(tags)

        return self._char_diff(old, new, html_transition, fmt=cgi.escape)

    def char_diff(self, old, new):
        """
        Return color-coded character-based diff between `old` and `new`.
        """
        def color_transition(old_type, new_type):
            new_color = termcolor.colored("", None, "on_red" if new_type ==
                                          "-" else "on_green" if new_type == "+" else None)
            return "{}{}".format(termcolor.RESET, new_color[:-len(termcolor.RESET)])

        return self._char_diff(old, new, color_transition)

    @staticmethod
    def _char_diff(old, new, transition, fmt=lambda c: c):
        """
        Returns a char-based diff between `old` and `new` where each character
        is formatted by `fmt` and transitions between blocks are determined by `transition`.
        """

        differ = difflib.ndiff(old, new)

        # Type of difference.
        dtype = None

        # Buffer for current line.
        line = []
        while True:
            # Get next diff or None if we're at the end.
            d = next(differ, (None,))
            if d[0] != dtype:
                line += transition(dtype, d[0])
                dtype = d[0]

            if dtype is None:
                break

            if d[2] == "\n":
                if dtype != " ":
                    # Show added/removed newlines.
                    line += [fmt(r"\n"), transition(dtype, " ")]
                yield "".join(line)
                line = [transition(" ", dtype)]
            else:
                # Show added/removed tabs.
                line.append(fmt(d[2] if dtype == " " else d[2].replace("\t", r"\t")))

        # Flush buffer before quitting.
        last = "".join(line)
        # Only print last line if it contains non-ANSI characters.
        if re.sub(r"\x1b[^m]*m", "", last):
            yield last


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
