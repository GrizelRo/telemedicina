from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField
from wtforms import BooleanField, TextAreaField, EmailField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from datetime import date

from app.models.usuario import Usuario
from app.utils.validators import validar_documento, validar_nombre, validar_telefono

class LoginForm(FlaskForm):
    """Formulario para el inicio de sesión."""
    numero_documento = StringField('Número de Documento', 
                                 validators=[DataRequired('Por favor ingrese su número de documento')])
    password = PasswordField('Contraseña', 
                          validators=[DataRequired('Por favor ingrese su contraseña')])
    recordar = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')


class RegistroBaseForm(FlaskForm):
    """Formulario base para el registro de usuarios."""
    tipo_documento = SelectField('Tipo de Documento', 
                               choices=[
                                   ('dni', 'DNI'), 
                                   ('cedula', 'Cédula'), 
                                   ('pasaporte', 'Pasaporte'),
                                   ('otro', 'Otro')
                               ],
                               validators=[DataRequired('Por favor seleccione el tipo de documento')])
    numero_documento = StringField('Número de Documento', 
                                 validators=[
                                     DataRequired('Por favor ingrese su número de documento'),
                                     validar_documento
                                 ])
    nombre = StringField('Nombres', 
                       validators=[
                           DataRequired('Por favor ingrese su nombre'),
                           Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres'),
                           validar_nombre
                       ])
    apellido = StringField('Apellidos', 
                         validators=[
                             DataRequired('Por favor ingrese su apellido'),
                             Length(min=2, max=100, message='El apellido debe tener entre 2 y 100 caracteres'),
                             validar_nombre
                         ])
    fecha_nacimiento = DateField('Fecha de Nacimiento', 
                               validators=[DataRequired('Por favor ingrese su fecha de nacimiento')])
    genero = SelectField('Género', 
                       choices=[
                           ('masculino', 'Masculino'), 
                           ('femenino', 'Femenino'), 
                           ('otro', 'Otro'),
                           ('prefiero_no_decir', 'Prefiero no decir')
                       ],
                       validators=[DataRequired('Por favor seleccione su género')])
    email = EmailField('Correo Electrónico', 
                     validators=[
                         DataRequired('Por favor ingrese su correo electrónico'),
                         Email('Por favor ingrese un correo electrónico válido')
                     ])
    telefono = StringField('Teléfono', 
                         validators=[
                             Optional(),
                             validar_telefono
                         ])
    direccion = StringField('Dirección', validators=[Optional()])
    ciudad = StringField('Ciudad', validators=[Optional()])
    departamento = StringField('Departamento', validators=[Optional()])
    password = PasswordField('Contraseña', 
                          validators=[
                              DataRequired('Por favor ingrese una contraseña'),
                              Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
                          ])
    confirmar_password = PasswordField('Confirmar Contraseña', 
                                    validators=[
                                        DataRequired('Por favor confirme su contraseña'),
                                        EqualTo('password', message='Las contraseñas deben coincidir')
                                    ])
    aceptar_terminos = BooleanField('Acepto los términos y condiciones', 
                                  validators=[DataRequired('Debe aceptar los términos y condiciones')])
    
    def validate_numero_documento(self, field):
        """Valida que el número de documento no esté ya registrado."""
        usuario = Usuario.query.filter_by(numero_documento=field.data).first()
        if usuario:
            raise ValidationError('Este número de documento ya está registrado.')
    
    def validate_email(self, field):
        """Valida que el email no esté ya registrado."""
        usuario = Usuario.query.filter_by(email=field.data).first()
        if usuario:
            raise ValidationError('Este correo electrónico ya está registrado.')
    
    def validate_fecha_nacimiento(self, field):
        """Valida que la fecha de nacimiento sea pasada y razonable."""
        if field.data > date.today():
            raise ValidationError('La fecha de nacimiento no puede ser en el futuro.')
        
        # Validar que la persona tenga al menos 1 año
        edad = date.today().year - field.data.year
        if edad < 1:
            raise ValidationError('La edad mínima es de 1 año.')


class RegistroPacienteForm(RegistroBaseForm):
    """Formulario para el registro de pacientes."""
    grupo_sanguineo = SelectField('Grupo Sanguíneo', 
                                choices=[
                                    ('', 'No sé / No estoy seguro'),
                                    ('A+', 'A+'), ('A-', 'A-'),
                                    ('B+', 'B+'), ('B-', 'B-'),
                                    ('AB+', 'AB+'), ('AB-', 'AB-'),
                                    ('O+', 'O+'), ('O-', 'O-')
                                ])
    alergias = TextAreaField('Alergias (opcional)')
    enfermedades_cronicas = TextAreaField('Enfermedades Crónicas (opcional)')
    contacto_emergencia_nombre = StringField('Nombre de Contacto de Emergencia')
    contacto_emergencia_telefono = StringField('Teléfono de Contacto de Emergencia',
                                             validators=[Optional(), validar_telefono])
    contacto_emergencia_relacion = StringField('Relación con el Contacto de Emergencia')
    seguro_medico = StringField('Seguro Médico (opcional)')
    numero_seguro = StringField('Número de Seguro (opcional)')
    submit = SubmitField('Registrarme como Paciente')


