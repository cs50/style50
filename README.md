# style50
style50 is a command-line tool with which you can check your code for consistency with [CS50’s style guide](https://cs50.readthedocs.io/style/c/) (for C)

## Usage
This command-line tool that checks your code for consistency with the [CS50 Style Guide](https://cs50.readthedocs.io/style/c/). It highlights lines that need more (or fewer) spaces, incorrect indentation, and missing comments.

To check the style of a file, run:

```bash
style50 file.c
```

### Modes

By default, `style50` runs in **character** mode, but you can change the output format using the `-o` or `--output` flag.

#### 1\. Character Mode (Default)

Highlights specific characters to add in green and characters to remove in red.

```bash
style50 hello.c
```

#### 2\. Split Mode

Displays your current code and the "correctly styled" version side-by-side.

```bash
style50 -o split hello.c
```

#### 3\. Unified Mode

Displays the style changes in a format similar to a `git diff`.

```bash
style50 -o unified hello.c
```

#### 4\. Score Mode

Provides a simple percentage score of how well-styled your code is.

```bash
style50 -o score hello.c
```

### Supported Languages

`style50` automatically detects the language based on the file extension. It currently supports:

  * **C** (`.c`, `.h`)
  * **C++** (`.cpp`, `.hpp`)
  * **Java** (`.java`)
  * **Python** (`.py`)
  * **JavaScript** (`.js`)

### CLI Options

| Flag | Description |
| :--- | :--- |
| `-h`, `--help` | Show help message and exit. |
| `-o MODE` | Set output mode (`character`, `split`, `unified`, `score`, `json`). |
| `-v`, `--verbose` | Print full tracebacks for errors. |
| `-V`, `--version` | Show program version. |



> Go to [https://cs50.readthedocs.io/style50/](CS50 Docs) for more info.
