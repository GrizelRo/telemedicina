from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask import current_app, send_from_directory, abort
from flask_login import login_required, current_user
import os

from app.models.documentos import RecetaMedica, OrdenLaboratorio
from app.utils.pdf_generator import generar_pdf_receta, generar_pdf_orden
from app.utils.decorators import login_required

# Crear el blueprint de documentos
documento_bp = Blueprint('documento', __name__)

@documento_bp.route('/recetas')
@login_required
def recetas():
    """Vista para listar las recetas médicas del usuario."""
    # Si es paciente, mostrar sus recetas
    if current_user.es_paciente:
        recetas = RecetaMedica.query.filter_by(paciente_id=current_user.paciente.usuario_id)\
                            .order_by(RecetaMedica.fecha_emision.desc()).all()
        
    # Si es médico, mostrar las recetas que ha emitido
    elif current_user.es_medico:
        recetas = RecetaMedica.query.filter_by(medico_id=current_user.medico.usuario_id)\
                            .order_by(RecetaMedica.fecha_emision.desc()).all()
    
    # Si es administrador, mostrar todas las recetas
    elif current_user.es_admin_sistema or current_user.es_admin_centro:
        recetas = RecetaMedica.query.order_by(RecetaMedica.fecha_emision.desc()).all()
    
    else:
        recetas = []
    
    return render_template('documento/recetas.html', recetas=recetas)

@documento_bp.route('/ordenes')
@login_required
def ordenes():
    """Vista para listar las órdenes de laboratorio del usuario."""
    # Si es paciente, mostrar sus órdenes
    if current_user.es_paciente:
        ordenes = OrdenLaboratorio.query.filter_by(paciente_id=current_user.paciente.usuario_id)\
                              .order_by(OrdenLaboratorio.fecha_emision.desc()).all()
        
    # Si es médico, mostrar las órdenes que ha emitido
    elif current_user.es_medico:
        ordenes = OrdenLaboratorio.query.filter_by(medico_id=current_user.medico.usuario_id)\
                              .order_by(OrdenLaboratorio.fecha_emision.desc()).all()
    
    # Si es administrador, mostrar todas las órdenes
    elif current_user.es_admin_sistema or current_user.es_admin_centro:
        ordenes = OrdenLaboratorio.query.order_by(OrdenLaboratorio.fecha_emision.desc()).all()
    
    else:
        ordenes = []
    
    return render_template('documento/ordenes.html', ordenes=ordenes)

