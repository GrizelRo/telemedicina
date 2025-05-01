from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask import current_app, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import uuid

from app.models.cita import Cita, Disponibilidad, SalaVirtual
from app.models.consulta import Consulta
from app.models.tipos_usuario import Medico, Especialidad, CentroMedico
from app.forms.cita import (AgendarCitaForm, BuscarHorariosForm, RegistrarDisponibilidadForm,
                         CancelarCitaForm, ReprogramarCitaForm)
from app.extensions import db
from app.utils.decorators import paciente_required, medico_required, validar_propiedad_cita
from app.utils.email import enviar_notificacion_cita, enviar_notificacion_cancelacion
from app.utils.security import generar_token

# Crear el blueprint de citas
cita_bp = Blueprint('cita', __name__)

@cita_bp.route('/agendar', methods=['GET', 'POST'])
@login_required
@paciente_required
def agendar():
    """Vista para agendar una nueva cita médica."""
    form = AgendarCitaForm()
    
    # Cargar las especialidades para el select
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    form.especialidad_id.choices = [(e.id, e.nombre) for e in especialidades]
    
    # Si es una petición GET, mostrar formulario vacío
    if request.method == 'GET':
        # Inicio con centros médicos vacíos
        form.centro_medico_id.choices = [('', 'Seleccione una especialidad primero')]
        form.medico_id.choices = [('', 'Seleccione un centro médico primero')]
        form.horario.choices = [('', 'Seleccione un médico primero')]
        
        # Si hay parámetros en la URL, prellenar el formulario
        especialidad_id = request.args.get('especialidad_id', type=int)
        centro_id = request.args.get('centro_id', type=int)
        medico_id = request.args.get('medico_id', type=int)
        fecha = request.args.get('fecha')
        
        if especialidad_id:
            form.especialidad_id.data = especialidad_id
            # Cargar centros médicos que ofrecen esta especialidad
            centros = CentroMedico.query.join(CentroMedico.especialidades)\
                                .filter_by(especialidad_id=especialidad_id, disponible=True)\
                                .filter(CentroMedico.activo==True)\
                                .order_by(CentroMedico.nombre).all()
            form.centro_medico_id.choices = [(c.id, c.nombre) for c in centros]
            
            if centro_id:
                form.centro_medico_id.data = centro_id
                # Cargar médicos disponibles
                medicos = Medico.query.join(Medico.centros_medicos)\
                              .filter_by(id=centro_id)\
                              .filter(Medico.especialidad_id==especialidad_id, 
                                     Medico.disponible==True)\
                              .join(Medico.usuario)\
                              .filter(Medico.usuario.has(activo=True))\
                              .all()
                form.medico_id.choices = [(m.usuario_id, m.usuario.nombre_completo) for m in medicos]
                
                if medico_id:
                    form.medico_id.data = medico_id
                    # Cargar fecha si está disponible
                    if fecha:
                        try:
                            form.fecha.data = datetime.strptime(fecha, '%Y-%m-%d').date()
                            # Cargar horarios disponibles
                            horarios = obtener_horarios_disponibles(medico_id, centro_id, form.fecha.data)
                            if horarios:
                                form.horario.choices = [(h.strftime('%H:%M'), h.strftime('%H:%M')) for h in horarios]
                            else:
                                form.horario.choices = [('', 'No hay horarios disponibles para esta fecha')]
                        except ValueError:
                            # Si la fecha no es válida, ignorarla
                            pass
    
    # Si es una petición POST, procesar el formulario
    if form.validate_on_submit():
        # Verificar nuevamente que el horario esté disponible
        fecha_hora = datetime.strptime(
            f"{form.fecha.data} {form.horario.data}", 
            '%Y-%m-%d %H:%M'
        )
        
        # Verificar si ya existe una cita para este médico y horario
        cita_existente = Cita.query.filter_by(
            medico_id=form.medico_id.data,
            fecha_hora=fecha_hora,
            estado=['pendiente', 'confirmada', 'en_curso']
        ).first()
        
        if cita_existente:
            flash('Este horario ya no está disponible. Por favor seleccione otro.', 'danger')
            return redirect(url_for('cita.agendar'))
        
        # Crear la nueva cita
        cita = Cita(
            paciente_id=current_user.paciente.usuario_id,
            medico_id=form.medico_id.data,
            centro_medico_id=form.centro_medico_id.data,
            especialidad_id=form.especialidad_id.data,
            fecha_hora=fecha_hora,
            tipo=form.tipo.data,
            motivo=form.motivo.data,
            estado='pendiente'
        )
        
        # Crear la sala virtual para la cita
        sala = SalaVirtual(
            token_medico=str(uuid.uuid4()),
            token_paciente=str(uuid.uuid4()),
            url=f"/sala/{uuid.uuid4()}",
            cita=cita
        )
        
        # Guardar en la base de datos
        db.session.add(cita)
        db.session.add(sala)
        db.session.commit()
        
        # Enviar notificaciones
        enviar_notificacion_cita(cita)
        
        flash('Cita agendada exitosamente. Recibirá un correo de confirmación.', 'success')
        return redirect(url_for('paciente.citas'))
    
    return render_template('cita/agendar.html', form=form)


