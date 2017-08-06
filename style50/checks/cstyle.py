import re

from .base import StyleCheckBase

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
