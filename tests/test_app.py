def test_index_redirect(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/apidocs' in response.location

def test_apidocs_redirect(client):
    response = client.get('/apidocs/')
    assert response.status_code == 302
    assert '/apidocs' in response.location

def test_create_app(app):
    assert app.testing
    
def test_swagger_config(app):
    assert app.config.get('SWAGGER')
    assert '/apidocs' in app.url_map.iter_rules()