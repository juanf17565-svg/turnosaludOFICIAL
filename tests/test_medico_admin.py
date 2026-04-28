"""Avisos del médico (auto-baneo a los 2) y acciones del admin."""
from turnosalud.db import query_db, modify_db, modify_db_id


def _crear_paciente_con_dos_reservas_medico_carlos():
    """Crea un paciente nuevo con dos reservas confirmadas con el médico Carlos."""
    from werkzeug.security import generate_password_hash
    pid = modify_db_id(
        'INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
        ('Test', 'Aviso', 'aviso@test.com', generate_password_hash('x'), 'paciente')
    )
    # Carlos es el primer médico del seed, medico_id=1
    turnos = query_db("SELECT id FROM turnos WHERE medico_id = 1 AND estado = 'disponible' LIMIT 2")
    reserva_ids = []
    for t in turnos:
        modify_db("UPDATE turnos SET estado = 'ocupado' WHERE id = %s", [t['id']])
        rid = modify_db_id(
            'INSERT INTO reservas (turno_id, paciente_id, motivo) VALUES (%s,%s,%s)',
            (t['id'], pid, 'test')
        )
        reserva_ids.append(rid)
    return pid, reserva_ids


def test_dos_avisos_banean_al_paciente(client, login_as, csrf_for):
    pid, reservas = _crear_paciente_con_dos_reservas_medico_carlos()
    login_as('carlos@turnosalud.com', 'medico123')
    token = csrf_for('/medico/reservas')

    # Aviso 1: solo aumenta contador
    client.post(f'/medico/reservas/{reservas[0]}/aviso',
                data={'tipo': 'no_asistio', 'csrf_token': token})
    estado = query_db('SELECT avisos, baneado FROM usuarios WHERE id = %s', [pid], one=True)
    assert estado['avisos'] == 1 and estado['baneado'] == 0

    # Aviso 2: dispara baneo automático
    client.post(f'/medico/reservas/{reservas[1]}/aviso',
                data={'tipo': 'cancelacion_tardia', 'csrf_token': token})
    estado = query_db('SELECT avisos, baneado FROM usuarios WHERE id = %s', [pid], one=True)
    assert estado['avisos'] == 2 and estado['baneado'] == 1


def test_paciente_baneado_no_puede_loguearse(client):
    # El test anterior dejó al paciente baneado@test.com baneado.
    pid = query_db("SELECT id FROM usuarios WHERE email = 'aviso@test.com'", one=True)['id']
    modify_db('UPDATE usuarios SET baneado = 1 WHERE id = %s', [pid])

    r = client.get('/login')
    import re
    token = re.search(r'value="([^"]+)"', r.get_data(as_text=True)).group(1)
    r = client.post('/login',
                    data={'email': 'aviso@test.com', 'password': 'x', 'csrf_token': token},
                    follow_redirects=False)
    assert r.status_code == 200
    assert 'suspend' in r.get_data(as_text=True).lower()


def test_admin_desbanear_resetea_avisos_y_baneo(client, login_as, csrf_for):
    pid = query_db("SELECT id FROM usuarios WHERE email = 'aviso@test.com'", one=True)['id']
    login_as('admin@turnosalud.com', 'admin123')
    token = csrf_for('/admin/pacientes')

    r = client.post(f'/admin/pacientes/{pid}/desbanear',
                    data={'csrf_token': token}, follow_redirects=False)
    assert r.status_code == 302

    estado = query_db('SELECT avisos, baneado FROM usuarios WHERE id = %s', [pid], one=True)
    assert estado['avisos'] == 0 and estado['baneado'] == 0
    avisos = query_db('SELECT COUNT(*) AS c FROM avisos WHERE paciente_id = %s', [pid], one=True)
    assert avisos['c'] == 0


def test_admin_eliminar_paciente_libera_turnos_futuros(client, login_as, csrf_for):
    from werkzeug.security import generate_password_hash
    from datetime import date, timedelta

    # Paciente nuevo con una reserva FUTURA
    pid = modify_db_id(
        'INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
        ('Borr', 'ame', 'borrame@test.com', generate_password_hash('x'), 'paciente')
    )
    futuro = (date.today() + timedelta(days=30)).isoformat()
    tid = modify_db_id(
        'INSERT INTO turnos (medico_id, fecha, hora_inicio, hora_fin, estado) VALUES (1,%s,%s,%s,%s)',
        (futuro, '10:00', '10:30', 'ocupado')
    )
    modify_db('INSERT INTO reservas (turno_id, paciente_id, motivo) VALUES (%s,%s,%s)',
              (tid, pid, 'test'))

    login_as('admin@turnosalud.com', 'admin123')
    token = csrf_for('/admin/pacientes')
    client.post(f'/admin/pacientes/{pid}/eliminar',
                data={'csrf_token': token})

    # El paciente desaparece
    assert query_db('SELECT id FROM usuarios WHERE id = %s', [pid], one=True) is None
    # El turno futuro vuelve a estar disponible
    estado = query_db('SELECT estado FROM turnos WHERE id = %s', [tid], one=True)
    assert estado['estado'] == 'disponible'
