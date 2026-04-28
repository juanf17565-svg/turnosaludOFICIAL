"""Punto de entrada del servidor de desarrollo.

Para producción usar `wsgi.py` con un servidor WSGI real (waitress / gunicorn).
"""
from turnosalud import create_app
from turnosalud.schema import init_db

app = create_app()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
