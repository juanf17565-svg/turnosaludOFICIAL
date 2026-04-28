"""Rutas del paciente: buscar turnos, reservar, ver propios, cancelar."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import query_db, modify_db
from ..decorators import paciente_required

bp = Blueprint('paciente', __name__)


@bp.route('/turnos')
@paciente_required
def turnos():
    especialidad = request.args.get('especialidad', '')
    medico_id    = request.args.get('medico_id', '')
    fecha        = request.args.get('fecha', '')
    hora_desde   = request.args.get('hora_desde', '')
    hora_hasta   = request.args.get('hora_hasta', '')

    q = '''
        SELECT t.id,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d') AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i') AS hora_fin,
               t.estado,
               u.nombre, u.apellido, m.id AS medico_id, m.especialidad,
               m.precio_consulta, m.notas,
               (SELECT COUNT(*) FROM turnos t2
                WHERE t2.medico_id = m.id AND t2.fecha = t.fecha
                  AND t2.estado = 'ocupado') AS ocupados_dia,
               (SELECT COUNT(*) FROM turnos t2
                WHERE t2.medico_id = m.id AND t2.fecha = t.fecha
                  AND t2.estado <> 'deshabilitado') AS total_dia
        FROM turnos t
        JOIN medicos m  ON t.medico_id  = m.id
        JOIN usuarios u ON m.usuario_id = u.id
        WHERE TIMESTAMP(t.fecha, t.hora_inicio) > NOW()
          AND t.estado = 'disponible'
    '''
    params = []
    if especialidad:
        q += ' AND m.especialidad = %s'; params.append(especialidad)
    if medico_id:
        q += ' AND m.id = %s';           params.append(medico_id)
    if fecha:
        q += ' AND t.fecha = %s';        params.append(fecha)
    if hora_desde:
        q += ' AND t.hora_inicio >= %s'; params.append(hora_desde)
    if hora_hasta:
        q += ' AND t.hora_inicio <= %s'; params.append(hora_hasta)
    q += ' ORDER BY m.especialidad, u.apellido, u.nombre, t.fecha, t.hora_inicio'

    turnos_list    = query_db(q, params)
    especialidades = query_db('SELECT DISTINCT especialidad FROM medicos ORDER BY especialidad')
    medicos = query_db('''
        SELECT m.id, u.nombre, u.apellido, m.especialidad
        FROM medicos m JOIN usuarios u ON m.usuario_id = u.id
        ORDER BY u.apellido
    ''')

    return render_template('paciente/turnos.html',
                           turnos=turnos_list, especialidades=especialidades, medicos=medicos,
                           filtro_especialidad=especialidad,
                           filtro_medico=medico_id,
                           filtro_fecha=fecha,
                           filtro_hora_desde=hora_desde,
                           filtro_hora_hasta=hora_hasta)


@bp.route('/reservar/<int:turno_id>', methods=['POST'])
@paciente_required
def reservar(turno_id):
    motivo = request.form.get('motivo', '').strip()
    turno  = query_db('SELECT * FROM turnos WHERE id = %s', [turno_id], one=True)

    if not turno or turno['estado'] != 'disponible':
        flash('Este turno ya no está disponible.', 'warning')
        return redirect(url_for('paciente.turnos'))

    ya_tiene = query_db('''
        SELECT r.id FROM reservas r
        JOIN turnos t ON r.turno_id = t.id
        WHERE r.paciente_id = %s AND t.fecha = %s AND t.medico_id = %s AND r.estado = 'confirmada'
    ''', [session['user_id'], turno['fecha'], turno['medico_id']], one=True)

    if ya_tiene:
        flash('Ya tenés un turno con este médico ese día.', 'warning')
        return redirect(url_for('paciente.turnos'))

    try:
        modify_db('UPDATE turnos SET estado = %s WHERE id = %s', ('ocupado', turno_id))
        modify_db('INSERT INTO reservas (turno_id, paciente_id, motivo) VALUES (%s,%s,%s)',
                  (turno_id, session['user_id'], motivo))
    except Exception:
        modify_db('UPDATE turnos SET estado = %s WHERE id = %s', ('disponible', turno_id))
        session.clear()
        flash('Sesión expirada. Iniciá sesión nuevamente.', 'warning')
        return redirect(url_for('public.login'))

    flash('¡Turno reservado exitosamente!', 'success')
    return redirect(url_for('paciente.mis_turnos'))


@bp.route('/mis-turnos')
@paciente_required
def mis_turnos():
    reservas = query_db('''
        SELECT r.id, r.motivo, r.estado, r.fecha_reserva,
               t.id AS turno_id,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')    AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i')  AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i')  AS hora_fin,
               u.nombre, u.apellido, m.especialidad
        FROM reservas r
        JOIN turnos t   ON r.turno_id   = t.id
        JOIN medicos m  ON t.medico_id  = m.id
        JOIN usuarios u ON m.usuario_id = u.id
        WHERE r.paciente_id = %s
        ORDER BY t.fecha DESC, t.hora_inicio DESC
    ''', [session['user_id']])
    return render_template('paciente/mis_turnos.html', reservas=reservas)


@bp.route('/cancelar/<int:reserva_id>', methods=['POST'])
@paciente_required
def cancelar(reserva_id):
    reserva = query_db('''
        SELECT r.*, t.id AS turno_id FROM reservas r JOIN turnos t ON r.turno_id = t.id
        WHERE r.id = %s AND r.paciente_id = %s
    ''', [reserva_id, session['user_id']], one=True)

    if not reserva or reserva['estado'] != 'confirmada':
        flash('Reserva no encontrada o ya cancelada.', 'warning')
        return redirect(url_for('paciente.mis_turnos'))

    modify_db('UPDATE reservas SET estado = %s WHERE id = %s', ('cancelada', reserva_id))
    modify_db('UPDATE turnos SET estado = %s WHERE id = %s', ('disponible', reserva['turno_id']))
    flash('Turno cancelado.', 'info')
    return redirect(url_for('paciente.mis_turnos'))
