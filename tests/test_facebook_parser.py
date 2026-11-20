import unittest
from facebook_parser import extract_post_id, extract_comment_id


class TestExtractPostId(unittest.TestCase):

    def test_valid_post_url(self):
        url = "https://www.facebook.com/COIceconditions/posts/123456789"

        result = extract_post_id(url)

        self.assertEqual(result, "123456789")

    def test_url_multiple_parameters(self):
        url = "https://www.facebook.com/COIceconditions/posts/123?foo=bar&comment_id=456&other=789"

        result = extract_post_id(url)

        self.assertEqual(result, "123")

    def test_reel_url(self):
        url = "https://www.facebook.com/reel/123456789"

        result = extract_post_id(url)

        self.assertIsNone(result)

    def test_invalid_url(self):
        url = "https://www.facebook.com/COIceconditions"

        result = extract_post_id(url)

        self.assertIsNone(result)


class TestExtractCommentId(unittest.TestCase):
    def test_valid_comment_url(self):
        url = "https://www.facebook.com/COIceconditions/posts/postid12345?comment_id=123456789&__abcdefg12345abcdefg12345"

        result = extract_comment_id(url)

        self.assertEqual(result, "123456789")

    def test_post_url(self):
        url = "https://www.facebook.com/COIceconditions/posts/postid12345"

        result = extract_comment_id(url)

        self.assertIsNone(result)

    def test_url_multiple_parameters(self):
            url = "https://www.facebook.com/COIceconditions/posts/123?foo=bar&comment_id=456&other=789"
    
            result = extract_comment_id(url)
    
            self.assertEqual(result, "456")


if __name__ == "__main__":
    unittest.main()