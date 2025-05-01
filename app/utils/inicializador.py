from app.extensions import db
from app.models.usuario import Rol, Usuario
from app.models.tipos_usuario import AdministradorSistema, Especialidad
import datetime

def crear_datos_iniciales():
    """
    Crea los datos iniciales necesarios para el funcionamiento del sistema.
    Incluye roles, especialidades médicas y un usuario administrador por defecto.
    """
    crear_roles()
    crear_especialidades()
    crear_admin_por_defecto()
    
    # Confirmar cambios
    db.session.commit()


def crear_roles():
    """Crea los roles básicos del sistema si no existen."""
    roles = [
        ('paciente', 'Usuario que puede agendar citas y recibir atención médica'),
        ('medico', 'Profesional médico que brinda atención a los pacientes'),
        ('administrador_centro', 'Administrador de un centro médico específico'),
        ('administrador_sistema', 'Administrador general de la plataforma')
    ]
    
    for nombre, descripcion in roles:
        # Verificar si el rol ya existe
        rol = Rol.query.filter_by(nombre=nombre).first()
        if not rol:
            rol = Rol(nombre=nombre, descripcion=descripcion)
            db.session.add(rol)
    
    db.session.commit()


def crear_especialidades():
    """Crea las especialidades médicas básicas si no existen."""
    especialidades = [
        ('Medicina General', 'Atención médica básica y preventiva'),
        ('Pediatría', 'Atención médica para niños y adolescentes'),
        ('Ginecología', 'Salud femenina y reproductiva'),
        ('Cardiología', 'Diagnóstico y tratamiento de enfermedades del corazón'),
        ('Dermatología', 'Enfermedades de la piel, cabello y uñas'),
        ('Oftalmología', 'Enfermedades de los ojos'),
        ('Otorrinolaringología', 'Oídos, nariz y garganta'),
        ('Traumatología', 'Sistema musculoesquelético'),
        ('Neurología', 'Sistema nervioso'),
        ('Psiquiatría', 'Salud mental'),
        ('Endocrinología', 'Sistema endocrino y metabolismo'),
        ('Gastroenterología', 'Sistema digestivo'),
        ('Urología', 'Sistema urinario y reproductor masculino'),
        ('Nefrología', 'Riñones'),
        ('Neumología', 'Sistema respiratorio'),
        ('Geriatría', 'Atención a adultos mayores'),
        ('Reumatología', 'Enfermedades reumáticas'),
        ('Oncología', 'Diagnóstico y tratamiento del cáncer'),
        ('Hematología', 'Enfermedades de la sangre'),
        ('Nutrición', 'Alimentación y nutrición')
    ]
    
    for nombre, descripcion in especialidades:
        # Verificar si la especialidad ya existe
        especialidad = Especialidad.query.filter_by(nombre=nombre).first()
        if not especialidad:
            especialidad = Especialidad(nombre=nombre, descripcion=descripcion)
            db.session.add(especialidad)
    
    db.session.commit()


def crear_admin_por_defecto():
    """
    Crea un usuario administrador por defecto si no existe uno.
    Este usuario se utilizará para la configuración inicial del sistema.
    """
    # Verificar si ya existe un administrador
    rol_admin = Rol.query.filter_by(nombre='administrador_sistema').first()
    admin_existente = Usuario.query.filter(Usuario.roles.contains(rol_admin)).first()
    
    if not admin_existente:
        # Crear usuario administrador
        admin = Usuario(
            tipo_documento='dni',
            numero_documento='admin123',
            nombre='Administrador',
            apellido='Sistema',
            fecha_nacimiento=datetime.date(2000, 1, 1),  # Fecha ficticia
            genero='otro',
            email='admin@telemedicina.org',
            telefono='0000000000',
            direccion='Dirección del Sistema',
            ciudad='Ciudad',
            departamento='Departamento',
            activo=True
        )
        admin.password = 'admin123'  # ¡Cambiar en producción!
        
        # Asignar rol de administrador
        admin.roles.append(rol_admin)
        
        # Crear perfil de administrador
        admin_perfil = AdministradorSistema(
            usuario=admin,
            nivel_acceso='completo',
            departamento='Sistemas',
            notas='Administrador creado automáticamente por el sistema'
        )
        
        db.session.add(admin)
        db.session.add(admin_perfil)
        db.session.commit()