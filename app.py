import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import current_user
from config import get_config
from models import db, login_manager, User
from utils.filters import register_filters
from routes.download import download_bp


def create_app():
    """Factory para crear la aplicación Flask"""
    app = Flask(__name__)

    # Cargar configuración
    config = get_config()
    app.config.from_object(config)

    # Base de datos — Railway inyecta DATABASE_URL 
    db_url = os.environ.get("DATABASE_URL", "sqlite:///rendiciones.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debes iniciar sesión para acceder a esta página.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        if user_id is None:
            return None
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Crear carpetas necesarias
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'comprobantes'), exist_ok=True)

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.rendiciones import rendiciones_bp
    from routes.aprobaciones import aprobaciones_bp
    from routes.usuarios import usuarios_bp
    from routes.reportes import reportes_bp
    from routes.notificaciones import notificaciones_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(rendiciones_bp)
    app.register_blueprint(aprobaciones_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(notificaciones_bp)
    app.register_blueprint(download_bp)

    # Registrar filtros personalizados
    register_filters(app)

    # Context processor
    @app.context_processor
    def inject_globals():
        notificaciones_count = 0
        if current_user.is_authenticated:
            notificaciones_count = current_user.get_notificaciones_no_leidas()
        return {
            'notificaciones_count': notificaciones_count,
            'app_name': 'Sistema de Rendiciones Primar'
        }

    #  Ruta temporal para crear admin en producción 
    @app.route('/setup-admin-primar')
    def setup_admin():
        try:
            db.create_all()
            admin = User.query.filter_by(email='admin@primar.cl').first()
            if not admin:
                admin = User(
                    nombre='Administrador',
                    email='admin@primar.cl',
                    rol='admin',
                    activo=True
                )
                admin.set_password('Admin123!')
                db.session.add(admin)
                db.session.commit()
                return 'Admin creado OK — email: admin@primar.cl / clave: Admin123!'
            else:
                admin.set_password('Admin123!')
                db.session.commit()
                return 'Contrasena reseteada OK — email: admin@primar.cl / clave: Admin123!'
        except Exception as e:
            return f'Error: {str(e)}'

    #  Ruta principal 
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Comando CLI para inicializar BD
    @app.cli.command()
    def init_db():
        """Inicializa la base de datos"""
        db.create_all()
        print('Base de datos inicializada correctamente')

    # Comando CLI para crear admin
    @app.cli.command()
    def create_admin():
        """Crea un usuario administrador"""
        admin = User.query.filter_by(email='admin@primar.cl').first()
        if admin:
            print('El usuario admin ya existe')
            return
        admin = User(
            nombre='Administrador',
            email='admin@primar.cl',
            rol='admin',
            activo=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        print('Admin creado — email: admin@primar.cl / clave: Admin123!')

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )