import uuid
import json
import logging
from datetime import datetime, timedelta
from flask import current_app
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)

class VideoConferenceManager:
    """Gestiona las salas de videoconferencia."""
    
    def __init__(self, socketio):
        """
        Inicializa el gestor de videoconferencia.
        
        Args:
            socketio: Instancia de SocketIO
        """
        self.socketio = socketio
        self.active_rooms = {}  # sala_id -> {usuarios, estado, inicio, etc}
    
    def create_room(self, sala_id, medico_id, paciente_id, duracion_maxima=60):
        """
        Crea una nueva sala de videoconferencia.
        
        Args:
            sala_id: ID de la sala virtual
            medico_id: ID del médico
            paciente_id: ID del paciente
            duracion_maxima: Duración máxima en minutos
            
        Returns:
            dict: Información de la sala creada
        """
        room_data = {
            'id': sala_id,
            'medico_id': medico_id,
            'paciente_id': paciente_id,
            'participantes': [],
            'estado': 'esperando', # estados: esperando, activa, finalizada
            'inicio': None,
            'fin': None,
            'duracion_maxima': duracion_maxima,
            'grabacion_activa': False,
            'url_grabacion': None,
            'mensajes': [],
            'ultima_actividad': datetime.utcnow()
        }
        
        self.active_rooms[sala_id] = room_data
        logger.info(f"Sala creada: {sala_id}")
        
        return room_data
    
    def join_room(self, sala_id, usuario_id, tipo_usuario, socket_id):
        """
        Une a un usuario a una sala de videoconferencia.
        
        Args:
            sala_id: ID de la sala virtual
            usuario_id: ID del usuario que se une
            tipo_usuario: 'medico' o 'paciente'
            socket_id: ID del socket del usuario
            
        Returns:
            bool: True si se unió correctamente
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de unirse a sala inexistente: {sala_id}")
            return False
            
        room = self.active_rooms[sala_id]
        
        # Verificar si el usuario tiene permiso
        if tipo_usuario == 'medico' and str(usuario_id) != str(room['medico_id']):
            logger.warning(f"Médico no autorizado: {usuario_id}")
            return False
            
        if tipo_usuario == 'paciente' and str(usuario_id) != str(room['paciente_id']):
            logger.warning(f"Paciente no autorizado: {usuario_id}")
            return False
        
        # Verificar si ya está en la sala
        for p in room['participantes']:
            if p['usuario_id'] == usuario_id:
                # Actualizar socket_id si cambió
                p['socket_id'] = socket_id
                p['ultima_actividad'] = datetime.utcnow()
                join_room(sala_id, sid=socket_id)
                logger.info(f"Usuario reconectado: {usuario_id} a sala: {sala_id}")
                return True
        
        # Agregar nuevo participante
        participante = {
            'usuario_id': usuario_id,
            'tipo': tipo_usuario,
            'socket_id': socket_id,
            'ingreso': datetime.utcnow(),
            'ultima_actividad': datetime.utcnow(),
            'video_activo': True,
            'audio_activo': True
        }
        
        room['participantes'].append(participante)
        room['ultima_actividad'] = datetime.utcnow()
        
        # Si es la primera persona, sala en espera
        if len(room['participantes']) == 1:
            room['estado'] = 'esperando'
            
        # Si ambos están, activar la sala
        if len(room['participantes']) == 2:
            if room['estado'] == 'esperando':
                room['estado'] = 'activa'
                room['inicio'] = datetime.utcnow()
        
        # Unir al socket a la sala
        join_room(sala_id, sid=socket_id)
        
        logger.info(f"Usuario unido: {usuario_id} ({tipo_usuario}) a sala: {sala_id}")
        
        # Notificar a todos en la sala
        self.socketio.emit('user_joined', {
            'usuario_id': usuario_id,
            'tipo': tipo_usuario,
            'estado_sala': room['estado'],
            'num_participantes': len(room['participantes'])
        }, room=sala_id)
        
        return True
    
    def leave_room(self, sala_id, socket_id):
        """
        Elimina a un usuario de una sala de videoconferencia.
        
        Args:
            sala_id: ID de la sala virtual
            socket_id: ID del socket del usuario
            
        Returns:
            bool: True si se salió correctamente
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de salir de sala inexistente: {sala_id}")
            return False
            
        room = self.active_rooms[sala_id]
        participante_idx = None
        
        # Buscar al participante por socket_id
        for i, p in enumerate(room['participantes']):
            if p['socket_id'] == socket_id:
                participante_idx = i
                break
        
        if participante_idx is not None:
            # Remover participante
            participante = room['participantes'].pop(participante_idx)
            
            # Salir de la sala de socket
            leave_room(sala_id, sid=socket_id)
            
            # Si no quedan participantes, cerrar la sala después de un tiempo
            if len(room['participantes']) == 0:
                if room['estado'] == 'activa':
                    room['estado'] = 'finalizada'
                    room['fin'] = datetime.utcnow()
            
            # Notificar a los demás
            self.socketio.emit('user_left', {
                'usuario_id': participante['usuario_id'],
                'tipo': participante['tipo'],
                'estado_sala': room['estado'],
                'num_participantes': len(room['participantes'])
            }, room=sala_id)
            
            logger.info(f"Usuario salió: {participante['usuario_id']} de sala: {sala_id}")
            return True
            
        logger.warning(f"Socket no encontrado en la sala: {socket_id}")
        return False
    
    def send_signal(self, sala_id, from_socket_id, to_socket_id, signal_data):
        """
        Envía una señal WebRTC entre usuarios.
        
        Args:
            sala_id: ID de la sala virtual
            from_socket_id: ID del socket emisor
            to_socket_id: ID del socket receptor
            signal_data: Datos de la señal WebRTC
            
        Returns:
            bool: True si se envió correctamente
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de enviar señal en sala inexistente: {sala_id}")
            return False
        
        self.socketio.emit('signal', {
            'from': from_socket_id,
            'signal': signal_data
        }, room=to_socket_id)
        
        return True
    
    def toggle_media(self, sala_id, socket_id, media_type, enabled):
        """
        Activa/desactiva video o audio de un usuario.
        
        Args:
            sala_id: ID de la sala virtual
            socket_id: ID del socket del usuario
            media_type: 'video' o 'audio'
            enabled: True para activar, False para desactivar
            
        Returns:
            bool: True si se cambió correctamente
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de cambiar media en sala inexistente: {sala_id}")
            return False
            
        room = self.active_rooms[sala_id]
        
        # Buscar al participante
        for p in room['participantes']:
            if p['socket_id'] == socket_id:
                if media_type == 'video':
                    p['video_activo'] = enabled
                elif media_type == 'audio':
                    p['audio_activo'] = enabled
                
                # Notificar a todos
                self.socketio.emit('media_toggle', {
                    'usuario_id': p['usuario_id'],
                    'tipo': p['tipo'],
                    'media': media_type,
                    'enabled': enabled
                }, room=sala_id)
                
                return True
        
        return False
    
    def get_room_status(self, sala_id):
        """
        Obtiene el estado actual de una sala.
        
        Args:
            sala_id: ID de la sala virtual
            
        Returns:
            dict: Información de la sala o None si no existe
        """
        if sala_id not in self.active_rooms:
            return None
            
        room = self.active_rooms[sala_id]
        
        # Verificar si la sala expiró por tiempo
        if room['estado'] == 'activa' and room['inicio'] is not None:
            duracion = datetime.utcnow() - room['inicio']
            if duracion.total_seconds() / 60 > room['duracion_maxima']:
                room['estado'] = 'finalizada'
                room['fin'] = datetime.utcnow()
        
        return {
            'id': room['id'],
            'estado': room['estado'],
            'inicio': room['inicio'],
            'fin': room['fin'],
            'participantes': [
                {
                    'usuario_id': p['usuario_id'],
                    'tipo': p['tipo'],
                    'video_activo': p['video_activo'],
                    'audio_activo': p['audio_activo']
                } for p in room['participantes']
            ],
            'mensajes_count': len(room['mensajes']),
            'duracion_maxima': room['duracion_maxima'],
            'grabacion_activa': room['grabacion_activa']
        }
    
    def add_message(self, sala_id, usuario_id, tipo_usuario, contenido):
        """
        Agrega un mensaje al chat de la sala.
        
        Args:
            sala_id: ID de la sala virtual
            usuario_id: ID del usuario que envía el mensaje
            tipo_usuario: 'medico' o 'paciente'
            contenido: Texto del mensaje
            
        Returns:
            dict: Mensaje creado o None si hay error
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de enviar mensaje en sala inexistente: {sala_id}")
            return None
            
        room = self.active_rooms[sala_id]
        
        # Solo permitir mensajes en salas activas
        if room['estado'] != 'activa':
            logger.warning(f"Intento de enviar mensaje en sala no activa: {sala_id}")
            return None
        
        # Crear mensaje
        mensaje = {
            'id': str(uuid.uuid4()),
            'usuario_id': usuario_id,
            'tipo_usuario': tipo_usuario,
            'contenido': contenido,
            'fecha': datetime.utcnow()
        }
        
        # Guardar mensaje
        room['mensajes'].append(mensaje)
        room['ultima_actividad'] = datetime.utcnow()
        
        # Notificar a todos en la sala
        self.socketio.emit('chat_message', mensaje, room=sala_id)
        
        return mensaje
    
    def get_messages(self, sala_id, count=20):
        """
        Obtiene los últimos mensajes de una sala.
        
        Args:
            sala_id: ID de la sala virtual
            count: Cantidad de mensajes a obtener
            
        Returns:
            list: Lista de mensajes o None si hay error
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de obtener mensajes de sala inexistente: {sala_id}")
            return None
            
        room = self.active_rooms[sala_id]
        
        # Obtener los últimos mensajes
        return room['mensajes'][-count:]
    
    def end_room(self, sala_id):
        """
        Finaliza una sala de videoconferencia.
        
        Args:
            sala_id: ID de la sala virtual
            
        Returns:
            bool: True si se finalizó correctamente
        """
        if sala_id not in self.active_rooms:
            logger.warning(f"Intento de finalizar sala inexistente: {sala_id}")
            return False
            
        room = self.active_rooms[sala_id]
        
        # Cambiar estado
        room['estado'] = 'finalizada'
        room['fin'] = datetime.utcnow()
        
        # Notificar a todos
        self.socketio.emit('room_ended', {
            'sala_id': sala_id,
            'fin': room['fin'].isoformat()
        }, room=sala_id)
        
        # Guardar datos en la base de datos
        if room['inicio'] is not None:
            duracion = room['fin'] - room['inicio']
            duracion_minutos = duracion.total_seconds() / 60
            
            # Aquí se podría guardar la duración en la base de datos
            # También se podrían guardar los mensajes
            
            logger.info(f"Sala finalizada: {sala_id}, duración: {duracion_minutos:.2f} minutos")
        
        return True

