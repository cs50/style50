import re

import jsbeautifier

from .cstyle import CStyleCheck


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
