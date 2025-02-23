from config_db import db, bcrypt, Usuario, app

def actualizar_password():
    with app.app_context():
        email = "gerardo.barberena@icloud.com"
        password = "deltamaxi45"  # La contraseña original que debe encriptarse

        # Buscar el usuario
        user = Usuario.query.filter_by(email=email).first()
        if not user:
            print("⚠️ Usuario no encontrado.")
            return
        
        # Generar un nuevo hash de contraseña con bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Actualizar la contraseña en la base de datos
        user.password = hashed_password
        db.session.commit()
        
        print("✅ Contraseña actualizada correctamente.")

# Ejecutar la actualización
if __name__ == "__main__":
    actualizar_password()
