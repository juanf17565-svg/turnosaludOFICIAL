"""Configuración cargada desde variables de entorno."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError(
            'Falta FLASK_SECRET_KEY. Copiá .env.example a .env y completalo, '
            'o exportá la variable antes de arrancar.'
        )

    DB_HOST     = os.environ.get('DB_HOST',     'localhost')
    DB_USER     = os.environ.get('DB_USER',     'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME     = os.environ.get('DB_NAME',     'turnosalud')
