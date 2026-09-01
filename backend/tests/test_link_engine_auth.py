from app import create_app


def _client(token: str | None):
    app = create_app()
    app.config.update(
        TESTING=False,
        LINK_ENGINE_API_TOKEN=token,
        LLM_API_KEY='test-llm-key',
        ZEP_API_KEY='test-zep-key',
    )
    return app.test_client()


def test_health_is_public_and_reports_configuration():
    client = _client('secret-token')
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json == {
        'status': 'ok',
        'service': 'MIROFISH-LINK-ENGINE',
        'api_auth': 'configured',
        'llm': 'configured',
        'zep': 'configured',
    }


def test_api_fails_closed_when_auth_is_not_configured():
    client = _client(None)
    response = client.get('/api/graph/project/list')

    assert response.status_code == 503
    assert response.json['error'] == 'api_auth_not_configured'


def test_api_rejects_missing_or_wrong_token():
    client = _client('secret-token')

    missing = client.get('/api/graph/project/list')
    wrong = client.get(
        '/api/graph/project/list',
        headers={'Authorization': 'Bearer wrong-token'},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert missing.json['error'] == 'unauthorized'
    assert wrong.json['error'] == 'unauthorized'


def test_api_accepts_bearer_token():
    client = _client('secret-token')
    response = client.get(
        '/api/graph/project/list',
        headers={'Authorization': 'Bearer secret-token'},
    )

    assert response.status_code == 200
    assert response.json['success'] is True


def test_api_accepts_internal_header_token():
    client = _client('secret-token')
    response = client.get(
        '/api/graph/project/list',
        headers={'X-Link-Engine-Token': 'secret-token'},
    )

    assert response.status_code == 200
    assert response.json['success'] is True
