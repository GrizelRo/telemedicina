from sqlalchemy.ext.declarative import declared_attr
from app.extensions import db
from app.models.usuario import UsuarioTipoMixin

class Paciente(UsuarioTipoMixin, db.Model):
    """Modelo para pacientes del sistema."""
    __tablename__ = 'pacientes'
    
    # Información médica básica
    grupo_sanguineo = db.Column(db.String(10), nullable=True)
    alergias = db.Column(db.Text, nullable=True)
    enfermedades_cronicas = db.Column(db.Text, nullable=True)
    contacto_emergencia_nombre = db.Column(db.String(200), nullable=True)
    contacto_emergencia_telefono = db.Column(db.String(20), nullable=True)
    contacto_emergencia_relacion = db.Column(db.String(50), nullable=True)
    seguro_medico = db.Column(db.String(100), nullable=True)
    numero_seguro = db.Column(db.String(50), nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='paciente')
    historial_clinico = db.relationship('HistorialClinico', uselist=False, 
                                       back_populates='paciente', cascade='all, delete-orphan')
    citas = db.relationship('Cita', back_populates='paciente', lazy='dynamic')
    
    def __repr__(self):
        return f"<Paciente {self.usuario_id}>"


class Medico(UsuarioTipoMixin, db.Model):
    """Modelo para médicos del sistema."""
    __tablename__ = 'medicos'
    
    # Información profesional
    numero_licencia = db.Column(db.String(50), unique=True, nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'), nullable=False)
    titulo_profesional = db.Column(db.String(200), nullable=False)
    biografia = db.Column(db.Text, nullable=True)
    anos_experiencia = db.Column(db.Integer, nullable=True)
    disponible = db.Column(db.Boolean, default=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='medico')
    especialidad = db.relationship('Especialidad', back_populates='medicos')
    citas = db.relationship('Cita', back_populates='medico', lazy='dynamic')
    horarios = db.relationship('HorarioMedico', back_populates='medico', cascade='all, delete-orphan')
    
    # Relación con centros médicos (un médico puede trabajar en varios centros)
    centros_medicos = db.relationship('CentroMedico', secondary='medicos_centros',
                                     back_populates='medicos')
    
    def __repr__(self):
        return f"<Médico {self.usuario_id} - Lic: {self.numero_licencia}>"


class AdministradorCentro(UsuarioTipoMixin, db.Model):
    """Modelo para administradores de centros médicos."""
    __tablename__ = 'administradores_centro'
    
    centro_medico_id = db.Column(db.Integer, db.ForeignKey('centros_medicos.id'), nullable=False)
    cargo = db.Column(db.String(100), nullable=True)
    departamento = db.Column(db.String(100), nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='admin_centro')
    centro_medico = db.relationship('CentroMedico', back_populates='administradores')
    
    def __repr__(self):
        return f"<Admin Centro {self.usuario_id} - Centro: {self.centro_medico_id}>"


class AdministradorSistema(UsuarioTipoMixin, db.Model):
    """Modelo para administradores del sistema."""
    __tablename__ = 'administradores_sistema'
    
    nivel_acceso = db.Column(db.String(50), default='completo')
    departamento = db.Column(db.String(100), nullable=True)
    notas = db.Column(db.Text, nullable=True)
    
    # Relaciones
    usuario = db.relationship('Usuario', back_populates='admin_sistema')
    
    def __repr__(self):
        return f"<Admin Sistema {self.usuario_id}>"


# Tabla de asociación entre médicos y centros médicos
medicos_centros = db.Table(
    'medicos_centros',
    db.Column('medico_id', db.Integer, db.ForeignKey('medicos.usuario_id'), primary_key=True),
    db.Column('centro_medico_id', db.Integer, db.ForeignKey('centros_medicos.id'), primary_key=True),
    db.Column('activo', db.Boolean, default=True),
    db.Column('fecha_inicio', db.Date, nullable=False)
)


class Especialidad(db.Model):
    """Modelo para especialidades médicas."""
    __tablename__ = 'especialidades'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    icono = db.Column(db.String(100), nullable=True)  # Ruta al icono representativo
    
    # Relaciones
    medicos = db.relationship('Medico', back_populates='especialidad')
    
    def __repr__(self):
        return f"<Especialidad {self.nombre}>"


class HorarioMedico(db.Model):
    """Modelo para los horarios de disponibilidad de los médicos."""
    __tablename__ = 'horarios_medicos'
    
    id = db.Column(db.Integer, primary_key=True)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.usuario_id'), nullable=False)
    centro_medico_id = db.Column(db.Integer, db.ForeignKey('centros_medicos.id'), nullable=False)
    dia_semana = db.Column(db.Integer, nullable=False)  # 0=Lunes, 1=Martes, etc.
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    medico = db.relationship('Medico', back_populates='horarios')
    centro_medico = db.relationship('CentroMedico')
    
    def __repr__(self):
        return f"<Horario {self.medico_id} - Día: {self.dia_semana}>"