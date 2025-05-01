from datetime import datetime
from app.extensions import db
from app.utils.security import generar_codigo_validacion

class DocumentoBase(object):
    """Clase base con atributos comunes para documentos médicos."""
    
    # Fechas
    fecha_emision = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_caducidad = db.Column(db.DateTime, nullable=True)
    
    # Estado del documento: activo, anulado, caducado
    estado = db.Column(db.String(20), default='activo', nullable=False)
    
    # Validación
    codigo_validacion = db.Column(db.String(8), nullable=False)
    
    # Motivo de anulación (si aplica)
    motivo_anulacion = db.Column(db.Text, nullable=True)
    
    # Persona que emitió el documento (generalmente el médico)
    emitido_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Fechas del sistema
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def anular(self, motivo):
        """
        Anula un documento.
        
        Args:
            motivo: Motivo de la anulación
            
        Returns:
            bool: True si se anuló correctamente
        """
        if self.estado != 'activo':
            return False
            
        self.estado = 'anulado'
        self.motivo_anulacion = motivo
        self.fecha_actualizacion = datetime.utcnow()
        return True
    
    @property
    def esta_activo(self):
        """Determina si el documento está activo."""
        if self.estado != 'activo':
            return False
            
        # Verificar caducidad si tiene fecha de caducidad
        if self.fecha_caducidad and datetime.utcnow() > self.fecha_caducidad:
            return False
            
        return True


class RecetaMedica(db.Model, DocumentoBase):
    """Modelo para recetas médicas."""
    __tablename__ = 'recetas_medicas'
    
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    
    # Datos del paciente y médico (para rápido acceso)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.usuario_id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.usuario_id'), nullable=False)
    
    # Información de la receta
    diagnostico = db.Column(db.Text, nullable=True)
    
    # Relaciones
    consulta = db.relationship('Consulta', back_populates='recetas')
    paciente = db.relationship('Paciente')
    medico = db.relationship('Medico')
    emisor = db.relationship('Usuario', foreign_keys=[emitido_por])
    medicamentos = db.relationship('MedicamentoReceta', back_populates='receta', 
                                cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(RecetaMedica, self).__init__(**kwargs)
        if not self.codigo_validacion:
            self.codigo_validacion = generar_codigo_validacion()
    
    def __repr__(self):
        return f"<RecetaMedica {self.id} - Médico: {self.medico_id}, Paciente: {self.paciente_id}>"
    
    @property
    def url_validacion(self):
        """Genera la URL para validar la receta."""
        from flask import url_for
        return url_for('verificacion.validar_receta', 
                    codigo=self.codigo_validacion, 
                    id=self.id, 
                    _external=True)


class MedicamentoReceta(db.Model):
    """Modelo para medicamentos en una receta."""
    __tablename__ = 'medicamentos_receta'
    
    id = db.Column(db.Integer, primary_key=True)
    receta_id = db.Column(db.Integer, db.ForeignKey('recetas_medicas.id'), nullable=False)
    
    # Información del medicamento
    nombre = db.Column(db.String(200), nullable=False)
    presentacion = db.Column(db.String(100), nullable=True)
    dosis = db.Column(db.String(100), nullable=False)
    via_administracion = db.Column(db.String(50), nullable=False)
    frecuencia = db.Column(db.String(100), nullable=False)
    duracion = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.String(50), nullable=True)
    
    # Instrucciones adicionales
    instrucciones = db.Column(db.Text, nullable=True)
    
    # Orden en la receta
    orden = db.Column(db.Integer, default=0)
    
    # Relaciones
    receta = db.relationship('RecetaMedica', back_populates='medicamentos')
    
    def __repr__(self):
        return f"<MedicamentoReceta {self.id} - {self.nombre}>"


class OrdenLaboratorio(db.Model, DocumentoBase):
    """Modelo para órdenes de laboratorio."""
    __tablename__ = 'ordenes_laboratorio'
    
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    
    # Datos del paciente y médico (para rápido acceso)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.usuario_id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.usuario_id'), nullable=False)
    
    # Información de la orden
    diagnostico_presuntivo = db.Column(db.Text, nullable=True)
    instrucciones_generales = db.Column(db.Text, nullable=True)
    ayuno_requerido = db.Column(db.Boolean, default=False)
    urgente = db.Column(db.Boolean, default=False)
    
    # Relaciones
    consulta = db.relationship('Consulta', back_populates='ordenes_laboratorio')
    paciente = db.relationship('Paciente')
    medico = db.relationship('Medico')
    emisor = db.relationship('Usuario', foreign_keys=[emitido_por])
    examenes = db.relationship('ExamenLaboratorio', back_populates='orden', 
                             cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(OrdenLaboratorio, self).__init__(**kwargs)
        if not self.codigo_validacion:
            self.codigo_validacion = generar_codigo_validacion()
    
    def __repr__(self):
        return f"<OrdenLaboratorio {self.id} - Médico: {self.medico_id}, Paciente: {self.paciente_id}>"
    
    @property
    def url_validacion(self):
        """Genera la URL para validar la orden de laboratorio."""
        from flask import url_for
        return url_for('verificacion.validar_orden', 
                     codigo=self.codigo_validacion, 
                     id=self.id, 
                     _external=True)


class ExamenLaboratorio(db.Model):
    """Modelo para exámenes en una orden de laboratorio."""
    __tablename__ = 'examenes_laboratorio'
    
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey('ordenes_laboratorio.id'), nullable=False)
    
    # Información del examen
    codigo = db.Column(db.String(20), nullable=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(100), nullable=True)  # Sangre, orina, etc.
    descripcion = db.Column(db.Text, nullable=True)
    
    # Instrucciones específicas para este examen
    instrucciones = db.Column(db.Text, nullable=True)
    
    # Orden en la lista de exámenes
    orden = db.Column(db.Integer, default=0)
    
    # Estado del examen: pendiente, realizado, anulado
    estado = db.Column(db.String(20), default='pendiente')
    
    # Resultado del examen (si aplica)
    resultado = db.Column(db.Text, nullable=True)
    fecha_resultado = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    orden = db.relationship('OrdenLaboratorio', back_populates='examenes')
    
    def __repr__(self):
        return f"<ExamenLaboratorio {self.id} - {self.nombre}>"