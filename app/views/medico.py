from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from app.models.tipos_usuario import Medico, Paciente, Especialidad, CentroMedico
from app.models.cita import Cita, Disponibilidad
from app.models.consulta import Consulta
from app.models.documentos import RecetaMedica, OrdenLaboratorio
from app.forms.cita import RegistrarDisponibilidadForm, CancelarCitaForm
from app.forms.consulta import IniciarConsultaForm, RegistrarConsultaForm
from app.extensions import db
from app.utils.decorators import medico_required

# Crear el blueprint de médico
medico_bp = Blueprint('medico', __name__)

@medico_bp.route('/')
@login_required
@medico_required
def inicio():
    """Vista principal del panel de médico."""
    today = date.today()
    
    # Obtener citas de hoy
    citas_hoy = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id
    ).filter(
        db.func.date(Cita.fecha_hora) == today,
        Cita.estado.in_(['pendiente', 'confirmada', 'en_curso'])
    ).order_by(Cita.fecha_hora).all()
    
    # Obtener próximas citas (no de hoy)
    citas_proximas = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id
    ).filter(
        db.func.date(Cita.fecha_hora) > today,
        Cita.estado.in_(['pendiente', 'confirmada'])
    ).order_by(Cita.fecha_hora).limit(5).all()
    
    # Obtener consultas pendientes de completar
    consultas_pendientes = Consulta.query.join(Consulta.cita).filter(
        Cita.medico_id == current_user.medico.usuario_id,
        Consulta.fecha_inicio != None,
        Consulta.fecha_fin == None
    ).all()
    
    # Obtener estadísticas básicas
    total_citas = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id
    ).count()
    
    citas_completadas = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        estado='completada'
    ).count()
    
    total_consultas = Consulta.query.join(Consulta.cita).filter(
        Cita.medico_id == current_user.medico.usuario_id,
        Consulta.fecha_fin != None
    ).count()
    
    total_recetas = RecetaMedica.query.filter_by(
        medico_id=current_user.medico.usuario_id
    ).count()
    
    return render_template(
        'medico/inicio.html',
        citas_hoy=citas_hoy,
        citas_proximas=citas_proximas,
        consultas_pendientes=consultas_pendientes,
        total_citas=total_citas,
        citas_completadas=citas_completadas,
        total_consultas=total_consultas,
        total_recetas=total_recetas
    )

