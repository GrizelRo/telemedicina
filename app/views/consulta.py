from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask import abort, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from app.models.consulta import Consulta
from app.models.cita import Cita
from app.models.documentos import RecetaMedica, MedicamentoReceta, OrdenLaboratorio, ExamenLaboratorio
from app.models.historial_clinico import HistorialClinico, RegistroHistorialClinico
from app.forms.consulta import (IniciarConsultaForm, RegistrarConsultaForm, 
                              EmitirRecetaForm, MedicamentoForm, 
                              EmitirOrdenLaboratorioForm, ExamenForm)
from app.extensions import db
from app.utils.decorators import medico_required, validar_propiedad_consulta
from app.utils.email import enviar_notificacion_documento
from app.utils.pdf_generator import generar_pdf_receta, generar_pdf_orden

# Crear el blueprint de consultas
consulta_bp = Blueprint('consulta', __name__)

@consulta_bp.route('/iniciar/<int:cita_id>', methods=['GET', 'POST'])
@login_required
@medico_required
def iniciar(cita_id):
    """Vista para iniciar una consulta médica."""
    # Obtener la cita
    cita = Cita.query.get_or_404(cita_id)
    
    # Verificar que la cita pertenece al médico actual
    if cita.medico_id != current_user.medico.usuario_id:
        abort(403)  # Forbidden
    
    # Verificar que la cita esté en estado "en_curso"
    if cita.estado != 'en_curso':
        flash('La cita debe estar en curso para iniciar la consulta.', 'danger')
        return redirect(url_for('medico.citas'))
    
    # Verificar si ya existe una consulta para esta cita
    consulta_existente = Consulta.query.filter_by(cita_id=cita.id).first()
    if consulta_existente:
        flash('Ya existe una consulta para esta cita.', 'info')
        return redirect(url_for('consulta.registrar', consulta_id=consulta_existente.id))
    
    form = IniciarConsultaForm()
    form.cita_id.data = cita.id
    
    if form.validate_on_submit():
        # Crear consulta
        consulta = Consulta(cita_id=cita.id)
        
        # Iniciar la consulta
        consulta.iniciar(current_user.id)
        
        # Guardar en la base de datos
        db.session.add(consulta)
        db.session.commit()
        
        flash('Consulta iniciada exitosamente.', 'success')
        return redirect(url_for('consulta.registrar', consulta_id=consulta.id))
    
    return render_template('consulta/iniciar.html', form=form, cita=cita)


@consulta_bp.route('/registrar/<int:consulta_id>', methods=['GET', 'POST'])
@login_required
@medico_required
@validar_propiedad_consulta
def registrar(consulta_id):
    """Vista para registrar los datos de una consulta médica."""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar que la consulta esté iniciada y no finalizada
    if not consulta.fecha_inicio or consulta.fecha_fin:
        flash('No se puede registrar esta consulta.', 'danger')
        return redirect(url_for('medico.citas'))
    
    form = RegistrarConsultaForm()
    form.consulta_id.data = consulta.id
    
    # Si es GET y la consulta ya tiene datos, prellenarlos
    if request.method == 'GET':
        form.motivo_consulta.data = consulta.motivo_consulta or consulta.cita.motivo
        form.sintomas.data = consulta.sintomas
        form.antecedentes.data = consulta.antecedentes
        form.exploracion.data = consulta.exploracion
        form.diagnostico.data = consulta.diagnostico
        form.plan_tratamiento.data = consulta.plan_tratamiento
        form.recomendaciones.data = consulta.recomendaciones
        form.requiere_seguimiento.data = consulta.requiere_seguimiento
        form.tiempo_seguimiento.data = consulta.tiempo_seguimiento
        form.instrucciones_seguimiento.data = consulta.instrucciones_seguimiento
    
    if form.validate_on_submit():
        # Actualizar datos de la consulta
        datos_consulta = {
            'motivo_consulta': form.motivo_consulta.data,
            'sintomas': form.sintomas.data,
            'antecedentes': form.antecedentes.data,
            'exploracion': form.exploracion.data,
            'diagnostico': form.diagnostico.data,
            'plan_tratamiento': form.plan_tratamiento.data,
            'recomendaciones': form.recomendaciones.data,
            'requiere_seguimiento': form.requiere_seguimiento.data,
            'tiempo_seguimiento': form.tiempo_seguimiento.data,
            'instrucciones_seguimiento': form.instrucciones_seguimiento.data
        }
        
        # Actualizar la consulta sin finalizarla
        for key, value in datos_consulta.items():
            setattr(consulta, key, value)
        
        # Guardar en la base de datos
        db.session.commit()
        
        flash('Datos de la consulta guardados exitosamente.', 'success')
        
        # Verificar si se presionó el botón para finalizar
        if 'finalizar' in request.form:
            return redirect(url_for('consulta.finalizar', consulta_id=consulta.id))
            
        # Recargar la página para mostrar los datos actualizados
        return redirect(url_for('consulta.registrar', consulta_id=consulta.id))
    
    return render_template('consulta/registrar.html', form=form, consulta=consulta, paciente=consulta.paciente)


