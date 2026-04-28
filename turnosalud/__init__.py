"""App factory para TurnoSalud."""
from flask import Flask
from flask_wtf.csrf import CSRFProtect

from .config import Config
from .decorators import register_session_guard
from .filters import register_template_helpers
from .blueprints.public   import bp as public_bp
from .blueprints.paciente import bp as paciente_bp
from .blueprints.medico   import bp as medico_bp
from .blueprints.admin    import bp as admin_bp

csrf = CSRFProtect()


def create_app(config: Config | None = None) -> Flask:
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')
    app.config.from_object(config or Config)
    app.secret_key = app.config['SECRET_KEY']

    csrf.init_app(app)
    register_template_helpers(app)
    register_session_guard(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(paciente_bp, url_prefix='/paciente')
    app.register_blueprint(medico_bp,   url_prefix='/medico')
    app.register_blueprint(admin_bp,    url_prefix='/admin')

    return app
