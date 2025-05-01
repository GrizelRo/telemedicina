from datetime import datetime, timedelta
from app.extensions import db
from sqlalchemy import event

class Cita(db.Model):
    """Modelo para las citas médicas."""
    __tablename__ = 'citas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.usuario_id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.usuario_id'), nullable=False)
    centro_medico_id = db.Column(db.Integer, db.ForeignKey('centros_medicos.id'), nullable=False)
    especialidad_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    duracion = db.Column(db.Integer, default=30)  # Duración en minutos
    
    # Estado de la cita: pendiente, confirmada, en_curso, completada, cancelada
    estado = db.Column(db.String(20), default='pendiente', nullable=False)
    
    # Tipo de cita: primera_vez, seguimiento, control, urgencia
    tipo = db.Column(db.String(20), default='primera_vez', nullable=False)
    
    # Motivo de la cita (indicado por el paciente)
    motivo = db.Column(db.Text, nullable=True)
    
    # Motivo de cancelación (si aplica)
    motivo_cancelacion = db.Column(db.Text, nullable=True)
    
    # Usuario que canceló la cita (si aplica)
    cancelado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Fechas de seguimiento
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Recordatorios enviados
    recordatorio_24h_enviado = db.Column(db.Boolean, default=False)
    recordatorio_1h_enviado = db.Column(db.Boolean, default=False)
    
    # Notas adicionales (para el personal administrativo)
    notas = db.Column(db.Text, nullable=True)
    
    # ID de la sala virtual (si aplica)
    sala_virtual_id = db.Column(db.Integer, db.ForeignKey('salas_virtuales.id'), nullable=True)
    
    # Relaciones
    paciente = db.relationship('Paciente', back_populates='citas')
    medico = db.relationship('Medico', back_populates='citas')
    centro_medico = db.relationship('CentroMedico', back_populates='citas')
    especialidad = db.relationship('Especialidad')
    sala_virtual = db.relationship('SalaVirtual', back_populates='cita', uselist=False, 
                                  cascade='all, delete-orphan', single_parent=True)
    consulta = db.relationship('Consulta', back_populates='cita', uselist=False)
    usuario_cancelador = db.relationship('Usuario', foreign_keys=[cancelado_por])
    
    def __repr__(self):
        return f"<Cita {self.id}: {self.paciente_id} con {self.medico_id} - {self.fecha_hora}>"
    
    @property
    def hora_inicio(self):
        """Devuelve la hora de inicio de la cita."""
        return self.fecha_hora
    
    @property
    def hora_fin(self):
        """Calcula la hora de finalización según la duración."""
        return self.fecha_hora + timedelta(minutes=self.duracion)
    
    @property
    def puede_cancelar(self):
        """Determina si la cita puede ser cancelada."""
        # Solo se pueden cancelar citas pendientes o confirmadas
        if self.estado not in ['pendiente', 'confirmada']:
            return False
        
        # No se pueden cancelar citas que ya han comenzado
        if self.fecha_hora <= datetime.utcnow():
            return False
        
        return True
    
    @property
    def puede_reprogramar(self):
        """Determina si la cita puede ser reprogramada."""
        # Solo se pueden reprogramar citas pendientes o confirmadas
        if self.estado not in ['pendiente', 'confirmada']:
            return False
        
        # No se pueden reprogramar citas que ya han comenzado
        if self.fecha_hora <= datetime.utcnow():
            return False
        
        return True
    
    def cancelar(self, usuario_id, motivo):
        """
        Cancela la cita.
        
        Args:
            usuario_id: ID del usuario que cancela la cita
            motivo: Motivo de la cancelación
        
        Returns:
            bool: True si se canceló correctamente
        """
        if not self.puede_cancelar:
            return False
        
        self.estado = 'cancelada'
        self.motivo_cancelacion = motivo
        self.cancelado_por = usuario_id
        self.fecha_actualizacion = datetime.utcnow()
        
        # Liberar la sala virtual si existe
        if self.sala_virtual:
            self.sala_virtual.estado = 'cancelada'
        
        return True
    
    def confirmar(self):
        """Confirma la cita."""
        if self.estado != 'pendiente':
            return False
        
        self.estado = 'confirmada'
        self.fecha_actualizacion = datetime.utcnow()
        return True
    
    def iniciar(self):
        """Marca la cita como en curso."""
        if self.estado != 'confirmada':
            return False
        
        self.estado = 'en_curso'
        self.fecha_actualizacion = datetime.utcnow()
        
        # Activar la sala virtual
        if self.sala_virtual:
            self.sala_virtual.estado = 'activa'
        
        return True
    
    def completar(self):
        """Marca la cita como completada."""
        if self.estado != 'en_curso':
            return False
        
        self.estado = 'completada'
        self.fecha_actualizacion = datetime.utcnow()
        
        # Cerrar la sala virtual
        if self.sala_virtual:
            self.sala_virtual.estado = 'cerrada'
        
        return True
    
    def reprogramar(self, nueva_fecha_hora):
        """
        Reprograma la cita para una nueva fecha y hora.
        
        Args:
            nueva_fecha_hora: Nueva fecha y hora para la cita
        
        Returns:
            bool: True si se reprogramó correctamente
        """
        if not self.puede_reprogramar:
            return False
        
        # Verificar que la nueva fecha sea futura
        if nueva_fecha_hora <= datetime.utcnow():
            return False
        
        # Verificar que el médico esté disponible en ese horario
        # (Esta verificación debería hacerse antes en el controlador)
        
        self.fecha_hora = nueva_fecha_hora
        self.fecha_actualizacion = datetime.utcnow()
        
        # Reiniciar los estados de recordatorios
        self.recordatorio_24h_enviado = False
        self.recordatorio_1h_enviado = False
        
        return True


