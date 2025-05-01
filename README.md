# Plataforma de Telemedicina para Centros Médicos Públicos

## Descripción
Sistema web diseñado para facilitar consultas médicas remotas a pacientes que no pueden acudir físicamente a un centro médico. Permite videoconferencias, emisión de recetas y órdenes de laboratorio con validación digital, y manejo seguro de historias clínicas.

## Tecnologías utilizadas
- Backend: Python 3.9+, Flask 2.2+
- ORM: SQLAlchemy
- Base de datos: PostgreSQL (producción), SQLite (desarrollo)
- Frontend: Bootstrap 5, JavaScript, WebRTC, Socket.IO

## Requisitos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Entorno virtual de Python (recomendado)

## Instalación para desarrollo

1. Clonar el repositorio:
   ```
   git clone [URL_DEL_REPOSITORIO]
   cd telemedicina
   ```

2. Crear y activar entorno virtual:
   ```
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```
   # Copiar archivo de ejemplo
   cp .env.example .env
   # Editar el archivo .env con tus configuraciones
   ```

5. Inicializar la base de datos:
   ```
   flask db init
   flask db migrate -m "Migración inicial"
   flask db upgrade
   ```

6. Crear superusuario para administración:
   ```
   flask create-superuser
   ```

7. Ejecutar el servidor de desarrollo:
   ```
   flask run
   # o alternativamente
   python run.py
   ```

## Estructura del proyecto
La estructura del proyecto sigue el patrón MVC adaptado a Flask:
- `app/models/`: Modelos de datos (SQLAlchemy)
- `app/views/`: Vistas (Blueprints de Flask)
- `app/forms/`: Formularios (Flask-WTF)
- `app/templates/`: Plantillas (Jinja2)
- `app/static/`: Archivos estáticos
- `app/utils/`: Utilidades varias

## Licencia
Este proyecto es software de código abierto.
# telemedicina
# telemedicina
