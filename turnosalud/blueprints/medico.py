"""Rutas del médico: dashboard, perfil, turnos, reservas, reprogramar, avisos."""
from datetime import date, timedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..db import query_db, modify_db
from ..decorators import medico_required
from ..services import get_medico_id, registrar_aviso

bp = Blueprint('medico', __name__)


@bp.route('/dashboard')
@medico_required
def dashboard():
    mid = get_medico_id()
    stats = query_db('''
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN estado = 'disponible' AND fecha >= CURDATE() THEN 1 ELSE 0 END) AS disponibles,
            SUM(CASE WHEN estado = 'ocupado'                           THEN 1 ELSE 0 END) AS ocupados,
            SUM(CASE WHEN estado = 'deshabilitado'                     THEN 1 ELSE 0 END) AS deshabilitados
        FROM turnos WHERE medico_id = %s
    ''', [mid], one=True)

    proximas = query_db('''
        SELECT DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i') AS hora_fin,
               u.nombre, u.apellido, u.email, r.motivo
        FROM reservas r
        JOIN turnos t   ON r.turno_id   = t.id
        JOIN usuarios u ON r.paciente_id = u.id
        WHERE t.medico_id = %s AND t.fecha >= CURDATE() AND r.estado = 'confirmada'
        ORDER BY t.fecha, t.hora_inicio
        LIMIT 6
    ''', [mid])

    return render_template('medico/dashboard.html', stats=stats, proximas=proximas)


@bp.route('/perfil', methods=['GET', 'POST'])
@medico_required
def perfil():
    mid = get_medico_id()
    if request.method == 'POST':
        precio_raw  = request.form.get('precio_consulta', '').strip().replace(',', '.')
        notas       = request.form.get('notas', '').strip() or None
        descripcion = request.form.get('descripcion', '').strip() or None
        try:
            precio = float(precio_raw) if precio_raw else None
            if precio is not None and precio < 0:
                raise ValueError
        except ValueError:
            flash('El precio debe ser un número válido mayor o igual a 0.', 'danger')
            return redirect(url_for('medico.perfil'))

        modify_db('''UPDATE medicos
                     SET precio_consulta = %s, notas = %s, descripcion = %s
                     WHERE id = %s''',
                  (precio, notas, descripcion, mid))
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('medico.perfil'))

    medico = query_db('''
        SELECT m.precio_consulta, m.notas, m.descripcion,
               m.especialidad, m.matricula, u.nombre, u.apellido, u.email
        FROM medicos m JOIN usuarios u ON m.usuario_id = u.id
        WHERE m.id = %s
    ''', [mid], one=True)
    return render_template('medico/perfil.html', medico=medico)


@bp.route('/turnos')
@medico_required
def turnos():
    mid           = get_medico_id()
    filtro_fecha  = request.args.get('fecha', '')
    filtro_estado = request.args.get('estado', '')

    q = '''
        SELECT t.id,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i') AS hora_fin,
               t.estado,
               r.id AS reserva_id, r.motivo,
               u.nombre, u.apellido, u.email
        FROM turnos t
        LEFT JOIN reservas r ON t.id = r.turno_id AND r.estado = 'confirmada'
        LEFT JOIN usuarios u ON r.paciente_id = u.id
        WHERE t.medico_id = %s
    '''
    params = [mid]
    if filtro_fecha:
        q += ' AND t.fecha = %s';   params.append(filtro_fecha)
    if filtro_estado:
        q += ' AND t.estado = %s';  params.append(filtro_estado)
    q += ' ORDER BY t.fecha, t.hora_inicio'

    turnos_list = query_db(q, params)
    return render_template('medico/turnos.html', turnos=turnos_list,
                           filtro_fecha=filtro_fecha, filtro_estado=filtro_estado)


