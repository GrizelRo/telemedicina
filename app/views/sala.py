from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from datetime import datetime

from app.models.cita import Cita, SalaVirtual
from app.extensions import db
from app.utils.video_conference import video_conference_manager

# Crear blueprint de sala virtual
sala_bp = Blueprint('sala', __name__)

@sala_bp.route('/medico/<token>')
@login_required
def medico(token):
    """Vista para que el médico acceda a la sala virtual."""
    # Verificar que el usuario es médico
    if not current_user.es_medico:
        flash('Acceso denegado. Se requieren permisos de médico.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Buscar la sala virtual por token de médico
    sala = SalaVirtual.query.filter_by(token_medico=token).first()
    
    if not sala:
        flash('Sala virtual no encontrada.', 'danger')
        return redirect(url_for('medico.citas'))
    
    # Verificar que la cita pertenece al médico actual
    cita = sala.cita
    if cita.medico_id != current_user.medico.usuario_id:
        flash('No tiene permiso para acceder a esta sala.', 'danger')
        return redirect(url_for('medico.citas'))
    
    # Verificar el estado de la sala
    if sala.estado == 'cerrada':
        flash('Esta sala ya ha sido cerrada.', 'warning')
        return redirect(url_for('consulta.resumen', consulta_id=cita.consulta.id))
    
    # Verificar tiempo límite (opcional)
    if sala.fecha_inicio and (datetime.utcnow() - sala.fecha_inicio).total_seconds() > sala.duracion_maxima * 60:
        flash('La sala ha excedido su tiempo máximo.', 'warning')
        return redirect(url_for('consulta.resumen', consulta_id=cita.consulta.id))
    
    # Si la sala no está activa, activarla
    if sala.estado != 'activa':
        sala.activar()
        db.session.commit()
    
    # Iniciar consulta si no existe
    consulta = cita.consulta
    if not consulta:
        from app.models.consulta import Consulta
        consulta = Consulta(cita_id=cita.id)
        consulta.iniciar(current_user.id)
        db.session.add(consulta)
        db.session.commit()
    
    # Obtener datos de la cita para la sala
    paciente = cita.paciente
    medico = cita.medico
    especialidad = cita.especialidad
    centro = cita.centro_medico
    
    return render_template('sala/medico.html',
                         sala=sala,
                         cita=cita,
                         consulta=consulta,
                         paciente=paciente,
                         medico=medico,
                         especialidad=especialidad,
                         centro=centro,
                         tipo_usuario='medico')


@sala_bp.route('/paciente/<token>')
@login_required
def paciente(token):
    """Vista para que el paciente acceda a la sala virtual."""
    # Verificar que el usuario es paciente
    if not current_user.es_paciente:
        flash('Acceso denegado. Se requieren permisos de paciente.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Buscar la sala virtual por token de paciente
    sala = SalaVirtual.query.filter_by(token_paciente=token).first()
    
    if not sala:
        flash('Sala virtual no encontrada.', 'danger')
        return redirect(url_for('paciente.citas'))
    
    # Verificar que la cita pertenece al paciente actual
    cita = sala.cita
    if cita.paciente_id != current_user.paciente.usuario_id:
        flash('No tiene permiso para acceder a esta sala.', 'danger')
        return redirect(url_for('paciente.citas'))
    
    # Verificar el estado de la sala
    if sala.estado == 'cerrada':
        flash('Esta sala ya ha sido cerrada.', 'warning')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    # Obtener datos de la cita para la sala
    paciente = cita.paciente
    medico = cita.medico
    especialidad = cita.especialidad
    centro = cita.centro_medico
    
    # Obtener consulta si existe
    consulta = cita.consulta
    
    return render_template('sala/paciente.html',
                         sala=sala,
                         cita=cita,
                         consulta=consulta,
                         paciente=paciente,
                         medico=medico,
                         especialidad=especialidad,
                         centro=centro,
                         tipo_usuario='paciente')


@sala_bp.route('/api/status/<int:sala_id>')
@login_required
def estado_sala(sala_id):
    """API para obtener el estado actual de la sala."""
    # Buscar la sala virtual
    sala = SalaVirtual.query.get_or_404(sala_id)
    
    # Verificar permiso
    cita = sala.cita
    tiene_permiso = (
        (current_user.es_medico and current_user.medico.usuario_id == cita.medico_id) or
        (current_user.es_paciente and current_user.paciente.usuario_id == cita.paciente_id)
    )
    
    if not tiene_permiso:
        abort(403)
    
    # Obtener estado actual
    if video_conference_manager:
        estado = video_conference_manager.get_room_status(sala_id)
        if estado:
            return jsonify(estado)
    
    # Si no hay gestor o la sala no existe en el gestor
    return jsonify({
        'id': sala.id,
        'estado': sala.estado,
        'inicio': sala.fecha_inicio,
        'fin': sala.fecha_fin,
        'participantes': [],
        'mensajes_count': 0,
        'duracion_maxima': sala.duracion_maxima,
        'grabacion_activa': False
    })


@sala_bp.route('/api/finalizar/<int:sala_id>', methods=['POST'])
@login_required
def finalizar_sala(sala_id):
    """API para finalizar la sala virtual."""
    # Buscar la sala virtual
    sala = SalaVirtual.query.get_or_404(sala_id)
    
    # Verificar permiso (solo el médico puede finalizar)
    cita = sala.cita
    if not current_user.es_medico or current_user.medico.usuario_id != cita.medico_id:
        abort(403)
    
    # Finalizar la sala
    sala.cerrar()
    db.session.commit()
    
    # Si hay consulta, finalizarla también
    if cita.consulta and not cita.consulta.fecha_fin:
        cita.consulta.finalizar()
        cita.completar()
        db.session.commit()
    
    # Notificar al gestor de videoconferencia
    if video_conference_manager:
        video_conference_manager.end_room(sala_id)
    
    return jsonify({'success': True})