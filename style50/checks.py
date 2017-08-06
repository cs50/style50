import re
import io
from tokenize import generate_tokens, STRING, INDENT, COMMENT

import autopep8
import jsbeautifier

from . import StyleCheckBase

class CStyleCheck(StyleCheckBase):
    extensions = [".c", ".h"]

    # Match (1) /**/ comments, and (2) // comments.
    match_comments = re.compile(r"(\/\*.*?\*\/)|(\/\/[^\n]*)", re.DOTALL)

    # Matches string literals.
    match_literals = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)


    def count_comments(self, code):
        # Remove all string literals.
        stripped = self.match_literals.sub("", code)
        return sum(1 for _ in self.match_comments.finditer(stripped))

    def style(self, code):
        command = [
           "astyle", "--ascii", "--add-braces", "--break-one-line-headers",
           "--align-pointer=name", "--pad-comma",
           "--pad-header", "--pad-oper",
           "--convert-tabs", "--indent=spaces=4",
           "--indent-continuation=1", "--indent-switches",
           "--min-conditional-indent=1", "--style=allman"
        ]

        return self.run(command, input=code)


class PyStyleCheck(StyleCheckBase):
    extensions = [".py"]

    def count_comments(self, code):
        prev, comments = INDENT, 0
        with io.StringIO(code) as codeio:
            # Iterate over tokens.
            for t_type, _, _, _, _ in generate_tokens(codeio.readline):
                # Increment if token is comment or docstring
                comments += t_type == COMMENT or (t_type == STRING and prev_type == INDENT)
                prev_type = t_type
        return comments

    # TODO: Determine which options (if any) should be passed to autopep8
    def style(self, code):
        return autopep8.fix_code(code)


# Inherit from CStyleCheck since counting comments is nearly the same, save more posibilities for literals
class JsStyleCheck(CStyleCheck):
    extensions = [".js"]

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
