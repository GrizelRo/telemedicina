from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from app.models.tipos_usuario import Medico, Especialidad
from app.models.centro_medico import CentroMedico, EspecialidadCentro
from app.models.cita import Cita
from app.extensions import db
from app.utils.decorators import admin_centro_required

# Crear el blueprint de administrador de centro
admin_centro_bp = Blueprint('admin_centro', __name__)

@admin_centro_bp.route('/')
@login_required
@admin_centro_required
def inicio():
    """Vista principal del panel de administrador de centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Estadísticas del centro
    total_medicos = db.session.query(Medico).join(
        Medico.centros_medicos).filter_by(id=centro.id).count()
    
    total_especialidades = EspecialidadCentro.query.filter_by(
        centro_medico_id=centro.id, disponible=True).count()
    
    # Citas de hoy
    citas_hoy = Cita.query.filter_by(centro_medico_id=centro.id).filter(
        db.func.date(Cita.fecha_hora) == date.today()).all()
    
    # Citas pendientes
    citas_pendientes = Cita.query.filter_by(
        centro_medico_id=centro.id, estado='pendiente').count()
    
    # Citas de los últimos 30 días
    fecha_inicio = date.today() - timedelta(days=30)
    citas_mes = Cita.query.filter_by(centro_medico_id=centro.id).filter(
        db.func.date(Cita.fecha_hora) >= fecha_inicio).count()
    
    return render_template(
        'admin_centro/inicio.html',
        centro=centro,
        total_medicos=total_medicos,
        total_especialidades=total_especialidades,
        citas_hoy=citas_hoy,
        citas_pendientes=citas_pendientes,
        citas_mes=citas_mes
    )

@admin_centro_bp.route('/medicos')
@login_required
@admin_centro_required
def medicos():
    """Vista para gestionar los médicos del centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener parámetros de filtro
    especialidad_id = request.args.get('especialidad_id', type=int)
    estado = request.args.get('estado', 'todos')
    busqueda = request.args.get('busqueda', '')
    
    # Consulta base
    query = db.session.query(Medico).join(Medico.centros_medicos).filter_by(id=centro.id)
    
    # Aplicar filtros
    if especialidad_id:
        query = query.filter(Medico.especialidad_id == especialidad_id)
    
    if estado != 'todos':
        if estado == 'activos':
            query = query.filter(Medico.disponible == True, Medico.usuario.has(activo=True))
        elif estado == 'inactivos':
            query = query.filter(db.or_(Medico.disponible == False, Medico.usuario.has(activo=False)))
    
    if busqueda:
        query = query.filter(
            db.or_(
                Medico.usuario.has(nombre=busqueda),
                Medico.usuario.has(apellido=busqueda),
                Medico.usuario.has(numero_documento=busqueda),
                Medico.usuario.has(email=busqueda),
                Medico.numero_licencia.like(f'%{busqueda}%')
            )
        )
    
    # Ordenar
    medicos = query.all()
    
    # Obtener especialidades para el filtro
    especialidades = Especialidad.query.join(EspecialidadCentro).filter_by(
        centro_medico_id=centro.id, disponible=True).all()
    
    return render_template(
        'admin_centro/medicos.html',
        centro=centro,
        medicos=medicos,
        especialidades=especialidades,
        especialidad_actual=especialidad_id,
        estado_actual=estado,
        busqueda=busqueda
    )

