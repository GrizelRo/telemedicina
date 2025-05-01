import os
from flask import Flask, render_template
from flask_babel import Babel
import datetime
from app.config import config
from app.extensions import init_extensions, db

# Importar modelos para que SQLAlchemy los reconozca
from app.models import usuario, tipos_usuario, centro_medico

def create_app(config_name=None):
    """
    Crea y configura la aplicación Flask.
    
    Args:
        config_name: Nombre de la configuración a utilizar
        
    Returns:
        app: Aplicación Flask configurada
    """
    if not config_name:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar extensiones
    init_extensions(app)
    
    # Inicializar Babel para internacionalización
    babel = Babel(app)
    
    # Definir la función para seleccionar el idioma
    def get_locale():
        """Selecciona el idioma para la interfaz."""
        # Por defecto, usar español
        return 'es'
    
    # Configurar Babel para usar la función get_locale
    babel.init_app(app, locale_selector=get_locale)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar comandos CLI
    register_commands(app)
    
    # Registrar contexto shell
    register_shell_context(app)
    
    # Crear datos iniciales si es necesario
    with app.app_context():
        from app.utils.inicializador import crear_datos_iniciales
        db.create_all()  # Crear tablas
        crear_datos_iniciales()  # Crear datos necesarios
    
    # Configurar jinja
    configure_jinja(app)
    
    return app


def register_blueprints(app):
    """
    Registra todos los blueprints de la aplicación.
    
    Args:
        app: Aplicación Flask
    """
    # Blueprint principal
    from app.views.main import main_bp
    app.register_blueprint(main_bp)
    
    # Blueprint de autenticación
    from app.views.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Blueprint de pacientes
    from app.views.paciente import paciente_bp
    app.register_blueprint(paciente_bp, url_prefix='/paciente')
    
    # Blueprint de médicos
    from app.views.medico import medico_bp
    app.register_blueprint(medico_bp, url_prefix='/medico')
    
    # Blueprint de administradores de centro
    from app.views.admin_centro import admin_centro_bp
    app.register_blueprint(admin_centro_bp, url_prefix='/admin-centro')
    
    # Blueprint de administradores del sistema
    from app.views.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Blueprint de citas
    from app.views.cita import cita_bp
    app.register_blueprint(cita_bp, url_prefix='/cita')
    
    # Blueprint de consultas
    from app.views.consulta import consulta_bp
    app.register_blueprint(consulta_bp, url_prefix='/consulta')
    
    # Blueprint de documentos médicos
    from app.views.documento import documento_bp
    app.register_blueprint(documento_bp, url_prefix='/documento')
    
    # Blueprint para verificación de documentos (público)
    from app.views.verificacion import verificacion_bp
    app.register_blueprint(verificacion_bp, url_prefix='/verificar')
    
    # Blueprint para API (opcional)
    # from app.api import api_bp
    # app.register_blueprint(api_bp, url_prefix='/api')


def register_commands(app):
    """
    Registra comandos personalizados para la interfaz de línea de comandos.
    
    Args:
        app: Aplicación Flask
    """
    from app.commands import create_superuser_command, reset_db_command
    
    # Registrar comandos
    app.cli.add_command(create_superuser_command)
    app.cli.add_command(reset_db_command)


def register_shell_context(app):
    """
    Registra objetos en el contexto de shell para facilitar pruebas.
    
    Args:
        app: Aplicación Flask
    """
    @app.shell_context_processor
    def make_shell_context():
        """Proporciona objetos importantes para el shell."""
        from app.models.usuario import Usuario, Rol
        from app.models.tipos_usuario import Paciente, Medico, AdministradorCentro, AdministradorSistema
        
        return {
            'db': db,
            'Usuario': Usuario,
            'Rol': Rol,
            'Paciente': Paciente,
            'Medico': Medico,
            'AdministradorCentro': AdministradorCentro,
            'AdministradorSistema': AdministradorSistema
        }


def configure_jinja(app):
    """
    Configura Jinja2 con funciones personalizadas y filtros.
    
    Args:
        app: Aplicación Flask
    """
    # Funciones personalizadas para las plantillas
    @app.template_filter('fecha_formato')
    def fecha_formato(fecha, formato='%d/%m/%Y'):
        """Formatea una fecha en el formato especificado."""
        if fecha:
            return fecha.strftime(formato)
        return ''
    
    @app.template_filter('fecha_hora_formato')
    def fecha_hora_formato(fecha, formato='%d/%m/%Y %H:%M'):
        """Formatea una fecha y hora en el formato especificado."""
        if fecha:
            return fecha.strftime(formato)
        return ''
    
    @app.template_global()
    def es_activo(ruta):
        """Determina si una ruta está activa para menús de navegación."""
        from flask import request
        return 'active' if request.path.startswith(ruta) else ''
    
    # Agregar funciones/variables globales para las plantillas
    @app.context_processor
    def utility_processor():
        """Proporciona utilidades globales para todas las plantillas."""
        return {
            'app_name': app.config['APP_NAME'],
            'app_version': app.config['APP_VERSION'],
            'current_year': datetime.datetime.now().year
        }