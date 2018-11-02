import io
import re
import sys
from tokenize import generate_tokens, STRING, INDENT, COMMENT, TokenError

import autopep8
import jsbeautifier

from . import StyleCheck, Error


class C(StyleCheck):
    extensions = ["c", "h", "cpp", "hpp"]
    magic_names = [] # Only recognize C files by their extension

    astyle = [
        "astyle", "--ascii", "--add-braces", "--break-one-line-headers",
        "--align-pointer=name", "--pad-comma", "--unpad-paren",
        "--pad-header", "--pad-oper", "--max-code-length=132",
        "--convert-tabs", "--indent=spaces=4",
        "--indent-continuation=1", "--indent-switches",
        "--lineend=linux", "--min-conditional-indent=1",
        "--options=none", "--style=allman"
    ]

    # Match (1) /**/ comments, and (2) // comments.
    match_comments = re.compile(r"(\/\*.*?\*\/)|(\/\/[^\n]*)", re.DOTALL)

    # Matches string literals.
    match_literals = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)

    def __init__(self, code):
        version_text = self.run(["astyle", "--version"])
        try:
            # Match astyle version via regex.
            version = re.match("Artistic Style Version (\d.+)", version_text).groups()[0]
        except IndexError:
            raise Error("could not determine astyle version")

        if tuple(map(int, version.split("."))) < (3, 0, 1):
            raise Error("style50 requires astyle version 3.0.1 or greater, "
                        "but version {} was found".format(version))

        # Call parent init.
        StyleCheck.__init__(self, code)

    def count_comments(self, code):
        # Remove all string literals.
        stripped = self.match_literals.sub("", code)
        return sum(1 for _ in self.match_comments.finditer(stripped))

    def style(self, code):
        return self.run(self.astyle, input=code)


class Python(StyleCheck):
    magic_names = ["Python script"]
    extensions = ["py"]

    def count_comments(self, code):
        # Make sure we count docstring at top of module
        prev_type = INDENT
        comments = 0

        code_lines = iter(code.splitlines(True))
        try:
            for t_type, _, _, _, _ in generate_tokens(lambda: next(code_lines)):
                # Increment if token is comment or docstring
                comments += t_type == COMMENT or (t_type == STRING and prev_type == INDENT)
                prev_type = t_type
        except TokenError:
            raise Error("failed to parse code, check for syntax errors!")
        except IndentationError as e:
            raise Error("make sure indentation is consistent on line {}!".format(e.lineno))
        return comments

    def count_lines(self, code):
        """
        count_lines ignores blank lines by default,
        but blank lines are relevant to style per pep8
        """
        return len(code.splitlines())

    # TODO: Determine which options (if any) should be passed to autopep8
    def style(self, code):
        return autopep8.fix_code(code, options={"max_line_length": 132, "ignore_local_config": True})


class Js(C):
    extensions = ["js"]
    magic_names = []

    # Taken from http://code.activestate.com/recipes/496882-javascript-code-compression/
    match_literals = re.compile(
        r"""
         (\'.*?(?<=[^\\])\')             |       # single-quoted strings
         (\".*?(?<=[^\\])\")             |       # double-quoted strings
         ((?<![\*\/])\/(?![\/\*]).*?(?<![\\])\/) # JS regexes, trying hard not to be tripped up by comments
         """, re.VERBOSE)

    # C.__init__ checks for astyle but we don't need this for Js
    __init__ = StyleCheck.__init__

    # TODO: Determine which options, if any should be passed here
    def style(self, code):
        opts = jsbeautifier.default_options()
        opts.end_with_newline = True
        opts.operator_position = "preserve-newline"
        opts.wrap_line_length = 132
        opts.brace_style = "collapse,preserve-inline"
        opts.keep_array_indentation = True
        return jsbeautifier.beautify(code, opts)


class Java(C):
    extensions = ["java"]
    magic_names = ["Java source"]
    astyle = C.astyle + ["--mode=java", "--style=java"]