@bp.route('/turnos/agregar', methods=['GET', 'POST'])
@medico_required
def agregar_turno():
    mid      = get_medico_id()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    if request.method == 'POST':
        modo        = request.form.get('modo', 'simple')
        fecha       = request.form.get('fecha', '')
        hora_inicio = request.form.get('hora_inicio', '')
        hora_fin    = request.form.get('hora_fin', '')

        if not all([fecha, hora_inicio, hora_fin]):
            flash('Todos los campos son obligatorios.', 'danger')
            return render_template('medico/agregar_turno.html', tomorrow=tomorrow)

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser anterior a la hora de fin.', 'danger')
            return render_template('medico/agregar_turno.html', tomorrow=tomorrow)

        if modo == 'bloque':
            intervalo    = int(request.form.get('intervalo', 30))
            h, m         = map(int, hora_inicio.split(':'))
            end_h, end_m = map(int, hora_fin.split(':'))
            end_total    = end_h * 60 + end_m
            created      = 0

            while h * 60 + m + intervalo <= end_total:
                s_str   = f"{h:02d}:{m:02d}"
                t_total = h * 60 + m + intervalo
                e_str   = f"{t_total // 60:02d}:{t_total % 60:02d}"
                if not query_db('SELECT id FROM turnos WHERE medico_id=%s AND fecha=%s AND hora_inicio=%s',
                                [mid, fecha, s_str], one=True):
                    modify_db('INSERT INTO turnos (medico_id, fecha, hora_inicio, hora_fin) VALUES (%s,%s,%s,%s)',
                              (mid, fecha, s_str, e_str))
                    created += 1
                h, m = divmod(t_total, 60)

            flash(f'Se crearon {created} turno(s).', 'success')
        else:
            if query_db('SELECT id FROM turnos WHERE medico_id=%s AND fecha=%s AND hora_inicio=%s',
                        [mid, fecha, hora_inicio], one=True):
                flash('Ya existe un turno en esa fecha y horario.', 'warning')
                return render_template('medico/agregar_turno.html', tomorrow=tomorrow)

            modify_db('INSERT INTO turnos (medico_id, fecha, hora_inicio, hora_fin) VALUES (%s,%s,%s,%s)',
                      (mid, fecha, hora_inicio, hora_fin))
            flash('Turno agregado.', 'success')

        return redirect(url_for('medico.turnos'))

    return render_template('medico/agregar_turno.html', tomorrow=tomorrow)


@bp.route('/turnos/<int:turno_id>/toggle', methods=['POST'])
@medico_required
def toggle_turno(turno_id):
    mid   = get_medico_id()
    turno = query_db('SELECT * FROM turnos WHERE id = %s AND medico_id = %s', [turno_id, mid], one=True)

    if not turno:
        flash('Turno no encontrado.', 'danger')
    elif turno['estado'] == 'ocupado':
        flash('No se puede modificar un turno con paciente asignado.', 'warning')
    else:
        nuevo = 'deshabilitado' if turno['estado'] == 'disponible' else 'disponible'
        modify_db('UPDATE turnos SET estado = %s WHERE id = %s', (nuevo, turno_id))
        flash('Turno deshabilitado.' if nuevo == 'deshabilitado' else 'Turno habilitado.', 'info')

    return redirect(url_for('medico.turnos'))


@bp.route('/turnos/<int:turno_id>/eliminar', methods=['POST'])
@medico_required
def eliminar_turno(turno_id):
    mid   = get_medico_id()
    turno = query_db('SELECT * FROM turnos WHERE id = %s AND medico_id = %s', [turno_id, mid], one=True)

    if not turno:
        flash('Turno no encontrado.', 'danger')
    elif turno['estado'] == 'ocupado':
        flash('No podés eliminar un turno con paciente asignado.', 'warning')
    else:
        modify_db('DELETE FROM turnos WHERE id = %s', [turno_id])
        flash('Turno eliminado.', 'info')

    return redirect(url_for('medico.turnos'))


@bp.route('/turnos/<int:turno_id>/editar', methods=['GET', 'POST'])
@medico_required
def editar_turno(turno_id):
    mid   = get_medico_id()
    turno = query_db('''
        SELECT id,
               DATE_FORMAT(fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(hora_fin,    '%%H:%%i') AS hora_fin,
               estado
        FROM turnos WHERE id = %s AND medico_id = %s
    ''', [turno_id, mid], one=True)

    if not turno:
        flash('Turno no encontrado.', 'danger')
        return redirect(url_for('medico.turnos'))

    if turno['estado'] == 'ocupado':
        flash('No se puede editar un turno con paciente asignado.', 'warning')
        return redirect(url_for('medico.turnos'))

    if request.method == 'POST':
        fecha       = request.form.get('fecha', '')
        hora_inicio = request.form.get('hora_inicio', '')
        hora_fin    = request.form.get('hora_fin', '')

        if not all([fecha, hora_inicio, hora_fin]):
            flash('Todos los campos son obligatorios.', 'danger')
        elif hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser anterior a la hora de fin.', 'danger')
        else:
            duplicado = query_db(
                'SELECT id FROM turnos WHERE medico_id=%s AND fecha=%s AND hora_inicio=%s AND id != %s',
                [mid, fecha, hora_inicio, turno_id], one=True
            )
            if duplicado:
                flash('Ya existe otro turno en esa fecha y horario.', 'warning')
            else:
                modify_db(
                    'UPDATE turnos SET fecha=%s, hora_inicio=%s, hora_fin=%s WHERE id=%s',
                    (fecha, hora_inicio, hora_fin, turno_id)
                )
                flash('Turno actualizado.', 'success')
                return redirect(url_for('medico.turnos'))

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return render_template('medico/editar_turno.html', turno=turno, tomorrow=tomorrow)


