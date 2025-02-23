# seed_user.py
from config_db import app, db, Usuario, bcrypt

with app.app_context():
    # Verifica si el usuario ya existe para evitar duplicados
    user = Usuario.query.filter_by(email="gerardo.barberena@icloud.com").first()
    if not user:
        hashed_password = bcrypt.generate_password_hash("deltamaxi45").decode("utf-8")
        user = Usuario(email="gerardo.barberena@icloud.com", password=hashed_password)
        db.session.add(user)
        db.session.commit()
        print("Usuario creado exitosamente")
    else:
        print("El usuario ya existe")
