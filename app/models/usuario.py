from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import declared_attr

from app.extensions import db

# Tabla de asociación entre usuarios y roles
usuarios_roles = db.Table(
    'usuarios_roles',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Usuario(UserMixin, db.Model):
    """Modelo base para todos los usuarios del sistema."""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_documento = db.Column(db.String(20), unique=True, nullable=False, index=True)
    tipo_documento = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    genero = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telefono = db.Column(db.String(20), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    roles = db.relationship('Rol', secondary=usuarios_roles, 
                            backref=db.backref('usuarios', lazy='dynamic'))
    
    # Relaciones con modelos específicos para cada tipo de usuario
    paciente = db.relationship('Paciente', uselist=False, back_populates='usuario')
    medico = db.relationship('Medico', uselist=False, back_populates='usuario')
    admin_centro = db.relationship('AdministradorCentro', uselist=False, back_populates='usuario')
    admin_sistema = db.relationship('AdministradorSistema', uselist=False, back_populates='usuario')
    
    # Historial de acceso del usuario
    accesos = db.relationship('HistorialAcceso', back_populates='usuario')
    
    @property
    def password(self):
        """Previene acceso a la contraseña."""
        raise AttributeError('La contraseña no es un atributo legible')
    
    @password.setter
    def password(self, password):
        """Establece la contraseña hasheada."""
        self.password_hash = generate_password_hash(password)
    
    def verificar_password(self, password):
        """Verifica si la contraseña es correcta."""
        return check_password_hash(self.password_hash, password)
    
    def tiene_rol(self, nombre_rol):
        """Verifica si el usuario tiene un rol específico."""
        return any(rol.nombre == nombre_rol for rol in self.roles)
    
    def asignar_rol(self, rol):
        """Asigna un rol al usuario."""
        if rol not in self.roles:
            self.roles.append(rol)
    
    def quitar_rol(self, rol):
        """Quita un rol al usuario."""
        if rol in self.roles:
            self.roles.remove(rol)
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario."""
        return f"{self.nombre} {self.apellido}"
    
    def registrar_acceso(self):
        """Registra el acceso del usuario al sistema."""
        self.ultimo_acceso = datetime.utcnow()
        
        # Registrar en historial de accesos
        acceso = HistorialAcceso(usuario_id=self.id)
        db.session.add(acceso)
    
    def __repr__(self):
        return f"<Usuario {self.numero_documento} - {self.nombre_completo}>"
    
    @property
    def es_admin_sistema(self):
        """Verifica si el usuario es administrador del sistema."""
        return self.tiene_rol('administrador_sistema')
    
    @property
    def es_admin_centro(self):
        """Verifica si el usuario es administrador de centro médico."""
        return self.tiene_rol('administrador_centro')
    
    @property
    def es_medico(self):
        """Verifica si el usuario es médico."""
        return self.tiene_rol('medico')
    
    @property
    def es_paciente(self):
        """Verifica si el usuario es paciente."""
        return self.tiene_rol('paciente')


class Rol(db.Model):
    """Modelo para los roles del sistema."""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f"<Rol {self.nombre}>"


class HistorialAcceso(db.Model):
    """Modelo para registrar los accesos de los usuarios al sistema."""
    __tablename__ = 'historial_accesos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow)
    direccion_ip = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='accesos')
    
    def __repr__(self):
        return f"<Acceso {self.usuario_id} - {self.fecha_hora}>"


# Mixin para modelos de usuarios específicos
class UsuarioTipoMixin:
    """Mixin para los diferentes tipos de usuarios."""
    @declared_attr
    def usuario_id(cls):
        return db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)