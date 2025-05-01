from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.documentos import RecetaMedica, OrdenLaboratorio
from app.utils.security import validar_documento_medico

# Crear blueprint de verificación (público)
verificacion_bp = Blueprint('verificacion', __name__)

@verificacion_bp.route('/', methods=['GET', 'POST'])
def index():
    """Vista principal para verificar documentos médicos."""
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        tipo = request.form.get('tipo', '')
        
        if not codigo or not tipo:
            flash('Por favor ingrese el código de validación y seleccione el tipo de documento.', 'warning')
            return redirect(url_for('verificacion.index'))
        
        if tipo == 'receta':
            return redirect(url_for('verificacion.verificar_receta', codigo=codigo))
        elif tipo == 'orden':
            return redirect(url_for('verificacion.verificar_orden', codigo=codigo))
        else:
            flash('Tipo de documento no válido.', 'danger')
            return redirect(url_for('verificacion.index'))
    
    return render_template('verificacion/index.html')

@verificacion_bp.route('/receta/<codigo>')
def verificar_receta(codigo):
    """Vista para verificar la autenticidad de una receta médica."""
    # Buscar receta por código de validación
    receta = RecetaMedica.query.filter_by(codigo_validacion=codigo.strip().upper()).first()
    
    if not receta:
        flash('No se encontró ninguna receta con ese código de validación.', 'danger')
        return redirect(url_for('verificacion.index'))
    
    # Verificar estado de la receta
    if receta.estado != 'activo':
        flash('Esta receta ha sido anulada o ha caducado.', 'warning')
    
    # Verificar fecha de caducidad
    if receta.fecha_caducidad and receta.fecha_caducidad < datetime.utcnow():
        flash('Esta receta ha caducado.', 'warning')
    
    return render_template('verificacion/receta.html', receta=receta, valida=receta.esta_activo)

@verificacion_bp.route('/orden/<codigo>')
def verificar_orden(codigo):
    """Vista para verificar la autenticidad de una orden de laboratorio."""
    # Buscar orden por código de validación
    orden = OrdenLaboratorio.query.filter_by(codigo_validacion=codigo.strip().upper()).first()
    
    if not orden:
        flash('No se encontró ninguna orden con ese código de validación.', 'danger')
        return redirect(url_for('verificacion.index'))
    
    # Verificar estado de la orden
    if orden.estado != 'activo':
        flash('Esta orden ha sido anulada o ha caducado.', 'warning')
    
    # Verificar fecha de caducidad
    if orden.fecha_caducidad and orden.fecha_caducidad < datetime.utcnow():
        flash('Esta orden ha caducado.', 'warning')
    
    return render_template('verificacion/orden.html', orden=orden, valida=orden.esta_activo)

@verificacion_bp.route('/validar-receta', methods=['GET'])
def validar_receta():
    """Vista para validar una receta desde otro sistema (API)."""
    codigo = request.args.get('codigo', '').strip().upper()
    id_receta = request.args.get('id', type=int)
    
    if not codigo or not id_receta:
        return {'valido': False, 'mensaje': 'Parámetros incompletos'}
    
    # Validar el documento
    es_valido = validar_documento_medico(codigo, 'receta', id_receta)
    
    if es_valido:
        # Obtener información básica de la receta
        receta = RecetaMedica.query.get(id_receta)
        if receta:
            return {
                'valido': True,
                'fecha_emision': receta.fecha_emision.strftime('%Y-%m-%d %H:%M'),
                'medico': receta.medico.usuario.nombre_completo,
                'paciente': receta.paciente.usuario.nombre_completo,
                'diagnostico': receta.diagnostico[:50] + '...' if len(receta.diagnostico) > 50 else receta.diagnostico,
                'cantidad_medicamentos': len(receta.medicamentos)
            }
    
    return {'valido': False, 'mensaje': 'Documento no válido o no encontrado'}

@verificacion_bp.route('/validar-orden', methods=['GET'])
def validar_orden():
    """Vista para validar una orden desde otro sistema (API)."""
    codigo = request.args.get('codigo', '').strip().upper()
    id_orden = request.args.get('id', type=int)
    
    if not codigo or not id_orden:
        return {'valido': False, 'mensaje': 'Parámetros incompletos'}
    
    # Validar el documento
    es_valido = validar_documento_medico(codigo, 'orden', id_orden)
    
    if es_valido:
        # Obtener información básica de la orden
        orden = OrdenLaboratorio.query.get(id_orden)
        if orden:
            return {
                'valido': True,
                'fecha_emision': orden.fecha_emision.strftime('%Y-%m-%d %H:%M'),
                'medico': orden.medico.usuario.nombre_completo,
                'paciente': orden.paciente.usuario.nombre_completo,
                'diagnostico': orden.diagnostico_presuntivo[:50] + '...' if len(orden.diagnostico_presuntivo) > 50 else orden.diagnostico_presuntivo,
                'cantidad_examenes': len(orden.examenes),
                'urgente': orden.urgente
            }
    
    return {'valido': False, 'mensaje': 'Documento no válido o no encontrado'}

@verificacion_bp.route('/qr/<tipo>/<codigo>')
def qr_codigo(tipo, codigo):
    """Vista para generar un código QR para verificación."""
    from flask import make_response
    import qrcode
    from io import BytesIO
    
    # Crear URL de verificación
    if tipo == 'receta':
        url = url_for('verificacion.verificar_receta', codigo=codigo, _external=True)
    elif tipo == 'orden':
        url = url_for('verificacion.verificar_orden', codigo=codigo, _external=True)
    else:
        return "Tipo no válido", 400
    
    # Generar código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen en un buffer
    buffer = BytesIO()
    img.save(buffer)
    buffer.seek(0)
    
    # Devolver la imagen como respuesta
    response = make_response(buffer.getvalue())
    response.mimetype = 'image/png'
    
    return response