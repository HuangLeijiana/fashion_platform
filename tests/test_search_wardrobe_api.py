import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_wardrobe_api_flag(client):
    client.application.config['FEATURE_SEARCH_WARDROBE_API'] = False
    rv = client.get('/search/api/wardrobe?q=衬衫')
    assert rv.status_code == 403

def test_wardrobe_api_enabled(client):
    client.application.config['FEATURE_SEARCH_WARDROBE_API'] = True
    rv = client.get('/search/api/wardrobe?q=衬衫')
    assert rv.status_code in (200, 500)
