"""Fixtures compartidas para los tests.

Usa una base de datos `turnosalud_test` aislada que se recrea antes de cada
sesión de tests, así nunca tocamos los datos de desarrollo.
"""
import os
import re
import pytest
import pymysql

# IMPORTANTE: setear DB_NAME ANTES de importar el paquete, para que Config
# levante con el nombre de test. Si .env no tiene SECRET_KEY, falla y los tests
# tampoco corren — pero el .env existente lo aporta.
os.environ['DB_NAME'] = 'turnosalud_test'

from turnosalud import create_app           # noqa: E402
from turnosalud.config import Config        # noqa: E402
from turnosalud.schema import init_db       # noqa: E402


def _admin_connection():
    """Conexión a MySQL sin elegir database, para crear/dropear la de test."""
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
    )


@pytest.fixture(scope='session', autouse=True)
def _test_database():
    """Crea la base de datos de test al inicio y la borra al final de la sesión."""
    conn = _admin_connection()
    cur  = conn.cursor()
    cur.execute(f'DROP DATABASE IF EXISTS {Config.DB_NAME}')
    cur.execute(f'CREATE DATABASE {Config.DB_NAME} CHARACTER SET utf8mb4')
    conn.commit()
    conn.close()

    init_db()  # crea schema + seed (Carlos, Ana, Luis, María, Juan, Admin)

    yield

    conn = _admin_connection()
    cur  = conn.cursor()
    cur.execute(f'DROP DATABASE IF EXISTS {Config.DB_NAME}')
    conn.commit()
    conn.close()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return app.test_client()


def _csrf(html: str) -> str:
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert m, 'csrf_token no encontrado en la página'
    return m.group(1)


@pytest.fixture
def login_as(client):
    """Devuelve una función para loguear y dejar la sesión activa en el client."""
    def _login(email: str, password: str):
        r = client.get('/login')
        token = _csrf(r.get_data(as_text=True))
        r = client.post('/login',
                        data={'email': email, 'password': password, 'csrf_token': token},
                        follow_redirects=False)
        assert r.status_code == 302, f'login fallido: {r.status_code}'
        return token
    return _login


@pytest.fixture
def csrf_for(client):
    """Devuelve el token CSRF para una URL GET (útil para forms anidados)."""
    def _token(url: str = '/paciente/turnos') -> str:
        r = client.get(url)
        return _csrf(r.get_data(as_text=True))
    return _token
