"""Login, registro y CSRF."""


def test_index_responde(client):
    r = client.get('/')
    assert r.status_code == 200


def test_login_sin_csrf_falla(client):
    r = client.post('/login', data={'email': 'juan@email.com', 'password': 'paciente123'})
    assert r.status_code == 400


def test_login_credenciales_validas(client, login_as):
    login_as('juan@email.com', 'paciente123')
    r = client.get('/paciente/mis-turnos')
    assert r.status_code == 200


def test_login_credenciales_invalidas(client):
    r = client.get('/login')
    import re
    token = re.search(r'value="([^"]+)"', r.get_data(as_text=True)).group(1)
    r = client.post('/login',
                    data={'email': 'juan@email.com', 'password': 'mal', 'csrf_token': token},
                    follow_redirects=False)
    assert r.status_code == 200  # se queda en la pantalla de login
    assert 'incorrectos' in r.get_data(as_text=True).lower()


def test_logout_limpia_sesion(client, login_as):
    login_as('juan@email.com', 'paciente123')
    client.get('/logout')
    # Sin sesión, /paciente/mis-turnos redirige a /login
    r = client.get('/paciente/mis-turnos', follow_redirects=False)
    assert r.status_code == 302
    assert '/login' in r.headers['Location']