# Instancia global para usar con Socket.IO
video_conference_manager = None

def init_video_conference(socketio):
    """
    Inicializa el gestor de videoconferencia.
    
    Args:
        socketio: Instancia de SocketIO
    """
    global video_conference_manager
    video_conference_manager = VideoConferenceManager(socketio)
    
    # Configurar eventos de Socket.IO
    @socketio.on('join')
    def handle_join(data):
        """Maneja un usuario uniéndose a la sala."""
        sala_id = data.get('sala_id')
        usuario_id = data.get('usuario_id')
        tipo_usuario = data.get('tipo_usuario')
        
        if not sala_id or not usuario_id or not tipo_usuario:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        success = video_conference_manager.join_room(
            sala_id=sala_id,
            usuario_id=usuario_id,
            tipo_usuario=tipo_usuario,
            socket_id=request.sid
        )
        
        if success:
            # Enviar estado actual de la sala
            room_status = video_conference_manager.get_room_status(sala_id)
            emit('room_status', room_status)
            
            # Enviar mensajes recientes
            messages = video_conference_manager.get_messages(sala_id)
            if messages:
                emit('chat_history', messages)
        else:
            emit('error', {'message': 'No se pudo unir a la sala'})
    
    @socketio.on('leave')
    def handle_leave(data):
        """Maneja un usuario saliendo de la sala."""
        sala_id = data.get('sala_id')
        
        if not sala_id:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        video_conference_manager.leave_room(
            sala_id=sala_id,
            socket_id=request.sid
        )
    
    @socketio.on('signal')
    def handle_signal(data):
        """Maneja señales WebRTC entre usuarios."""
        sala_id = data.get('sala_id')
        to_socket_id = data.get('to')
        signal = data.get('signal')
        
        if not sala_id or not to_socket_id or not signal:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        video_conference_manager.send_signal(
            sala_id=sala_id,
            from_socket_id=request.sid,
            to_socket_id=to_socket_id,
            signal_data=signal
        )
    
    @socketio.on('toggle_media')
    def handle_toggle_media(data):
        """Maneja cambios en video/audio."""
        sala_id = data.get('sala_id')
        media_type = data.get('media')
        enabled = data.get('enabled')
        
        if not sala_id or not media_type or enabled is None:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        video_conference_manager.toggle_media(
            sala_id=sala_id,
            socket_id=request.sid,
            media_type=media_type,
            enabled=enabled
        )
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Maneja mensajes de chat."""
        sala_id = data.get('sala_id')
        usuario_id = data.get('usuario_id')
        tipo_usuario = data.get('tipo_usuario')
        contenido = data.get('contenido')
        
        if not sala_id or not usuario_id or not tipo_usuario or not contenido:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        video_conference_manager.add_message(
            sala_id=sala_id,
            usuario_id=usuario_id,
            tipo_usuario=tipo_usuario,
            contenido=contenido
        )
    
    @socketio.on('end_room')
    def handle_end_room(data):
        """Maneja finalización de sala."""
        sala_id = data.get('sala_id')
        
        if not sala_id:
            emit('error', {'message': 'Parámetros incompletos'})
            return
        
        video_conference_manager.end_room(sala_id=sala_id)
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Maneja desconexión de socket."""
        # Buscar en todas las salas activas
        for sala_id, room in list(video_conference_manager.active_rooms.items()):
            for p in room['participantes']:
                if p['socket_id'] == request.sid:
                    video_conference_manager.leave_room(
                        sala_id=sala_id,
                        socket_id=request.sid
                    )
                    break

    # Importar aquí para evitar problemas circulares
    from flask import request