@cita_bp.route('/horarios-disponibles', methods=['POST'])
@login_required
def horarios_disponibles():
    """Vista AJAX para obtener los horarios disponibles de un médico en una fecha específica."""
    medico_id = request.form.get('medico_id', type=int)
    centro_id = request.form.get('centro_id', type=int)
    fecha_str = request.form.get('fecha')
    
    if not medico_id or not centro_id or not fecha_str:
        return jsonify({'error': 'Parámetros incompletos'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido'}), 400
    
    # Obtener horarios disponibles
    horarios = obtener_horarios_disponibles(medico_id, centro_id, fecha)
    
    # Formatear horarios para JSON
    horarios_json = [h.strftime('%H:%M') for h in horarios]
    
    return jsonify({'horarios': horarios_json})


@cita_bp.route('/centros-por-especialidad/<int:especialidad_id>', methods=['GET'])
@login_required
def centros_por_especialidad(especialidad_id):
    """Vista AJAX para obtener los centros médicos que ofrecen una especialidad."""
    centros = CentroMedico.query.join(CentroMedico.especialidades)\
                        .filter_by(especialidad_id=especialidad_id, disponible=True)\
                        .filter(CentroMedico.activo==True)\
                        .order_by(CentroMedico.nombre).all()
    
    centros_json = [{'id': c.id, 'nombre': c.nombre} for c in centros]
    
    return jsonify({'centros': centros_json})


@cita_bp.route('/medicos-por-centro/<int:especialidad_id>/<int:centro_id>', methods=['GET'])
@login_required
def medicos_por_centro(especialidad_id, centro_id):
    """Vista AJAX para obtener los médicos disponibles en un centro para una especialidad."""
    medicos = Medico.query.join(Medico.centros_medicos)\
                    .filter_by(id=centro_id)\
                    .filter(Medico.especialidad_id==especialidad_id, 
                           Medico.disponible==True)\
                    .join(Medico.usuario)\
                    .filter(Medico.usuario.has(activo=True))\
                    .all()
    
    medicos_json = [
        {
            'id': m.usuario_id, 
            'nombre': m.usuario.nombre_completo,
            'especialidad': m.especialidad.nombre
        } 
        for m in medicos
    ]
    
    return jsonify({'medicos': medicos_json})


@cita_bp.route('/disponibilidad', methods=['GET', 'POST'])
@login_required
@medico_required
def registrar_disponibilidad():
    """Vista para que los médicos registren su disponibilidad."""
    form = RegistrarDisponibilidadForm()
    
    # Cargar centros médicos donde trabaja el médico
    centros = CentroMedico.query.join(CentroMedico.medicos)\
                        .filter_by(usuario_id=current_user.medico.usuario_id)\
                        .filter(CentroMedico.activo==True)\
                        .order_by(CentroMedico.nombre).all()
    
    form.centro_medico_id.choices = [(c.id, c.nombre) for c in centros]
    
    if form.validate_on_submit():
        # Convertir días de la semana a enteros
        dias_semana = [int(d) for d in form.dias_semana.data]
        
        # Convertir fechas a objetos date
        fecha_inicio = form.fecha_inicio.data
        fecha_fin = form.fecha_fin.data
        
        # Obtener intervalo de citas
        intervalo_citas = int(form.intervalo_citas.data)
        
        # Obtener máximo de citas (si se especificó)
        citas_maximas = int(form.citas_maximas.data) if form.citas_maximas.data else 0
        
        # Iterar por cada día en el rango de fechas
        fecha_actual = fecha_inicio
        dias_creados = 0
        
        while fecha_actual <= fecha_fin:
            # Verificar si este día de la semana está seleccionado
            if fecha_actual.weekday() in dias_semana:
                # Verificar si ya existe disponibilidad para este día
                disponibilidad_existente = Disponibilidad.query.filter_by(
                    medico_id=current_user.medico.usuario_id,
                    centro_medico_id=form.centro_medico_id.data,
                    fecha=fecha_actual,
                    hora_inicio=form.hora_inicio.data,
                    hora_fin=form.hora_fin.data
                ).first()
                
                if not disponibilidad_existente:
                    # Crear nueva disponibilidad
                    disponibilidad = Disponibilidad(
                        medico_id=current_user.medico.usuario_id,
                        centro_medico_id=form.centro_medico_id.data,
                        fecha=fecha_actual,
                        hora_inicio=form.hora_inicio.data,
                        hora_fin=form.hora_fin.data,
                        intervalo_citas=intervalo_citas,
                        citas_maximas=citas_maximas
                    )
                    
                    db.session.add(disponibilidad)
                    dias_creados += 1
            
            # Avanzar al siguiente día
            fecha_actual += timedelta(days=1)
        
        db.session.commit()
        
        flash(f'Disponibilidad registrada exitosamente para {dias_creados} días.', 'success')
        return redirect(url_for('medico.horarios'))
    
    return render_template('cita/registrar_disponibilidad.html', form=form)


@cita_bp.route('/buscar-horarios', methods=['GET', 'POST'])
@login_required
@paciente_required
def buscar_horarios():
    """Vista para buscar horarios disponibles."""
    form = BuscarHorariosForm()
    
    # Cargar las especialidades para el select
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    form.especialidad_id.choices = [(e.id, e.nombre) for e in especialidades]
    
    # Agregar opción vacía para centro y médico
    form.centro_medico_id.choices = [('', 'Todos los centros')] + [
        (c.id, c.nombre) for c in CentroMedico.query.filter_by(activo=True).order_by(CentroMedico.nombre).all()
    ]
    
    form.medico_id.choices = [('', 'Todos los médicos')]
    
    # Inicializar resultados vacíos
    resultados = []
    
    if form.validate_on_submit():
        # Buscar disponibilidad según los criterios
        query = Disponibilidad.query.filter(
            Disponibilidad.fecha >= form.fecha_inicio.data,
            Disponibilidad.fecha <= form.fecha_fin.data
        )
        
        # Filtrar por médico si se especificó
        if form.medico_id.data:
            query = query.filter_by(medico_id=form.medico_id.data)
        else:
            # Si no se especificó médico, filtrar por especialidad
            query = query.join(Disponibilidad.medico).filter_by(especialidad_id=form.especialidad_id.data)
        
        # Filtrar por centro médico si se especificó
        if form.centro_medico_id.data:
            query = query.filter_by(centro_medico_id=form.centro_medico_id.data)
        
        # Ejecutar la consulta
        disponibilidades = query.order_by(Disponibilidad.fecha, Disponibilidad.hora_inicio).all()
        
        # Procesar resultados
        for disp in disponibilidades:
            # Obtener horarios disponibles para esta disponibilidad
            horarios = disp.generar_horarios_disponibles()
            
            if horarios:
                medico = disp.medico
                centro = disp.centro_medico
                
                for horario in horarios:
                    resultados.append({
                        'fecha': disp.fecha,
                        'hora': horario.time(),
                        'medico_id': medico.usuario_id,
                        'medico_nombre': medico.usuario.nombre_completo,
                        'especialidad': medico.especialidad.nombre,
                        'centro_id': centro.id,
                        'centro_nombre': centro.nombre
                    })
    
    return render_template('cita/buscar_horarios.html', form=form, resultados=resultados)


@cita_bp.route('/detalle/<int:cita_id>', methods=['GET'])
@login_required
@validar_propiedad_cita
def detalle(cita_id):
    """Vista para ver los detalles de una cita."""
    cita = Cita.query.get_or_404(cita_id)
    return render_template('cita/detalle.html', cita=cita)


@cita_bp.route('/cancelar/<int:cita_id>', methods=['GET', 'POST'])
@login_required
@validar_propiedad_cita
def cancelar(cita_id):
    """Vista para cancelar una cita."""
    cita = Cita.query.get_or_404(cita_id)
    
    # Verificar si la cita puede ser cancelada
    if not cita.puede_cancelar:
        flash('Esta cita no puede ser cancelada.', 'danger')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    form = CancelarCitaForm()
    form.cita_id.data = cita.id
    
    if form.validate_on_submit():
        # Cancelar la cita
        if cita.cancelar(current_user.id, form.motivo_cancelacion.data):
            db.session.commit()
            
            # Enviar notificaciones
            enviar_notificacion_cancelacion(cita, form.motivo_cancelacion.data, current_user.id)
            
            flash('Cita cancelada exitosamente.', 'success')
            
            # Redireccionar según el rol
            if current_user.es_paciente:
                return redirect(url_for('paciente.citas'))
            elif current_user.es_medico:
                return redirect(url_for('medico.citas'))
            else:
                return redirect(url_for('cita.detalle', cita_id=cita.id))
        else:
            flash('No se pudo cancelar la cita.', 'danger')
    
    return render_template('cita/cancelar.html', form=form, cita=cita)


@cita_bp.route('/reprogramar/<int:cita_id>', methods=['GET', 'POST'])
@login_required
@validar_propiedad_cita
def reprogramar(cita_id):
    """Vista para reprogramar una cita."""
    cita = Cita.query.get_or_404(cita_id)
    
    # Verificar si la cita puede ser reprogramada
    if not cita.puede_reprogramar:
        flash('Esta cita no puede ser reprogramada.', 'danger')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    form = ReprogramarCitaForm()
    form.cita_id.data = cita.id
    
    if request.method == 'GET':
        # Inicializar el select de horarios como vacío
        form.horario.choices = [('', 'Seleccione una fecha primero')]
    
    if form.validate_on_submit():
        # Verificar disponibilidad del nuevo horario
        fecha_hora = datetime.strptime(
            f"{form.fecha.data} {form.horario.data}", 
            '%Y-%m-%d %H:%M'
        )
        
        # Verificar si ya existe una cita para este médico y horario
        cita_existente = Cita.query.filter(
            Cita.medico_id == cita.medico_id,
            Cita.fecha_hora == fecha_hora,
            Cita.estado.in_(['pendiente', 'confirmada', 'en_curso']),
            Cita.id != cita.id  # Excluir la cita actual
        ).first()
        
        if cita_existente:
            flash('Este horario ya no está disponible. Por favor seleccione otro.', 'danger')
            return redirect(url_for('cita.reprogramar', cita_id=cita.id))
        
        # Registrar motivo de reprogramación
        notas_anteriores = cita.notas or ""
        cita.notas = f"{notas_anteriores}\n[{datetime.now()}] Reprogramación: {form.motivo_reprogramacion.data}"
        
        # Reprogramar la cita
        if cita.reprogramar(fecha_hora):
            db.session.commit()
            
            # Enviar notificaciones
            # Aquí debería enviarse una notificación de reprogramación
            
            flash('Cita reprogramada exitosamente.', 'success')
            
            # Redireccionar según el rol
            if current_user.es_paciente:
                return redirect(url_for('paciente.citas'))
            elif current_user.es_medico:
                return redirect(url_for('medico.citas'))
            else:
                return redirect(url_for('cita.detalle', cita_id=cita.id))
        else:
            flash('No se pudo reprogramar la cita.', 'danger')
    
    return render_template('cita/reprogramar.html', form=form, cita=cita)


@cita_bp.route('/confirmar/<int:cita_id>', methods=['POST'])
@login_required
@medico_required
@validar_propiedad_cita
def confirmar(cita_id):
    """Vista para confirmar una cita (solo médicos)."""
    cita = Cita.query.get_or_404(cita_id)
    
    # Verificar que la cita esté pendiente
    if cita.estado != 'pendiente':
        flash('Esta cita no puede ser confirmada.', 'danger')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    # Confirmar la cita
    if cita.confirmar():
        db.session.commit()
        
        # Enviar notificación de confirmación
        # Aquí debería enviarse una notificación de confirmación
        
        flash('Cita confirmada exitosamente.', 'success')
    else:
        flash('No se pudo confirmar la cita.', 'danger')
    
    return redirect(url_for('medico.citas'))


@cita_bp.route('/iniciar/<int:cita_id>', methods=['GET'])
@login_required
@validar_propiedad_cita
def iniciar_sala(cita_id):
    """Vista para iniciar la sala virtual de una cita."""
    cita = Cita.query.get_or_404(cita_id)
    
    # Verificar que la cita esté confirmada y sea hoy
    if cita.estado != 'confirmada':
        flash('Esta cita no puede ser iniciada.', 'danger')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    # Verificar la fecha (10 minutos antes hasta 10 minutos después)
    ahora = datetime.now()
    tiempo_minimo = cita.fecha_hora - timedelta(minutes=10)
    tiempo_maximo = cita.fecha_hora + timedelta(minutes=10)
    
    if not (tiempo_minimo <= ahora <= tiempo_maximo):
        flash('La sala virtual solo puede ser iniciada 10 minutos antes o después de la hora programada.', 'warning')
        return redirect(url_for('cita.detalle', cita_id=cita.id))
    
    # Iniciar la cita y la sala virtual
    cita.iniciar()
    if cita.sala_virtual:
        cita.sala_virtual.activar()
    
    db.session.commit()
    
    # Redireccionar a la sala virtual según el rol
    if current_user.es_medico:
        return redirect(url_for('sala.medico', token=cita.sala_virtual.token_medico))
    else:
        return redirect(url_for('sala.paciente', token=cita.sala_virtual.token_paciente))


def obtener_horarios_disponibles(medico_id, centro_id, fecha):
    """
    Función auxiliar para obtener los horarios disponibles de un médico en una fecha específica.
    
    Args:
        medico_id: ID del médico
        centro_id: ID del centro médico
        fecha: Fecha para la que se buscan horarios
        
    Returns:
        list: Lista de objetos datetime con los horarios disponibles
    """
    # Buscar disponibilidades del médico para esta fecha y centro
    disponibilidades = Disponibilidad.query.filter_by(
        medico_id=medico_id,
        centro_medico_id=centro_id,
        fecha=fecha
    ).all()
    
    # Si no hay disponibilidades, retornar lista vacía
    if not disponibilidades:
        return []
    
    # Obtener todos los horarios disponibles de todas las disponibilidades
    todos_horarios = []
    for disponibilidad in disponibilidades:
        todos_horarios.extend(disponibilidad.generar_horarios_disponibles())
    
    # Ordenar horarios
    todos_horarios.sort()
    
    return todos_horarios