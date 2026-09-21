import unittest
from pathlib import Path

from tools.check_workspace import cjk_outside_comments


class TextPolicyTests(unittest.TestCase):
    def test_c_and_cpp_comments_may_contain_cjk(self):
        source = '// \u4e2d\u6587\u884c\u6ce8\u91ca\nconst char *text = "English"; /* \u4e2d\u6587\u5757\u6ce8\u91ca */\n'
        self.assertFalse(cjk_outside_comments(Path("example.cpp"), source))

    def test_cjk_in_cpp_string_is_not_treated_as_comment(self):
        source = 'const char *text = "\u4e2d\u6587\u5b57\u7b26\u4e32"; // \u4e2d\u6587\u6ce8\u91ca\n'
        self.assertTrue(cjk_outside_comments(Path("example.cpp"), source))

    def test_hash_comments_may_contain_cjk(self):
        config = '# \u4e2d\u6587\u6ce8\u91ca\nStyle: "value#not-comment" # \u4e2d\u6587\u5c3e\u6ce8\n'
        self.assertFalse(cjk_outside_comments(Path(".clang-format"), config))

    def test_cjk_in_quoted_config_value_is_not_treated_as_comment(self):
        config = 'Label: "\u4e2d\u6587\u503c" # \u4e2d\u6587\u6ce8\u91ca\n'
        self.assertTrue(cjk_outside_comments(Path("config.yaml"), config))


if __name__ == "__main__":
    unittest.main()
