"""数据备份导出路由。

本项目所有业务数据都落在 `data/` 目录下的 JSON 文件与 SQLite（memory.db）里，
此前没有任何备份手段 —— 一次误删或磁盘故障就会永久丢失全部角色 / 消息 / 记忆。

本模块提供 `GET /api/export/backup`：把全部数据打包成一个 zip 下载。
- JSON 文件直接打包；
- memory.db（记忆 / 关系）走 sqlite 官方 backup API，保证在 WAL 模式下也拿到一致快照，
  避免直接复制到写入一半的 .db/.wal 导致备份损坏。

安全提示：备份包含 `api_configs.json`（含密钥），请妥善保管。
"""

from __future__ import annotations

import io
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from config import DATA_DIR, MEMORY_DB_FILE

router = APIRouter()


def _add_memory_db_to_zip(zf: zipfile.ZipFile) -> bool:
    """用 sqlite backup API 生成 memory.db 的一致快照并写入 zip。"""
    if not os.path.exists(MEMORY_DB_FILE):
        return False
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)
    try:
        src = sqlite3.connect(MEMORY_DB_FILE, timeout=10)
        dst = sqlite3.connect(tmp_path)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        zf.write(tmp_path, arcname="memory.db")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[export] memory.db 备份失败：{exc}")
        return False
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@router.get("/api/export/backup")
async def export_backup():
    """打包导出全部数据（JSON + memory.db）为 zip，供用户本地留存。"""
    buf = io.BytesIO()
    json_count = 0
    db_included = False

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(os.listdir(DATA_DIR)):
            path = os.path.join(DATA_DIR, name)
            if os.path.isfile(path) and name.endswith(".json"):
                zf.write(path, arcname=name)
                json_count += 1
        db_included = _add_memory_db_to_zip(zf)

        # 附一份清单，便于用户核对备份内容
        manifest = (
            f"AI Word WeChat 数据备份\n"
            f"导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"JSON 文件数：{json_count}\n"
            f"包含记忆数据库：{'是' if db_included else '否'}\n"
            f"注意：api_configs.json 含 API 密钥，请勿外传。\n"
        )
        zf.writestr("MANIFEST.txt", manifest.encode("utf-8"))

    buf.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"ai-word-backup-{timestamp}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Json-Count": str(json_count),
            "X-Export-Db-Included": "1" if db_included else "0",
        },
    )


@router.get("/api/export/summary")
async def export_summary():
    """返回数据规模概览，供前端在导出前展示（文件数、大小等）。"""
    json_files = []
    total_size = 0
    if os.path.isdir(DATA_DIR):
        for name in sorted(os.listdir(DATA_DIR)):
            path = os.path.join(DATA_DIR, name)
            if os.path.isfile(path) and name.endswith(".json"):
                size = os.path.getsize(path)
                json_files.append({"name": name, "size": size})
                total_size += size
    db_size = os.path.getsize(MEMORY_DB_FILE) if os.path.exists(MEMORY_DB_FILE) else 0

    return {
        "success": True,
        "data": {
            "json_file_count": len(json_files),
            "json_total_size": total_size,
            "memory_db_size": db_size,
            "files": json_files,
        },
    }
