from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField
from wtforms import IntegerField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError

class IniciarConsultaForm(FlaskForm):
    """Formulario para iniciar una consulta médica."""
    cita_id = HiddenField('ID de la Cita', validators=[DataRequired()])
    
    confirmacion = BooleanField('Confirmo que estoy listo para iniciar la consulta', 
                              validators=[DataRequired('Debe confirmar para iniciar la consulta')])
    
    submit = SubmitField('Iniciar Consulta')


class RegistrarConsultaForm(FlaskForm):
    """Formulario para registrar los datos de una consulta médica."""
    consulta_id = HiddenField('ID de la Consulta', validators=[DataRequired()])
    
    motivo_consulta = TextAreaField('Motivo de Consulta', 
                                  validators=[
                                      DataRequired('Por favor ingrese el motivo de la consulta'),
                                      Length(min=10, max=1000, 
                                            message='El motivo debe tener entre 10 y 1000 caracteres')
                                  ])
    
    sintomas = TextAreaField('Síntomas', 
                           validators=[
                               DataRequired('Por favor describa los síntomas'),
                               Length(min=10, max=1000, 
                                     message='La descripción debe tener entre 10 y 1000 caracteres')
                           ])
    
    antecedentes = TextAreaField('Antecedentes Relevantes', 
                               validators=[Optional()])
    
    exploracion = TextAreaField('Exploración Física', 
                              validators=[Optional()])
    
    diagnostico = TextAreaField('Diagnóstico', 
                              validators=[
                                  DataRequired('Por favor ingrese el diagnóstico'),
                                  Length(min=10, max=1000, 
                                        message='El diagnóstico debe tener entre 10 y 1000 caracteres')
                              ])
    
    plan_tratamiento = TextAreaField('Plan de Tratamiento', 
                                   validators=[
                                       DataRequired('Por favor ingrese el plan de tratamiento'),
                                       Length(min=10, max=1000, 
                                             message='El plan debe tener entre 10 y 1000 caracteres')
                                   ])
    
    recomendaciones = TextAreaField('Recomendaciones', 
                                  validators=[
                                      Optional(),
                                      Length(max=1000, 
                                            message='Las recomendaciones no deben exceder los 1000 caracteres')
                                  ])
    
    requiere_seguimiento = BooleanField('Requiere Seguimiento')
    
    tiempo_seguimiento = IntegerField('Tiempo de Seguimiento (días)', 
                                    validators=[Optional(), 
                                               NumberRange(min=1, max=365, 
                                                         message='El tiempo debe estar entre 1 y 365 días')])
    
    instrucciones_seguimiento = TextAreaField('Instrucciones de Seguimiento', 
                                            validators=[Optional()])
    
    submit = SubmitField('Guardar Consulta')
    
    def validate_tiempo_seguimiento(self, field):
        """Valida que se ingrese el tiempo de seguimiento si se requiere seguimiento."""
        if self.requiere_seguimiento.data and not field.data:
            raise ValidationError('Por favor indique el tiempo de seguimiento.')


class EmitirRecetaForm(FlaskForm):
    """Formulario para emitir una receta médica."""
    consulta_id = HiddenField('ID de la Consulta', validators=[DataRequired()])
    
    diagnostico = TextAreaField('Diagnóstico', 
                              validators=[
                                  DataRequired('Por favor ingrese el diagnóstico'),
                                  Length(min=10, max=500, 
                                        message='El diagnóstico debe tener entre 10 y 500 caracteres')
                              ])
    
    # Los medicamentos se agregan dinámicamente con JavaScript
    # Este campo solo sirve para validar que haya al menos un medicamento
    hay_medicamentos = HiddenField('Hay Medicamentos', validators=[DataRequired('Debe agregar al menos un medicamento')])
    
    submit = SubmitField('Emitir Receta')