@consulta_bp.route('/finalizar/<int:consulta_id>', methods=['GET', 'POST'])
@login_required
@medico_required
@validar_propiedad_consulta
def finalizar(consulta_id):
    """Vista para finalizar una consulta médica."""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar que la consulta esté iniciada y no finalizada
    if not consulta.fecha_inicio or consulta.fecha_fin:
        flash('No se puede finalizar esta consulta.', 'danger')
        return redirect(url_for('medico.citas'))
    
    if request.method == 'POST':
        # Finalizar la consulta
        consulta.finalizar()
        
        # Generar registro en el historial clínico
        consulta.generar_registro_historial()
        
        db.session.commit()
        
        flash('Consulta finalizada exitosamente.', 'success')
        return redirect(url_for('consulta.resumen', consulta_id=consulta.id))
    
    return render_template('consulta/finalizar.html', consulta=consulta)


@consulta_bp.route('/resumen/<int:consulta_id>')
@login_required
@validar_propiedad_consulta
def resumen(consulta_id):
    """Vista para ver el resumen de una consulta finalizada."""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Si la consulta no está finalizada y el usuario es médico, redirigir a registrar
    if not consulta.fecha_fin and current_user.es_medico:
        return redirect(url_for('consulta.registrar', consulta_id=consulta.id))
    
    # Obtener recetas y órdenes asociadas
    recetas = RecetaMedica.query.filter_by(consulta_id=consulta.id).all()
    ordenes = OrdenLaboratorio.query.filter_by(consulta_id=consulta.id).all()
    
    return render_template('consulta/resumen.html', 
                         consulta=consulta, 
                         recetas=recetas, 
                         ordenes=ordenes)


@consulta_bp.route('/historial-paciente/<int:paciente_id>')
@login_required
@medico_required
def historial_paciente(paciente_id):
    """Vista para ver el historial clínico de un paciente."""
    from app.models.tipos_usuario import Paciente
    
    # Verificar que el paciente existe
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Obtener el historial clínico
    historial = HistorialClinico.query.filter_by(paciente_id=paciente.usuario_id).first()
    
    # Si no existe, crear uno nuevo
    if not historial:
        historial = HistorialClinico(paciente_id=paciente.usuario_id)
        db.session.add(historial)
        db.session.commit()
    
    # Obtener consultas previas
    consultas_previas = Consulta.query.join(Consulta.cita)\
                              .filter(Cita.paciente_id==paciente.usuario_id, Consulta.fecha_fin!=None)\
                              .order_by(Consulta.fecha_fin.desc()).all()
    
    # Obtener registros del historial
    registros = historial.obtener_registros_recientes(20)
    
    # Obtener alergias y enfermedades crónicas
    alergias = historial.obtener_alergias()
    enfermedades_cronicas = historial.obtener_enfermedades_cronicas()
    
    return render_template('consulta/historial_paciente.html', 
                         paciente=paciente, 
                         historial=historial,
                         consultas=consultas_previas,
                         registros=registros,
                         alergias=alergias,
                         enfermedades_cronicas=enfermedades_cronicas)


