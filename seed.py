from app import app, db, User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='demo@primar.cl').first():
        demo = User(nombre="Usuario Demo", email="demo@primar.cl", rol="admin", activo=True)
        demo.set_password("demo123")
        db.session.add(demo)
        db.session.commit()
        print("Usuario demo creado")