@medico_bp.route('/citas')
@login_required
@medico_required
def citas():
    """Vista para listar todas las citas del médico."""
    # Obtener parámetros de filtro
    estado = request.args.get('estado', 'todas')
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    
    # Procesar fechas
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        else:
            fecha_inicio = date.today() - timedelta(days=30)
        
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        else:
            fecha_fin = date.today() + timedelta(days=30)
    except ValueError:
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today() + timedelta(days=30)
    
    # Consulta base
    query = Cita.query.filter_by(medico_id=current_user.medico.usuario_id)
    
    # Aplicar filtros
    if estado != 'todas':
        query = query.filter_by(estado=estado)
    
    query = query.filter(
        db.func.date(Cita.fecha_hora) >= fecha_inicio,
        db.func.date(Cita.fecha_hora) <= fecha_fin
    )
    
    # Ordenar
    citas = query.order_by(Cita.fecha_hora).all()
    
    return render_template('medico/citas.html', 
                         citas=citas, 
                         estado_actual=estado,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

@medico_bp.route('/horarios', methods=['GET', 'POST'])
@login_required
@medico_required
def horarios():
    """Vista para gestionar los horarios de disponibilidad."""
    # Si es POST, redirigir a la vista de registro de disponibilidad
    if request.method == 'POST':
        return redirect(url_for('cita.registrar_disponibilidad'))
    
    # Obtener fechas de filtro
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    
    # Procesar fechas
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        else:
            fecha_inicio = date.today()
        
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        else:
            fecha_fin = date.today() + timedelta(days=30)
    except ValueError:
        fecha_inicio = date.today()
        fecha_fin = date.today() + timedelta(days=30)
    
    # Obtener disponibilidades
    disponibilidades = Disponibilidad.query.filter_by(
        medico_id=current_user.medico.usuario_id
    ).filter(
        Disponibilidad.fecha >= fecha_inicio,
        Disponibilidad.fecha <= fecha_fin
    ).order_by(Disponibilidad.fecha, Disponibilidad.hora_inicio).all()
    
    # Obtener formulario para nueva disponibilidad
    form = RegistrarDisponibilidadForm()
    
    # Cargar centros médicos donde trabaja el médico
    centros = CentroMedico.query.join(CentroMedico.medicos)\
                        .filter_by(usuario_id=current_user.medico.usuario_id)\
                        .filter(CentroMedico.activo==True)\
                        .order_by(CentroMedico.nombre).all()
    
    form.centro_medico_id.choices = [(c.id, c.nombre) for c in centros]
    
    return render_template('medico/horarios.html', 
                         disponibilidades=disponibilidades,
                         form=form,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin)

@medico_bp.route('/pacientes')
@login_required
@medico_required
def pacientes():
    """Vista para listar los pacientes atendidos por el médico."""
    # Obtener pacientes únicos atendidos
    pacientes_ids = db.session.query(Cita.paciente_id).filter_by(
        medico_id=current_user.medico.usuario_id,
        estado='completada'
    ).distinct().all()
    
    pacientes_ids = [p[0] for p in pacientes_ids]
    
    # Obtener información de los pacientes
    pacientes = Paciente.query.filter(Paciente.usuario_id.in_(pacientes_ids)).all()
    
    # Para cada paciente, obtener la última consulta
    pacientes_data = []
    for paciente in pacientes:
        ultima_cita = Cita.query.filter_by(
            medico_id=current_user.medico.usuario_id,
            paciente_id=paciente.usuario_id,
            estado='completada'
        ).order_by(Cita.fecha_hora.desc()).first()
        
        ultima_consulta = None
        if ultima_cita:
            ultima_consulta = Consulta.query.filter_by(cita_id=ultima_cita.id).first()
        
        pacientes_data.append({
            'paciente': paciente,
            'ultima_cita': ultima_cita,
            'ultima_consulta': ultima_consulta
        })
    
    return render_template('medico/pacientes.html', pacientes_data=pacientes_data)

@medico_bp.route('/paciente/<int:paciente_id>')
@login_required
@medico_required
def ver_paciente(paciente_id):
    """Vista para ver la información de un paciente."""
    # Obtener el paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Verificar que el médico ha atendido a este paciente
    ha_atendido = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        paciente_id=paciente.usuario_id,
        estado='completada'
    ).first() is not None
    
    if not ha_atendido:
        flash('No tiene permiso para ver la información de este paciente.', 'danger')
        return redirect(url_for('medico.pacientes'))
    
    # Obtener historial de citas
    citas = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        paciente_id=paciente.usuario_id
    ).order_by(Cita.fecha_hora.desc()).all()
    
    # Obtener consultas
    consultas = []
    for cita in citas:
        consulta = Consulta.query.filter_by(cita_id=cita.id).first()
        if consulta:
            consultas.append(consulta)
    
    # Obtener recetas emitidas
    recetas = RecetaMedica.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        paciente_id=paciente.usuario_id
    ).order_by(RecetaMedica.fecha_emision.desc()).all()
    
    # Obtener órdenes emitidas
    ordenes = OrdenLaboratorio.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        paciente_id=paciente.usuario_id
    ).order_by(OrdenLaboratorio.fecha_emision.desc()).all()
    
    return render_template('medico/ver_paciente.html',
                         paciente=paciente,
                         citas=citas,
                         consultas=consultas,
                         recetas=recetas,
                         ordenes=ordenes)

