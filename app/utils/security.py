import secrets
import string
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import current_app

def generar_token(data, expiracion=3600):
    """
    Genera un token seguro para operaciones como:
    - Confirmar correo electrónico
    - Restablecer contraseña
    - Validar documentos médicos
    
    Args:
        data: Datos a incluir en el token (generalmente el email del usuario)
        expiracion: Tiempo de expiración en segundos (por defecto 1 hora)
        
    Returns:
        str: Token generado
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(data, salt=current_app.config['SECURITY_PASSWORD_SALT'])


def verificar_token(token, expiracion=3600):
    """
    Verifica un token y retorna los datos contenidos si es válido.
    
    Args:
        token: Token a verificar
        expiracion: Tiempo máximo de validez en segundos
        
    Returns:
        mixed: Datos contenidos en el token o None si es inválido
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(
            token, 
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiracion
        )
        return data
    except (SignatureExpired, BadSignature):
        return None


def generar_codigo_validacion(longitud=8):
    """
    Genera un código alfanumérico para validar documentos médicos.
    
    Args:
        longitud: Longitud del código (por defecto 8 caracteres)
        
    Returns:
        str: Código generado
    """
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))


def cifrar_datos_sensibles(datos):
    """
    Cifra datos sensibles antes de almacenarlos.
    
    Args:
        datos: Datos a cifrar
        
    Returns:
        str: Datos cifrados
    """
    # Implementación simplificada, en producción usar una biblioteca de cifrado
    # como cryptography
    return datos  # Placeholder, implementar cifrado real


def descifrar_datos_sensibles(datos_cifrados):
    """
    Descifra datos sensibles.
    
    Args:
        datos_cifrados: Datos cifrados a descifrar
        
    Returns:
        str: Datos descifrados
    """
    # Implementación simplificada, en producción usar una biblioteca de cifrado
    # como cryptography
    return datos_cifrados  # Placeholder, implementar descifrado real


def validar_documento_medico(codigo, tipo_documento, id_documento):
    """
    Valida un documento médico (receta o orden de laboratorio).
    
    Args:
        codigo: Código de validación del documento
        tipo_documento: Tipo de documento ('receta' o 'orden')
        id_documento: ID del documento en la base de datos
        
    Returns:
        bool: True si el documento es válido, False en caso contrario
    """
    if tipo_documento == 'receta':
        from app.models.documentos import RecetaMedica
        documento = RecetaMedica.query.get(id_documento)
    elif tipo_documento == 'orden':
        from app.models.documentos import OrdenLaboratorio
        documento = OrdenLaboratorio.query.get(id_documento)
    else:
        return False
    
    return documento and documento.codigo_validacion == codigo and documento.activo