class SalaVirtual(db.Model):
    """Modelo para las salas virtuales de consulta."""
    __tablename__ = 'salas_virtuales'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Códigos de acceso a la sala
    token_medico = db.Column(db.String(100), nullable=False)
    token_paciente = db.Column(db.String(100), nullable=False)
    
    # URL única para la sala
    url = db.Column(db.String(255), unique=True, nullable=False)
    
    # Estado: pendiente, activa, cerrada, cancelada
    estado = db.Column(db.String(20), default='pendiente')
    
    # Duración máxima en minutos
    duracion_maxima = db.Column(db.Integer, default=60)
    
    # Fechas
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    
    # Características habilitadas
    video_habilitado = db.Column(db.Boolean, default=True)
    audio_habilitado = db.Column(db.Boolean, default=True)
    chat_habilitado = db.Column(db.Boolean, default=True)
    compartir_pantalla_habilitado = db.Column(db.Boolean, default=True)
    
    # Configuraciones adicionales
    grabacion_permitida = db.Column(db.Boolean, default=False)
    url_grabacion = db.Column(db.String(255), nullable=True)
    consentimiento_grabacion = db.Column(db.Boolean, default=False)
    
    # Relaciones
    cita_id = db.Column(db.Integer, db.ForeignKey('citas.id'), nullable=False)
    cita = db.relationship('Cita', back_populates='sala_virtual')
    mensajes = db.relationship('MensajeChat', back_populates='sala', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<SalaVirtual {self.id}: {self.estado}>"
    
    @property
    def activa(self):
        """Determina si la sala está activa actualmente."""
        return self.estado == 'activa'
    
    @property
    def tiempo_restante(self):
        """Calcula el tiempo restante de la consulta en minutos."""
        if not self.fecha_inicio or self.estado != 'activa':
            return 0
            
        tiempo_transcurrido = datetime.utcnow() - self.fecha_inicio
        minutos_transcurridos = tiempo_transcurrido.total_seconds() / 60
        
        tiempo_restante = max(0, self.duracion_maxima - minutos_transcurridos)
        return round(tiempo_restante)
    
    def activar(self):
        """Activa la sala virtual."""
        if self.estado != 'pendiente':
            return False
            
        self.estado = 'activa'
        self.fecha_inicio = datetime.utcnow()
        return True
    
    def cerrar(self):
        """Cierra la sala virtual."""
        if self.estado != 'activa':
            return False
            
        self.estado = 'cerrada'
        self.fecha_fin = datetime.utcnow()
        return True


class MensajeChat(db.Model):
    """Modelo para los mensajes de chat en una sala virtual."""
    __tablename__ = 'mensajes_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    sala_id = db.Column(db.Integer, db.ForeignKey('salas_virtuales.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    sala = db.relationship('SalaVirtual', back_populates='mensajes')
    usuario = db.relationship('Usuario')
    
    def __repr__(self):
        return f"<MensajeChat {self.id}: {self.usuario_id} en {self.sala_id}>"


class Disponibilidad(db.Model):
    """Modelo para la disponibilidad de médicos."""
    __tablename__ = 'disponibilidades'
    
    id = db.Column(db.Integer, primary_key=True)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.usuario_id'), nullable=False)
    centro_medico_id = db.Column(db.Integer, db.ForeignKey('centros_medicos.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    
    # Intervalo entre citas en minutos (por defecto 30 minutos)
    intervalo_citas = db.Column(db.Integer, default=30)
    
    # Estado: disponible, parcial, no_disponible
    estado = db.Column(db.String(20), default='disponible')
    
    # Número máximo de citas permitidas en este horario
    citas_maximas = db.Column(db.Integer, default=0)  # 0 = sin límite
    
    # Relaciones
    medico = db.relationship('Medico')
    centro_medico = db.relationship('CentroMedico')
    
    # Restricción de unicidad: un médico no puede tener dos disponibilidades 
    # en el mismo centro, fecha y hora
    __table_args__ = (
        db.UniqueConstraint('medico_id', 'centro_medico_id', 'fecha', 'hora_inicio', 
                         name='uq_disponibilidad_medico_centro_fecha_hora'),
    )
    
    def __repr__(self):
        return f"<Disponibilidad {self.medico_id}: {self.fecha} {self.hora_inicio}-{self.hora_fin}>"
    
    @property
    def duracion_total_minutos(self):
        """Calcula la duración total en minutos."""
        horas = self.hora_fin.hour - self.hora_inicio.hour
        minutos = self.hora_fin.minute - self.hora_inicio.minute
        return horas * 60 + minutos
    
    @property
    def slots_disponibles(self):
        """Calcula el número de slots de tiempo disponibles."""
        if self.intervalo_citas <= 0:
            return 0
            
        return self.duracion_total_minutos // self.intervalo_citas
    
    def generar_horarios_disponibles(self):
        """
        Genera una lista de horarios disponibles en base a esta disponibilidad.
        
        Returns:
            list: Lista de objetos datetime con los horarios disponibles
        """
        from datetime import datetime, timedelta
        
        horarios = []
        fecha_base = datetime.combine(self.fecha, self.hora_inicio)
        minutos_totales = self.duracion_total_minutos
        
        # Iterar por cada intervalo posible
        for i in range(0, minutos_totales, self.intervalo_citas):
            horario = fecha_base + timedelta(minutes=i)
            
            # Verificar si este horario ya está ocupado
            from app.models.cita import Cita
            cita_existente = Cita.query.filter_by(
                medico_id=self.medico_id,
                fecha_hora=horario,
                estado=['pendiente', 'confirmada', 'en_curso']
            ).first()
            
            if not cita_existente:
                horarios.append(horario)
                
            # Si hay un límite de citas y ya lo alcanzamos, terminar
            if self.citas_maximas > 0 and len(horarios) >= self.citas_maximas:
                break
        
        return horarios