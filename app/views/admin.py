from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from app.models.usuario import Usuario, Rol
from app.models.tipos_usuario import Medico, Paciente, AdministradorCentro, AdministradorSistema, Especialidad
from app.models.centro_medico import CentroMedico
from app.models.cita import Cita
from app.extensions import db
from app.utils.decorators import admin_required

# Crear el blueprint de administrador del sistema
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def inicio():
    """Vista principal del panel de administrador del sistema."""
    # Estadísticas generales
    total_usuarios = Usuario.query.count()
    total_medicos = Medico.query.count()
    total_pacientes = Paciente.query.count()
    total_centros = CentroMedico.query.count()
    
    # Registros recientes
    usuarios_recientes = Usuario.query.order_by(Usuario.fecha_registro.desc()).limit(5).all()
    
    # Citas hoy
    citas_hoy = Cita.query.filter(
        db.func.date(Cita.fecha_hora) == date.today()
    ).count()
    
    # Médicos pendientes de validación
    medicos_pendientes = Usuario.query.join(Usuario.roles).filter(
        Rol.nombre == 'medico',
        Usuario.activo == False
    ).count()
    
    return render_template(
        'admin/inicio.html',
        total_usuarios=total_usuarios,
        total_medicos=total_medicos,
        total_pacientes=total_pacientes,
        total_centros=total_centros,
        usuarios_recientes=usuarios_recientes,
        citas_hoy=citas_hoy,
        medicos_pendientes=medicos_pendientes
    )

@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    """Vista para listar y gestionar los usuarios del sistema."""
    # Obtener parámetros de filtro
    rol = request.args.get('rol', 'todos')
    estado = request.args.get('estado', 'todos')
    busqueda = request.args.get('busqueda', '')
    
    # Consulta base
    query = Usuario.query
    
    # Aplicar filtros
    if rol != 'todos':
        query = query.join(Usuario.roles).filter(Rol.nombre == rol)
    
    if estado != 'todos':
        activo = estado == 'activos'
        query = query.filter(Usuario.activo == activo)
    
    if busqueda:
        query = query.filter(
            db.or_(
                Usuario.nombre.like(f'%{busqueda}%'),
                Usuario.apellido.like(f'%{busqueda}%'),
                Usuario.numero_documento.like(f'%{busqueda}%'),
                Usuario.email.like(f'%{busqueda}%')
            )
        )
    
    # Ordenar
    usuarios = query.order_by(Usuario.apellido, Usuario.nombre).all()
    
    # Obtener roles para el filtro
    roles = Rol.query.all()
    
    return render_template('admin/usuarios.html', 
                         usuarios=usuarios, 
                         roles=roles,
                         rol_actual=rol,
                         estado_actual=estado,
                         busqueda=busqueda)

@admin_bp.route('/medicos')
@login_required
@admin_required
def medicos():
    """Vista para listar y gestionar los médicos del sistema."""
    # Obtener parámetros de filtro
    especialidad_id = request.args.get('especialidad_id', type=int)
    estado = request.args.get('estado', 'todos')
    busqueda = request.args.get('busqueda', '')
    
    # Consulta base
    query = Medico.query.join(Medico.usuario)
    
    # Aplicar filtros
    if especialidad_id:
        query = query.filter_by(especialidad_id=especialidad_id)
    
    if estado != 'todos':
        if estado == 'activos':
            query = query.filter(Medico.disponible == True, Medico.usuario.has(activo=True))
        elif estado == 'inactivos':
            query = query.filter(db.or_(Medico.disponible == False, Medico.usuario.has(activo=False)))
        elif estado == 'pendientes':
            query = query.filter(Medico.usuario.has(activo=False))
    
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
    medicos = query.order_by(Medico.usuario.has(apellido=db.asc()), Medico.usuario.has(nombre=db.asc())).all()
    
    # Obtener especialidades para el filtro
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    
    return render_template('admin/medicos.html', 
                         medicos=medicos, 
                         especialidades=especialidades,
                         especialidad_actual=especialidad_id,
                         estado_actual=estado,
                         busqueda=busqueda)

