"""
AIWeChat 记忆服务模块
记忆存储、检索、关系亲密度、向量检索等。
"""

from __future__ import annotations

import contextlib
import json
import math
import random
import threading
import time
import uuid
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from models import Memory, MemoryType
from models import MomentPost
from storage import (
    load_json, save_json, get_characters, get_api_configs, pick_enabled_rerank_config
)
from config import (
    MEMORIES_FILE, MEMORY_DB_FILE, MILLISECONDS_PER_DAY
)

# =====================================================================
#  SQLite 连接管理
# =====================================================================

_memory_conn: Optional[sqlite3.Connection] = None

# 共享单连接下的访问锁：串行化读改写，避免多线程/多任务交错破坏事务
_MEMORY_DB_LOCK = threading.RLock()


@contextlib.contextmanager
def _memory_db():
    """统一的数据库访问上下文。

    - 加锁：本项目共用一个 sqlite 连接对象，多线程并发 execute 会交错，
      必须串行化；否则会出现「读到别人未提交的中间态」或事务错乱。
    - 退出时 commit、异常时 rollback，与 sqlite3.Connection 自身的语义一致。
    """
    with _MEMORY_DB_LOCK:
        conn = get_memory_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def get_memory_conn() -> sqlite3.Connection:
    """获取 SQLite 连接"""
    global _memory_conn
    if _memory_conn is not None:
        # sqlite3.Connection 没有 `.closed` 属性；用轻量查询探测连接是否仍可用
        try:
            _memory_conn.execute("SELECT 1")
            return _memory_conn
        except sqlite3.Error:
            _memory_conn = None

    # check_same_thread=False + timeout：允许跨线程使用同一连接（本项目用全局连接），
    # 并在锁竞争时最多等 30 秒而不是立刻抛 "database is locked"。
    _memory_conn = sqlite3.connect(MEMORY_DB_FILE, timeout=30, check_same_thread=False)
    _memory_conn.row_factory = sqlite3.Row
    _memory_conn.execute("PRAGMA journal_mode=WAL")
    _memory_conn.execute("PRAGMA synchronous=NORMAL")
    _memory_conn.execute("PRAGMA busy_timeout=30000")
    return _memory_conn


