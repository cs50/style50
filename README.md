# style50

This is style50, a tool with which code can be checked against the CS50 style guide.

## Installation

```bash
pip install style50
```

In order to style check C, C++, or Java code, a recent version (`>=14.0.0`) of `clang-format` must be installed. `clang-format` may be downloaded [here](https://clang.llvm.org/docs/ClangFormat.html).

### Windows

Along with most of CS50's command line tools, `style50` supports being run on Windows but only via the [Linux Subsystem in Windows 10](https://msdn.microsoft.com/en-us/commandline/wsl/install_guide). After launching it, `style50` can be installed using the `pip` command above.

## Usage

```
usage: style50 [-h] [-o MODE] [-y] [-i] [-v] [-V] [-E] [--ignore PATTERN]
               [--clang-format-style STYLE]
               FILE [FILE ...]

positional arguments:
FILE                  file or directory to lint

options:
-h, --help            show this help message and exit
-o, --output MODE     output mode, which can be character (default), split,
                      unified, score, json, html, or format
-y, --side-by-side    show side-by-side diff (equivalent to -o split)
-i, --in-place        rewrite files in place with style50 formatting
-v, --verbose         print full tracebacks of errors
-V, --version         show program's version number and exit
-E, --extensions      print supported file extensions (as JSON list) and
                      exit
--ignore PATTERN      paths/patterns to be ignored
--clang-format-style STYLE
                      clang-format style string or file:// URI (overrides
                      default CS50 config)
```

`STYLE50_IGNORE` is also supported as a comma-separated environment variable fallback for ignore patterns.

`character`, `split`, and `unified` modes output character-based, side-by-side, and unified (respectively) diffs between the inputted file and the correctly styled version. `score` outputs the raw percentage of correct (unchanged) lines, `json` outputs a JSON object containing structured results, `html` outputs browser-readable results, and `format` outputs only the formatted code.

### Common examples

```bash
# Diff-only mode (default)
style50 foo.c
style50 foo.c bar.py
style50 *.c *.py

# In-place rewrite
style50 -i foo.c
style50 -i foo.c bar.py
style50 -i *.c *.py

# Side-by-side diff
style50 -y foo.c bar.py

# Ignore files/patterns
style50 --ignore "*/.*" foo.c bar.py

# Emit only formatted code (single file only)
style50 -o format foo.c
```

### `--output` modes

`--output` supports:

- `character` (default)
- `split`
- `unified`
- `score`
- `json`
- `html`
- `format`

### `-i` and `--output`

`-i/--in-place` rewrites files and therefore cannot be combined with `--output` or `--side-by-side`.

## Language Support

`style50` currently supports the following languages:

- C++
- C
- Python
- Javascript
- Java
- HTML
- CSS
- SQL

### Adding a new language

Adding a new language is very simple. Language checks are encoded as classes which inherit from the `StyleCheck` base class (see `style50/languages.py` for more real-world examples). The following is a template for style checks which allows style50 to check the imaginary FooBar language for style.

```python
import re

from style50 import StyleCheck, Style50


class FooBar(StyleCheck):

    # REQUIRED: this property informs style50 what file extensions this
    # check should be run on (in this case, all .fb and .foobar files)
    extensions = ["fb", "foobar"]

    # REQUIRED: should return a correctly styled version of `code`
    def style(self, code):
        # All FooBar code is perfectly styled
        return code

    # OPTIONAL: should return the number of comments in `code`.
    # If this function is not defined, `style50` will not warn the student about
    # too few comments
    def count_comments(self, code):
        # A real-world, check would need to worry about not counting '#' in string-literals
        return len(re.findall(r"#.*", code))
```

All classes which inherit from `StyleCheck` are automatically registered with `style50`'s `Style50` class, making style50 easily extensible. Adding the following to the above code creates a script which checks the code that `style50` already does as well as FooBar programs.

```python
    # Style check the current directory, printing a unified diff
    Style50("unified").run(["."])
```