@admin_bp.route('/centros')
@login_required
@admin_required
def centros():
    """Vista para listar y gestionar los centros médicos."""
    # Obtener parámetros de filtro
    estado = request.args.get('estado', 'todos')
    busqueda = request.args.get('busqueda', '')
    
    # Consulta base
    query = CentroMedico.query
    
    # Aplicar filtros
    if estado != 'todos':
        activo = estado == 'activos'
        query = query.filter(CentroMedico.activo == activo)
    
    if busqueda:
        query = query.filter(
            db.or_(
                CentroMedico.nombre.like(f'%{busqueda}%'),
                CentroMedico.ciudad.like(f'%{busqueda}%'),
                CentroMedico.direccion.like(f'%{busqueda}%')
            )
        )
    
    # Ordenar
    centros = query.order_by(CentroMedico.nombre).all()
    
    return render_template('admin/centros.html', 
                         centros=centros,
                         estado_actual=estado,
                         busqueda=busqueda)

@admin_bp.route('/especialidades')
@login_required
@admin_required
def especialidades():
    """Vista para listar y gestionar las especialidades médicas."""
    # Obtener todas las especialidades
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    
    return render_template('admin/especialidades.html', especialidades=especialidades)

@admin_bp.route('/activar-medico/<int:medico_id>', methods=['POST'])
@login_required
@admin_required
def activar_medico(medico_id):
    """Vista para activar un médico pendiente de validación."""
    medico = Medico.query.get_or_404(medico_id)
    
    # Verificar que el médico está pendiente
    if medico.usuario.activo:
        flash('Este médico ya está activo.', 'info')
        return redirect(url_for('admin.medicos'))
    
    # Activar usuario y médico
    medico.usuario.activo = True
    medico.disponible = True
    
    db.session.commit()
    
    # Enviar notificación al médico
    # TODO: Implementar envío de correo
    
    flash('Médico activado exitosamente.', 'success')
    return redirect(url_for('admin.medicos'))

@admin_bp.route('/desactivar-medico/<int:medico_id>', methods=['POST'])
@login_required
@admin_required
def desactivar_medico(medico_id):
    """Vista para desactivar un médico."""
    medico = Medico.query.get_or_404(medico_id)
    
    # Verificar que el médico está activo
    if not medico.usuario.activo:
        flash('Este médico ya está inactivo.', 'info')
        return redirect(url_for('admin.medicos'))
    
    # Desactivar el médico
    medico.disponible = False
    
    db.session.commit()
    
    # Enviar notificación al médico
    # TODO: Implementar envío de correo
    
    flash('Médico desactivado exitosamente.', 'success')
    return redirect(url_for('admin.medicos'))

@admin_bp.route('/activar-centro/<int:centro_id>', methods=['POST'])
@login_required
@admin_required
def activar_centro(centro_id):
    """Vista para activar un centro médico."""
    centro = CentroMedico.query.get_or_404(centro_id)
    
    # Verificar que el centro no está activo
    if centro.activo:
        flash('Este centro médico ya está activo.', 'info')
        return redirect(url_for('admin.centros'))
    
    # Activar el centro
    centro.activo = True
    
    db.session.commit()
    
    flash('Centro médico activado exitosamente.', 'success')
    return redirect(url_for('admin.centros'))

@admin_bp.route('/desactivar-centro/<int:centro_id>', methods=['POST'])
@login_required
@admin_required
def desactivar_centro(centro_id):
    """Vista para desactivar un centro médico."""
    centro = CentroMedico.query.get_or_404(centro_id)
    
    # Verificar que el centro está activo
    if not centro.activo:
        flash('Este centro médico ya está inactivo.', 'info')
        return redirect(url_for('admin.centros'))
    
    # Desactivar el centro
    centro.activo = False
    
    db.session.commit()
    
    flash('Centro médico desactivado exitosamente.', 'success')
    return redirect(url_for('admin.centros'))

@admin_bp.route('/agregar-especialidad', methods=['POST'])
@login_required
@admin_required
def agregar_especialidad():
    """Vista para agregar una nueva especialidad médica."""
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    
    if not nombre:
        flash('El nombre de la especialidad es obligatorio.', 'danger')
        return redirect(url_for('admin.especialidades'))
    
    # Verificar que no exista una especialidad con el mismo nombre
    existente = Especialidad.query.filter(db.func.lower(Especialidad.nombre) == db.func.lower(nombre)).first()
    if existente:
        flash('Ya existe una especialidad con ese nombre.', 'danger')
        return redirect(url_for('admin.especialidades'))
    
    # Crear la especialidad
    especialidad = Especialidad(nombre=nombre, descripcion=descripcion)
    
    db.session.add(especialidad)
    db.session.commit()
    
    flash('Especialidad médica agregada exitosamente.', 'success')
    return redirect(url_for('admin.especialidades'))