@documento_bp.route('/receta/<int:receta_id>')
@login_required
def ver_receta(receta_id):
    """Vista para ver los detalles de una receta médica."""
    receta = RecetaMedica.query.get_or_404(receta_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == receta.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == receta.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    elif current_user.es_admin_centro:
        # Verificar si el médico pertenece al centro que administra
        if current_user.admin_centro.centro_medico_id == receta.consulta.cita.centro_medico_id:
            puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    return render_template('documento/ver_receta.html', receta=receta)

@documento_bp.route('/orden/<int:orden_id>')
@login_required
def ver_orden(orden_id):
    """Vista para ver los detalles de una orden de laboratorio."""
    orden = OrdenLaboratorio.query.get_or_404(orden_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == orden.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == orden.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    elif current_user.es_admin_centro:
        # Verificar si el médico pertenece al centro que administra
        if current_user.admin_centro.centro_medico_id == orden.consulta.cita.centro_medico_id:
            puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    return render_template('documento/ver_orden.html', orden=orden)

@documento_bp.route('/descargar/receta/<int:receta_id>')
@login_required
def descargar_receta(receta_id):
    """Vista para descargar el PDF de una receta médica."""
    receta = RecetaMedica.query.get_or_404(receta_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == receta.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == receta.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    elif current_user.es_admin_centro:
        # Verificar si el médico pertenece al centro que administra
        if current_user.admin_centro.centro_medico_id == receta.consulta.cita.centro_medico_id:
            puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    # Generar o recuperar el PDF
    upload_folder = current_app.config['UPLOAD_FOLDER']
    pdf_dir = os.path.join(upload_folder, 'pdfs', 'recetas')
    filename = f"receta_{receta.id}_{receta.codigo_validacion}.pdf"
    
    # Verificar si el PDF ya existe
    pdf_path = os.path.join(pdf_dir, filename)
    if not os.path.exists(pdf_path):
        # Si no existe, generarlo
        generar_pdf_receta(receta)
    
    # Enviar el archivo al cliente
    return send_from_directory(pdf_dir, filename, as_attachment=True)

@documento_bp.route('/descargar/orden/<int:orden_id>')
@login_required
def descargar_orden(orden_id):
    """Vista para descargar el PDF de una orden de laboratorio."""
    orden = OrdenLaboratorio.query.get_or_404(orden_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == orden.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == orden.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    elif current_user.es_admin_centro:
        # Verificar si el médico pertenece al centro que administra
        if current_user.admin_centro.centro_medico_id == orden.consulta.cita.centro_medico_id:
            puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    # Generar o recuperar el PDF
    upload_folder = current_app.config['UPLOAD_FOLDER']
    pdf_dir = os.path.join(upload_folder, 'pdfs', 'ordenes')
    filename = f"orden_{orden.id}_{orden.codigo_validacion}.pdf"
    
    # Verificar si el PDF ya existe
    pdf_path = os.path.join(pdf_dir, filename)
    if not os.path.exists(pdf_path):
        # Si no existe, generarlo
        generar_pdf_orden(orden)
    
    # Enviar el archivo al cliente
    return send_from_directory(pdf_dir, filename, as_attachment=True)

@documento_bp.route('/anular/receta/<int:receta_id>', methods=['GET', 'POST'])
@login_required
def anular_receta(receta_id):
    """Vista para anular una receta médica."""
    receta = RecetaMedica.query.get_or_404(receta_id)
    
    # Verificar permisos
    puede_anular = False
    
    if current_user.es_medico and current_user.medico.usuario_id == receta.medico_id:
        puede_anular = True
    elif current_user.es_admin_sistema:
        puede_anular = True
    
    if not puede_anular:
        abort(403)  # Forbidden
    
    # Verificar que la receta esté activa
    if receta.estado != 'activo':
        flash('Esta receta ya ha sido anulada o ha caducado.', 'warning')
        return redirect(url_for('documento.ver_receta', receta_id=receta.id))
    
    if request.method == 'POST':
        motivo = request.form.get('motivo', '')
        
        if not motivo:
            flash('Por favor ingrese el motivo de la anulación.', 'danger')
        else:
            # Anular la receta
            receta.anular(motivo)
            
            # Guardar en la base de datos
            db.session.commit()
            
            flash('Receta anulada exitosamente.', 'success')
            return redirect(url_for('documento.ver_receta', receta_id=receta.id))
    
    return render_template('documento/anular_receta.html', receta=receta)

@documento_bp.route('/anular/orden/<int:orden_id>', methods=['GET', 'POST'])
@login_required
def anular_orden(orden_id):
    """Vista para anular una orden de laboratorio."""
    orden = OrdenLaboratorio.query.get_or_404(orden_id)
    
    # Verificar permisos
    puede_anular = False
    
    if current_user.es_medico and current_user.medico.usuario_id == orden.medico_id:
        puede_anular = True
    elif current_user.es_admin_sistema:
        puede_anular = True
    
    if not puede_anular:
        abort(403)  # Forbidden
    
    # Verificar que la orden esté activa
    if orden.estado != 'activo':
        flash('Esta orden ya ha sido anulada o ha caducado.', 'warning')
        return redirect(url_for('documento.ver_orden', orden_id=orden.id))
    
    if request.method == 'POST':
        motivo = request.form.get('motivo', '')
        
        if not motivo:
            flash('Por favor ingrese el motivo de la anulación.', 'danger')
        else:
            # Anular la orden
            orden.anular(motivo)
            
            # Guardar en la base de datos
            db.session.commit()
            
            flash('Orden anulada exitosamente.', 'success')
            return redirect(url_for('documento.ver_orden', orden_id=orden.id))
    
    return render_template('documento/anular_orden.html', orden=orden)