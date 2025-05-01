import click
from flask.cli import with_appcontext
from datetime import datetime

from app.extensions import db
from app.models.usuario import Usuario, Rol
from app.models.tipos_usuario import AdministradorSistema

@click.command('create-superuser')
@click.option('--documento', prompt='Número de documento', help='Número de documento del superusuario')
@click.option('--nombre', prompt='Nombre', help='Nombre del superusuario')
@click.option('--apellido', prompt='Apellido', help='Apellido del superusuario')
@click.option('--email', prompt='Email', help='Email del superusuario')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Contraseña del superusuario')
@with_appcontext
def create_superuser_command(documento, nombre, apellido, email, password):
    """Crea un nuevo superusuario (administrador del sistema)."""
    try:
        # Verificar si ya existe un usuario con ese documento o email
        usuario_existente = Usuario.query.filter(
            (Usuario.numero_documento == documento) | (Usuario.email == email)
        ).first()
        
        if usuario_existente:
            click.echo(click.style(
                f"Error: Ya existe un usuario con ese documento o email.", fg='red'))
            return
        
        # Obtener el rol de administrador
        rol_admin = Rol.query.filter_by(nombre='administrador_sistema').first()
        if not rol_admin:
            click.echo(click.style(
                "Error: No se encontró el rol de administrador. Ejecute primero el inicializador.", fg='red'))
            return
        
        # Crear usuario administrador
        usuario = Usuario(
            tipo_documento='dni',
            numero_documento=documento,
            nombre=nombre,
            apellido=apellido,
            fecha_nacimiento=datetime.now().date(),  # Fecha actual como placeholder
            genero='otro',
            email=email,
            activo=True
        )
        usuario.password = password
        
        # Asignar rol de administrador
        usuario.roles.append(rol_admin)
        
        # Crear perfil de administrador
        admin_perfil = AdministradorSistema(
            usuario=usuario,
            nivel_acceso='completo',
            departamento='Sistemas',
            notas='Superusuario creado mediante comando CLI'
        )
        
        # Guardar en la base de datos
        db.session.add(usuario)
        db.session.add(admin_perfil)
        db.session.commit()
        
        click.echo(click.style(
            f"Superusuario {nombre} {apellido} creado exitosamente.", fg='green'))
            
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"Error: {str(e)}", fg='red'))


@click.command('reset-db')
@click.option('--yes', is_flag=True, help='Confirmar reset sin prompt')
@with_appcontext
def reset_db_command(yes):
    """Elimina todas las tablas y las vuelve a crear."""
    if not yes:
        confirmation = click.prompt(
            '¿Está seguro de que desea eliminar TODOS los datos? (escriba "SI" para confirmar)',
            type=str
        )
        if confirmation != 'SI':
            click.echo('Operación cancelada.')
            return
    
    try:
        click.echo('Eliminando todas las tablas...')
        db.drop_all()
        click.echo('Creando tablas nuevas...')
        db.create_all()
        
        # Recrear datos iniciales
        from app.utils.inicializador import crear_datos_iniciales
        crear_datos_iniciales()
        
        click.echo(click.style('Base de datos reiniciada exitosamente.', fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))