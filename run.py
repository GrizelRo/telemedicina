import os
from app import create_app
from app.extensions import socketio

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Usar Socket.IO en lugar de app.run()
    socketio.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=app.config['DEBUG']
    )