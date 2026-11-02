"""AIWeChat 上传路由：聊天图片等二进制文件上传。

与前端 index.html 的 `uploadChatImageFile` 契约保持一致：
POST /api/uploads/chat-image  (multipart/form-data, 字段名 file)
返回: { "success": true, "data": { "url": "/uploads/chat-image/<filename>" } }
文件由 main.py 中挂载的 /uploads 静态目录对外提供访问。
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime

import aiofiles
from fastapi import APIRouter, File, HTTPException, UploadFile

from config import UPLOADS_DIR

router = APIRouter()

CHAT_IMAGE_SUBDIR = os.path.join(UPLOADS_DIR, "chat-image")
os.makedirs(CHAT_IMAGE_SUBDIR, exist_ok=True)

# 允许的图片扩展名与其扩展名正规化映射
_ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 单张图片上限 5MB


def _safe_ext(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    return ext


@router.post("/api/uploads/chat-image")
async def upload_chat_image(file: UploadFile = File(...)):
    """接收聊天图片并以随机文件名落盘，返回可直接访问的相对 URL。"""
    if file is None or not file.filename:
        raise HTTPException(status_code=400, detail="未收到文件")

    ext = _safe_ext(file.filename)
    if ext not in _ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式：{ext or '未知'}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件为空")
    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="图片过大（上限 5MB）")

    fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(CHAT_IMAGE_SUBDIR, fname)
    async with aiofiles.open(dest, "wb") as fh:
        await fh.write(content)

    return {"success": True, "data": {"url": f"/uploads/chat-image/{fname}"}}
