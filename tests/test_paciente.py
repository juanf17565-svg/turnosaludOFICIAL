"""Reservar y cancelar turnos."""
from turnosalud.db import query_db, modify_db


def _algun_turno_disponible():
    return query_db("SELECT id FROM turnos WHERE estado = 'disponible' LIMIT 1", one=True)


def test_paciente_reserva_y_aparece_en_mis_turnos(client, login_as, csrf_for):
    login_as('juan@email.com', 'paciente123')
    turno = _algun_turno_disponible()
    assert turno, 'el seed debe haber creado turnos'

    token = csrf_for('/paciente/turnos')
    r = client.post(f'/paciente/reservar/{turno["id"]}',
                    data={'motivo': 'Dolor de cabeza', 'csrf_token': token},
                    follow_redirects=False)
    assert r.status_code == 302
    assert '/paciente/mis-turnos' in r.headers['Location']

    # El turno quedó ocupado
    estado = query_db('SELECT estado FROM turnos WHERE id = %s', [turno['id']], one=True)
    assert estado['estado'] == 'ocupado'

    # Y aparece en mis-turnos con el motivo
    html = client.get('/paciente/mis-turnos').get_data(as_text=True)
    assert 'Dolor de cabeza' in html


def test_paciente_no_puede_reservar_dos_con_mismo_medico_mismo_dia(client, login_as, csrf_for):
    login_as('juan@email.com', 'paciente123')

    # Tomamos dos turnos del mismo medico el mismo día
    turnos = query_db('''
        SELECT id, medico_id, fecha FROM turnos
        WHERE estado = 'disponible'
        ORDER BY medico_id, fecha, hora_inicio LIMIT 2
    ''')
    assert len(turnos) == 2 and turnos[0]['medico_id'] == turnos[1]['medico_id'] \
        and turnos[0]['fecha'] == turnos[1]['fecha']

    token = csrf_for('/paciente/turnos')
    client.post(f'/paciente/reservar/{turnos[0]["id"]}', data={'csrf_token': token})
    r = client.post(f'/paciente/reservar/{turnos[1]["id"]}',
                    data={'csrf_token': token}, follow_redirects=True)
    assert 'Ya tenés un turno' in r.get_data(as_text=True)
    # Cleanup
    modify_db("UPDATE turnos SET estado='disponible' WHERE id = %s", [turnos[0]['id']])
    modify_db("DELETE FROM reservas WHERE turno_id = %s", [turnos[0]['id']])