class RegistroMedicoForm(RegistroBaseForm):
    """Formulario para el registro de médicos."""
    numero_licencia = StringField('Número de Licencia Médica', 
                                validators=[
                                    DataRequired('Por favor ingrese su número de licencia médica')
                                ])
    especialidad_id = SelectField('Especialidad', coerce=int,
                                validators=[DataRequired('Por favor seleccione su especialidad')])
    titulo_profesional = StringField('Título Profesional', 
                                   validators=[DataRequired('Por favor ingrese su título profesional')])
    biografia = TextAreaField('Biografía Profesional', 
                            validators=[Optional()])
    anos_experiencia = StringField('Años de Experiencia', 
                                 validators=[Optional()])
    submit = SubmitField('Solicitar Registro como Médico')
    
    def validate_numero_licencia(self, field):
        """Valida que el número de licencia no esté ya registrado."""
        from app.models.tipos_usuario import Medico
        medico = Medico.query.filter_by(numero_licencia=field.data).first()
        if medico:
            raise ValidationError('Este número de licencia ya está registrado.')


class RegistroAdminCentroForm(RegistroBaseForm):
    """Formulario para el registro de administradores de centro médico."""
    centro_medico_id = SelectField('Centro Médico', coerce=int,
                                 validators=[DataRequired('Por favor seleccione el centro médico')])
    cargo = StringField('Cargo', validators=[DataRequired('Por favor ingrese su cargo')])
    departamento = StringField('Departamento', validators=[Optional()])
    submit = SubmitField('Solicitar Registro como Administrador de Centro')


class CambioPasswordForm(FlaskForm):
    """Formulario para cambiar la contraseña."""
    password_actual = PasswordField('Contraseña Actual', 
                                  validators=[DataRequired('Por favor ingrese su contraseña actual')])
    password_nuevo = PasswordField('Nueva Contraseña', 
                                 validators=[
                                     DataRequired('Por favor ingrese una nueva contraseña'),
                                     Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
                                 ])
    confirmar_password = PasswordField('Confirmar Nueva Contraseña', 
                                     validators=[
                                         DataRequired('Por favor confirme su nueva contraseña'),
                                         EqualTo('password_nuevo', message='Las contraseñas deben coincidir')
                                     ])
    submit = SubmitField('Cambiar Contraseña')


class RecuperarPasswordForm(FlaskForm):
    """Formulario para solicitar recuperación de contraseña."""
    email = EmailField('Correo Electrónico', 
                     validators=[
                         DataRequired('Por favor ingrese su correo electrónico'),
                         Email('Por favor ingrese un correo electrónico válido')
                     ])
    submit = SubmitField('Recuperar Contraseña')


class RestablecerPasswordForm(FlaskForm):
    """Formulario para restablecer la contraseña."""
    password = PasswordField('Nueva Contraseña', 
                          validators=[
                              DataRequired('Por favor ingrese una nueva contraseña'),
                              Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
                          ])
    confirmar_password = PasswordField('Confirmar Nueva Contraseña', 
                                     validators=[
                                         DataRequired('Por favor confirme su nueva contraseña'),
                                         EqualTo('password', message='Las contraseñas deben coincidir')
                                     ])
    submit = SubmitField('Restablecer Contraseña')


class PerfilUsuarioForm(FlaskForm):
    """Formulario para actualizar el perfil de usuario."""
    nombre = StringField('Nombres', 
                       validators=[
                           DataRequired('Por favor ingrese su nombre'),
                           Length(min=2, max=100, message='El nombre debe tener entre 2 y 100 caracteres'),
                           validar_nombre
                       ])
    apellido = StringField('Apellidos', 
                         validators=[
                             DataRequired('Por favor ingrese su apellido'),
                             Length(min=2, max=100, message='El apellido debe tener entre 2 y 100 caracteres'),
                             validar_nombre
                         ])
    telefono = StringField('Teléfono', 
                         validators=[
                             Optional(),
                             validar_telefono
                         ])
    direccion = StringField('Dirección', validators=[Optional()])
    ciudad = StringField('Ciudad', validators=[Optional()])
    departamento = StringField('Departamento', validators=[Optional()])
    email = EmailField('Correo Electrónico', 
                     validators=[
                         DataRequired('Por favor ingrese su correo electrónico'),
                         Email('Por favor ingrese un correo electrónico válido')
                     ])
    submit = SubmitField('Actualizar Perfil')
    
    def __init__(self, usuario_original=None, *args, **kwargs):
        super(PerfilUsuarioForm, self).__init__(*args, **kwargs)
        self.usuario_original = usuario_original
    
    def validate_email(self, field):
        """Valida que el email no esté ya registrado por otro usuario."""
        if self.usuario_original and field.data != self.usuario_original.email:
            usuario = Usuario.query.filter_by(email=field.data).first()
            if usuario:
                raise ValidationError('Este correo electrónico ya está registrado por otro usuario.')