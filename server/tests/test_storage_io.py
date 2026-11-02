"""数据持久化层回归测试。

背景：旧版 `save_json` 直接 `open(filename, 'w')` 截断写入，
若写盘中途进程被 kill / 磁盘写满，原文件会被毁成半截 JSON，数据全丢。
现已改为「临时文件 + fsync + os.replace」原子写，并支持损坏文件自动备份。

本文件锁定这四条不变量：
1. 正常读写往返正确（含中文）
2. 写入失败时原文件内容必须保持不变（原子性）
3. 读到损坏 JSON 时返回默认值并留下 .corrupt.* 备份，而不是静默清空
4. 多线程并发写同一文件后，文件仍是某个写入者的完整内容（不交错、不损坏）
"""

import json
import os
import threading

import storage


def test_save_json_roundtrip(tmp_path):
    path = str(tmp_path / "a.json")
    payload = {"x": 1, "中文键": ["值1", "值2"]}
    assert storage.save_json(path, payload) is True
    assert storage.load_json(path) == payload


def test_load_json_missing_returns_default(tmp_path):
    path = str(tmp_path / "missing.json")
    assert storage.load_json(path) == []
    assert storage.load_json(path, default={"k": 1}) == {"k": 1}


def test_save_json_failure_keeps_original(tmp_path):
    """写入不可序列化对象必须失败，且原文件内容原封不动。"""
    path = str(tmp_path / "b.json")
    assert storage.save_json(path, {"k": "old"}) is True

    # set 无法被 json 序列化，必然抛错
    assert storage.save_json(path, {"k": {"bad"}}) is False

    # 原文件未被破坏
    assert storage.load_json(path) == {"k": "old"}

    # 不留临时文件
    leftovers = [f for f in os.listdir(tmp_path) if f.endswith(".tmp")]
    assert leftovers == []


def test_load_json_corrupt_backs_up_and_returns_default(tmp_path):
    path = str(tmp_path / "c.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"broken": ')  # 故意写半截 JSON

    result = storage.load_json(path, default={"d": 1})
    assert result == {"d": 1}

    # 损坏文件应被改名备份，避免被后续 save 覆盖后无处追查
    backups = [f for f in os.listdir(tmp_path) if f.startswith("c.json.corrupt.")]
    assert len(backups) == 1
    assert not os.path.exists(path)


def test_save_json_concurrent_writes_stay_valid(tmp_path):
    """并发写同一文件：最终内容应是某一次写入的完整结果，不能交错损坏。"""
    path = str(tmp_path / "d.json")
    assert storage.save_json(path, []) is True

    errors = []

    def worker(i: int):
        try:
            storage.save_json(path, [{"writer": i, "seq": s} for s in range(50)])
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    data = storage.load_json(path)
    assert isinstance(data, list)
    assert len(data) == 50
    # 所有条目必须来自同一个写入者（否则说明发生了交错）
    writer_ids = {row["writer"] for row in data}
    assert len(writer_ids) == 1


def test_save_load_real_model_roundtrip(tmp_path, monkeypatch):
    """用真实模型（Character）验证序列化路径，防 pydantic 字段变化导致写入异常。"""
    from models import Character

    path = str(tmp_path / "chars.json")
    chars = [Character(name="测试", age=25, gender="女", occupation="设计师", personality="内向")]
    assert storage.save_json(path, [c.model_dump() for c in chars]) is True

    raw = storage.load_json(path)
    assert raw[0]["name"] == "测试"
    assert raw[0]["age"] == 25
