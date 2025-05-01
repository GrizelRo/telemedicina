from flask import current_app, render_template
from flask_mail import Message
from threading import Thread
from app.extensions import mail

def enviar_email_asincrono(app, msg):
    """
    Envía un email de forma asíncrona en un hilo separado.
    
    Args:
        app: Aplicación Flask
        msg: Mensaje a enviar
    """
    with app.app_context():
        mail.send(msg)


def enviar_email(destinatario, asunto, template, **kwargs):
    """
    Configura y envía un email utilizando una plantilla.
    
    Args:
        destinatario: Dirección de correo del destinatario
        asunto: Asunto del correo
        template: Ruta de la plantilla (sin extensión)
        **kwargs: Argumentos adicionales para la plantilla
        
    Returns:
        bool: True si el email se envió correctamente
    """
    app = current_app._get_current_object()
    msg = Message(
        asunto,
        sender=app.config['MAIL_DEFAULT_SENDER'],
        recipients=[destinatario]
    )
    
    # Renderizar las versiones HTML y de texto plano
    msg.body = render_template(f'{template}.txt', **kwargs)
    msg.html = render_template(f'{template}.html', **kwargs)
    
    # Enviar de forma asíncrona si está configurado
    if app.config.get('MAIL_ASYNC', False):
        Thread(target=enviar_email_asincrono, args=(app, msg)).start()
    else:
        mail.send(msg)
    
    return True


def enviar_notificacion_cita(cita):
    """
    Envía notificaciones por correo sobre una cita médica.
    
    Args:
        cita: Objeto de la cita médica
    """
    # Notificar al paciente
    enviar_email(
        destinatario=cita.paciente.usuario.email,
        asunto=f'Confirmación de Cita Médica - {cita.especialidad.nombre}',
        template='email/cita_paciente',
        cita=cita
    )
    
    # Notificar al médico
    enviar_email(
        destinatario=cita.medico.usuario.email,
        asunto=f'Nueva Cita Médica Programada - {cita.paciente.usuario.nombre_completo}',
        template='email/cita_medico',
        cita=cita
    )


def enviar_recordatorio_cita(cita):
    """
    Envía recordatorios de citas próximas.
    
    Args:
        cita: Objeto de la cita médica
    """
    # Recordatorio al paciente
    enviar_email(
        destinatario=cita.paciente.usuario.email,
        asunto=f'Recordatorio: Cita Médica Mañana - {cita.especialidad.nombre}',
        template='email/recordatorio_cita',
        cita=cita
    )


def enviar_notificacion_cancelacion(cita, razon, cancelado_por):
    """
    Notifica sobre la cancelación de una cita.
    
    Args:
        cita: Objeto de la cita médica
        razon: Motivo de la cancelación
        cancelado_por: Usuario que canceló la cita
    """
    # Notificar al paciente
    if cancelado_por != cita.paciente.usuario_id:
        enviar_email(
            destinatario=cita.paciente.usuario.email,
            asunto='Su Cita Médica Ha Sido Cancelada',
            template='email/cancelacion_cita_paciente',
            cita=cita,
            razon=razon,
            cancelado_por=cancelado_por
        )
    
    # Notificar al médico
    if cancelado_por != cita.medico.usuario_id:
        enviar_email(
            destinatario=cita.medico.usuario.email,
            asunto=f'Cita Cancelada - {cita.paciente.usuario.nombre_completo}',
            template='email/cancelacion_cita_medico',
            cita=cita,
            razon=razon,
            cancelado_por=cancelado_por
        )


def enviar_notificacion_documento(documento, tipo, destinatario):
    """
    Notifica sobre la emisión de un documento médico.
    
    Args:
        documento: Objeto del documento (receta u orden)
        tipo: Tipo de documento ('receta' o 'orden')
        destinatario: Dirección de correo del destinatario
    """
    if tipo == 'receta':
        enviar_email(
            destinatario=destinatario,
            asunto='Nueva Receta Médica Emitida',
            template='email/nueva_receta',
            receta=documento
        )
    elif tipo == 'orden':
        enviar_email(
            destinatario=destinatario,
            asunto='Nueva Orden de Laboratorio Emitida',
            template='email/nueva_orden',
            orden=documento
        )