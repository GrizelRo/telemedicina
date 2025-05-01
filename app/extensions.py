from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

# Inicializar extensiones sin vincularlas a la aplicación
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
moment = Moment()
limiter = Limiter(key_func=get_remote_address)
socketio = SocketIO()

# Configuración del LoginManager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario desde la base de datos usando su ID."""
    from app.models.usuario import Usuario
    return Usuario.query.get(int(user_id))

def init_extensions(app):
    """
    Inicializa todas las extensiones con la aplicación Flask.
    
    Args:
        app: Aplicación Flask
    """
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    moment.init_app(app)
    
    # Configurar limitador de tasa de solicitudes
    limiter.init_app(app)
    
    # Configurar Socket.IO para chat y videoconferencia
    socketio.init_app(app, 
                     cors_allowed_origins="*",  # En producción, restringir a dominio específico
                     async_mode='eventlet')  # Usar eventlet para mejor rendimiento
    
    # Configurar manejo de errores personalizado
    register_error_handlers(app)


def register_error_handlers(app):
    """
    Registra manejadores de errores personalizados.
    
    Args:
        app: Aplicación Flask
    """
    @app.errorhandler(403)
    def forbidden_page(error):
        """Maneja error 403: Acceso prohibido."""
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def page_not_found(error):
        """Maneja error 404: Página no encontrada."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def server_error_page(error):
        """Maneja error 500: Error interno del servidor."""
        return render_template('errors/500.html'), 500
    
    # Importar render_template aquí para evitar importación circular
    from flask import render_template