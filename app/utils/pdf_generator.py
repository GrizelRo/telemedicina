import os
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus import Flowable, PageBreak
from reportlab.lib.units import inch, cm

def generar_pdf_receta(receta):
    """
    Genera un PDF para una receta médica.
    
    Args:
        receta: Objeto RecetaMedica
        
    Returns:
        str: Ruta del archivo PDF generado
    """
    # Crear directorio para PDFs si no existe
    upload_folder = current_app.config['UPLOAD_FOLDER']
    pdf_dir = os.path.join(upload_folder, 'pdfs', 'recetas')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"receta_{receta.id}_{receta.codigo_validacion}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenido del PDF
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # Centrado
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=0,  # Izquierda
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Pie',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,  # Centrado
        textColor=colors.gray
    ))
    
    # Encabezado
    if hasattr(receta.medico, 'especialidad'):
        especialidad = receta.medico.especialidad.nombre
    else:
        especialidad = "Especialidad no especificada"
    
    # Logo
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
        elementos.append(logo)
    
    # Título
    elementos.append(Paragraph("RECETA MÉDICA", styles['Titulo']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información del médico
    medico_info = [
        ["<b>Médico:</b>", receta.medico.usuario.nombre_completo],
        ["<b>Especialidad:</b>", especialidad],
        ["<b>Licencia:</b>", receta.medico.numero_licencia],
        ["<b>Centro Médico:</b>", receta.consulta.cita.centro_medico.nombre]
    ]
    
    tabla_medico = Table(medico_info, colWidths=[100, 300])
    tabla_medico.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_medico)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información del paciente
    paciente_info = [
        ["<b>Paciente:</b>", receta.paciente.usuario.nombre_completo],
        ["<b>Documento:</b>", f"{receta.paciente.usuario.tipo_documento}: {receta.paciente.usuario.numero_documento}"],
        ["<b>Fecha Nacimiento:</b>", receta.paciente.usuario.fecha_nacimiento.strftime("%d/%m/%Y")]
    ]
    
    tabla_paciente = Table(paciente_info, colWidths=[100, 300])
    tabla_paciente.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_paciente)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información de la receta
    elementos.append(Paragraph("<b>Diagnóstico:</b>", styles['Subtitulo']))
    elementos.append(Paragraph(receta.diagnostico, styles['Normal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Medicamentos
    elementos.append(Paragraph("<b>Medicamentos:</b>", styles['Subtitulo']))
    
    for i, medicamento in enumerate(receta.medicamentos):
        med_info = [
            ["<b>Nombre:</b>", medicamento.nombre],
            ["<b>Presentación:</b>", medicamento.presentacion or ""],
            ["<b>Dosis:</b>", medicamento.dosis],
            ["<b>Vía:</b>", medicamento.via_administracion],
            ["<b>Frecuencia:</b>", medicamento.frecuencia],
            ["<b>Duración:</b>", medicamento.duracion],
            ["<b>Cantidad:</b>", medicamento.cantidad or ""]
        ]
        
        tabla_med = Table(med_info, colWidths=[100, 300])
        tabla_med.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabla_med)
        
        if medicamento.instrucciones:
            elementos.append(Paragraph("<b>Instrucciones:</b> " + medicamento.instrucciones, styles['Normal']))
        
        # Separador entre medicamentos
        if i < len(receta.medicamentos) - 1:
            elementos.append(Spacer(1, 0.1*inch))
            elementos.append(Paragraph("--------------------", styles['Normal']))
            elementos.append(Spacer(1, 0.1*inch))
    
    # Información de validación
    elementos.append(Spacer(1, 0.5*inch))
    elementos.append(Paragraph("<b>Información de validación:</b>", styles['Subtitulo']))
    
    validacion_info = [
        ["<b>Código de Validación:</b>", receta.codigo_validacion],
        ["<b>Fecha de Emisión:</b>", receta.fecha_emision.strftime("%d/%m/%Y %H:%M")],
        ["<b>URL de Verificación:</b>", f"https://telemedicina.org/verificar/receta/{receta.codigo_validacion}"]
    ]
    
    tabla_validacion = Table(validacion_info, colWidths=[150, 250])
    tabla_validacion.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_validacion)
    
    # Generar QR code para validación
    try:
        import qrcode
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        
        # URL para verificación
        url = f"https://telemedicina.org/verificar/receta/{receta.codigo_validacion}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar en buffer
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        # Agregar a PDF
        elementos.append(Spacer(1, 0.2*inch))
        qr_img = Image(ImageReader(buffer), width=2*inch, height=2*inch)
        elementos.append(qr_img)
        
    except ImportError:
        # Si no está disponible qrcode, omitir
        pass
    
    # Pie de página
    elementos.append(Spacer(1, 0.5*inch))
    elementos.append(Paragraph(current_app.config.get('PDF_FOOTER_TEXT', 
                                                    'Documento generado por la Plataforma de Telemedicina'), 
                             styles['Pie']))
    
    # Generar el documento
    doc.build(elementos)
    
    return filepath


def generar_pdf_orden(orden):
    """
    Genera un PDF para una orden de laboratorio.
    
    Args:
        orden: Objeto OrdenLaboratorio
        
    Returns:
        str: Ruta del archivo PDF generado
    """
    # Crear directorio para PDFs si no existe
    upload_folder = current_app.config['UPLOAD_FOLDER']
    pdf_dir = os.path.join(upload_folder, 'pdfs', 'ordenes')
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Nombre del archivo
    filename = f"orden_{orden.id}_{orden.codigo_validacion}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    
    # Crear el documento PDF
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Contenido del PDF
    elementos = []
    
    # Estilos
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Titulo',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # Centrado
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=0,  # Izquierda
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Normal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Pie',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,  # Centrado
        textColor=colors.gray
    ))
    styles.add(ParagraphStyle(
        name='Alerta',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Centrado
        textColor=colors.red,
        spaceAfter=6
    ))
    
    # Encabezado
    if hasattr(orden.medico, 'especialidad'):
        especialidad = orden.medico.especialidad.nombre
    else:
        especialidad = "Especialidad no especificada"
    
    # Logo
    logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.5*inch, height=0.5*inch)
        elementos.append(logo)
    
    # Título
    elementos.append(Paragraph("ORDEN DE LABORATORIO", styles['Titulo']))
    
    # Si es urgente, mostrar alerta
    if orden.urgente:
        elementos.append(Paragraph("*** URGENTE ***", styles['Alerta']))
    
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información del médico
    medico_info = [
        ["<b>Médico:</b>", orden.medico.usuario.nombre_completo],
        ["<b>Especialidad:</b>", especialidad],
        ["<b>Licencia:</b>", orden.medico.numero_licencia],
        ["<b>Centro Médico:</b>", orden.consulta.cita.centro_medico.nombre]
    ]
    
    tabla_medico = Table(medico_info, colWidths=[100, 300])
    tabla_medico.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_medico)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información del paciente
    paciente_info = [
        ["<b>Paciente:</b>", orden.paciente.usuario.nombre_completo],
        ["<b>Documento:</b>", f"{orden.paciente.usuario.tipo_documento}: {orden.paciente.usuario.numero_documento}"],
        ["<b>Fecha Nacimiento:</b>", orden.paciente.usuario.fecha_nacimiento.strftime("%d/%m/%Y")]
    ]
    
    tabla_paciente = Table(paciente_info, colWidths=[100, 300])
    tabla_paciente.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_paciente)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Información de la orden
    elementos.append(Paragraph("<b>Diagnóstico Presuntivo:</b>", styles['Subtitulo']))
    elementos.append(Paragraph(orden.diagnostico_presuntivo, styles['Normal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Instrucciones generales
    if orden.instrucciones_generales:
        elementos.append(Paragraph("<b>Instrucciones Generales:</b>", styles['Subtitulo']))
        elementos.append(Paragraph(orden.instrucciones_generales, styles['Normal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Indicación de ayuno
    if orden.ayuno_requerido:
        elementos.append(Paragraph("<b>REQUIERE AYUNO</b>", styles['Alerta']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Exámenes
    elementos.append(Paragraph("<b>Exámenes Solicitados:</b>", styles['Subtitulo']))
    
    # Tabla de exámenes
    data = [["<b>Código</b>", "<b>Examen</b>", "<b>Tipo</b>"]]
    
    for examen in orden.examenes:
        data.append([examen.codigo or "", examen.nombre, examen.tipo])
    
    tabla_examenes = Table(data, colWidths=[80, 250, 70])
    tabla_examenes.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_examenes)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Instrucciones específicas de exámenes
    for examen in orden.examenes:
        if examen.instrucciones:
            elementos.append(Paragraph(f"<b>{examen.nombre} - Instrucciones:</b> {examen.instrucciones}", styles['Normal']))
    
    # Información de validación
    elementos.append(Spacer(1, 0.5*inch))
    elementos.append(Paragraph("<b>Información de validación:</b>", styles['Subtitulo']))
    
    validacion_info = [
        ["<b>Código de Validación:</b>", orden.codigo_validacion],
        ["<b>Fecha de Emisión:</b>", orden.fecha_emision.strftime("%d/%m/%Y %H:%M")],
        ["<b>URL de Verificación:</b>", f"https://telemedicina.org/verificar/orden/{orden.codigo_validacion}"]
    ]
    
    tabla_validacion = Table(validacion_info, colWidths=[150, 250])
    tabla_validacion.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elementos.append(tabla_validacion)
    
    # Generar QR code para validación
    try:
        import qrcode
        from reportlab.lib.utils import ImageReader
        from io import BytesIO
        
        # URL para verificación
        url = f"https://telemedicina.org/verificar/orden/{orden.codigo_validacion}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar en buffer
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        
        # Agregar a PDF
        elementos.append(Spacer(1, 0.2*inch))
        qr_img = Image(ImageReader(buffer), width=2*inch, height=2*inch)
        elementos.append(qr_img)
        
    except ImportError:
        # Si no está disponible qrcode, omitir
        pass
    
    # Pie de página
    elementos.append(Spacer(1, 0.5*inch))
    elementos.append(Paragraph(current_app.config.get('PDF_FOOTER_TEXT', 
                                                    'Documento generado por la Plataforma de Telemedicina'), 
                             styles['Pie']))
    
    # Generar el documento
    doc.build(elementos)
    
    return filepath