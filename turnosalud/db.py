"""Helpers de acceso a MySQL."""
import pymysql
import pymysql.cursors
from .config import Config


def get_db():
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
    )


def query_db(query, args=(), one=False):
    db  = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    rv  = cur.fetchall()
    db.close()
    return (rv[0] if rv else None) if one else rv


def modify_db(query, args=()):
    db  = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    db.close()


def modify_db_id(query, args=()):
    db      = get_db()
    cur     = db.cursor()
    cur.execute(query, args)
    last_id = cur.lastrowid
    db.commit()
    db.close()
    return last_id
