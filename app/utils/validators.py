import re
from wtforms.validators import ValidationError

def validar_documento(form, field):
    """
    Valida que el número de documento tenga un formato válido.
    Permite letras, números y guiones. Longitud entre 5 y 20 caracteres.
    """
    patron = re.compile(r'^[A-Za-z0-9\-]{5,20}$')
    if not patron.match(field.data):
        raise ValidationError('El número de documento debe contener entre 5 y 20 caracteres, '
                             'solo letras, números y guiones.')


def validar_nombre(form, field):
    """
    Valida que el nombre o apellido solo contenga letras, espacios, 
    apóstrofes y guiones (para nombres compuestos).
    """
    patron = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s\'\-]+$')
    if not patron.match(field.data):
        raise ValidationError('Este campo solo debe contener letras, espacios, apóstrofes y guiones.')


def validar_telefono(form, field):
    """
    Valida que el número de teléfono tenga un formato válido.
    Permite números, espacios, paréntesis, guiones y el signo más.
    Longitud entre 7 y 20 caracteres.
    """
    if field.data:  # Solo validar si se proporcionó un número
        patron = re.compile(r'^[0-9\s\(\)\-\+]{7,20}$')
        if not patron.match(field.data):
            raise ValidationError('El número de teléfono debe contener entre 7 y 20 caracteres, '
                                'solo números, espacios, paréntesis, guiones y el signo más.')


def validar_codigo_validacion(form, field):
    """
    Valida que el código de validación tenga un formato válido.
    Solo letras mayúsculas y números, longitud exacta de 8 caracteres.
    """
    patron = re.compile(r'^[A-Z0-9]{8}$')
    if not patron.match(field.data):
        raise ValidationError('El código de validación debe contener exactamente 8 caracteres, '
                             'solo letras mayúsculas y números.')


def validar_url(form, field):
    """
    Valida que la URL tenga un formato válido.
    """
    if field.data:  # Solo validar si se proporcionó una URL
        patron = re.compile(
            r'^(https?:\/\/)?' # http:// o https://
            r'(www\.)?' # www.
            r'[-a-zA-Z0-9@:%._\+~#=]{1,256}' # dominio
            r'\.' # punto
            r'[a-zA-Z0-9()]{1,6}' # com, org, etc.
            r'([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$' # parámetros
        )
        if not patron.match(field.data):
            raise ValidationError('Por favor ingrese una URL válida.')


def validar_codigo_postal(form, field):
    """
    Valida que el código postal tenga un formato válido.
    Solo números, longitud entre 3 y 10 caracteres.
    """
    if field.data:  # Solo validar si se proporcionó un código postal
        patron = re.compile(r'^[0-9]{3,10}$')
        if not patron.match(field.data):
            raise ValidationError('El código postal debe contener entre 3 y 10 dígitos.')


def validar_licencia_medica(form, field):
    """
    Valida que el número de licencia médica tenga un formato válido.
    Permite letras, números y guiones. Longitud entre 5 y 20 caracteres.
    """
    patron = re.compile(r'^[A-Za-z0-9\-]{5,20}$')
    if not patron.match(field.data):
        raise ValidationError('El número de licencia médica debe contener entre 5 y 20 caracteres, '
                             'solo letras, números y guiones.')


def validar_seguro_medico(form, field):
    """
    Valida que el número de seguro médico tenga un formato válido.
    Permite letras, números y guiones. Longitud entre 5 y 20 caracteres.
    """
    if field.data:  # Solo validar si se proporcionó un número
        patron = re.compile(r'^[A-Za-z0-9\-]{5,20}$')
        if not patron.match(field.data):
            raise ValidationError('El número de seguro médico debe contener entre 5 y 20 caracteres, '
                                'solo letras, números y guiones.')