import pytest


def test_python_formatter_runs():
    from style50.languages import Python

    original = "x=1\n\nprint(  x)\n"
    formatted = Python(original).styled
    assert isinstance(formatted, str)
    assert formatted.endswith("\n")


def test_js_formatter_runs():
    from style50.languages import Js

    original = "function f(){return 1;}\n"
    formatted = Js(original).styled
    assert isinstance(formatted, str)
    assert formatted.endswith("\n")


def test_css_formatter_runs():
    from style50.languages import Css

    original = "body{color:red;}\n"
    formatted = Css(original).styled
    assert isinstance(formatted, str)
    assert formatted.endswith("\n")


def test_sql_formatter_runs():
    from style50.languages import Sql

    original = "select * from foo;\n"
    formatted = Sql(original).styled
    assert isinstance(formatted, str)
    assert "FROM" in formatted


def test_html_formatter_invokes_djhtml(monkeypatch):
    from style50.languages import Html
    from style50._api import StyleCheck

    calls = {"cmd": None}

    def fake_run(command, input=None, exit=0, shell=False):
        calls["cmd"] = command
        # Pretend the formatter normalizes whitespace, but keep it simple.
        return "<!doctype html>\n"

    monkeypatch.setattr(StyleCheck, "run", staticmethod(fake_run))
    formatted = Html("<html></html>\n").styled
    assert calls["cmd"] == ["djhtml", "-"]
    assert formatted == "<!doctype html>\n"


def test_clang_format_style_override_preserves_java_flags(monkeypatch):
    """
    Ensure override style does not drop Java's '-assume-filename=.java' flag.
    This is tested by capturing the command rather than invoking clang-format.
    """
    from style50.languages import Java
    from style50._api import StyleCheck

    seen = {"cmd": None}

    def fake_run(command, input=None, exit=0, shell=False):
        seen["cmd"] = command
        return input.decode() if isinstance(input, (bytes, bytearray)) else (input or "")

    monkeypatch.setattr(StyleCheck, "run", staticmethod(fake_run))
    _ = Java("class X{}\n", clang_format_style="{IndentWidth: 2}").styled

    assert isinstance(seen["cmd"], list)
    assert "clang-format" in seen["cmd"][0]
    assert any(arg.startswith("-style=") for arg in seen["cmd"])
    assert "-assume-filename=.java" in seen["cmd"]


@pytest.mark.parametrize("value", ["undefined", "null", "none", "  'undefined'  "])
def test_clang_format_style_override_ignores_stringified_nulls(monkeypatch, value):
    from style50.languages import C
    from style50._api import StyleCheck

    seen = {"cmd": None}

    def fake_run(command, input=None, exit=0, shell=False):
        seen["cmd"] = command
        return input.decode() if isinstance(input, (bytes, bytearray)) else (input or "")

    monkeypatch.setattr(StyleCheck, "run", staticmethod(fake_run))
    _ = C("int main(){}\n", clang_format_style=value).styled

    assert seen["cmd"] == C.clangFormat

