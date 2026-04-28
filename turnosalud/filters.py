"""Filtros y context processors compartidos por todas las vistas."""
from datetime import datetime
from .constants import ESPECIALIDADES, ESPECIALIDADES_COLORES, color_especialidad


def fecha_formato(value):
    """Convierte una fecha en string tipo 'Lunes 5 de enero'."""
    d     = datetime.strptime(str(value), '%Y-%m-%d') if isinstance(value, str) else value
    dias  = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    return f"{dias[d.weekday()]} {d.day} de {meses[d.month - 1]}"


def register_template_helpers(app):
    """Registra el filtro fecha_formato y los globales de plantillas."""
    app.add_template_filter(fecha_formato, name='fecha_formato')

    @app.context_processor
    def inject_globals():
        return {
            'current_year':           datetime.now().year,
            'ESPECIALIDADES':         ESPECIALIDADES,
            'ESPECIALIDADES_COLORES': ESPECIALIDADES_COLORES,
            'color_especialidad':     color_especialidad,
        }
