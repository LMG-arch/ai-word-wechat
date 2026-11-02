"""数据备份导出功能测试。

覆盖：
- `GET /api/export/summary` 返回数据规模概览
- `GET /api/export/backup` 返回可解压的 zip，含全部 JSON、MANIFEST，以及一致快照的 memory.db
- 响应头正确声明文件数与是否含数据库
"""

import io
import zipfile

from fastapi.testclient import TestClient

import main


def _client():
    return TestClient(main.app)


def test_summary_shape():
    resp = _client().get("/api/export/summary")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data["json_file_count"], int)
    assert data["json_file_count"] >= 1
    assert isinstance(data["json_total_size"], int)
    assert isinstance(data["memory_db_size"], int)
    assert isinstance(data["files"], list)


def test_backup_is_valid_zip():
    resp = _client().get("/api/export/backup")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers["content-disposition"]
    assert ".zip" in resp.headers["content-disposition"]

    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert zf.testzip() is None  # 完整性校验
    names = zf.namelist()
    assert "MANIFEST.txt" in names
    # 至少包含角色数据
    assert any(n.endswith(".json") for n in names)


def test_backup_manifest_content():
    resp = _client().get("/api/export/backup")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    manifest = zf.read("MANIFEST.txt").decode("utf-8")
    assert "数据备份" in manifest
    assert "JSON 文件数" in manifest
    assert "API 密钥" in manifest  # 安全提示必须存在


def test_backup_headers_match_content():
    resp = _client().get("/api/export/backup")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    json_in_zip = [n for n in zf.namelist() if n.endswith(".json")]
    assert int(resp.headers["X-Export-Json-Count"]) == len(json_in_zip)
    db_flag = resp.headers["X-Export-Db-Included"]
    assert db_flag in ("0", "1")
    assert (db_flag == "1") == ("memory.db" in zf.namelist())


def test_summary_matches_backup_json_count():
    client = _client()
    summary = client.get("/api/export/summary").json()["data"]
    backup = client.get("/api/export/backup")
    zf = zipfile.ZipFile(io.BytesIO(backup.content))
    json_in_zip = [n for n in zf.namelist() if n.endswith(".json")]
    assert summary["json_file_count"] == len(json_in_zip)
