from config_db import db, app

with app.app_context():
    db.drop_all()    # BORRA todas las tablas de la BD
    db.create_all()  # CREA nuevamente las tablas basadas en tus modelos
print("Base de datos reseteada correctamente")
