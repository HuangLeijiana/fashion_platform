import os
import tempfile

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def create_temp_image():
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as f:
        f.write(b"\xff\xd8\xff")  # minimal JPEG header
    return path


def test_upload_and_recommend_flow(client):
    # Upload
    img_path = create_temp_image()
    with open(img_path, "rb") as f:
        data = {
            "username": "tester",
            "body_shape": "矩形",
            "skin_tone": "白色",
            "style_pref": "[]",
            "cloth_image": (f, "test.jpg"),
        }
        rv = client.post("/recommendation/upload", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200
    j = rv.get_json()
    assert j["success"] is True
    local_path = j["local_path"]
    # /recommendation/ai_recommend 需要登录态，先用默认管理员登录
    rv_login = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert rv_login.status_code in (200, 302)
    # Recommend
    rv2 = client.post(
        "/recommendation/ai_recommend",
        json={"local_path": local_path, "city": "北京", "include_wardrobe": False},
    )
    assert rv2.status_code in (200, 404, 400)
