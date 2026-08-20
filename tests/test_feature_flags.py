import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return app.test_client()


def test_weather_feature_flag(client):
    # Disable weather service
    client.application.config["FEATURE_WEATHER_SERVICE"] = False
    rv = client.post("/recommendation/weather", json={"city": "北京"})
    assert rv.status_code == 503
    j = rv.get_json()
    assert j["success"] is False


def test_wardrobe_recommendation_flag(client, tmp_path):
    client.application.config["FEATURE_WARDROBE_RECOMMENDATION"] = False
    # /recommendation/ai_recommend 需要登录态，先用默认管理员登录（成功为 302 重定向）
    rv_login = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert rv_login.status_code == 302
    # Prepare a fake image path
    img = tmp_path / "x.jpg"
    img.write_bytes(b"\xff\xd8\xff")
    rv = client.post(
        "/recommendation/ai_recommend",
        json={"local_path": str(img), "city": "北京", "include_wardrobe": True},
    )
    assert rv.status_code in (200, 400, 404)
    # When disabled, response should not include used_wardrobe flag
    if rv.status_code == 200:
        j = rv.get_json()
        assert "used_wardrobe" not in j
