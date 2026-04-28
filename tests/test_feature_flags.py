import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_weather_feature_flag(client):
    # Disable weather service
    client.application.config['FEATURE_WEATHER_SERVICE'] = False
    rv = client.post('/recommendation/weather', json={'city': '北京'})
    assert rv.status_code == 503
    j = rv.get_json()
    assert j['success'] is False

def test_wardrobe_recommendation_flag(client, tmp_path):
    client.application.config['FEATURE_WARDROBE_RECOMMENDATION'] = False
    # Prepare a fake image path
    img = tmp_path / "x.jpg"
    img.write_bytes(b"\xFF\xD8\xFF")
    rv = client.post('/recommendation/ai_recommend', json={'local_path': str(img), 'city': '北京', 'include_wardrobe': True})
    assert rv.status_code in (200, 400, 404)
    # When disabled, response should not include used_wardrobe flag
    if rv.status_code == 200:
        j = rv.get_json()
        assert 'used_wardrobe' not in j

