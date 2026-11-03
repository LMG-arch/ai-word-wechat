"""V4.0 包A4：朋友圈进阶（话题 / 位置 / @好友）"""
import pytest

from services.moment_extras import (
    extract_topics, extract_mention_names, resolve_mentioned_ids,
    topic_leaderboard, location_leaderboard, normalize_topic,
    mentioned_reply_text,
)


def test_extract_topics_basic():
    assert extract_topics("今天 #周末去哪儿# 好开心") == ["周末去哪儿"]


def test_extract_topics_multiple_and_dedup():
    content = "#咖啡# 和 #咖啡# 还有 #加班#"
    assert extract_topics(content) == ["咖啡", "加班"]


def test_extract_topics_ignores_unclosed():
    assert extract_topics("只有一个 #没闭合") == []
    assert extract_topics("") == []


def test_extract_topics_caps_at_five():
    content = "".join(f"#话题{i}#" for i in range(9))
    assert len(extract_topics(content)) == 5


def test_normalize_topic_strips_hashes():
    assert normalize_topic("  #咖啡#  ") == "咖啡"


def test_extract_mention_names():
    assert extract_mention_names("今天 @小李 和 @小王 一起吃饭") == ["小李", "小王"]


def test_extract_mention_names_stops_at_punctuation():
    names = extract_mention_names("@小李，你在吗")
    assert names == ["小李"]


def test_resolve_mentioned_ids_maps_by_name():
    class C:
        def __init__(self, i, n):
            self.id = i
            self.name = n

    chars = [C("1", "小李"), C("2", "小王")]
    assert resolve_mentioned_ids(["小王"], chars) == ["2"]
    assert resolve_mentioned_ids(["不存在"], chars) == []
    assert resolve_mentioned_ids([], chars, extra_names=["小李"]) == ["1"]


def test_topic_leaderboard_sorted_by_count():
    class P:
        def __init__(self, topics, ts):
            self.topics = topics
            self.timestamp = ts

    posts = [P(["咖啡"], 1), P(["咖啡", "加班"], 2), P(["加班"], 3)]
    board = topic_leaderboard(posts)
    assert board[0]["topic"] in ("咖啡", "加班")
    assert board[0]["count"] == 2


def test_location_leaderboard_skips_empty():
    class P:
        def __init__(self, loc, ts):
            self.location = loc
            self.timestamp = ts

    posts = [P("咖啡馆", 1), P("", 2), P(None, 3), P("咖啡馆", 4)]
    board = location_leaderboard(posts)
    assert len(board) == 1
    assert board[0]["location"] == "咖啡馆"
    assert board[0]["count"] == 2


def test_mentioned_reply_mentions_author():
    text = mentioned_reply_text("用户", "小李")
    assert "用户" in text


# ---------------- 端点级 ----------------


def test_create_moment_with_topic_location_mention(isolated_client):
    client, chars = isolated_client
    target = chars[0]

    resp = client.post("/api/users/moments", json={
        "content": f"周末探店 #咖啡# #探店# @{target.name} 一起来",
        "visibility": "public",
        "location": "城市咖啡馆",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["topics"] == ["咖啡", "探店"]
    assert data["location"] == "城市咖啡馆"
    assert target.id in data["mentioned_ids"]
    assert data["visibility"] == "public"


def test_moment_topics_endpoint(isolated_client):
    client, _ = isolated_client
    client.post("/api/users/moments", json={"content": "第一条 #咖啡#", "visibility": "public"})
    client.post("/api/users/moments", json={"content": "第二条 #咖啡# #加班#", "visibility": "public"})

    resp = client.get("/api/moments/topics")
    assert resp.status_code == 200
    board = resp.json()["data"]
    assert board[0]["topic"] == "咖啡"
    assert board[0]["count"] == 2


def test_moment_locations_endpoint(isolated_client):
    client, _ = isolated_client
    client.post("/api/users/moments", json={"content": "打卡", "location": "图书馆", "visibility": "public"})

    resp = client.get("/api/moments/locations")
    assert resp.status_code == 200
    assert resp.json()["data"][0]["location"] == "图书馆"


def test_moment_filter_by_topic(isolated_client):
    client, _ = isolated_client
    client.post("/api/users/moments", json={"content": "只有 #咖啡#", "visibility": "public"})
    client.post("/api/users/moments", json={"content": "只有 #加班#", "visibility": "public"})

    all_resp = client.get("/api/moments")
    assert len(all_resp.json()["data"]) >= 2

    filtered = client.get("/api/moments", params={"topic": "咖啡"})
    assert filtered.status_code == 200
    assert all("咖啡" in (m["topics"] or []) for m in filtered.json()["data"])
    assert len(filtered.json()["data"]) == 1


def test_moment_filter_by_location(isolated_client):
    client, _ = isolated_client
    client.post("/api/users/moments", json={"content": "甲", "location": "图书馆", "visibility": "public"})
    client.post("/api/users/moments", json={"content": "乙", "location": "食堂", "visibility": "public"})

    filtered = client.get("/api/moments", params={"location": "图书馆"})
    assert len(filtered.json()["data"]) == 1
    assert filtered.json()["data"][0]["location"] == "图书馆"


def test_mentioned_character_replies_in_comments(isolated_client):
    """被 @ 的角色会出现在评论区（BackgroundTasks 在 TestClient 中同步执行）"""
    client, chars = isolated_client
    target = chars[0]

    resp = client.post("/api/users/moments", json={
        "content": f"@{target.name} 出来聊天",
        "visibility": "public",
    })
    assert resp.status_code == 200
    mid = resp.json()["data"]["id"]

    moments = client.get("/api/moments").json()["data"]
    post = next(m for m in moments if m["id"] == mid)
    assert any(c["author_id"] == target.id for c in post["comments"])
