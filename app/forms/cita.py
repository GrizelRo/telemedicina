from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField
from wtforms import BooleanField, HiddenField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from datetime import datetime, date, timedelta

class AgendarCitaForm(FlaskForm):
    """Formulario para agendar una nueva cita médica."""
    especialidad_id = SelectField('Especialidad', coerce=int,
                                validators=[DataRequired('Por favor seleccione una especialidad')])
    
    centro_medico_id = SelectField('Centro Médico', coerce=int,
                                 validators=[DataRequired('Por favor seleccione un centro médico')])
    
    medico_id = SelectField('Médico', coerce=int,
                          validators=[DataRequired('Por favor seleccione un médico')])
    
    fecha = DateField('Fecha', format='%Y-%m-%d',
                    validators=[DataRequired('Por favor seleccione una fecha')])
    
    horario = SelectField('Horario Disponible',
                        validators=[DataRequired('Por favor seleccione un horario')])
    
    tipo = SelectField('Tipo de Consulta',
                     choices=[
                         ('primera_vez', 'Primera vez'),
                         ('seguimiento', 'Seguimiento'),
                         ('control', 'Control'),
                         ('urgencia', 'Urgencia')
                     ],
                     validators=[DataRequired('Por favor seleccione el tipo de consulta')])
    
    motivo = TextAreaField('Motivo de la Consulta',
                         validators=[
                             DataRequired('Por favor indique el motivo de su consulta'),
                             Length(min=10, max=500, 
                                   message='El motivo debe tener entre 10 y 500 caracteres')
                         ])
    
    submit = SubmitField('Agendar Cita')
    
    def validate_fecha(self, field):
        """Valida que la fecha seleccionada sea en el futuro."""
        if field.data < date.today():
            raise ValidationError('La fecha de la cita no puede ser en el pasado.')
        
        # Verificar que no sea más de 3 meses en el futuro
        max_fecha = date.today() + timedelta(days=90)
        if field.data > max_fecha:
            raise ValidationError('No puede agendar citas con más de 3 meses de anticipación.')


class BuscarHorariosForm(FlaskForm):
    """Formulario para buscar horarios disponibles para una cita."""
    especialidad_id = SelectField('Especialidad', coerce=int,
                                validators=[DataRequired('Por favor seleccione una especialidad')])
    
    centro_medico_id = SelectField('Centro Médico', coerce=int,
                                 validators=[Optional()])
    
    medico_id = SelectField('Médico (opcional)', coerce=int,
                          validators=[Optional()])
    
    fecha_inicio = DateField('Desde', format='%Y-%m-%d',
                           validators=[DataRequired('Por favor seleccione una fecha inicial')])
    
    fecha_fin = DateField('Hasta', format='%Y-%m-%d',
                        validators=[DataRequired('Por favor seleccione una fecha final')])
    
    submit = SubmitField('Buscar Horarios')
    
    def validate_fecha_inicio(self, field):
        """Valida que la fecha inicial sea hoy o en el futuro."""
        if field.data < date.today():
            raise ValidationError('La fecha inicial no puede ser en el pasado.')
    
    def validate_fecha_fin(self, field):
        """Valida que la fecha final sea después de la inicial y no más de 30 días después."""
        if self.fecha_inicio.data and field.data < self.fecha_inicio.data:
            raise ValidationError('La fecha final debe ser posterior a la fecha inicial.')
        
        if self.fecha_inicio.data:
            max_dias = 30
            max_fecha = self.fecha_inicio.data + timedelta(days=max_dias)
            if field.data > max_fecha:
                raise ValidationError(f'El rango de fechas no puede ser mayor a {max_dias} días.')


