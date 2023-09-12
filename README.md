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
usage: style50 [-h] [-o MODE] [-v] [-V] [-E] [-i PATTERN] file [file ...]

positional arguments:
file                  file or directory to lint

optional arguments:
-h, --help            show this help message and exit
-o MODE, --output MODE
                        output mode, which can be character (default), split,
                        unified, score, or json
-v, --verbose         print full tracebacks of errors
-V, --version         show program's version number and exit
-E, --extensions      print supported file extensions (as JSON list) and
                        exit
-i PATTERN, --ignore PATTERN
                        paths/patterns to be ignored
```

`character`, `split`, and `unified` modes output character-based, side-by-side, and unified (respectively) diffs between the inputted file and the correctly styled version. `score` outputs the raw percentage of correct (unchanged) lines, while `json` outputs a json object containing information pertinent to the CS50 IDE plugin (coming soon).

## Language Support

`style50` currently supports the following languages:

- C++
- C
- Python
- Javascript
- Java

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