def init_memory_db():
    """初始化记忆数据库"""
    with _memory_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                importance REAL DEFAULT 0.5,
                emotion TEXT,
                related_entities_json TEXT,
                timestamp INTEGER NOT NULL,
                valid_from INTEGER NOT NULL,
                valid_to INTEGER,
                embedding_json TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed INTEGER,
                metadata_json TEXT
            );
            
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                from_id TEXT NOT NULL,
                to_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                intimacy REAL DEFAULT 0,
                valid_from INTEGER NOT NULL,
                valid_to INTEGER,
                properties_json TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_memories_char ON memories(character_id);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
            CREATE INDEX IF NOT EXISTS idx_memories_ts ON memories(timestamp);
            CREATE INDEX IF NOT EXISTS idx_relationships_pair ON relationships(from_id, to_id);
            CREATE INDEX IF NOT EXISTS idx_relationships_active ON relationships(relation_type, valid_to);
        """)
        conn.commit()


def migrate_legacy_memories_if_needed():
    """迁移旧版 JSON 记忆到 SQLite"""
    try:
        with _memory_db() as conn:
            count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            if count > 0:
                return  # 已有数据，跳过迁移
    except Exception:
        return
    
    data = load_json(MEMORIES_FILE, [])
    if not data:
        return
    
    with _memory_db() as conn:
        for item in data:
            try:
                mem = Memory(**item)
                conn.execute(
                    "INSERT OR IGNORE INTO memories (id, character_id, memory_type, content, importance, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                    (mem.id, mem.character_id, mem.memory_type, mem.content, mem.importance, mem.timestamp),
                )
            except Exception:
                continue
        conn.commit()


# =====================================================================
#  记忆序列化
# =====================================================================

def memory_to_row(memory: Memory) -> tuple:
    """将 Memory 对象转为数据库行"""
    return (
        memory.id,
        memory.character_id,
        memory.memory_type.value if isinstance(memory.memory_type, MemoryType) else memory.memory_type,
        memory.content,
        float(memory.importance),
        memory.emotion,
        json.dumps(memory.related_entities, ensure_ascii=False),
        memory.timestamp,
        memory.valid_from,
        memory.valid_to,
        json.dumps(memory.embedding, ensure_ascii=False) if memory.embedding else None,
        memory.access_count,
        memory.last_accessed,
        json.dumps(memory.metadata, ensure_ascii=False),
    )


def row_to_memory(row: sqlite3.Row) -> Memory:
    """将数据库行转为 Memory 对象"""
    return Memory(
        id=row["id"],
        character_id=row["character_id"],
        memory_type=row["memory_type"],
        content=row["content"],
        importance=float(row["importance"] or 0.5),
        emotion=row["emotion"],
        related_entities=json.loads(row["related_entities_json"] or "[]"),
        timestamp=row["timestamp"],
        valid_from=row["valid_from"],
        valid_to=row["valid_to"],
        embedding=json.loads(row["embedding_json"]) if row["embedding_json"] else None,
        access_count=row["access_count"] or 0,
        last_accessed=row["last_accessed"],
        metadata=json.loads(row["metadata_json"] or "{}"),
    )


# =====================================================================
#  JSON 记忆操作（兼容旧版）
# =====================================================================

def get_memories() -> List[Memory]:
    """获取所有记忆（从 SQLite）"""
    with _memory_db() as conn:
        rows = conn.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT 500").fetchall()
    return [row_to_memory(r) for r in rows]


def save_memories(memories: List[Memory]):
    """保存记忆（批量更新）"""
    with _memory_db() as conn:
        for m in memories:
            conn.execute(
                "INSERT OR REPLACE INTO memories (id, character_id, memory_type, content, importance, emotion, related_entities_json, timestamp, valid_from, valid_to, embedding_json, access_count, last_accessed, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                memory_to_row(m),
            )
        conn.commit()


def get_character_memories(character_id: str, limit: int = 100) -> List[Memory]:
    """获取角色记忆"""
    with _memory_db() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE character_id = ? ORDER BY timestamp DESC LIMIT ?",
            (character_id, limit),
        ).fetchall()
    return [row_to_memory(r) for r in rows]


async def store_memory(
    character_id: str,
    memory_type: str,
    content: str,
    importance: float = 0.5,
    emotion: Optional[str] = None,
    related_entities: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Memory:
    """存储记忆（向量来自 API 配置中已启用的 embedding 模型，无配置则不写入向量）。"""
    from services.ai_service import get_embedding

    embedding = None
    try:
        embedding = await get_embedding(content[:500])
    except Exception:
        pass
    
    memory = Memory(
        id=str(uuid.uuid4()),
        character_id=character_id,
        memory_type=memory_type if isinstance(memory_type, MemoryType) else MemoryType(memory_type),
        content=content,
        importance=importance,
        emotion=emotion,
        related_entities=related_entities or [],
        embedding=embedding,
        metadata=metadata or {},
    )
    
    with _memory_db() as conn:
        conn.execute(
            """
            INSERT INTO memories (
                id, character_id, memory_type, content, importance, emotion,
                related_entities_json, timestamp, valid_from, valid_to,
                embedding_json, access_count, last_accessed, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            memory_to_row(memory),
        )
        conn.commit()
    
    return memory


# =====================================================================
#  关系亲密度
# =====================================================================

def get_relationship_intimacy(viewer_id: str, author_id: str) -> float:
    """获取两人之间的亲密度"""
    if not viewer_id or not author_id or viewer_id == author_id:
        return 50.0
    
    with _memory_db() as conn:
        row = conn.execute(
            """
            SELECT intimacy FROM relationships
            WHERE relation_type = 'FRIEND_WITH'
              AND valid_to IS NULL
              AND ((from_id = ? AND to_id = ?) OR (from_id = ? AND to_id = ?))
            ORDER BY valid_from DESC
            LIMIT 1
            """,
            (viewer_id, author_id, author_id, viewer_id),
        ).fetchone()
    
    return float(row["intimacy"]) if row else 20.0


def can_view_moment(viewer_id: Optional[str], post: MomentPost) -> bool:
    """检查是否可以查看朋友圈"""
    if not viewer_id:
        return True
    if viewer_id == "user":
        return True
    if viewer_id == post.author_id:
        return True
    visibility = (getattr(post, "visibility", None) or "friends").lower()
    if visibility == "public":
        return True
    if visibility == "private":
        return False
    intimacy = get_relationship_intimacy(viewer_id, post.author_id)
    return intimacy >= post.visible_min_intimacy


# =====================================================================
#  关系管理
# =====================================================================

def _get_active_relationship_row(a: str, b: str) -> Optional[sqlite3.Row]:
    """获取活跃关系行"""
    with _memory_db() as conn:
        row = conn.execute(
            """
            SELECT * FROM relationships
            WHERE (
                (from_id = ? AND to_id = ?)
                OR (from_id = ? AND to_id = ?)
            )
            AND relation_type = 'FRIEND_WITH'
            AND valid_to IS NULL
            ORDER BY valid_from DESC
            LIMIT 1
            """,
            (a, b, b, a),
        ).fetchone()
    return row


