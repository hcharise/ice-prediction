import unittest
from facebook_parser import extract_post_id


class TestExtractPostId(unittest.TestCase):

    def test_valid_post_url(self):
        url = "https://www.facebook.com/COIceconditions/posts/123456789"

        result = extract_post_id(url)

        self.assertEqual(result, "123456789")

    def test_reel_url(self):
        url = "https://www.facebook.com/reel/123456789"

        result = extract_post_id(url)

        self.assertIsNone(result)

    def test_invalid_url(self):
        url = "https://www.facebook.com/COIceconditions"

        result = extract_post_id(url)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()