@bp.route('/reservas')
@medico_required
def reservas():
    mid = get_medico_id()
    reservas_list = query_db('''
        SELECT r.id, r.motivo, r.estado, r.fecha_reserva,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i') AS hora_fin,
               (TIMESTAMP(t.fecha, t.hora_inicio) > NOW()) AS es_futuro,
               u.id AS paciente_id, u.nombre, u.apellido, u.email,
               u.avisos AS paciente_avisos, u.baneado AS paciente_baneado
        FROM reservas r
        JOIN turnos t   ON r.turno_id   = t.id
        JOIN usuarios u ON r.paciente_id = u.id
        WHERE t.medico_id = %s
        ORDER BY t.fecha DESC, t.hora_inicio DESC
    ''', [mid])
    return render_template('medico/reservas.html', reservas=reservas_list)


@bp.route('/reservas/<int:reserva_id>/reprogramar', methods=['GET', 'POST'])
@medico_required
def reprogramar_reserva(reserva_id):
    mid = get_medico_id()
    info = query_db('''
        SELECT r.id AS reserva_id, r.estado AS r_estado,
               t.id AS turno_id,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               TIME_FORMAT(t.hora_fin,    '%%H:%%i') AS hora_fin,
               u.nombre, u.apellido, u.email
        FROM reservas r
        JOIN turnos t   ON r.turno_id   = t.id
        JOIN usuarios u ON r.paciente_id = u.id
        WHERE r.id = %s AND t.medico_id = %s
    ''', [reserva_id, mid], one=True)

    if not info:
        flash('Reserva no encontrada.', 'danger')
        return redirect(url_for('medico.reservas'))

    if info['r_estado'] != 'confirmada':
        flash('Solo se pueden reprogramar reservas confirmadas.', 'warning')
        return redirect(url_for('medico.reservas'))

    if request.method == 'POST':
        fecha       = request.form.get('fecha', '')
        hora_inicio = request.form.get('hora_inicio', '')
        hora_fin    = request.form.get('hora_fin', '')

        if not all([fecha, hora_inicio, hora_fin]):
            flash('Todos los campos son obligatorios.', 'danger')
        elif hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser anterior a la hora de fin.', 'danger')
        else:
            conflicto = query_db(
                'SELECT id FROM turnos WHERE medico_id=%s AND fecha=%s AND hora_inicio=%s AND id != %s',
                [mid, fecha, hora_inicio, info['turno_id']], one=True
            )
            if conflicto:
                flash('Ya tenés otro turno en esa fecha y horario.', 'warning')
            else:
                modify_db(
                    'UPDATE turnos SET fecha=%s, hora_inicio=%s, hora_fin=%s WHERE id=%s',
                    (fecha, hora_inicio, hora_fin, info['turno_id'])
                )
                flash(f'Turno de {info["nombre"]} {info["apellido"]} reprogramado para {fecha} {hora_inicio}.', 'success')
                return redirect(url_for('medico.reservas'))

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    return render_template('medico/reprogramar_reserva.html', info=info, tomorrow=tomorrow)


@bp.route('/reservas/<int:reserva_id>/aviso', methods=['POST'])
@medico_required
def emitir_aviso(reserva_id):
    mid  = get_medico_id()
    tipo = request.form.get('tipo', '')
    if tipo not in ('no_asistio', 'cancelacion_tardia'):
        flash('Tipo de aviso inválido.', 'danger')
        return redirect(url_for('medico.reservas'))

    reserva = query_db('''
        SELECT r.id, r.paciente_id, r.estado
        FROM reservas r JOIN turnos t ON r.turno_id = t.id
        WHERE r.id = %s AND t.medico_id = %s
    ''', [reserva_id, mid], one=True)

    if not reserva:
        flash('Reserva no encontrada.', 'danger')
        return redirect(url_for('medico.reservas'))

    if reserva['estado'] != 'confirmada':
        flash('La reserva ya fue marcada o cancelada.', 'warning')
        return redirect(url_for('medico.reservas'))

    motivo = request.form.get('motivo', '').strip() or None
    modify_db('UPDATE reservas SET estado = %s WHERE id = %s', (tipo, reserva_id))
    total = registrar_aviso(reserva['paciente_id'], mid, reserva_id, tipo, motivo)

    if total >= 2:
        flash(f'Aviso registrado. El paciente acumuló {total} avisos y fue baneado automáticamente.', 'warning')
    else:
        flash(f'Aviso registrado. El paciente lleva {total} aviso(s) de 2.', 'info')
    return redirect(url_for('medico.reservas'))
