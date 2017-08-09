import io
import re
import sys
from tokenize import generate_tokens, STRING, INDENT, COMMENT

import autopep8
import jsbeautifier

from . import StyleCheck


class C(StyleCheck):
    extensions = ["c", "h", "cpp", "hpp"]

    astyle = [
        "astyle", "--ascii", "--add-braces", "--break-one-line-headers",
        "--align-pointer=name", "--pad-comma",
        "--pad-header", "--pad-oper", "--max-code-length=100",
        "--convert-tabs", "--indent=spaces=4",
        "--indent-continuation=1", "--indent-switches",
        "--min-conditional-indent=1", "--style=allman"
    ]

    # Match (1) /**/ comments, and (2) // comments.
    match_comments = re.compile(r"(\/\*.*?\*\/)|(\/\/[^\n]*)", re.DOTALL)

    # Matches string literals.
    match_literals = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)

    def count_comments(self, code):
        # Remove all string literals.
        stripped = self.match_literals.sub("", code)
        return sum(1 for _ in self.match_comments.finditer(stripped))

    def style(self, code):
        return self.run(self.astyle, input=code)


class Python(StyleCheck):
    extensions = ["py"]

    def count_comments(self, code):
        # Make sure we count docstring at top of module
        prev_type = INDENT
        comments = 0

        code_lines = iter(code.splitlines(True))
        for t_type, _, _, _, _ in generate_tokens(lambda: next(code_lines)):
            # Increment if token is comment or docstring
            comments += t_type == COMMENT or (t_type == STRING and prev_type == INDENT)
            prev_type = t_type
        return comments

    # TODO: Determine which options (if any) should be passed to autopep8
    def style(self, code):
        return autopep8.fix_code(code, options={"max_line_length": 100})


class Js(C):
    extensions = ["js"]

    # Taken from http://code.activestate.com/recipes/496882-javascript-code-compression/
    match_literals = re.compile(
        r"""
         (\'.*?(?<=[^\\])\')             |       # single-quoted strings
         (\".*?(?<=[^\\])\")             |       # double-quoted strings
         ((?<![\*\/])\/(?![\/\*]).*?(?<![\\])\/) # JS regexes, trying hard not to be tripped up by comments
         """, re.VERBOSE)

    # TODO: Determine which options, if any should be passed here
    def style(self, code):
        return jsbeautifier.beautify(code)


class Java(C):
    extensions = ["java"]
    astyle = C.astyle + ["--mode=java", "--style=java"]
