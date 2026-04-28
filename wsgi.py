"""Entry point para servidores WSGI de producción (waitress, gunicorn).

Ejemplos:
  waitress-serve --port=8000 wsgi:app
  gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
"""
from turnosalud import create_app

app = create_app()
