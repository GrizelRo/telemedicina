import os
from datetime import timedelta

class Config:
    """Configuración base para todas las configuraciones."""
    
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-muy-segura-y-dificil-de-adivinar'
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'sal-segura-para-tokens'
    
    # Base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Correo electrónico
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@telemedicina.org')
    MAIL_ASYNC = True  # Enviar correos de forma asíncrona
    
    # Carpeta de subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Zona horaria
    TIMEZONE = 'America/Bogota'
    
    # Configuraciones específicas para videoconferencia
    VIDEOCONFERENCE_TIMEOUT = 3600  # 1 hora en segundos
    
    # Configuraciones para WebRTC
    WEBRTC_ICE_SERVERS = [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'}
    ]
    
    # Límites de datos
    MAX_APPOINTMENTS_PER_DOCTOR_DAY = 20  # Máximo de citas por día para un médico
    
    # Rutas protegidas
    LOGIN_REQUIRED_PATHS = ['/paciente', '/medico', '/admin']
    
    # Configuraciones para la documentación
    PDF_FOOTER_TEXT = 'Documento generado por la Plataforma de Telemedicina - No requiere firma manuscrita'
    
    # Título y datos de la plataforma
    APP_NAME = 'Plataforma de Telemedicina'
    APP_DESCRIPTION = 'Sistema de telemedicina para centros médicos públicos'
    APP_VERSION = '1.0.0'
    
    @staticmethod
    def init_app(app):
        """Inicialización de la aplicación."""
        # Crear carpetas necesarias
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])


class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data-dev.sqlite')
    
    # Configuraciones específicas para desarrollo
    TEMPLATES_AUTO_RELOAD = True
    MAIL_SUPPRESS_SEND = True  # No enviar correos realmente en desarrollo


class TestingConfig(Config):
    """Configuración para pruebas."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data-test.sqlite')
    
    # Desactivar CSRF para testing
    WTF_CSRF_ENABLED = False
    
    # No enviar correos en testing
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(Config):
    """Configuración para producción."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.sqlite')
    
    # Configuraciones específicas para producción
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        """Inicialización específica para producción."""
        Config.init_app(app)
        
        # Configurar logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('logs/telemedicina.log', maxBytes=10485760, backupCount=10)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Iniciando aplicación de Telemedicina')
        
        # Medidas de seguridad adicionales para producción
        @app.after_request
        def agregar_encabezados_seguridad(response):
            """Agrega encabezados de seguridad a las respuestas."""
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            return response


class HerokuConfig(ProductionConfig):
    """Configuración para Heroku."""
    
    @classmethod
    def init_app(cls, app):
        """Inicialización específica para Heroku."""
        ProductionConfig.init_app(app)
        
        # Configuraciones específicas para Heroku
        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        
        # Configurar proxy para Heroku
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)


# Mapeo de configuraciones
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}