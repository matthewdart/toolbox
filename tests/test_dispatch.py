import json
import unittest

from core.dispatch import dispatch


class DispatchTests(unittest.TestCase):
    def test_normalize_markdown_success(self):
        payload = {"text": "hello  \nworld"}
        result = dispatch("text.normalize_markdown", payload)
        self.assertTrue(result["ok"], result)
        output = result["result"]
        self.assertIn("text", output)
        self.assertIn("changes", output)
        self.assertEqual(output["text"], "hello\nworld\n")
        self.assertIn("trim_trailing_whitespace", output["changes"])
        self.assertIn("ensure_final_newline", output["changes"])

    def test_normalize_markdown_validation_error(self):
        payload = {"text": 123}
        result = dispatch("text.normalize_markdown", payload)
        self.assertFalse(result["ok"], result)
        self.assertEqual(result["error"]["type"], "validation_error")


if __name__ == "__main__":
    unittest.main()
