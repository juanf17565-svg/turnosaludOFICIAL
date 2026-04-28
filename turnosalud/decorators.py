"""Decoradores de autorización por rol y guardia de sesión."""
from functools import wraps
from flask import flash, redirect, request, session, url_for

from .db import query_db


def _role_required(rol_esperado):
    """Devuelve un decorador que exige sesión activa con el rol indicado."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                flash('Debés iniciar sesión para continuar.', 'warning')
                return redirect(url_for('public.login'))
            if session.get('rol') != rol_esperado:
                flash('Acceso no autorizado.', 'danger')
                return redirect(url_for('public.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


paciente_required = _role_required('paciente')
medico_required   = _role_required('medico')
admin_required    = _role_required('admin')


def register_session_guard(app):
    """Cierra la sesión si el usuario fue eliminado o baneado."""
    @app.before_request
    def verificar_sesion():
        if 'user_id' in session:
            user = query_db('SELECT id, baneado FROM usuarios WHERE id = %s',
                            [session['user_id']], one=True)
            if not user:
                session.clear()
            elif user.get('baneado') and request.endpoint != 'public.logout':
                session.clear()
                flash('Tu cuenta fue suspendida.', 'danger')
