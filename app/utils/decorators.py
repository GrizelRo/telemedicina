from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user

def admin_required(f):
    """
    Decorador que restringe el acceso a los administradores del sistema.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin_sistema:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_centro_required(f):
    """
    Decorador que restringe el acceso a los administradores de centro médico.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.es_admin_centro or current_user.es_admin_sistema):
            flash('Acceso denegado. Se requieren permisos de administrador de centro médico.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def medico_required(f):
    """
    Decorador que restringe el acceso a los médicos.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_medico:
            flash('Acceso denegado. Se requieren permisos de médico.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def paciente_required(f):
    """
    Decorador que restringe el acceso a los pacientes.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_paciente:
            flash('Acceso denegado. Se requieren permisos de paciente.', 'danger')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def sin_autenticar(f):
    """
    Decorador que redirige a usuarios autenticados a su página de inicio.
    Útil para páginas como login o registro.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            # Redireccionar según el rol
            if current_user.es_admin_sistema:
                return redirect(url_for('admin.inicio'))
            elif current_user.es_admin_centro:
                return redirect(url_for('admin_centro.inicio'))
            elif current_user.es_medico:
                return redirect(url_for('medico.inicio'))
            else:
                return redirect(url_for('paciente.inicio'))
        return f(*args, **kwargs)
    return decorated_function


def validar_propiedad_cita(f):
    """
    Decorador que verifica que el usuario actual tenga permiso para acceder a una cita.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models.cita import Cita
        
        cita_id = kwargs.get('cita_id')
        cita = Cita.query.get_or_404(cita_id)
        
        # Acceso permitido si:
        # - Es el médico asignado a la cita
        # - Es el paciente de la cita
        # - Es administrador del centro médico donde se realizará la cita
        # - Es administrador del sistema
        
        permitido = (
            (current_user.es_medico and current_user.medico.usuario_id == cita.medico_id) or
            (current_user.es_paciente and current_user.paciente.usuario_id == cita.paciente_id) or
            (current_user.es_admin_centro and current_user.admin_centro.centro_medico_id == cita.centro_medico_id) or
            current_user.es_admin_sistema
        )
        
        if not permitido:
            abort(403)  # Forbidden
            
        return f(*args, **kwargs)
    return decorated_function


def validar_propiedad_consulta(f):
    """
    Decorador que verifica que el usuario actual tenga permiso para acceder a una consulta.
    
    Args:
        f: Función a decorar
        
    Returns:
        Function: Función decorada
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.models.consulta import Consulta
        
        consulta_id = kwargs.get('consulta_id')
        consulta = Consulta.query.get_or_404(consulta_id)
        
        # Obtener la cita asociada
        cita = consulta.cita
        
        # Acceso permitido si:
        # - Es el médico que realizó la consulta
        # - Es el paciente de la consulta
        # - Es administrador del centro médico donde se realizó la consulta
        # - Es administrador del sistema
        
        permitido = (
            (current_user.es_medico and current_user.medico.usuario_id == cita.medico_id) or
            (current_user.es_paciente and current_user.paciente.usuario_id == cita.paciente_id) or
            (current_user.es_admin_centro and current_user.admin_centro.centro_medico_id == cita.centro_medico_id) or
            current_user.es_admin_sistema
        )
        
        if not permitido:
            abort(403)  # Forbidden
            
        return f(*args, **kwargs)
    return decorated_function