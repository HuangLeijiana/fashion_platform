import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()

def test_track_event_enabled(client):
    client.application.config['FEATURE_ANALYTICS_EVENTS'] = True
    rv = client.post('/analytics/track', json={'event': 'unit_test', 'payload': {'ok': True}})
    assert rv.status_code == 200
    assert rv.get_json()['success'] is True

def test_track_event_disabled(client):
    client.application.config['FEATURE_ANALYTICS_EVENTS'] = False
    rv = client.post('/analytics/track', json={'event': 'unit_test'})
    assert rv.status_code == 403
