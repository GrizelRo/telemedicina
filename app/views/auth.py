from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash
import uuid
from datetime import datetime, timedelta

from app.models.usuario import Usuario, Rol, HistorialAcceso
from app.models.tipos_usuario import Paciente, Medico, AdministradorCentro, AdministradorSistema
from app.forms.auth import (LoginForm, RegistroPacienteForm, RegistroMedicoForm, 
                           RegistroAdminCentroForm, CambioPasswordForm, 
                           RecuperarPasswordForm, RestablecerPasswordForm, 
                           PerfilUsuarioForm)
from app.extensions import db
from app.utils.email import enviar_email
from app.utils.security import generar_token, verificar_token
from app.utils.decorators import admin_required, admin_centro_required, sin_autenticar

# Crear el blueprint de autenticación
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
@sin_autenticar
def login():
    """Vista para el inicio de sesión."""
    form = LoginForm()
    
    if form.validate_on_submit():
        # Buscar al usuario por número de documento
        usuario = Usuario.query.filter_by(numero_documento=form.numero_documento.data).first()
        
        if usuario and usuario.verificar_password(form.password.data):
            # Verificar si el usuario está activo
            if not usuario.activo:
                flash('Su cuenta está desactivada. Por favor contacte al administrador.', 'danger')
                return render_template('auth/login.html', form=form)
                
            # Crear sesión
            login_user(usuario, remember=form.recordar.data)
            
            # Registrar el acceso
            usuario.registrar_acceso()
            
            # Guardar información de acceso
            acceso = HistorialAcceso(usuario_id=usuario.id)
            acceso.direccion_ip = request.remote_addr
            acceso.user_agent = request.user_agent.string
            
            db.session.add(acceso)
            db.session.commit()
            
            # Redireccionar a la página solicitada o a la página de inicio
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redireccionar según el rol
            if usuario.es_admin_sistema:
                return redirect(url_for('admin.inicio'))
            elif usuario.es_admin_centro:
                return redirect(url_for('admin_centro.inicio'))
            elif usuario.es_medico:
                return redirect(url_for('medico.inicio'))
            else:
                return redirect(url_for('paciente.inicio'))
        else:
            flash('Número de documento o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Vista para cerrar sesión."""
    logout_user()
    flash('Ha cerrado sesión correctamente.', 'success')
    return redirect(url_for('main.inicio'))


@auth_bp.route('/registro/paciente', methods=['GET', 'POST'])
@sin_autenticar
def registro_paciente():
    """Vista para el registro de pacientes."""
    form = RegistroPacienteForm()
    
    if form.validate_on_submit():
        # Crear usuario
        usuario = Usuario(
            tipo_documento=form.tipo_documento.data,
            numero_documento=form.numero_documento.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            genero=form.genero.data,
            email=form.email.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data,
            ciudad=form.ciudad.data,
            departamento=form.departamento.data,
            password=form.password.data
        )
        
        # Asignar rol de paciente
        rol_paciente = Rol.query.filter_by(nombre='paciente').first()
        usuario.roles.append(rol_paciente)
        
        # Crear paciente
        paciente = Paciente(
            usuario=usuario,
            grupo_sanguineo=form.grupo_sanguineo.data,
            alergias=form.alergias.data,
            enfermedades_cronicas=form.enfermedades_cronicas.data,
            contacto_emergencia_nombre=form.contacto_emergencia_nombre.data,
            contacto_emergencia_telefono=form.contacto_emergencia_telefono.data,
            contacto_emergencia_relacion=form.contacto_emergencia_relacion.data,
            seguro_medico=form.seguro_medico.data,
            numero_seguro=form.numero_seguro.data
        )
        
        # Guardar en la base de datos
        db.session.add(usuario)
        db.session.add(paciente)
        db.session.commit()
        
        # Enviar email de confirmación
        token = generar_token(usuario.email)
        enviar_email(
            destinatario=usuario.email,
            asunto='Confirme su cuenta en la Plataforma de Telemedicina',
            template='email/confirmar_cuenta',
            usuario=usuario,
            token=token
        )
        
        flash('¡Registro exitoso! Por favor revise su correo para confirmar su cuenta.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/registro_paciente.html', form=form)


@auth_bp.route('/registro/medico', methods=['GET', 'POST'])
@sin_autenticar
def registro_medico():
    """Vista para el registro de médicos."""
    from app.models.tipos_usuario import Especialidad
    
    form = RegistroMedicoForm()
    
    # Cargar las especialidades para el select
    form.especialidad_id.choices = [(e.id, e.nombre) for e in Especialidad.query.order_by('nombre')]
    
    if form.validate_on_submit():
        # Crear usuario
        usuario = Usuario(
            tipo_documento=form.tipo_documento.data,
            numero_documento=form.numero_documento.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            genero=form.genero.data,
            email=form.email.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data,
            ciudad=form.ciudad.data,
            departamento=form.departamento.data,
            password=form.password.data,
            activo=False  # Los médicos deben ser validados por un administrador
        )
        
        # Asignar rol de médico
        rol_medico = Rol.query.filter_by(nombre='medico').first()
        usuario.roles.append(rol_medico)
        
        # Crear médico
        medico = Medico(
            usuario=usuario,
            numero_licencia=form.numero_licencia.data,
            especialidad_id=form.especialidad_id.data,
            titulo_profesional=form.titulo_profesional.data,
            biografia=form.biografia.data,
            anos_experiencia=form.anos_experiencia.data,
            disponible=False  # No disponible hasta ser aprobado
        )
        
        # Guardar en la base de datos
        db.session.add(usuario)
        db.session.add(medico)
        db.session.commit()
        
        # Notificar a los administradores
        # Esto podría ser un email o una notificación interna
        administradores = Usuario.query.filter(Usuario.roles.any(nombre='administrador_sistema')).all()
        for admin in administradores:
            enviar_email(
                destinatario=admin.email,
                asunto='Nueva solicitud de registro médico',
                template='email/notificar_registro_medico',
                admin=admin,
                medico=medico
            )
        
        flash('Su solicitud de registro como médico ha sido enviada. '
              'Un administrador revisará sus credenciales y se comunicará con usted.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/registro_medico.html', form=form)


@auth_bp.route('/registro/admin-centro', methods=['GET', 'POST'])
@admin_required
def registro_admin_centro():
    """Vista para el registro de administradores de centro médico."""
    from app.models.centro_medico import CentroMedico
    
    form = RegistroAdminCentroForm()
    
    # Cargar los centros médicos para el select
    form.centro_medico_id.choices = [(c.id, c.nombre) for c in CentroMedico.query.order_by('nombre')]
    
    if form.validate_on_submit():
        # Crear usuario
        usuario = Usuario(
            tipo_documento=form.tipo_documento.data,
            numero_documento=form.numero_documento.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            genero=form.genero.data,
            email=form.email.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data,
            ciudad=form.ciudad.data,
            departamento=form.departamento.data,
            password=form.password.data
        )
        
        # Asignar rol de administrador de centro
        rol_admin_centro = Rol.query.filter_by(nombre='administrador_centro').first()
        usuario.roles.append(rol_admin_centro)
        
        # Crear administrador de centro
        admin_centro = AdministradorCentro(
            usuario=usuario,
            centro_medico_id=form.centro_medico_id.data,
            cargo=form.cargo.data,
            departamento=form.departamento.data
        )
        
        # Guardar en la base de datos
        db.session.add(usuario)
        db.session.add(admin_centro)
        db.session.commit()
        
        # Enviar email de confirmación
        token = generar_token(usuario.email)
        enviar_email(
            destinatario=usuario.email,
            asunto='Cuenta de Administrador de Centro Médico Creada',
            template='email/confirmar_cuenta_admin',
            usuario=usuario,
            token=token
        )
        
        flash('Administrador de centro médico registrado exitosamente.', 'success')
        return redirect(url_for('admin.administradores'))
    
    return render_template('auth/registro_admin_centro.html', form=form)


@auth_bp.route('/confirmar/<token>')
def confirmar_email(token):
    """Confirma la cuenta de un usuario a través del token enviado por email."""
    # Verificar el token
    email = verificar_token(token)
    if not email:
        flash('El enlace de confirmación es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Buscar al usuario por email
    usuario = Usuario.query.filter_by(email=email).first()
    if not usuario:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Si el usuario ya está activo
    if usuario.activo:
        flash('Su cuenta ya está confirmada. Por favor inicie sesión.', 'info')
        return redirect(url_for('auth.login'))
    
    # Activar la cuenta
    usuario.activo = True
    db.session.commit()
    
    flash('¡Su cuenta ha sido confirmada! Ahora puede iniciar sesión.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/recuperar-password', methods=['GET', 'POST'])
@sin_autenticar
def recuperar_password():
    """Vista para solicitar recuperación de contraseña."""
    form = RecuperarPasswordForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        # Siempre mostrar este mensaje, incluso si el email no existe
        # para evitar enumerar usuarios
        flash('Si su correo está registrado, recibirá instrucciones para restablecer su contraseña.', 'info')
        
        if usuario:
            token = generar_token(usuario.email)
            enviar_email(
                destinatario=usuario.email,
                asunto='Recuperación de Contraseña',
                template='email/recuperar_password',
                usuario=usuario,
                token=token
            )
            
        return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_password.html', form=form)


@auth_bp.route('/restablecer-password/<token>', methods=['GET', 'POST'])
@sin_autenticar
def restablecer_password(token):
    """Vista para restablecer la contraseña."""
    # Verificar el token
    email = verificar_token(token)
    if not email:
        flash('El enlace para restablecer la contraseña es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.recuperar_password'))
    
    form = RestablecerPasswordForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario:
            usuario.password = form.password.data
            db.session.commit()
            
            flash('Su contraseña ha sido restablecida. Ahora puede iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('auth.recuperar_password'))
    
    return render_template('auth/restablecer_password.html', form=form)


@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """Vista para ver y editar el perfil de usuario."""
    form = PerfilUsuarioForm(usuario_original=current_user)
    
    # Cargar los datos actuales al cargar la página
    if request.method == 'GET':
        form.nombre.data = current_user.nombre
        form.apellido.data = current_user.apellido
        form.telefono.data = current_user.telefono
        form.direccion.data = current_user.direccion
        form.ciudad.data = current_user.ciudad
        form.departamento.data = current_user.departamento
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        current_user.nombre = form.nombre.data
        current_user.apellido = form.apellido.data
        current_user.telefono = form.telefono.data
        current_user.direccion = form.direccion.data
        current_user.ciudad = form.ciudad.data
        current_user.departamento = form.departamento.data
        
        # Si el email cambió, pedir confirmación
        if form.email.data != current_user.email:
            # Guardar el email anterior
            email_anterior = current_user.email
            
            # Actualizar el email
            current_user.email = form.email.data
            current_user.activo = False  # Desactivar hasta confirmar
            
            # Guardar cambios
            db.session.commit()
            
            # Enviar email de confirmación al nuevo correo
            token = generar_token(current_user.email)
            enviar_email(
                destinatario=current_user.email,
                asunto='Confirme su nuevo correo electrónico',
                template='email/confirmar_cambio_email',
                usuario=current_user,
                token=token
            )
            
            # Notificar al correo anterior
            enviar_email(
                destinatario=email_anterior,
                asunto='Cambio de correo electrónico en su cuenta',
                template='email/notificar_cambio_email',
                usuario=current_user
            )
            
            # Cerrar sesión para forzar reconfirmación
            logout_user()
            
            flash('Su correo electrónico ha sido actualizado. '
                 'Por favor confirme su nuevo correo para activar su cuenta.', 'info')
            return redirect(url_for('auth.login'))
        
        # Si solo se actualizaron otros datos
        db.session.commit()
        flash('Perfil actualizado correctamente.', 'success')
        return redirect(url_for('auth.perfil'))
    
    # Mostrar información adicional según el rol
    datos_adicionales = {}
    
    if current_user.es_paciente and current_user.paciente:
        datos_adicionales['Tipo'] = 'Paciente'
        datos_adicionales['Grupo Sanguíneo'] = current_user.paciente.grupo_sanguineo or 'No especificado'
        
    elif current_user.es_medico and current_user.medico:
        datos_adicionales['Tipo'] = 'Médico'
        datos_adicionales['Especialidad'] = current_user.medico.especialidad.nombre
        datos_adicionales['Licencia'] = current_user.medico.numero_licencia
        
    elif current_user.es_admin_centro and current_user.admin_centro:
        datos_adicionales['Tipo'] = 'Administrador de Centro'
        datos_adicionales['Centro'] = current_user.admin_centro.centro_medico.nombre
        datos_adicionales['Cargo'] = current_user.admin_centro.cargo
        
    elif current_user.es_admin_sistema and current_user.admin_sistema:
        datos_adicionales['Tipo'] = 'Administrador del Sistema'
        datos_adicionales['Nivel'] = current_user.admin_sistema.nivel_acceso
    
    return render_template('auth/perfil.html', form=form, datos_adicionales=datos_adicionales)


@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    """Vista para cambiar la contraseña."""
    form = CambioPasswordForm()
    
    if form.validate_on_submit():
        if current_user.verificar_password(form.password_actual.data):
            current_user.password = form.password_nuevo.data
            db.session.commit()
            
            flash('Su contraseña ha sido actualizada correctamente.', 'success')
            return redirect(url_for('auth.perfil'))
        else:
            flash('La contraseña actual es incorrecta.', 'danger')
    
    return render_template('auth/cambiar_password.html', form=form)