class MedicamentoForm(FlaskForm):
    """Formulario para un medicamento dentro de una receta."""
    nombre = StringField('Nombre del Medicamento', 
                       validators=[
                           DataRequired('Por favor ingrese el nombre del medicamento'),
                           Length(min=3, max=200, 
                                 message='El nombre debe tener entre 3 y 200 caracteres')
                       ])
    
    presentacion = StringField('Presentación', 
                             validators=[Optional()])
    
    dosis = StringField('Dosis', 
                      validators=[
                          DataRequired('Por favor ingrese la dosis'),
                          Length(min=3, max=100, 
                                message='La dosis debe tener entre 3 y 100 caracteres')
                      ])
    
    via_administracion = SelectField('Vía de Administración', 
                                   choices=[
                                       ('oral', 'Oral'),
                                       ('sublingual', 'Sublingual'),
                                       ('topica', 'Tópica'),
                                       ('inhalatoria', 'Inhalatoria'),
                                       ('rectal', 'Rectal'),
                                       ('vaginal', 'Vaginal'),
                                       ('ocular', 'Ocular'),
                                       ('otica', 'Ótica'),
                                       ('nasal', 'Nasal'),
                                       ('parenteral', 'Parenteral'),
                                       ('otra', 'Otra')
                                   ],
                                   validators=[DataRequired('Por favor seleccione la vía de administración')])
    
    frecuencia = StringField('Frecuencia', 
                           validators=[
                               DataRequired('Por favor ingrese la frecuencia'),
                               Length(min=3, max=100, 
                                     message='La frecuencia debe tener entre 3 y 100 caracteres')
                           ])
    
    duracion = StringField('Duración', 
                         validators=[
                             DataRequired('Por favor ingrese la duración'),
                             Length(min=3, max=100, 
                                   message='La duración debe tener entre 3 y 100 caracteres')
                         ])
    
    cantidad = StringField('Cantidad', validators=[Optional()])
    
    instrucciones = TextAreaField('Instrucciones Adicionales', validators=[Optional()])


class EmitirOrdenLaboratorioForm(FlaskForm):
    """Formulario para emitir una orden de laboratorio."""
    consulta_id = HiddenField('ID de la Consulta', validators=[DataRequired()])
    
    diagnostico_presuntivo = TextAreaField('Diagnóstico Presuntivo', 
                                         validators=[
                                             DataRequired('Por favor ingrese el diagnóstico presuntivo'),
                                             Length(min=10, max=500, 
                                                   message='El diagnóstico debe tener entre 10 y 500 caracteres')
                                         ])
    
    instrucciones_generales = TextAreaField('Instrucciones Generales', 
                                          validators=[Optional()])
    
    ayuno_requerido = BooleanField('Requiere Ayuno')
    
    urgente = BooleanField('Urgente')
    
    # Los exámenes se agregan dinámicamente con JavaScript
    # Este campo solo sirve para validar que haya al menos un examen
    hay_examenes = HiddenField('Hay Exámenes', validators=[DataRequired('Debe agregar al menos un examen')])
    
    submit = SubmitField('Emitir Orden')


class ExamenForm(FlaskForm):
    """Formulario para un examen dentro de una orden de laboratorio."""
    codigo = StringField('Código (opcional)', validators=[Optional()])
    
    nombre = StringField('Nombre del Examen', 
                       validators=[
                           DataRequired('Por favor ingrese el nombre del examen'),
                           Length(min=3, max=200, 
                                 message='El nombre debe tener entre 3 y 200 caracteres')
                       ])
    
    tipo = SelectField('Tipo de Muestra', 
                     choices=[
                         ('sangre', 'Sangre'),
                         ('orina', 'Orina'),
                         ('heces', 'Heces'),
                         ('tejido', 'Tejido'),
                         ('secrecion', 'Secreción'),
                         ('liquido', 'Líquido'),
                         ('otro', 'Otro')
                     ],
                     validators=[DataRequired('Por favor seleccione el tipo de muestra')])
    
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    
    instrucciones = TextAreaField('Instrucciones Específicas', validators=[Optional()])