@admin_bp.route('/editar-especialidad/<int:especialidad_id>', methods=['POST'])
@login_required
@admin_required
def editar_especialidad(especialidad_id):
    """Vista para editar una especialidad médica."""
    especialidad = Especialidad.query.get_or_404(especialidad_id)
    
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    
    if not nombre:
        flash('El nombre de la especialidad es obligatorio.', 'danger')
        return redirect(url_for('admin.especialidades'))
    
    # Verificar que no exista otra especialidad con el mismo nombre
    existente = Especialidad.query.filter(
        db.func.lower(Especialidad.nombre) == db.func.lower(nombre),
        Especialidad.id != especialidad_id
    ).first()
    
    if existente:
        flash('Ya existe otra especialidad con ese nombre.', 'danger')
        return redirect(url_for('admin.especialidades'))
    
    # Actualizar la especialidad
    especialidad.nombre = nombre
    especialidad.descripcion = descripcion
    
    db.session.commit()
    
    flash('Especialidad médica actualizada exitosamente.', 'success')
    return redirect(url_for('admin.especialidades'))


@admin_bp.route('/estadisticas')
@login_required
@admin_required
def estadisticas():
    """Vista para ver estadísticas del sistema."""
    # Estadísticas generales
    total_usuarios = Usuario.query.count()
    total_medicos = Medico.query.count()
    total_pacientes = Paciente.query.count()
    total_centros = CentroMedico.query.count()
    total_citas = Cita.query.count()
    
    # Citas por estado
    citas_pendientes = Cita.query.filter_by(estado='pendiente').count()
    citas_confirmadas = Cita.query.filter_by(estado='confirmada').count()
    citas_completadas = Cita.query.filter_by(estado='completada').count()
    citas_canceladas = Cita.query.filter_by(estado='cancelada').count()
    
    # Estadísticas por especialidad
    especialidades = Especialidad.query.all()
    estadisticas_especialidad = []
    
    for esp in especialidades:
        medicos_esp = Medico.query.filter_by(especialidad_id=esp.id).count()
        citas_esp = Cita.query.join(Cita.medico).filter(Medico.especialidad_id == esp.id).count()
        
        estadisticas_especialidad.append({
            'especialidad': esp,
            'medicos': medicos_esp,
            'citas': citas_esp
        })
    
    # Estadísticas por centro médico
    centros = CentroMedico.query.all()
    estadisticas_centro = []
    
    for centro in centros:
        medicos_centro = db.session.query(Medico).join(
            Medico.centros_medicos
        ).filter_by(id=centro.id).count()
        
        citas_centro = Cita.query.filter_by(centro_medico_id=centro.id).count()
        
        estadisticas_centro.append({
            'centro': centro,
            'medicos': medicos_centro,
            'citas': citas_centro
        })
    
    # Estadísticas temporales (últimos 30 días)
    fecha_inicio = date.today() - timedelta(days=30)
    
    # Nuevos usuarios por día
    nuevos_usuarios = db.session.query(
        db.func.date(Usuario.fecha_registro).label('fecha'),
        db.func.count(Usuario.id).label('cantidad')
    ).filter(
        Usuario.fecha_registro >= fecha_inicio
    ).group_by(
        db.func.date(Usuario.fecha_registro)
    ).all()
    
    # Citas por día
    citas_por_dia = db.session.query(
        db.func.date(Cita.fecha_hora).label('fecha'),
        db.func.count(Cita.id).label('cantidad')
    ).filter(
        Cita.fecha_hora >= fecha_inicio
    ).group_by(
        db.func.date(Cita.fecha_hora)
    ).all()
    
    return render_template(
        'admin/estadisticas.html',
        total_usuarios=total_usuarios,
        total_medicos=total_medicos,
        total_pacientes=total_pacientes,
        total_centros=total_centros,
        total_citas=total_citas,
        citas_pendientes=citas_pendientes,
        citas_confirmadas=citas_confirmadas,
        citas_completadas=citas_completadas,
        citas_canceladas=citas_canceladas,
        estadisticas_especialidad=estadisticas_especialidad,
        estadisticas_centro=estadisticas_centro,
        nuevos_usuarios=nuevos_usuarios,
        citas_por_dia=citas_por_dia
    )


@admin_bp.route('/configuracion')
@login_required
@admin_required
def configuracion():
    """Vista para la configuración del sistema."""
    return render_template('admin/configuracion.html')