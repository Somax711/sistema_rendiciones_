from app import _seed_demo_user, create_app
from models import db, User


def init_database():
    app = create_app()
    
    with app.app_context():
        print("Creando tablas...")
        db.create_all()
        print("✓ Tablas creadas exitosamente")
        
        # Crear admin si no existe
        admin = User.query.filter_by(email='admin@primar.cl').first()
        if not admin:
            print("\nCreando usuario administrador por defecto...")
            admin = User(
                nombre='Administrador',
                email='admin@primar.cl',
                rol='admin',
                activo=True,
                email_verificado=True,
                departamento='TI',
                cargo='Administrador del Sistema'
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            db.session.commit()
            print("✓ Usuario administrador creado:")
            print("  Email: admin@primar.cl")
            print("  Contraseña: Admin123!")
        else:
            print("\n✓ El usuario administrador ya existe")

        # Crear usuario demo
        _seed_demo_user()
        print("✓ Usuario demo listo: demo@primar.cl")
        
        print("\n✓ Base de datos inicializada correctamente")
        print("Puedes iniciar la aplicación con: python app.py")


if __name__ == '__main__':
    init_database()