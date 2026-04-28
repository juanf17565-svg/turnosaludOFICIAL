"""Rutas del administrador: dashboard, médicos, pacientes, ban/unban/delete."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from ..db import query_db, modify_db, modify_db_id
from ..decorators import admin_required
from ..services import registrar_aviso

bp = Blueprint('admin', __name__)


@bp.route('/dashboard')
@admin_required
def dashboard():
    stats = query_db('''
        SELECT
            (SELECT COUNT(*) FROM medicos)                                            AS total_medicos,
            (SELECT COUNT(*) FROM usuarios WHERE rol = 'paciente')                   AS total_pacientes,
            (SELECT COUNT(*) FROM turnos WHERE fecha >= CURDATE())                   AS turnos_proximos,
            (SELECT COUNT(*) FROM reservas WHERE estado = 'confirmada')              AS reservas_activas,
            (SELECT COUNT(*) FROM reservas r
             JOIN turnos t ON r.turno_id = t.id
             WHERE t.fecha = CURDATE() AND r.estado = 'confirmada')                  AS reservas_hoy
    ''', one=True)

    recientes = query_db('''
        SELECT r.fecha_reserva, r.estado,
               DATE_FORMAT(t.fecha, '%%Y-%%m-%%d')   AS fecha,
               TIME_FORMAT(t.hora_inicio, '%%H:%%i') AS hora_inicio,
               up.nombre AS p_nombre, up.apellido AS p_apellido,
               um.nombre AS m_nombre, um.apellido AS m_apellido,
               m.especialidad
        FROM reservas r
        JOIN turnos t   ON r.turno_id    = t.id
        JOIN medicos m  ON t.medico_id   = m.id
        JOIN usuarios um ON m.usuario_id = um.id
        JOIN usuarios up ON r.paciente_id = up.id
        ORDER BY r.fecha_reserva DESC
        LIMIT 8
    ''')
    return render_template('admin/dashboard.html', stats=stats, recientes=recientes)


@bp.route('/medicos')
@admin_required
def medicos():
    medicos_list = query_db('''
        SELECT u.id, u.nombre, u.apellido, u.email,
               DATE_FORMAT(u.created_at, '%%Y-%%m-%%d') AS created_at,
               m.id AS medico_id, m.especialidad, m.matricula,
               COUNT(CASE WHEN t.estado = 'disponible' AND t.fecha >= CURDATE() THEN 1 END) AS disponibles,
               COUNT(CASE WHEN t.estado = 'ocupado'                              THEN 1 END) AS ocupados
        FROM usuarios u
        JOIN medicos m  ON u.id = m.usuario_id
        LEFT JOIN turnos t ON m.id = t.medico_id
        GROUP BY u.id, m.id
        ORDER BY u.apellido
    ''')
    return render_template('admin/medicos.html', medicos=medicos_list)


@bp.route('/medicos/crear', methods=['GET', 'POST'])
@admin_required
def crear_medico():
    if request.method == 'POST':
        nombre       = request.form.get('nombre', '').strip()
        apellido     = request.form.get('apellido', '').strip()
        email        = request.form.get('email', '').strip()
        password     = request.form.get('password', '')
        especialidad = request.form.get('especialidad', '').strip()
        matricula    = request.form.get('matricula', '').strip()
        descripcion  = request.form.get('descripcion', '').strip()

        if not all([nombre, apellido, email, password, especialidad]):
            flash('Nombre, apellido, email, contraseña y especialidad son obligatorios.', 'danger')
        elif query_db('SELECT id FROM usuarios WHERE email = %s', [email], one=True):
            flash('Ya existe un usuario con ese email.', 'danger')
        else:
            uid = modify_db_id(
                'INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
                (nombre, apellido, email, generate_password_hash(password), 'medico')
            )
            modify_db(
                'INSERT INTO medicos (usuario_id, especialidad, matricula, descripcion) VALUES (%s,%s,%s,%s)',
                (uid, especialidad, matricula or None, descripcion or None)
            )
            flash(f'Cuenta creada para Dr/a. {nombre} {apellido}.', 'success')
            return redirect(url_for('admin.medicos'))

    return render_template('admin/crear_medico.html')


@bp.route('/medicos/<int:medico_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_medico(medico_id):
    tiene_futuras = query_db('''
        SELECT r.id FROM reservas r
        JOIN turnos t ON r.turno_id = t.id
        WHERE t.medico_id = %s AND t.fecha >= CURDATE() AND r.estado = 'confirmada'
        LIMIT 1
    ''', [medico_id], one=True)

    if tiene_futuras:
        flash('No se puede eliminar: el médico tiene turnos reservados próximos.', 'danger')
        return redirect(url_for('admin.medicos'))

    medico = query_db('SELECT usuario_id FROM medicos WHERE id = %s', [medico_id], one=True)
    if not medico:
        flash('Médico no encontrado.', 'danger')
        return redirect(url_for('admin.medicos'))

    modify_db('DELETE r FROM reservas r JOIN turnos t ON r.turno_id = t.id WHERE t.medico_id = %s', [medico_id])
    modify_db('DELETE FROM turnos WHERE medico_id = %s', [medico_id])
    modify_db('DELETE FROM medicos WHERE id = %s', [medico_id])
    modify_db('DELETE FROM usuarios WHERE id = %s', [medico['usuario_id']])
    flash('Médico eliminado.', 'info')
    return redirect(url_for('admin.medicos'))


@bp.route('/pacientes')
@admin_required
def pacientes():
    pacientes_list = query_db('''
        SELECT u.id, u.nombre, u.apellido, u.email, u.avisos, u.baneado,
               DATE_FORMAT(u.created_at, '%%Y-%%m-%%d') AS created_at,
               COUNT(r.id)                                              AS total_reservas,
               SUM(CASE WHEN r.estado = 'confirmada' THEN 1 ELSE 0 END) AS reservas_activas
        FROM usuarios u
        LEFT JOIN reservas r ON u.id = r.paciente_id
        WHERE u.rol = 'paciente'
        GROUP BY u.id
        ORDER BY u.baneado DESC, u.avisos DESC, u.apellido
    ''')
    return render_template('admin/pacientes.html', pacientes=pacientes_list)


@bp.route('/pacientes/<int:paciente_id>/banear', methods=['POST'])
@admin_required
def banear_paciente(paciente_id):
    paciente = query_db("SELECT id, nombre, apellido FROM usuarios WHERE id = %s AND rol = 'paciente'",
                        [paciente_id], one=True)
    if not paciente:
        flash('Paciente no encontrado.', 'danger')
        return redirect(url_for('admin.pacientes'))

    motivo = request.form.get('motivo', '').strip() or 'Baneo manual por administrador'
    modify_db('UPDATE usuarios SET baneado = 1 WHERE id = %s', [paciente_id])
    registrar_aviso(paciente_id, None, None, 'baneo_admin', motivo)
    flash(f'{paciente["nombre"]} {paciente["apellido"]} fue baneado/a.', 'warning')
    return redirect(url_for('admin.pacientes'))


@bp.route('/pacientes/<int:paciente_id>/desbanear', methods=['POST'])
@admin_required
def desbanear_paciente(paciente_id):
    paciente = query_db("SELECT id, nombre, apellido FROM usuarios WHERE id = %s AND rol = 'paciente'",
                        [paciente_id], one=True)
    if not paciente:
        flash('Paciente no encontrado.', 'danger')
        return redirect(url_for('admin.pacientes'))

    modify_db('UPDATE usuarios SET baneado = 0, avisos = 0 WHERE id = %s', [paciente_id])
    modify_db('DELETE FROM avisos WHERE paciente_id = %s', [paciente_id])
    flash(f'{paciente["nombre"]} {paciente["apellido"]} fue desbaneado/a y sus avisos reiniciados.', 'success')
    return redirect(url_for('admin.pacientes'))


@bp.route('/pacientes/<int:paciente_id>/eliminar', methods=['POST'])
@admin_required
def eliminar_paciente(paciente_id):
    paciente = query_db("SELECT id, nombre, apellido FROM usuarios WHERE id = %s AND rol = 'paciente'",
                        [paciente_id], one=True)
    if not paciente:
        flash('Paciente no encontrado.', 'danger')
        return redirect(url_for('admin.pacientes'))

    modify_db('''UPDATE turnos t
                 JOIN reservas r ON r.turno_id = t.id
                 SET t.estado = 'disponible'
                 WHERE r.paciente_id = %s AND t.fecha >= CURDATE() AND r.estado = 'confirmada' ''',
              [paciente_id])
    modify_db('DELETE FROM avisos   WHERE paciente_id = %s', [paciente_id])
    modify_db('DELETE FROM reservas WHERE paciente_id = %s', [paciente_id])
    modify_db('DELETE FROM usuarios WHERE id = %s',          [paciente_id])
    flash(f'{paciente["nombre"]} {paciente["apellido"]} fue eliminado/a del sistema.', 'info')
    return redirect(url_for('admin.pacientes'))
