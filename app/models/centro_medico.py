from app.extensions import db
from datetime import datetime

class CentroMedico(db.Model):
    """Modelo para centros médicos."""
    __tablename__ = 'centros_medicos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)  # Hospital, Clínica, Centro de salud, etc.
    direccion = db.Column(db.String(200), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(20), nullable=True)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    sitio_web = db.Column(db.String(200), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    horario_atencion = db.Column(db.Text, nullable=True)
    latitud = db.Column(db.Float, nullable=True)
    longitud = db.Column(db.Float, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    logo = db.Column(db.String(200), nullable=True)  # Ruta al logo del centro médico
    
    # Relaciones
    medicos = db.relationship('Medico', secondary='medicos_centros', back_populates='centros_medicos')
    administradores = db.relationship('AdministradorCentro', back_populates='centro_medico')
    
    # Especialidades disponibles en este centro
    especialidades = db.relationship('EspecialidadCentro', back_populates='centro_medico', 
                                    cascade='all, delete-orphan')
    
    # Citas asociadas a este centro
    citas = db.relationship('Cita', back_populates='centro_medico', lazy='dynamic')
    
    def __repr__(self):
        return f"<Centro Médico {self.nombre} - {self.ciudad}>"
    
    @property
    def direccion_completa(self):
        """Retorna la dirección completa del centro médico."""
        return f"{self.direccion}, {self.ciudad}, {self.departamento}"


class EspecialidadCentro(db.Model):
    """Modelo para especialidades disponibles en un centro médico."""
    __tablename__ = 'especialidades_centro'
    
    id = db.Column(db.Integer, primary_key=True)
    centro_medico_id = db.Column(db.Integer, db.ForeignKey('centros_medicos.id'), nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'), nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    notas = db.Column(db.Text, nullable=True)
    
    # Relaciones
    centro_medico = db.relationship('CentroMedico', back_populates='especialidades')
    especialidad = db.relationship('Especialidad')
    
    def __repr__(self):
        return f"<Especialidad Centro {self.centro_medico_id} - Esp: {self.especialidad_id}>"