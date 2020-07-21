import contextlib
import io
import json
import os
import pathlib
import tempfile
import unittest

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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = pathlib.Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_c_0(self):
        result = self.style.check(["tests/fixtures/hello0.c"])
        self.assertAlmostEqual(result["score"], 1)

    def test_c_1(self):
        result = self.style.check(["tests/fixtures/hello1.c"])
        self.assertAlmostEqual(result["score"], .416, 2)

    def test_java_0(self):
        result = self.style.check(["tests/fixtures/hello0.java"])
        self.assertAlmostEqual(result["score"], 1)

    def test_java_1(self):
        result = self.style.check(["tests/fixtures/hello1.java"])
        self.assertAlmostEqual(result["score"], .4, 2)

    def test_js_0(self):
        result = self.style.check(["tests/fixtures/hello0.js"])
        self.assertAlmostEqual(result["score"], 1)
    
    def test_js_1(self):
        result = self.style.check(["tests/fixtures/hello1.js"])
        self.assertAlmostEqual(result["score"], 0)

    def test_python_0(self):
        result = self.style.check(["tests/fixtures/hello0.py"])
        self.assertAlmostEqual(result["score"], 1)

    def test_python_1(self):
        result = self.style.check(["tests/fixtures/hello1.py"])
        self.assertAlmostEqual(result["score"], .57, 2)

    def test_binary(self):
        result = self.style.check(["tests/fixtures/binary.c"])
        self.assertTrue("file does not seem to contain text, skipping..." in result["files"][0].values())

    def test_empty(self):
        fname = self.temp_path / "empty.c"
        with open(fname, "w") as f:
            pass

        result = self.style.check([str(fname)])
        self.assertTrue("file is empty" in result["files"][0].values())

    def test_nonexistent(self):
        result = self.style.check(["nonexistent.c"])
        self.assertTrue("file \"nonexistent.c\" not found" in result["files"][0].values())

    def test_unknown_type(self):
        fname = self.temp_path / "file.mystery"
        with open(fname, "w") as f:
            pass

        result = self.style.check([str(fname)])
        self.assertTrue(f"unknown file type \"{fname}\", skipping..." in result["files"][0].values())


class TestStyle50_Run(unittest.TestCase):
    def setUp(self):
        self.paths = ["tests/fixtures/hello0.c"]

    def test_json(self):
        style = style50._api.Style50("json")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            style.run(self.paths)

        expected = style.check(self.paths)
        received = json.loads(f.getvalue())
        self.assertDictEqual(received, expected)

    def test_score(self):
        style = style50._api.Style50("score")

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            style.run(self.paths)

        expected = style.check(self.paths)
        received = f.getvalue()
        self.assertEqual(received.strip(), str(expected["score"]))


if __name__ == '__main__':
    os.chdir("..")
    unittest.main()