@consulta_bp.route('/emitir-receta/<int:consulta_id>', methods=['GET', 'POST'])
@login_required
@medico_required
@validar_propiedad_consulta
def emitir_receta(consulta_id):
    """Vista para emitir una receta médica."""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar que la consulta esté iniciada
    if not consulta.fecha_inicio:
        flash('No se puede emitir una receta para esta consulta.', 'danger')
        return redirect(url_for('medico.citas'))
    
    # Inicializar formulario
    form = EmitirRecetaForm()
    form.consulta_id.data = consulta.id
    
    # Si es GET y la consulta ya tiene diagnóstico, prellena el formulario
    if request.method == 'GET' and consulta.diagnostico:
        form.diagnostico.data = consulta.diagnostico
    
    if form.validate_on_submit():
        # Crear la receta
        receta = RecetaMedica(
            consulta_id=consulta.id,
            paciente_id=consulta.paciente.usuario_id,
            medico_id=current_user.medico.usuario_id,
            diagnostico=form.diagnostico.data,
            emitido_por=current_user.id
        )
        
        # Agregar medicamentos desde el formulario
        medicamentos_data = json.loads(request.form.get('medicamentos_json', '[]'))
        
        for i, med_data in enumerate(medicamentos_data):
            medicamento = MedicamentoReceta(
                nombre=med_data.get('nombre', ''),
                presentacion=med_data.get('presentacion', ''),
                dosis=med_data.get('dosis', ''),
                via_administracion=med_data.get('via_administracion', ''),
                frecuencia=med_data.get('frecuencia', ''),
                duracion=med_data.get('duracion', ''),
                cantidad=med_data.get('cantidad', ''),
                instrucciones=med_data.get('instrucciones', ''),
                orden=i
            )
            receta.medicamentos.append(medicamento)
        
        # Guardar en la base de datos
        db.session.add(receta)
        db.session.commit()
        
        # Generar PDF de la receta
        pdf_path = generar_pdf_receta(receta)
        
        # Notificar al paciente
        enviar_notificacion_documento(receta, 'receta', consulta.paciente.usuario.email)
        
        flash('Receta emitida exitosamente.', 'success')
        
        # Si la consulta está finalizada, redirigir al resumen
        if consulta.fecha_fin:
            return redirect(url_for('consulta.resumen', consulta_id=consulta.id))
        else:
            return redirect(url_for('consulta.registrar', consulta_id=consulta.id))
    
    return render_template('consulta/emitir_receta.html', form=form, consulta=consulta)


