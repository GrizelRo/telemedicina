from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from app.models.tipos_usuario import Paciente, Medico, Especialidad, CentroMedico
from app.models.cita import Cita
from app.models.documentos import RecetaMedica, OrdenLaboratorio
from app.forms.cita import AgendarCitaForm, BuscarHorariosForm, CancelarCitaForm, ReprogramarCitaForm
from app.extensions import db
from app.utils.decorators import paciente_required

# Crear el blueprint de paciente
paciente_bp = Blueprint('paciente', __name__)

@paciente_bp.route('/')
@login_required
@paciente_required
def inicio():
    """Vista principal del panel de paciente."""
    # Obtener próximas citas
    citas_proximas = Cita.query.filter_by(
        paciente_id=current_user.paciente.usuario_id,
        estado=['pendiente', 'confirmada']
    ).filter(
        Cita.fecha_hora > datetime.now()
    ).order_by(Cita.fecha_hora).limit(5).all()
    
    # Obtener citas pasadas
    citas_pasadas = Cita.query.filter_by(
        paciente_id=current_user.paciente.usuario_id,
        estado='completada'
    ).order_by(Cita.fecha_hora.desc()).limit(3).all()
    
    # Obtener últimas recetas
    recetas = RecetaMedica.query.filter_by(
        paciente_id=current_user.paciente.usuario_id,
        estado='activo'
    ).order_by(RecetaMedica.fecha_emision.desc()).limit(3).all()
    
    # Obtener últimas órdenes
    ordenes = OrdenLaboratorio.query.filter_by(
        paciente_id=current_user.paciente.usuario_id,
        estado='activo'
    ).order_by(OrdenLaboratorio.fecha_emision.desc()).limit(3).all()
    
    return render_template(
        'paciente/inicio.html',
        citas_proximas=citas_proximas,
        citas_pasadas=citas_pasadas,
        recetas=recetas,
        ordenes=ordenes
    )

@paciente_bp.route('/citas')
@login_required
@paciente_required
def citas():
    """Vista para listar todas las citas del paciente."""
    # Obtener parámetros de filtro
    estado = request.args.get('estado', 'todas')
    
    # Consulta base
    query = Cita.query.filter_by(paciente_id=current_user.paciente.usuario_id)
    
    # Aplicar filtros
    if estado == 'proximas':
        query = query.filter(
            Cita.estado.in_(['pendiente', 'confirmada']),
            Cita.fecha_hora > datetime.now()
        )
    elif estado == 'pasadas':
        query = query.filter(
            Cita.estado.in_(['completada', 'cancelada']),
            Cita.fecha_hora <= datetime.now()
        )
    elif estado == 'pendientes':
        query = query.filter_by(estado='pendiente')
    elif estado == 'confirmadas':
        query = query.filter_by(estado='confirmada')
    elif estado == 'completadas':
        query = query.filter_by(estado='completada')
    elif estado == 'canceladas':
        query = query.filter_by(estado='cancelada')
    
    # Ordenar
    citas = query.order_by(Cita.fecha_hora.desc()).all()
    
    return render_template('paciente/citas.html', citas=citas, estado_actual=estado)

@paciente_bp.route('/agendar-cita', methods=['GET', 'POST'])
@login_required
@paciente_required
def agendar_cita():
    """Vista para agendar una nueva cita."""
    # Redirigir a la vista de agendamiento en el blueprint de citas
    return redirect(url_for('cita.agendar'))

@paciente_bp.route('/buscar-horarios', methods=['GET', 'POST'])
@login_required
@paciente_required
def buscar_horarios():
    """Vista para buscar horarios disponibles."""
    # Redirigir a la vista de búsqueda de horarios en el blueprint de citas
    return redirect(url_for('cita.buscar_horarios'))

@paciente_bp.route('/historial')
@login_required
@paciente_required
def historial():
    """Vista para ver el historial clínico del paciente."""
    from app.models.historial_clinico import HistorialClinico
    
    # Obtener el historial clínico
    historial = HistorialClinico.query.filter_by(paciente_id=current_user.paciente.usuario_id).first()
    
    # Si no existe, crear uno nuevo
    if not historial:
        historial = HistorialClinico(paciente_id=current_user.paciente.usuario_id)
        db.session.add(historial)
        db.session.commit()
    
    # Obtener registros del historial
    registros = historial.obtener_registros_recientes(20)
    
    # Obtener alergias y enfermedades crónicas
    alergias = historial.obtener_alergias()
    enfermedades_cronicas = historial.obtener_enfermedades_cronicas()
    
    return render_template('paciente/historial.html', 
                         historial=historial,
                         registros=registros,
                         alergias=alergias,
                         enfermedades_cronicas=enfermedades_cronicas)

@paciente_bp.route('/recetas')
@login_required
@paciente_required
def recetas():
    """Vista para listar las recetas del paciente."""
    # Obtener todas las recetas del paciente
    recetas = RecetaMedica.query.filter_by(paciente_id=current_user.paciente.usuario_id)\
                        .order_by(RecetaMedica.fecha_emision.desc()).all()
    
    return render_template('paciente/recetas.html', recetas=recetas)

@paciente_bp.route('/ordenes')
@login_required
@paciente_required
def ordenes():
    """Vista para listar las órdenes de laboratorio del paciente."""
    # Obtener todas las órdenes del paciente
    ordenes = OrdenLaboratorio.query.filter_by(paciente_id=current_user.paciente.usuario_id)\
                              .order_by(OrdenLaboratorio.fecha_emision.desc()).all()
    
    return render_template('paciente/ordenes.html', ordenes=ordenes)

@paciente_bp.route('/perfil-medico/<int:medico_id>')
@login_required
@paciente_required
def perfil_medico(medico_id):
    """Vista para ver el perfil de un médico."""
    # Obtener el médico
    medico = Medico.query.get_or_404(medico_id)
    
    # Verificar que el médico esté activo
    if not medico.disponible or not medico.usuario.activo:
        flash('Este médico no está disponible actualmente.', 'warning')
        return redirect(url_for('paciente.inicio'))
    
    # Obtener centros médicos donde atiende
    centros = CentroMedico.query.join(CentroMedico.medicos)\
                         .filter_by(usuario_id=medico_id)\
                         .filter(CentroMedico.activo==True)\
                         .all()
    
    # Obtener especialidad
    especialidad = medico.especialidad
    
    return render_template('paciente/perfil_medico.html', 
                         medico=medico,
                         centros=centros,
                         especialidad=especialidad)


@paciente_bp.route('/centro-medico/<int:centro_id>')
@login_required
@paciente_required
def centro_medico(centro_id):
    """Vista para ver la información de un centro médico."""
    # Obtener el centro médico
    centro = CentroMedico.query.get_or_404(centro_id)
    
    # Verificar que el centro esté activo
    if not centro.activo:
        flash('Este centro médico no está disponible actualmente.', 'warning')
        return redirect(url_for('paciente.inicio'))
    
    # Obtener especialidades disponibles en este centro
    especialidades = Especialidad.query.join(CentroMedico.especialidades)\
                              .filter_by(centro_medico_id=centro_id, disponible=True)\
                              .all()
    
    # Obtener médicos que trabajan en este centro
    medicos = Medico.query.join(Medico.centros_medicos)\
                    .filter_by(id=centro_id)\
                    .join(Medico.usuario)\
                    .filter(Medico.usuario.has(activo=True), Medico.disponible==True)\
                    .all()
    
    return render_template('paciente/centro_medico.html', 
                         centro=centro,
                         especialidades=especialidades,
                         medicos=medicos)