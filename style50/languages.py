import io
import re
import sys
from tokenize import generate_tokens, STRING, INDENT, COMMENT, TokenError

import autopep8
import cssbeautifier
import jsbeautifier
import sqlparse

from . import StyleCheck, Error


class C(StyleCheck):
    extensions = ["c", "h", "cpp", "hpp"]
    magic_names = [] # Only recognize C files by their extension

    styleConfig = '{ AllowShortFunctionsOnASingleLine: Empty, BraceWrapping: { AfterCaseLabel: true, AfterControlStatement: true, AfterFunction: true, AfterStruct: true, BeforeElse: true, BeforeWhile: true }, BreakBeforeBraces: Custom, ColumnLimit: 100, IndentCaseLabels: true, IndentWidth: 4, SpaceAfterCStyleCast: true, TabWidth: 4 }'
    clangFormat = [
        "clang-format", f"-style={styleConfig}"
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
        clang_format_style = self._config.get("clang_format_style")
        if isinstance(clang_format_style, str):
            normalized = clang_format_style.strip().strip('"').strip("'").strip()
            if normalized.lower() in {"", "undefined", "null", "none"}:
                clang_format_style = None

        if clang_format_style:
            cmd = [c for c in self.clangFormat if not str(c).startswith("-style=")]
            cmd.append(f"-style={clang_format_style}")
            return self.run(cmd, input=code)
        return self.run(self.clangFormat, input=code)


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
        return autopep8.fix_code(code, options={"max_line_length": 100, "ignore_local_config": True})


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

    # TODO: Determine which options, if any should be passed here
    def style(self, code):
        opts = jsbeautifier.default_options()
        opts.end_with_newline = True
        opts.operator_position = "preserve-newline"
        opts.wrap_line_length = 100
        opts.brace_style = "collapse,preserve-inline"
        opts.keep_array_indentation = True
        return jsbeautifier.beautify(code, opts)


class Java(C):
    extensions = ["java"]
    magic_names = ["Java source"]
    clangFormat = C.clangFormat.copy() + ["-assume-filename=.java"]


class Html(StyleCheck):
    extensions = ["html"]
    magic_names = ["HTML document"]

    def style(self, code):
        # djhtml returns exit 1 when it reformats (same convention as diff/black),
        # so exit=None is required to avoid treating successful reformats as errors.
        return self.run(["djhtml", "-"], input=code, exit=None)


class Css(StyleCheck):
    extensions = ["css"]
    magic_names = []

    def style(self, code):
        opts = cssbeautifier.default_options()
        opts.indent_size = 4
        opts.end_with_newline = True
        return cssbeautifier.beautify(code, opts)


class Sql(StyleCheck):
    extensions = ["sql"]
    magic_names = []

    def style(self, code):
        formatted = sqlparse.format(code, reindent=True, keyword_case="upper", indent_width=4)
        if not formatted.endswith("\n"):
            formatted += "\n"
        return formatted
