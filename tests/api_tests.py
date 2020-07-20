import unittest
import os
import sys
import contextlib
import pathlib
import tempfile
import io
import re
import logging
import subprocess
import time
import termcolor
import pexpect

import style50._api

class TestStyle50_Init(unittest.TestCase):
    def test_output_invalid(self):
        with self.assertRaises(style50.Error):
            style50._api.Style50("invalid")

    def test_output_score(self):
        style = style50._api.Style50("score")
        self.assertEqual(style.output, "score")
        self.assertTrue(isinstance(style.diff, type(lambda:0)))

    def test_output_html(self):
        style = style50._api.Style50("json")
        self.assertEqual(style.output, "json")
        self.assertEqual(style.diff, style.html_diff)

        style = style50._api.Style50("html")
        self.assertEqual(style.output, "html")
        self.assertEqual(style.diff, style.html_diff)

    def test_output_char(self):
        style = style50._api.Style50("character")
        self.assertEqual(style.output, "character")
        self.assertEqual(style.diff, style.char_diff)

    def test_output_split(self):
        style = style50._api.Style50("split")
        self.assertEqual(style.output, "split")
        self.assertEqual(style.diff, style.split_diff)

    def test_output_unified(self):
        style = style50._api.Style50("unified")
        self.assertEqual(style.output, "unified")
        self.assertEqual(style.diff, style.unified)


class TestStyle50_Check(unittest.TestCase):
    def setUp(self):
        self.style = style50._api.Style50("score")

    def test_c_0(self):
        result = self.style.check(["tests/fixtures/hello0.c"])
        self.assertAlmostEqual(result["score"], 1)

    def test_c_1(self):
        result = self.style.check(["tests/fixtures/hello1.c"])
        self.assertLessEqual(result["score"], .5)

    def test_java_0(self):
        result = self.style.check(["tests/fixtures/hello0.java"])
        self.assertAlmostEqual(result["score"], 1)

    def test_java_1(self):
        result = self.style.check(["tests/fixtures/hello1.java"])
        self.assertLessEqual(result["score"], .5)

    def test_js_0(self):
        result = self.style.check(["tests/fixtures/hello0.js"])
        self.assertAlmostEqual(result["score"], 1)
    
    def test_js_1(self):
        result = self.style.check(["tests/fixtures/hello1.js"])
        self.assertLessEqual(result["score"], .3)

    def test_python_0(self):
        result = self.style.check(["tests/fixtures/hello0.py"])
        self.assertAlmostEqual(result["score"], 1)

    def test_python_1(self):
        result = self.style.check(["tests/fixtures/hello1.py"])
        self.assertLessEqual(result["score"], .8)

    def test_binary(self):
        result = self.style.check(["tests/fixtures/binary.c"])
        self.assertTrue("file does not seem to contain text, skipping..." in result["files"][0].values())

    def test_empty(self):
        with open("tests/fixtures/empty.c", "w") as f:
            pass

        result = self.style.check(["tests/fixtures/empty.c"])
        self.assertTrue("file is empty" in result["files"][0].values())

    def test_nonexistent(self):
        result = self.style.check(["nonexistent.c"])
        self.assertTrue("file \"nonexistent.c\" not found" in result["files"][0].values())

    def test_unknown_type(self):
        with open("tests/fixtures/file.mystery", "w") as f:
            pass

        result = self.style.check(["tests/fixtures/file.mystery"])
        self.assertTrue("unknown file type \"tests/fixtures/file.mystery\", skipping..." in result["files"][0].values())


if __name__ == '__main__':
    unittest.main()
