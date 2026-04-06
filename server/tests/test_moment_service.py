"""测试 moment_service 模块"""
import pytest
from services.moment_service import (
    fallback_moment_image_url,
    should_continue_reply,
    has_commented_moment,
)


class TestFallbackImageUrl:
    """测试兜底朋友圈图片 URL"""
    
    def test_deterministic_output(self):
        url1 = fallback_moment_image_url("seed1")
        url2 = fallback_moment_image_url("seed1")
        assert url1 == url2
    
    def test_different_seeds(self):
        url1 = fallback_moment_image_url("seed1")
        url2 = fallback_moment_image_url("seed2")
        assert url1 != url2


class TestShouldContinueReply:
    """测试是否应继续回复"""
    
    def test_high_intimacy_continue(self):
        assert should_continue_reply("parent", "reply", 0.9) is True
    
    def test_low_intimacy_stop(self):
        assert should_continue_reply("parent", "reply", 0.1) is False
    
    def test_long_parent_stop(self):
        long_content = "x" * 500
        assert should_continue_reply(long_content, "reply", 0.5) is False


class TestHasCommentedMoment:
    """测试是否已评论"""
    
    def test_empty_comments(self):
        post = type('MockPost', (), {'comments': []})()
        assert has_commented_moment(post, "user1") is False
    
    def test_author_commented(self):
        comment = type('MockComment', (), {'author_id': "user1"})()
        post = type('MockPost', (), {'comments': [comment]})()
        assert has_commented_moment(post, "user1") is True
    
    def test_other_commented(self):
        comment = type('MockComment', (), {'author_id': "user2"})()
        post = type('MockPost', (), {'comments': [comment]})()
        assert has_commented_moment(post, "user1") is False
