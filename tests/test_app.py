def test_index_redirect(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/apidocs' in response.location

def test_create_app(app):
    assert app.testing
    