@consulta_bp.route('/emitir-orden/<int:consulta_id>', methods=['GET', 'POST'])
@login_required
@medico_required
@validar_propiedad_consulta
def emitir_orden(consulta_id):
    """Vista para emitir una orden de laboratorio."""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Verificar que la consulta esté iniciada
    if not consulta.fecha_inicio:
        flash('No se puede emitir una orden para esta consulta.', 'danger')
        return redirect(url_for('medico.citas'))
    
    # Inicializar formulario
    form = EmitirOrdenLaboratorioForm()
    form.consulta_id.data = consulta.id
    
    # Si es GET y la consulta ya tiene diagnóstico, prellena el formulario
    if request.method == 'GET' and consulta.diagnostico:
        form.diagnostico_presuntivo.data = consulta.diagnostico
    
    if form.validate_on_submit():
        # Crear la orden
        orden = OrdenLaboratorio(
            consulta_id=consulta.id,
            paciente_id=consulta.paciente.usuario_id,
            medico_id=current_user.medico.usuario_id,
            diagnostico_presuntivo=form.diagnostico_presuntivo.data,
            instrucciones_generales=form.instrucciones_generales.data,
            ayuno_requerido=form.ayuno_requerido.data,
            urgente=form.urgente.data,
            emitido_por=current_user.id
        )
        
        # Agregar exámenes desde el formulario
        examenes_data = json.loads(request.form.get('examenes_json', '[]'))
        
        for i, exam_data in enumerate(examenes_data):
            examen = ExamenLaboratorio(
                codigo=exam_data.get('codigo', ''),
                nombre=exam_data.get('nombre', ''),
                tipo=exam_data.get('tipo', ''),
                descripcion=exam_data.get('descripcion', ''),
                instrucciones=exam_data.get('instrucciones', ''),
                orden=i
            )
            orden.examenes.append(examen)
        
        # Guardar en la base de datos
        db.session.add(orden)
        db.session.commit()
        
        # Generar PDF de la orden
        pdf_path = generar_pdf_orden(orden)
        
        # Notificar al paciente
        enviar_notificacion_documento(orden, 'orden', consulta.paciente.usuario.email)
        
        flash('Orden de laboratorio emitida exitosamente.', 'success')
        
        # Si la consulta está finalizada, redirigir al resumen
        if consulta.fecha_fin:
            return redirect(url_for('consulta.resumen', consulta_id=consulta.id))
        else:
            return redirect(url_for('consulta.registrar', consulta_id=consulta.id))
    
    return render_template('consulta/emitir_orden.html', form=form, consulta=consulta)


@consulta_bp.route('/ver-receta/<int:receta_id>')
@login_required
def ver_receta(receta_id):
    """Vista para ver una receta médica."""
    receta = RecetaMedica.query.get_or_404(receta_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == receta.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == receta.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    return render_template('consulta/ver_receta.html', receta=receta)


@consulta_bp.route('/ver-orden/<int:orden_id>')
@login_required
def ver_orden(orden_id):
    """Vista para ver una orden de laboratorio."""
    orden = OrdenLaboratorio.query.get_or_404(orden_id)
    
    # Verificar permisos
    puede_ver = False
    
    if current_user.es_medico and current_user.medico.usuario_id == orden.medico_id:
        puede_ver = True
    elif current_user.es_paciente and current_user.paciente.usuario_id == orden.paciente_id:
        puede_ver = True
    elif current_user.es_admin_sistema:
        puede_ver = True
    
    if not puede_ver:
        abort(403)  # Forbidden
    
    return render_template('consulta/ver_orden.html', orden=orden)


@consulta_bp.route('/agregar-historial/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
@medico_required
def agregar_historial(paciente_id):
    """Vista para agregar una entrada al historial clínico."""
    from app.models.tipos_usuario import Paciente
    
    # Verificar que el paciente existe
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Obtener el historial clínico
    historial = HistorialClinico.query.filter_by(paciente_id=paciente.usuario_id).first()
    
    # Si no existe, crear uno nuevo
    if not historial:
        historial = HistorialClinico(paciente_id=paciente.usuario_id)
        db.session.add(historial)
        db.session.commit()
    
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        descripcion = request.form.get('descripcion')
        detalles = request.form.get('detalles', '{}')
        
        # Validar datos
        if not tipo or not descripcion:
            flash('Todos los campos son obligatorios.', 'danger')
        else:
            # Convertir detalles a diccionario
            try:
                detalles_dict = json.loads(detalles)
            except:
                detalles_dict = {}
            
            # Agregar registro
            historial.agregar_registro(
                tipo=tipo,
                descripcion=descripcion,
                detalles=detalles_dict,
                consulta_id=None  # No está asociado a una consulta específica
            )
            
            db.session.commit()
            
            flash('Registro agregado exitosamente al historial.', 'success')
            return redirect(url_for('consulta.historial_paciente', paciente_id=paciente.usuario_id))
    
    return render_template('consulta/agregar_historial.html', paciente=paciente)