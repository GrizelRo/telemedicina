from flask import Blueprint, render_template, redirect, url_for, request, current_app, abort
from flask_login import current_user
from app.models.tipos_usuario import Especialidad, Medico
from app.models.centro_medico import CentroMedico

# Crear blueprint principal
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def inicio():
    """Página de inicio de la plataforma."""
    # Si el usuario está autenticado, redirigir a su panel correspondiente
    if current_user.is_authenticated:
        if current_user.es_admin_sistema:
            return redirect(url_for('admin.inicio'))
        elif current_user.es_admin_centro:
            return redirect(url_for('admin_centro.inicio'))
        elif current_user.es_medico:
            return redirect(url_for('medico.inicio'))
        elif current_user.es_paciente:
            return redirect(url_for('paciente.inicio'))
    
    # Obtener algunas especialidades y centros médicos para mostrar
    especialidades = Especialidad.query.order_by(Especialidad.nombre).limit(8).all()
    centros_medicos = CentroMedico.query.filter_by(activo=True).order_by(CentroMedico.nombre).limit(4).all()
    
    return render_template('main/inicio.html', 
                         especialidades=especialidades,
                         centros_medicos=centros_medicos)


@main_bp.route('/acerca-de')
def acerca_de():
    """Página con información sobre la plataforma."""
    return render_template('main/acerca_de.html')


@main_bp.route('/contacto')
def contacto():
    """Página de contacto."""
    return render_template('main/contacto.html')


@main_bp.route('/ayuda')
def ayuda():
    """Página de ayuda y preguntas frecuentes."""
    return render_template('main/ayuda.html')


@main_bp.route('/terminos-condiciones')
def terminos():
    """Página de términos y condiciones."""
    return render_template('main/terminos.html')


@main_bp.route('/privacidad')
def privacidad():
    """Página de política de privacidad."""
    return render_template('main/privacidad.html')


@main_bp.route('/especialidades')
def especialidades():
    """Página que muestra todas las especialidades disponibles."""
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    return render_template('main/especialidades.html', especialidades=especialidades)


@main_bp.route('/especialidad/<int:id>')
def especialidad(id):
    """Muestra información sobre una especialidad específica."""
    especialidad = Especialidad.query.get_or_404(id)
    
    # Obtener médicos con esta especialidad
    medicos = Medico.query.filter_by(especialidad_id=id, disponible=True)\
                    .join(Medico.usuario)\
                    .filter(Medico.usuario.has(activo=True))\
                    .all()
    
    return render_template('main/detalle_especialidad.html', 
                         especialidad=especialidad,
                         medicos=medicos)


@main_bp.route('/centros-medicos')
def centros_medicos():
    """Página que muestra todos los centros médicos disponibles."""
    centros = CentroMedico.query.filter_by(activo=True).order_by(CentroMedico.nombre).all()
    return render_template('main/centros_medicos.html', centros=centros)


@main_bp.route('/centro-medico/<int:id>')
def centro_medico(id):
    """Muestra información sobre un centro médico específico."""
    centro = CentroMedico.query.get_or_404(id)
    
    # Obtener especialidades disponibles en este centro
    especialidades = Especialidad.query.join(CentroMedico.especialidades)\
                              .filter_by(centro_medico_id=id, disponible=True)\
                              .all()
    
    # Obtener médicos que trabajan en este centro
    medicos = Medico.query.join(Medico.centros_medicos)\
                    .filter_by(id=id)\
                    .join(Medico.usuario)\
                    .filter(Medico.usuario.has(activo=True), Medico.disponible==True)\
                    .all()
    
    return render_template('main/detalle_centro.html', 
                         centro=centro,
                         especialidades=especialidades,
                         medicos=medicos)


@main_bp.route('/medicos')
def medicos():
    """Página que muestra todos los médicos disponibles."""
    # Filtros
    especialidad_id = request.args.get('especialidad', type=int)
    centro_id = request.args.get('centro', type=int)
    
    # Consulta base
    query = Medico.query.filter_by(disponible=True)\
                 .join(Medico.usuario)\
                 .filter(Medico.usuario.has(activo=True))
    
    # Aplicar filtros
    if especialidad_id:
        query = query.filter_by(especialidad_id=especialidad_id)
    
    if centro_id:
        query = query.join(Medico.centros_medicos)\
                     .filter_by(id=centro_id)
    
    # Obtener médicos
    medicos = query.all()
    
    # Obtener especialidades y centros para los filtros
    especialidades = Especialidad.query.order_by(Especialidad.nombre).all()
    centros = CentroMedico.query.filter_by(activo=True).order_by(CentroMedico.nombre).all()
    
    return render_template('main/medicos.html', 
                         medicos=medicos,
                         especialidades=especialidades,
                         centros=centros,
                         especialidad_seleccionada=especialidad_id,
                         centro_seleccionado=centro_id)


@main_bp.route('/medico/<int:id>')
def medico(id):
    """Muestra información sobre un médico específico."""
    medico = Medico.query.get_or_404(id)
    
    # Verificar que el médico esté activo y disponible
    if not (medico.disponible and medico.usuario.activo):
        abort(404)
    
    # Obtener centros médicos donde atiende este médico
    centros = CentroMedico.query.join(CentroMedico.medicos)\
                         .filter_by(usuario_id=id)\
                         .filter(CentroMedico.activo==True)\
                         .all()
    
    return render_template('main/detalle_medico.html', 
                         medico=medico,
                         centros=centros)


@main_bp.route('/verificar-documento')
def verificar_documento_form():
    """Página para verificar la autenticidad de un documento médico."""
    return render_template('main/verificar_documento.html')


@main_bp.route('/info-pacientes')
def info_pacientes():
    """Información útil para pacientes."""
    return render_template('main/info_pacientes.html')


@main_bp.route('/instrucciones-uso')
def instrucciones_uso():
    """Instrucciones de uso de la plataforma."""
    return render_template('main/instrucciones_uso.html')


@main_bp.route('/accesibilidad')
def accesibilidad():
    """Información sobre accesibilidad de la plataforma."""
    return render_template('main/accesibilidad.html')