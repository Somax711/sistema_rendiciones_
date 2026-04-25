import os
from app import app, db, User
def seed():
    with app.app_context():
        print("Iniciando creación de tablas y usuario demo...")
        # 1. Crear tablas
        db.create_all()
        
        # 2. Verificar usuario demo
        demo_user = User.query.filter_by(email='demo@primar.cl').first()
        
        if not demo_user:
            print("Creando usuario demo...")
            # Ajusta los campos según tu modelo User
            demo = User(
                nombre="Usuario Demo",
                email="demo@primar.cl",
                rol="admin", # o 'administrador'
                activo=True
            )
            
            demo.set_password("demo123") 
            
            db.session.add(demo)
            db.session.commit()
            print(" Usuario demo creado con éxito.")
        else:
            print(" El usuario demo ya existía.")

if __name__ == "__main__":
    seed()