@admin_centro_bp.route('/especialidades')
@login_required
@admin_centro_required
def especialidades():
    """Vista para gestionar las especialidades del centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener especialidades del centro
    especialidades_centro = EspecialidadCentro.query.filter_by(
        centro_medico_id=centro.id).all()
    
    # Obtener todas las especialidades disponibles
    todas_especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    
    return render_template(
        'admin_centro/especialidades.html',
        centro=centro,
        especialidades_centro=especialidades_centro,
        todas_especialidades=todas_especialidades
    )

@admin_centro_bp.route('/citas')
@login_required
@admin_centro_required
def citas():
    """Vista para gestionar las citas del centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener parámetros de filtro
    estado = request.args.get('estado', 'todas')
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    
    # Procesar fechas
    try:
        if fecha_inicio_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        else:
            fecha_inicio = date.today() - timedelta(days=7)
        
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        else:
            fecha_fin = date.today() + timedelta(days=30)
    except ValueError:
        fecha_inicio = date.today() - timedelta(days=7)
        fecha_fin = date.today() + timedelta(days=30)
    
    # Consulta base
    query = Cita.query.filter_by(centro_medico_id=centro.id)
    
    # Aplicar filtros
    if estado != 'todas':
        query = query.filter_by(estado=estado)
    
    query = query.filter(
        db.func.date(Cita.fecha_hora) >= fecha_inicio,
        db.func.date(Cita.fecha_hora) <= fecha_fin
    )
    
    # Ordenar
    citas = query.order_by(Cita.fecha_hora).all()
    
    return render_template(
        'admin_centro/citas.html',
        centro=centro,
        citas=citas,
        estado_actual=estado,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@admin_centro_bp.route('/estadisticas')
@login_required
@admin_centro_required
def estadisticas():
    """Vista para ver estadísticas del centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Estadísticas generales
    total_medicos = db.session.query(Medico).join(
        Medico.centros_medicos).filter_by(id=centro.id).count()
    
    total_especialidades = EspecialidadCentro.query.filter_by(
        centro_medico_id=centro.id, disponible=True).count()
    
    total_citas = Cita.query.filter_by(centro_medico_id=centro.id).count()
    
    # Citas por estado
    citas_pendientes = Cita.query.filter_by(centro_medico_id=centro.id, estado='pendiente').count()
    citas_confirmadas = Cita.query.filter_by(centro_medico_id=centro.id, estado='confirmada').count()
    citas_completadas = Cita.query.filter_by(centro_medico_id=centro.id, estado='completada').count()
    citas_canceladas = Cita.query.filter_by(centro_medico_id=centro.id, estado='cancelada').count()
    
    # Estadísticas por especialidad
    especialidades_centro = EspecialidadCentro.query.filter_by(centro_medico_id=centro.id).all()
    estadisticas_especialidad = []
    
    for esp_centro in especialidades_centro:
        medicos_esp = db.session.query(Medico).filter_by(
            especialidad_id=esp_centro.especialidad_id
        ).join(Medico.centros_medicos).filter_by(id=centro.id).count()
        
        citas_esp = Cita.query.filter_by(
            centro_medico_id=centro.id,
            especialidad_id=esp_centro.especialidad_id
        ).count()
        
        estadisticas_especialidad.append({
            'especialidad': esp_centro.especialidad,
            'medicos': medicos_esp,
            'citas': citas_esp
        })
    
    # Estadísticas temporales (últimos 30 días)
    fecha_inicio = date.today() - timedelta(days=30)
    
    # Citas por día
    citas_por_dia = db.session.query(
        db.func.date(Cita.fecha_hora).label('fecha'),
        db.func.count(Cita.id).label('cantidad')
    ).filter(
        Cita.centro_medico_id == centro.id,
        Cita.fecha_hora >= fecha_inicio
    ).group_by(
        db.func.date(Cita.fecha_hora)
    ).all()
    
    # Médicos más solicitados
    medicos_top = db.session.query(
        Medico,
        db.func.count(Cita.id).label('total_citas')
    ).join(Cita).filter(
        Cita.centro_medico_id == centro.id
    ).group_by(Medico).order_by(
        db.func.count(Cita.id).desc()
    ).limit(5).all()
    
    return render_template(
        'admin_centro/estadisticas.html',
        centro=centro,
        total_medicos=total_medicos,
        total_especialidades=total_especialidades,
        total_citas=total_citas,
        citas_pendientes=citas_pendientes,
        citas_confirmadas=citas_confirmadas,
        citas_completadas=citas_completadas,
        citas_canceladas=citas_canceladas,
        estadisticas_especialidad=estadisticas_especialidad,
        citas_por_dia=citas_por_dia,
        medicos_top=medicos_top
    )

@admin_centro_bp.route('/configuracion')
@login_required
@admin_centro_required
def configuracion():
    """Vista para la configuración del centro médico."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    return render_template('admin_centro/configuracion.html', centro=centro)

@admin_centro_bp.route('/agregar-especialidad', methods=['POST'])
@login_required
@admin_centro_required
def agregar_especialidad():
    """Vista para agregar una especialidad al centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    especialidad_id = request.form.get('especialidad_id', type=int)
    
    if not especialidad_id:
        flash('Por favor seleccione una especialidad.', 'danger')
        return redirect(url_for('admin_centro.especialidades'))
    
    # Verificar si ya existe la especialidad en el centro
    existente = EspecialidadCentro.query.filter_by(
        centro_medico_id=centro.id,
        especialidad_id=especialidad_id
    ).first()
    
    if existente:
        flash('Esta especialidad ya está registrada en este centro.', 'warning')
        return redirect(url_for('admin_centro.especialidades'))
    
    # Obtener la especialidad
    especialidad = Especialidad.query.get_or_404(especialidad_id)
    
    # Agregar la especialidad al centro
    especialidad_centro = EspecialidadCentro(
        centro_medico_id=centro.id,
        especialidad_id=especialidad_id,
        disponible=True
    )
    
    db.session.add(especialidad_centro)
    db.session.commit()
    
    flash(f'Especialidad "{especialidad.nombre}" agregada exitosamente al centro.', 'success')
    return redirect(url_for('admin_centro.especialidades'))

@admin_centro_bp.route('/cambiar-estado-especialidad/<int:especialidad_centro_id>', methods=['POST'])
@login_required
@admin_centro_required
def cambiar_estado_especialidad(especialidad_centro_id):
    """Vista para cambiar el estado de una especialidad en el centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener la especialidad del centro
    especialidad_centro = EspecialidadCentro.query.get_or_404(especialidad_centro_id)
    
    # Verificar que pertenece al centro administrado
    if especialidad_centro.centro_medico_id != centro.id:
        flash('No tiene permiso para modificar esta especialidad.', 'danger')
        return redirect(url_for('admin_centro.especialidades'))
    
    # Cambiar el estado
    especialidad_centro.disponible = not especialidad_centro.disponible
    
    db.session.commit()
    
    estado = 'habilitada' if especialidad_centro.disponible else 'deshabilitada'
    flash(f'Especialidad {estado} exitosamente.', 'success')
    return redirect(url_for('admin_centro.especialidades'))

@admin_centro_bp.route('/editar-notas-especialidad/<int:especialidad_centro_id>', methods=['POST'])
@login_required
@admin_centro_required
def editar_notas_especialidad(especialidad_centro_id):
    """Vista para editar las notas de una especialidad en el centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener la especialidad del centro
    especialidad_centro = EspecialidadCentro.query.get_or_404(especialidad_centro_id)
    
    # Verificar que pertenece al centro administrado
    if especialidad_centro.centro_medico_id != centro.id:
        flash('No tiene permiso para modificar esta especialidad.', 'danger')
        return redirect(url_for('admin_centro.especialidades'))
    
    # Actualizar las notas
    notas = request.form.get('notas', '')
    especialidad_centro.notas = notas
    
    db.session.commit()
    
    flash('Notas actualizadas exitosamente.', 'success')
    return redirect(url_for('admin_centro.especialidades'))

@admin_centro_bp.route('/pacientes')
@login_required
@admin_centro_required
def pacientes():
    """Vista para ver los pacientes que han tenido citas en el centro."""
    # Obtener el centro médico administrado
    centro = current_user.admin_centro.centro_medico
    
    # Obtener pacientes únicos que han tenido citas en el centro
    from app.models.tipos_usuario import Paciente
    
    pacientes_ids = db.session.query(Cita.paciente_id).filter_by(
        centro_medico_id=centro.id
    ).distinct().all()
    
    pacientes_ids = [p[0] for p in pacientes_ids]
    
    # Obtener información de los pacientes
    pacientes = Paciente.query.filter(Paciente.usuario_id.in_(pacientes_ids)).all()
    
    return render_template('admin_centro/pacientes.html', centro=centro, pacientes=pacientes)