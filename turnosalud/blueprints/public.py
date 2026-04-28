"""Rutas públicas: landing, login, registro, logout."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..db import query_db, modify_db_id

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    medicos = query_db('''
        SELECT u.id, u.nombre, u.apellido,
               m.id AS medico_id, m.especialidad, m.descripcion,
               COUNT(CASE WHEN t.estado = 'disponible'
                           AND TIMESTAMP(t.fecha, t.hora_inicio) > NOW()
                          THEN 1 END) AS disponibles
        FROM usuarios u
        JOIN medicos m  ON u.id = m.usuario_id
        LEFT JOIN turnos t ON m.id = t.medico_id
        GROUP BY u.id, m.id
        ORDER BY m.especialidad
    ''')
    return render_template('index.html', medicos=medicos)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user     = query_db('SELECT * FROM usuarios WHERE email = %s', [email], one=True)

        if user and check_password_hash(user['password'], password):
            if user.get('baneado'):
                flash('Tu cuenta fue suspendida por incumplimientos repetidos. Contactá al administrador.', 'danger')
                return render_template('auth/login.html')
            session['user_id'] = user['id']
            session['nombre']  = user['nombre']
            session['rol']     = user['rol']
            flash(f'¡Bienvenido/a, {user["nombre"]}!', 'success')
            destinos = {'medico': 'medico.dashboard', 'admin': 'admin.dashboard'}
            return redirect(url_for(destinos.get(user['rol'], 'paciente.turnos')))

        flash('Email o contraseña incorrectos.', 'danger')

    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('public.index'))

    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not all([nombre, apellido, email, password]):
            flash('Todos los campos son obligatorios.', 'danger')
        elif password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
        elif len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
        elif query_db('SELECT id FROM usuarios WHERE email = %s', [email], one=True):
            flash('Ya existe una cuenta con ese email.', 'danger')
        else:
            uid = modify_db_id(
                'INSERT INTO usuarios (nombre, apellido, email, password, rol) VALUES (%s,%s,%s,%s,%s)',
                (nombre, apellido, email, generate_password_hash(password), 'paciente')
            )
            session['user_id'] = uid
            session['nombre']  = nombre
            session['rol']     = 'paciente'
            flash('¡Cuenta creada exitosamente!', 'success')
            return redirect(url_for('paciente.turnos'))

    return render_template('auth/register.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada.', 'info')
    return redirect(url_for('public.index'))
