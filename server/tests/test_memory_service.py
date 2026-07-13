"""测试 memory_service 模块"""
import pytest
from services.memory_service import (
    can_view_moment,
    get_relationship_intimacy,
    apply_relationship_interaction,
    build_memory_context,
    init_memory_db,
)
from models import MomentPost, Memory


@pytest.fixture(autouse=True)
def _ensure_memory_db():
    # 记忆/关系表需先初始化，模拟应用启动时的 init_memory_db()
    init_memory_db()


class TestMomentVisibility:
    """测试朋友圈可见性"""
    
    def test_public_moment(self):
        post = MomentPost(
            author_id="author1",
            author_name="测试作者",
            content="测试内容",
            visibility="public"
        )
        assert can_view_moment("viewer1", post) is True
    
    def test_private_moment_same_author(self):
        post = MomentPost(
            author_id="author1",
            author_name="测试作者",
            content="测试内容",
            visibility="private"
        )
        assert can_view_moment("author1", post) is True
    
    def test_private_moment_different_author(self):
        post = MomentPost(
            author_id="author1",
            author_name="测试作者",
            content="测试内容",
            visibility="private"
        )
        # 私密朋友圈，非作者不可见
        assert can_view_moment("viewer1", post) is False


class TestRelationshipIntimacy:
    """测试亲密度计算"""
    
    def test_initial_intimacy(self):
        # 无记录时应返回默认值
        result = get_relationship_intimacy("user1", "user2")
        assert isinstance(result, (int, float))


class TestMemoryContext:
    """测试记忆上下文构建"""
    
    def test_empty_memories(self):
        result = build_memory_context([], max_length=1000)
        assert result == ""
    
    def test_single_memory(self):
        memory = Memory(
            character_id="char1",
            content="测试记忆内容",
            memory_type="event",
            importance=0.5,
        )
        result = build_memory_context([memory], max_length=1000)
        assert "测试记忆" in result
    
    def test_max_length_truncation(self):
        memories = [
            Memory(
                character_id="char1",
                content=f"记忆内容{i}" * 50,
                memory_type="event",
                importance=0.5,
            )
            for i in range(5)
        ]
        result = build_memory_context(memories, max_length=200)
        assert len(result) <= 200
