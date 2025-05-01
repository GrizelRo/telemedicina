from datetime import datetime
from app.extensions import db

class Consulta(db.Model):
    """Modelo para las consultas médicas realizadas."""
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False, unique=True)
    
    # Datos clínicos básicos
    motivo_consulta = db.Column(db.Text, nullable=True)
    sintomas = db.Column(db.Text, nullable=True)
    antecedentes = db.Column(db.Text, nullable=True)
    exploracion = db.Column(db.Text, nullable=True)
    diagnostico = db.Column(db.Text, nullable=True)
    plan_tratamiento = db.Column(db.Text, nullable=True)
    recomendaciones = db.Column(db.Text, nullable=True)
    
    # Datos de seguimiento
    requiere_seguimiento = db.Column(db.Boolean, default=False)
    tiempo_seguimiento = db.Column(db.Integer, nullable=True)  # Días para seguimiento
    instrucciones_seguimiento = db.Column(db.Text, nullable=True)
    
    # Fechas
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    duracion_minutos = db.Column(db.Integer, nullable=True)
    
    # Persona que registra la consulta (generalmente el médico)
    registrado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Fechas del sistema
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    cita = db.relationship('Cita', back_populates='consulta')
    registrador = db.relationship('Usuario', foreign_keys=[registrado_por])
    recetas = db.relationship('RecetaMedica', back_populates='consulta', cascade='all, delete-orphan')
    ordenes_laboratorio = db.relationship('OrdenLaboratorio', back_populates='consulta', cascade='all, delete-orphan')
    registros_historial = db.relationship('RegistroHistorialClinico', back_populates='consulta')
    
    def __repr__(self):
        return f"<Consulta {self.id} - Cita: {self.cita_id}>"
    
    @property
    def paciente(self):
        """Obtiene el paciente de la consulta a través de la cita."""
        return self.cita.paciente if self.cita else None
    
    @property
    def medico(self):
        """Obtiene el médico de la consulta a través de la cita."""
        return self.cita.medico if self.cita else None
    
    def iniciar(self, usuario_id):
        """
        Inicia una consulta médica.
        
        Args:
            usuario_id: ID del usuario (médico) que inicia la consulta
            
        Returns:
            bool: True si se inició correctamente
        """
        if self.fecha_inicio:
            return False  # Ya fue iniciada
            
        self.fecha_inicio = datetime.utcnow()
        self.registrado_por = usuario_id
        return True
    
    def finalizar(self, datos_consulta=None):
        """
        Finaliza una consulta médica y registra los datos.
        
        Args:
            datos_consulta: Diccionario con los datos de la consulta
            
        Returns:
            bool: True si se finalizó correctamente
        """
        if not self.fecha_inicio or self.fecha_fin:
            return False  # No iniciada o ya finalizada
            
        self.fecha_fin = datetime.utcnow()
        
        # Calcular duración en minutos
        duracion = self.fecha_fin - self.fecha_inicio
        self.duracion_minutos = int(duracion.total_seconds() / 60)
        
        # Actualizar datos de la consulta si se proporcionaron
        if datos_consulta:
            self.motivo_consulta = datos_consulta.get('motivo_consulta', self.motivo_consulta)
            self.sintomas = datos_consulta.get('sintomas', self.sintomas)
            self.antecedentes = datos_consulta.get('antecedentes', self.antecedentes)
            self.exploracion = datos_consulta.get('exploracion', self.exploracion)
            self.diagnostico = datos_consulta.get('diagnostico', self.diagnostico)
            self.plan_tratamiento = datos_consulta.get('plan_tratamiento', self.plan_tratamiento)
            self.recomendaciones = datos_consulta.get('recomendaciones', self.recomendaciones)
            self.requiere_seguimiento = datos_consulta.get('requiere_seguimiento', self.requiere_seguimiento)
            self.tiempo_seguimiento = datos_consulta.get('tiempo_seguimiento', self.tiempo_seguimiento)
            self.instrucciones_seguimiento = datos_consulta.get('instrucciones_seguimiento', self.instrucciones_seguimiento)
        
        # Marcar la cita como completada
        if self.cita:
            self.cita.completar()
        
        return True
    
    def generar_registro_historial(self):
        """
        Genera un registro en el historial clínico del paciente.
        
        Returns:
            RegistroHistorialClinico: El registro creado o None si no se pudo crear
        """
        if not self.paciente:
            return None
            
        # Obtener o crear el historial clínico del paciente
        from app.models.historial_clinico import HistorialClinico, RegistroHistorialClinico
        
        historial = HistorialClinico.query.filter_by(paciente_id=self.paciente.usuario_id).first()
        if not historial:
            historial = HistorialClinico(paciente_id=self.paciente.usuario_id)
            db.session.add(historial)
            db.session.flush()  # Para obtener el ID
        
        # Crear el registro
        registro = RegistroHistorialClinico(
            historial_id=historial.id,
            consulta_id=self.id,
            tipo='consulta',
            descripcion=f"Consulta con Dr. {self.medico.usuario.nombre_completo}",
            detalles={
                "motivo": self.motivo_consulta,
                "diagnostico": self.diagnostico,
                "tratamiento": self.plan_tratamiento
            }
        )
        
        db.session.add(registro)
        return registro