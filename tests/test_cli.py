import os
import subprocess
import sys

import pytest


def run_style50(args, *, cwd=None, env=None):
    merged_env = None
    if env is not None:
        merged_env = dict(**env)
        baseline = os.environ.copy()
        baseline.update(merged_env)
        merged_env = baseline

    return subprocess.run(
        [sys.executable, "-m", "style50", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=merged_env,
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


def test_in_place_rewrites_file(tmp_path):
    f = tmp_path / "t.py"
    original = "x=1\nprint(  x)\n"
    f.write_text(original, encoding="utf-8")

    proc = run_style50(["-i", str(f)])
    assert proc.returncode == 0

    updated = f.read_text(encoding="utf-8")
    assert updated != original
    assert "print(x)" in updated


def test_in_place_multiple_files(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("x=1\nprint(  x)\n", encoding="utf-8")
    f2.write_text("y=2\nprint(  y)\n", encoding="utf-8")

    proc = run_style50(["-i", str(f1), str(f2)])
    assert proc.returncode == 0
    assert "print(x)" in f1.read_text(encoding="utf-8")
    assert "print(y)" in f2.read_text(encoding="utf-8")


def test_in_place_skips_already_styled(tmp_path):
    f = tmp_path / "t.py"
    original = "x = 1\nprint(x)\n"
    f.write_text(original, encoding="utf-8")

    proc = run_style50(["-i", str(f)])
    assert proc.returncode == 0
    assert f.read_text(encoding="utf-8") == original


def test_side_by_side_flag(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-y", str(f)])
    assert proc.returncode == 0
    assert proc.stdout.strip() != ""


def test_in_place_and_side_by_side_conflict(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-i", "-y", str(f)])
    assert proc.returncode != 0
    assert "--in-place cannot be combined with --side-by-side" in (proc.stdout + proc.stderr)


def test_in_place_respects_ignore(tmp_path):
    keep = tmp_path / "keep.py"
    skip = tmp_path / "skip.py"
    keep.write_text("x=1\nprint(  x)\n", encoding="utf-8")
    skip.write_text("y=1\nprint(  y)\n", encoding="utf-8")

    proc = run_style50(["-i", "--ignore", "*skip.py", str(keep), str(skip)])
    assert proc.returncode == 0

    assert "print(x)" in keep.read_text(encoding="utf-8")
    assert "print(  y)" in skip.read_text(encoding="utf-8")


def test_in_place_and_output_conflict(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-i", "-o", "split", str(f)])
    assert proc.returncode != 0
    assert "--in-place cannot be combined with --output" in (proc.stdout + proc.stderr)


def test_in_place_and_output_character_conflict(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-i", "-o", "character", str(f)])
    assert proc.returncode != 0
    assert "--in-place cannot be combined with --output" in (proc.stdout + proc.stderr)


def test_in_place_directory_input_and_ignore(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    keep = src / "keep.py"
    skip = src / "skip.py"
    keep.write_text("x=1\nprint(  x)\n", encoding="utf-8")
    skip.write_text("y=1\nprint(  y)\n", encoding="utf-8")

    proc = run_style50(["-i", "--ignore", "*skip.py", str(src)])
    assert proc.returncode == 0
    assert "print(x)" in keep.read_text(encoding="utf-8")
    assert "print(  y)" in skip.read_text(encoding="utf-8")


def test_in_place_respects_style50_ignore_env(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    keep = src / "keep.py"
    skip = src / "skip.py"
    keep.write_text("x=1\nprint(  x)\n", encoding="utf-8")
    skip.write_text("y=1\nprint(  y)\n", encoding="utf-8")

    proc = run_style50(["-i", str(src)], env={"STYLE50_IGNORE": "*skip.py"})
    assert proc.returncode == 0
    assert "print(x)" in keep.read_text(encoding="utf-8")
    assert "print(  y)" in skip.read_text(encoding="utf-8")


def test_in_place_returns_nonzero_when_any_file_fails(tmp_path):
    existing = tmp_path / "good.py"
    missing = tmp_path / "missing.py"
    existing.write_text("x=1\nprint(  x)\n", encoding="utf-8")

    proc = run_style50(["-i", str(existing), str(missing)])
    assert proc.returncode != 0
    # Existing file should still be processed.
    assert "print(x)" in existing.read_text(encoding="utf-8")


def test_format_mode_html_css_sql(tmp_path):
    html = tmp_path / "t.html"
    css = tmp_path / "t.css"
    sql = tmp_path / "t.sql"
    html.write_text("<html><body><h1>x</h1></body></html>\n", encoding="utf-8")
    css.write_text("body{color:red;}\n", encoding="utf-8")
    sql.write_text("select * from users where id=1;\n", encoding="utf-8")

    proc_html = run_style50(["-o", "format", str(html)])
    # Skip only if djhtml is unavailable in this environment.
    if proc_html.returncode != 0 and "requires djhtml" in (proc_html.stdout + proc_html.stderr):
        pytest.skip("djhtml not installed in test environment")
    assert proc_html.returncode == 0
    assert proc_html.stdout.strip() != ""

    proc_css = run_style50(["-o", "format", str(css)])
    assert proc_css.returncode == 0
    assert proc_css.stdout.strip() != ""

    proc_sql = run_style50(["-o", "format", str(sql)])
    assert proc_sql.returncode == 0
    assert "SELECT" in proc_sql.stdout