class RegistrarDisponibilidadForm(FlaskForm):
    """Formulario para que los médicos registren su disponibilidad."""
    centro_medico_id = SelectField('Centro Médico', coerce=int,
                                 validators=[DataRequired('Por favor seleccione un centro médico')])
    
    fecha_inicio = DateField('Fecha Inicial', format='%Y-%m-%d',
                           validators=[DataRequired('Por favor seleccione una fecha inicial')])
    
    fecha_fin = DateField('Fecha Final', format='%Y-%m-%d',
                        validators=[DataRequired('Por favor seleccione una fecha final')])
    
    hora_inicio = TimeField('Hora de Inicio', format='%H:%M',
                          validators=[DataRequired('Por favor seleccione la hora de inicio')])
    
    hora_fin = TimeField('Hora de Finalización', format='%H:%M',
                       validators=[DataRequired('Por favor seleccione la hora de finalización')])
    
    intervalo_citas = SelectField('Duración de cada Cita (en minutos)',
                                choices=[
                                    ('15', '15 minutos'),
                                    ('20', '20 minutos'),
                                    ('30', '30 minutos'),
                                    ('45', '45 minutos'),
                                    ('60', '60 minutos')
                                ],
                                validators=[DataRequired('Por favor seleccione la duración de las citas')])
    
    dias_semana = SelectMultipleField('Días de la Semana',
                                    choices=[
                                        ('0', 'Lunes'),
                                        ('1', 'Martes'),
                                        ('2', 'Miércoles'),
                                        ('3', 'Jueves'),
                                        ('4', 'Viernes'),
                                        ('5', 'Sábado'),
                                        ('6', 'Domingo')
                                    ],
                                    validators=[DataRequired('Por favor seleccione al menos un día')])
    
    citas_maximas = StringField('Máximo de Citas (opcional, dejar en blanco para no limitar)',
                              validators=[Optional()])
    
    submit = SubmitField('Registrar Disponibilidad')
    
    def validate_fecha_inicio(self, field):
        """Valida que la fecha inicial sea hoy o en el futuro."""
        if field.data < date.today():
            raise ValidationError('La fecha inicial no puede ser en el pasado.')
    
    def validate_fecha_fin(self, field):
        """Valida que la fecha final sea después de la inicial."""
        if self.fecha_inicio.data and field.data < self.fecha_inicio.data:
            raise ValidationError('La fecha final debe ser posterior a la fecha inicial.')
    
    def validate_hora_fin(self, field):
        """Valida que la hora final sea después de la inicial."""
        if self.hora_inicio.data and field.data <= self.hora_inicio.data:
            raise ValidationError('La hora de finalización debe ser posterior a la hora de inicio.')
    
    def validate_citas_maximas(self, field):
        """Valida que el máximo de citas sea un número entero positivo."""
        if field.data:
            try:
                valor = int(field.data)
                if valor <= 0:
                    raise ValidationError('El máximo de citas debe ser un número positivo.')
            except ValueError:
                raise ValidationError('Por favor ingrese un número válido.')


class CancelarCitaForm(FlaskForm):
    """Formulario para cancelar una cita."""
    motivo_cancelacion = TextAreaField('Motivo de la Cancelación',
                                     validators=[
                                         DataRequired('Por favor indique el motivo de la cancelación'),
                                         Length(min=10, max=500, 
                                               message='El motivo debe tener entre 10 y 500 caracteres')
                                     ])
    
    confirmar = BooleanField('Confirmo que deseo cancelar esta cita',
                           validators=[DataRequired('Debe confirmar la cancelación')])
    
    cita_id = HiddenField('ID de la Cita', validators=[DataRequired()])
    
    submit = SubmitField('Cancelar Cita')


class ReprogramarCitaForm(FlaskForm):
    """Formulario para reprogramar una cita."""
    fecha = DateField('Nueva Fecha', format='%Y-%m-%d',
                    validators=[DataRequired('Por favor seleccione una fecha')])
    
    horario = SelectField('Nuevo Horario',
                        validators=[DataRequired('Por favor seleccione un horario')])
    
    motivo_reprogramacion = TextAreaField('Motivo de la Reprogramación',
                                        validators=[
                                            DataRequired('Por favor indique el motivo de la reprogramación'),
                                            Length(min=10, max=500, 
                                                  message='El motivo debe tener entre 10 y 500 caracteres')
                                        ])
    
    confirmar = BooleanField('Confirmo que deseo reprogramar esta cita',
                           validators=[DataRequired('Debe confirmar la reprogramación')])
    
    cita_id = HiddenField('ID de la Cita', validators=[DataRequired()])
    
    submit = SubmitField('Reprogramar Cita')
    
    def validate_fecha(self, field):
        """Valida que la fecha seleccionada sea en el futuro."""
        if field.data < date.today():
            raise ValidationError('La fecha de la cita no puede ser en el pasado.')
        
        # Verificar que no sea más de 3 meses en el futuro
        max_fecha = date.today() + timedelta(days=90)
        if field.data > max_fecha:
            raise ValidationError('No puede reprogramar citas con más de 3 meses de anticipación.')