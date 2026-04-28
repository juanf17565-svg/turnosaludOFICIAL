"""Lógica de negocio reutilizable entre blueprints."""
from flask import session

from .db import query_db, modify_db


def get_medico_id():
    """Devuelve el medico.id correspondiente al usuario logueado, o None."""
    row = query_db('SELECT id FROM medicos WHERE usuario_id = %s',
                   [session['user_id']], one=True)
    return row['id'] if row else None


def registrar_aviso(paciente_id, medico_id, reserva_id, tipo, motivo):
    """Inserta un aviso, recalcula el contador del paciente y banea si llega a 2.

    Retorna el total de avisos del paciente luego de la inserción.
    """
    modify_db('''INSERT INTO avisos (paciente_id, medico_id, reserva_id, tipo, motivo)
                 VALUES (%s, %s, %s, %s, %s)''',
              (paciente_id, medico_id, reserva_id, tipo, motivo))
    total = query_db('SELECT COUNT(*) AS c FROM avisos WHERE paciente_id = %s',
                     [paciente_id], one=True)['c']
    if total >= 2:
        modify_db('UPDATE usuarios SET avisos = %s, baneado = 1 WHERE id = %s',
                  (total, paciente_id))
    else:
        modify_db('UPDATE usuarios SET avisos = %s WHERE id = %s', (total, paciente_id))
    return total
