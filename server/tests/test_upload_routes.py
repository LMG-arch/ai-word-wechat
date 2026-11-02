"""V3.8 回归测试：聊天图片上传端点 /api/uploads/chat-image 及其静态访问。

该端点修复了此前「前端调用但后端缺失」的断链（上传图片功能 404）。
"""

import glob
import os

import pytest
from fastapi.testclient import TestClient

import main
from config import UPLOADS_DIR

# 1x1 PNG
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c63600000020001e221bc33000000"
    "0049454e44ae426082"
)


@pytest.fixture
def client():
    return TestClient(main.app)


def _cleanup_uploads():
    for f in glob.glob(os.path.join(UPLOADS_DIR, "chat-image", "*")):
        try:
            os.remove(f)
        except OSError:
            pass


def test_upload_and_served(client):
    _cleanup_uploads()
    r = client.post("/api/uploads/chat-image", files={"file": ("a.png", PNG, "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    url = body["data"]["url"]
    assert url.startswith("/uploads/chat-image/")

    served = client.get(url)
    assert served.status_code == 200
    assert served.content == PNG
    _cleanup_uploads()


def test_reject_bad_extension(client):
    r = client.post("/api/uploads/chat-image", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_reject_empty_file(client):
    r = client.post("/api/uploads/chat-image", files={"file": ("a.png", b"", "image/png")})
    assert r.status_code == 400