def _close_active_relationships(conn: sqlite3.Connection, a: str, b: str, now_ms: int):
    """关闭活跃关系"""
    conn.execute(
        """
        UPDATE relationships
        SET valid_to = ?
        WHERE relation_type = 'FRIEND_WITH'
          AND valid_to IS NULL
          AND (
            (from_id = ? AND to_id = ?)
            OR (from_id = ? AND to_id = ?)
          )
        """,
        (now_ms, a, b, b, a),
    )


def set_pair_relationship(a: str, b: str, intimacy: float, metadata: Optional[Dict[str, Any]] = None):
    """设置两人关系"""
    if not a or not b or a == b:
        return
    now_ms = int(time.time() * 1000)
    metadata = metadata or {}
    with _memory_db() as conn:
        _close_active_relationships(conn, a, b, now_ms)
        if intimacy >= 20:
            properties = {
                "last_interaction_at": now_ms,
                "last_decay_at": now_ms,
                **metadata,
            }
            for from_id, to_id in ((a, b), (b, a)):
                conn.execute(
                    """
                    INSERT INTO relationships (
                        id, from_id, to_id, relation_type, intimacy, valid_from, valid_to, properties_json
                    ) VALUES (?, ?, ?, 'FRIEND_WITH', ?, ?, NULL, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        from_id,
                        to_id,
                        float(max(0, min(100, intimacy))),
                        now_ms,
                        json.dumps(properties, ensure_ascii=False),
                    ),
                )
        conn.commit()


def apply_relationship_interaction(from_id: str, to_id: str, action: str) -> float:
    """应用关系互动"""
    if not from_id or not to_id or from_id == to_id:
        return 0.0
    action = (action or "").lower()
    if action == "chat":
        delta = random.randint(1, 3)
    elif action == "like":
        delta = 1
    elif action == "comment":
        delta = 2
    elif action == "meet":
        delta = random.randint(2, 5)
    elif action == "collaborate":
        delta = random.randint(1, 10)
    elif action == "conflict":
        delta = -random.randint(5, 15)
    else:
        delta = 0

    current = get_relationship_intimacy(from_id, to_id)
    if current <= 20:
        coefficient = 1.2
    elif current >= 81:
        coefficient = 0.8
    else:
        coefficient = 1.0
    new_intimacy = max(0.0, min(100.0, current + delta * coefficient))
    set_pair_relationship(from_id, to_id, new_intimacy, {"last_action": action})
    return new_intimacy


def apply_inactivity_decay() -> int:
    """应用不活跃衰减"""
    now_ms = int(time.time() * 1000)
    with _memory_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM relationships
            WHERE relation_type = 'FRIEND_WITH'
              AND valid_to IS NULL
            ORDER BY valid_from DESC
            """
        ).fetchall()
    seen = set()
    changed = 0
    for row in rows:
        a, b = row["from_id"], row["to_id"]
        key = _pair_key(a, b)
        if key in seen:
            continue
        seen.add(key)
        properties = json.loads(row["properties_json"] or "{}")
        last_interaction = int(properties.get("last_interaction_at", row["valid_from"]))
        elapsed_days = int((now_ms - last_interaction) // MILLISECONDS_PER_DAY)
        if elapsed_days <= 3:
            continue
        decay = elapsed_days - 3
        current = float(row["intimacy"])
        new_intimacy = max(0.0, current - decay)
        set_pair_relationship(a, b, new_intimacy, {"last_decay_at": now_ms, "last_action": "inactivity_decay"})
        changed += 1
    return changed


def _pair_key(a: str, b: str) -> str:
    """生成关系键"""
    x, y = sorted([a, b])
    return f"{x}:{y}"


def get_active_friend_pairs(min_intimacy_exclusive: float = 15.0) -> Dict[str, Dict[str, Any]]:
    """获取亲密度 **严格大于** min_intimacy_exclusive 的好友对（默认 >15 可建双人私聊群）。"""
    with _memory_db() as conn:
        rows = conn.execute(
            """
            SELECT from_id, to_id, intimacy
            FROM relationships
            WHERE relation_type = 'FRIEND_WITH'
              AND valid_to IS NULL
              AND intimacy > ?
            ORDER BY valid_from DESC
            """,
            (min_intimacy_exclusive,),
        ).fetchall()
    pairs: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = _pair_key(row["from_id"], row["to_id"])
        if key in pairs:
            continue
        pairs[key] = {
            "member_ids": sorted([row["from_id"], row["to_id"]]),
            "intimacy": float(row["intimacy"]),
        }
    return pairs


def sync_private_groups() -> Dict[str, int]:
    """同步私聊群"""
    from storage import get_private_groups, save_private_groups
    from models import PrivateGroupChat
    
    groups = get_private_groups()
    chars = {c.id: c for c in get_characters()}
    active_pairs = get_active_friend_pairs(15.0)
    now_ms = int(time.time() * 1000)
    created = 0
    dissolved = 0

    existing_active: Dict[str, PrivateGroupChat] = {}
    for g in groups:
        if g.is_active and len(g.member_ids) == 2:
            existing_active[_pair_key(g.member_ids[0], g.member_ids[1])] = g

    for key, pair in active_pairs.items():
        if key in existing_active:
            continue
        member_ids = pair["member_ids"]
        member_names = [chars[mid].name for mid in member_ids if mid in chars]
        if len(member_names) != 2:
            continue

        group = PrivateGroupChat(
            id=str(uuid.uuid4()),
            member_ids=member_ids,
            member_names=[member_names[0], member_names[1]],
            is_active=True,
            created_at=now_ms,
        )
        groups.append(group)
        created += 1

    for key, g in list(existing_active.items()):
        if key not in active_pairs:
            g.is_active = False
            dissolved += 1

    if created or dissolved:
        save_private_groups(groups)

    return {"created": created, "dissolved": dissolved}


# =====================================================================
#  记忆检索
# =====================================================================

def time_decay_weight(timestamp: int, is_reflection: bool = False) -> float:
    """时间衰减函数"""
    hours_since = (time.time() * 1000 - timestamp) / (1000 * 60 * 60)
    half_life = 168 if is_reflection else 72
    return math.exp(-hours_since / half_life)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


async def recall_memories(
    character_id: str,
    query: str,
    top_k: int = 10,
    time_range: tuple = None
) -> List[Memory]:
    """召回相关记忆：先用向量配置做相似度粗排，若有 rerank 配置再精排。"""
    from services.ai_service import get_embedding, rerank_documents_order

    char_memories = get_character_memories(character_id, limit=300)
    
    if time_range:
        start_time, end_time = time_range
        char_memories = [
            m for m in char_memories 
            if start_time <= m.timestamp <= end_time
        ]
    
    query_embedding = await get_embedding(query)
    
    scored_memories = []
    for memory in char_memories:
        if query_embedding and memory.embedding:
            similarity = cosine_similarity(query_embedding, memory.embedding)
        else:
            similarity = simple_text_similarity(query, memory.content)
        
        is_reflection = memory.memory_type == MemoryType.REFLECTION
        time_weight = time_decay_weight(memory.timestamp, is_reflection)
        importance_weight = memory.importance
        final_score = similarity * time_weight * (0.5 + importance_weight * 0.5)
        
        scored_memories.append((memory, final_score))
    
    scored_memories.sort(key=lambda x: x[1], reverse=True)
    pool_size = max(top_k * 6, 36)
    pool = scored_memories[: min(pool_size, len(scored_memories))]
    memories_only = [m for m, _ in pool]
    cfg_rerank = pick_enabled_rerank_config(get_api_configs())
    if cfg_rerank and len(memories_only) > 1:
        docs = [m.content[:500] for m in memories_only]
        order = await rerank_documents_order(query, docs, cfg_rerank)
        if order:
            reordered = []
            seen = set()
            for i in order:
                if isinstance(i, int) and 0 <= i < len(memories_only) and i not in seen:
                    seen.add(i)
                    reordered.append(memories_only[i])
            for i in range(len(memories_only)):
                if i not in seen:
                    reordered.append(memories_only[i])
            memories_only = reordered
    result = memories_only[:top_k]
    
    for memory in result:
        memory.access_count += 1
        memory.last_accessed = int(time.time() * 1000)
    
    if result:
        with _memory_db() as conn:
            conn.executemany(
                "UPDATE memories SET access_count = ?, last_accessed = ? WHERE id = ?",
                [(m.access_count, m.last_accessed, m.id) for m in result],
            )
            conn.commit()
    
    return result


def simple_text_similarity(query: str, content: str) -> float:
    """简单文本相似度"""
    query_words = set(query.lower().split())
    content_words = set(content.lower().split())
    
    if not query_words:
        return 0.0
    
    intersection = query_words & content_words
    return len(intersection) / len(query_words)


def build_memory_context(memories: List[Memory], max_length: int = 1000) -> str:
    """构建记忆上下文"""
    if not memories:
        return ""
    
    context_parts = []
    total_length = 0
    
    for memory in memories:
        time_str = datetime.fromtimestamp(memory.timestamp / 1000).strftime("%Y-%m-%d %H:%M")
        memory_text = f"[{time_str}] {memory.content}"
        
        if total_length + len(memory_text) > max_length:
            break
        
        context_parts.append(memory_text)
        total_length += len(memory_text)
    
    return "\n".join(context_parts)
