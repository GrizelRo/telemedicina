from datetime import datetime
import json
from app.extensions import db

class HistorialClinico(db.Model):
    """Modelo para el historial clínico de pacientes."""
    __tablename__ = 'historiales_clinicos'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.usuario_id'), unique=True, nullable=False)
    
    # Metadata
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    paciente = db.relationship('Paciente', back_populates='historial_clinico')
    registros = db.relationship('RegistroHistorialClinico', back_populates='historial', 
                               cascade='all, delete-orphan', order_by='desc(RegistroHistorialClinico.fecha)')
    
    def __repr__(self):
        return f"<HistorialClinico {self.id} - Paciente: {self.paciente_id}>"
    
    def agregar_registro(self, tipo, descripcion, detalles=None, consulta_id=None):
        """
        Agrega un nuevo registro al historial.
        
        Args:
            tipo: Tipo de registro (consulta, medicamento, alergia, etc.)
            descripcion: Descripción breve del registro
            detalles: Diccionario con detalles adicionales
            consulta_id: ID de la consulta relacionada (si aplica)
            
        Returns:
            RegistroHistorialClinico: El registro creado
        """
        registro = RegistroHistorialClinico(
            historial_id=self.id,
            tipo=tipo,
            descripcion=descripcion,
            detalles=detalles,
            consulta_id=consulta_id
        )
        
        db.session.add(registro)
        self.fecha_actualizacion = datetime.utcnow()
        
        return registro
    
    def obtener_registros_por_tipo(self, tipo):
        """
        Obtiene todos los registros de un tipo específico.
        
        Args:
            tipo: Tipo de registro a buscar
            
        Returns:
            list: Lista de registros del tipo especificado
        """
        return RegistroHistorialClinico.query.filter_by(
            historial_id=self.id, 
            tipo=tipo
        ).order_by(RegistroHistorialClinico.fecha.desc()).all()
    
    def obtener_registros_recientes(self, limite=10):
        """
        Obtiene los registros más recientes.
        
        Args:
            limite: Número máximo de registros a retornar
            
        Returns:
            list: Lista de registros recientes
        """
        return RegistroHistorialClinico.query.filter_by(
            historial_id=self.id
        ).order_by(RegistroHistorialClinico.fecha.desc()).limit(limite).all()
    
    def obtener_alergias(self):
        """Obtiene todas las alergias registradas."""
        return self.obtener_registros_por_tipo('alergia')
    
    def obtener_enfermedades_cronicas(self):
        """Obtiene todas las enfermedades crónicas registradas."""
        return self.obtener_registros_por_tipo('enfermedad_cronica')
    
    def obtener_antecedentes_familiares(self):
        """Obtiene todos los antecedentes familiares registrados."""
        return self.obtener_registros_por_tipo('antecedente_familiar')


class RegistroHistorialClinico(db.Model):
    """Modelo para registros individuales en el historial clínico."""
    __tablename__ = 'registros_historial_clinico'
    
    id = db.Column(db.Integer, primary_key=True)
    historial_id = db.Column(db.Integer, db.ForeignKey('historiales_clinicos.id'), nullable=False)
    
    # Tipo de registro (consulta, medicamento, alergia, enfermedad_cronica, etc.)
    tipo = db.Column(db.String(50), nullable=False)
    
    # Descripción breve del registro
    descripcion = db.Column(db.String(255), nullable=False)
    
    # Detalles del registro (almacenados como JSON)
    _detalles = db.Column('detalles', db.Text, nullable=True)
    
    # Consulta relacionada (si aplica)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=True)
    
    # Persona que registró la entrada
    registrado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Fechas
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    historial = db.relationship('HistorialClinico', back_populates='registros')
    consulta = db.relationship('Consulta', back_populates='registros_historial')
    registrador = db.relationship('Usuario', foreign_keys=[registrado_por])
    
    def __repr__(self):
        return f"<RegistroHistorial {self.id} - {self.tipo}: {self.descripcion[:20]}...>"
    
    @property
    def detalles(self):
        """Convierte los detalles de JSON a diccionario."""
        if not self._detalles:
            return {}
        return json.loads(self._detalles)
    
    @detalles.setter
    def detalles(self, valor):
        """Convierte el diccionario a JSON para almacenamiento."""
        if valor is None:
            self._detalles = None
        else:
            self._detalles = json.dumps(valor)