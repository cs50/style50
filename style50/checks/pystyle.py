import io
from tokenize import generate_tokens, STRING, INDENT, COMMENT

import autopep8

from .base import StyleCheckBase


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
