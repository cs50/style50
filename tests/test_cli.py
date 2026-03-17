import subprocess
import sys


def run_style50(args, *, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "style50", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_format_mode_requires_one_file(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("x=1\n", encoding="utf-8")
    f2.write_text("y=2\n", encoding="utf-8")

    proc = run_style50(["-o", "format", str(f1), str(f2)])
    assert proc.returncode != 0
    assert "format mode requires exactly one file" in (proc.stderr + proc.stdout)


def test_format_mode_outputs_formatted_code(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-o", "format", str(f)])
    assert proc.returncode == 0
    assert "print(" in proc.stdout
    assert proc.stdout.endswith("\n")


def test_clang_format_style_arg_is_accepted_in_format_mode(tmp_path):
    """
    The flag should be accepted even for non-clang languages (it will be unused).
    This ensures the CLI contract used by the VS Code extension is stable.
    """
    f = tmp_path / "t.py"
    f.write_text("x=1\n", encoding="utf-8")

    proc = run_style50(["-o", "format", "--clang-format-style", "{IndentWidth: 2}", str(f)])
    assert proc.returncode == 0
    assert proc.stdout.strip() != ""