@medico_bp.route('/eliminar-disponibilidad/<int:disponibilidad_id>', methods=['POST'])
@login_required
@medico_required
def eliminar_disponibilidad(disponibilidad_id):
    """Vista para eliminar una disponibilidad."""
    disponibilidad = Disponibilidad.query.get_or_404(disponibilidad_id)
    
    # Verificar que la disponibilidad pertenece al médico actual
    if disponibilidad.medico_id != current_user.medico.usuario_id:
        flash('No tiene permiso para eliminar esta disponibilidad.', 'danger')
        return redirect(url_for('medico.horarios'))
    
    # Verificar que no existan citas para esta disponibilidad
    fecha = disponibilidad.fecha
    hora_inicio = disponibilidad.hora_inicio
    hora_fin = disponibilidad.hora_fin
    
    # Crear rango de horas para verificar conflictos
    hora_inicio_dt = datetime.combine(fecha, hora_inicio)
    hora_fin_dt = datetime.combine(fecha, hora_fin)
    
    # Buscar citas en este horario
    citas_existentes = Cita.query.filter_by(
        medico_id=current_user.medico.usuario_id,
        centro_medico_id=disponibilidad.centro_medico_id
    ).filter(
        Cita.fecha_hora >= hora_inicio_dt,
        Cita.fecha_hora < hora_fin_dt,
        Cita.estado.in_(['pendiente', 'confirmada', 'en_curso'])
    ).all()
    
    if citas_existentes:
        flash('No se puede eliminar esta disponibilidad porque ya existen citas programadas.', 'danger')
        return redirect(url_for('medico.horarios'))
    
    # Eliminar la disponibilidad
    db.session.delete(disponibilidad)
    db.session.commit()
    
    flash('Disponibilidad eliminada exitosamente.', 'success')
    return redirect(url_for('medico.horarios'))

@medico_bp.route('/consultas')
@login_required
@medico_required
def consultas():
    """Vista para listar las consultas realizadas por el médico."""
    # Obtener parámetros de filtro
    estado = request.args.get('estado', 'todas')
    
    # Consulta base
    query = Consulta.query.join(Consulta.cita).filter(
        Cita.medico_id == current_user.medico.usuario_id
    )
    
    # Aplicar filtros
    if estado == 'pendientes':
        # Consultas iniciadas pero no finalizadas
        query = query.filter(
            Consulta.fecha_inicio != None,
            Consulta.fecha_fin == None
        )
    elif estado == 'finalizadas':
        # Consultas finalizadas
        query = query.filter(Consulta.fecha_fin != None)
    
    # Ordenar
    consultas = query.order_by(Consulta.fecha_inicio.desc()).all()
    
    return render_template('medico/consultas.html', 
                         consultas=consultas, 
                         estado_actual=estado)

@medico_bp.route('/iniciar-consulta/<int:cita_id>', methods=['GET', 'POST'])
@login_required
@medico_required
def iniciar_consulta(cita_id):
    """Vista para iniciar una consulta."""
    # Redirigir a la vista de inicio de consulta en el blueprint de consulta
    return redirect(url_for('consulta.iniciar', cita_id=cita_id))

@medico_bp.route('/recetas')
@login_required
@medico_required
def recetas():
    """Vista para listar las recetas emitidas por el médico."""
    # Obtener todas las recetas emitidas por el médico
    recetas = RecetaMedica.query.filter_by(medico_id=current_user.medico.usuario_id)\
                        .order_by(RecetaMedica.fecha_emision.desc()).all()
    
    return render_template('medico/recetas.html', recetas=recetas)

@medico_bp.route('/ordenes')
@login_required
@medico_required
def ordenes():
    """Vista para listar las órdenes de laboratorio emitidas por el médico."""
    # Obtener todas las órdenes emitidas por el médico
    ordenes = OrdenLaboratorio.query.filter_by(medico_id=current_user.medico.usuario_id)\
                              .order_by(OrdenLaboratorio.fecha_emision.desc()).all()
    
    return render_template('medico/ordenes.html', ordenes=ordenes)