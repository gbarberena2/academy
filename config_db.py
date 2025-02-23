from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template
import os
from sqlalchemy import text
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la base de datos PostgreSQL
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Crear instancia de Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"  # Cambiar por una clave segura

# Opciones de seguridad para cookies (opcionales, ajusta según tu entorno)
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Configurar Flask-Limiter
limiter = Limiter(get_remote_address, app=app)

@app.errorhandler(429)
def ratelimit_error(e):
    return render_template("429.html"), 429

# Inicializar extensiones
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor, inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"


############################################################
#                     MODELOS                              #
############################################################

class Nota(db.Model):
    __tablename__ = "notas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey("preguntas.id"), nullable=False)

    # Estos campos te permiten guardar la info de la pregunta
    no_pregunta = db.Column(db.Integer, nullable=True)
    pagina = db.Column(db.Integer, nullable=True)

    # Contenido de la nota
    contenido = db.Column(db.Text, nullable=False)

    # Fecha de creación de la nota
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaciones (opcional, si quieres navegar inversamente)
    usuario = db.relationship("Usuario", backref="notas", lazy=True)
    pregunta = db.relationship("Pregunta", backref="notas", lazy=True)


class ResumenExamenResultados(db.Model):
    __tablename__ = "resumen_examen_resultados"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_finalizacion = db.Column(db.DateTime, nullable=False)
    porcentaje = db.Column(db.Float, nullable=False)

    # Relación con Usuario (opcional, para poder acceder al usuario)
    usuario = db.relationship("Usuario", backref="resumenes_examen", lazy=True)



class DetalleExamenRespuesta(db.Model):
    __tablename__ = "detalle_examen_respuesta"

    id = db.Column(db.Integer, primary_key=True)
    config_id = db.Column(db.Integer, db.ForeignKey("config_examen_ml.id"), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey("preguntas.id"), nullable=False)

    # Almacena también el texto de la pregunta, para referencia rápida
    pregunta_texto = db.Column(db.Text, nullable=False)

    opcion_correcta = db.Column(db.Text, nullable=False)
    opcion_incorrecta1 = db.Column(db.Text, nullable=False)
    opcion_incorrecta2 = db.Column(db.Text, nullable=False)
    opcion_incorrecta3 = db.Column(db.Text, nullable=False)

    # Relación con ConfigExamenML (opcional, si deseas acceder inversamente)
    # config = db.relationship("ConfigExamenML", backref="detalles_respuesta")



class ConfigExamenML(db.Model):
    __tablename__ = "config_examen_ml"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    num_preguntas = db.Column(db.Integer, nullable=False)
    fecha_configuracion = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Agregar clave foránea para relacionar con `examenes`
    examen_id = db.Column(db.Integer, db.ForeignKey("examenes.id"), nullable=True)

    # ✅ Relación con Examen (opcional, si deseas acceder al examen desde ConfigExamenML)
    examen = db.relationship("Examen", backref="configuracion_ml", lazy=True)



# ------------------ Modelo Usuario ------------------ #
class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


# ------------------ Modelo Pregunta ------------------ #
class Pregunta(db.Model):
    __tablename__ = "preguntas"

    id = db.Column(db.Integer, primary_key=True)
    no_pregunta = db.Column(db.Integer, unique=True, nullable=False)
    pregunta = db.Column(db.Text, nullable=False)
    pagina = db.Column(db.Integer, nullable=True)

    # Relación con Respuesta
    respuestas = db.relationship("Respuesta", backref="pregunta", lazy=True)


# ------------------ Modelo Respuesta ------------------ #
class Respuesta(db.Model):
    __tablename__ = "respuestas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)  # Puede ser anónimo
    pregunta_id = db.Column(db.Integer, db.ForeignKey("preguntas.id"), nullable=False)
    respuesta_usuario = db.Column(db.Text, nullable=False)
    es_correcta = db.Column(db.Boolean, nullable=False)

    # Almacenar las opciones generadas por OpenAI
    opcion_correcta = db.Column(db.Text, nullable=False)
    opcion_incorrecta1 = db.Column(db.Text, nullable=False)
    opcion_incorrecta2 = db.Column(db.Text, nullable=False)
    opcion_incorrecta3 = db.Column(db.Text, nullable=False)

    # Relación con Usuario (opcional)
    usuario = db.relationship("Usuario", backref="respuestas")


# ------------------ Modelo Examen ------------------ #
class Examen(db.Model):
    __tablename__ = "examenes"  # IMPORTANTE para coincidir con 'examenes.id'

    id = db.Column(db.Integer, primary_key=True)
    tema = db.Column(db.String(255), nullable=False)
    nivel = db.Column(db.String(50), nullable=False)
    sistema = db.Column(db.String(50), nullable=False)
    fecha_realizacion = db.Column(db.DateTime, nullable=True)
    resultado = db.Column(db.Float, nullable=True)

    # Definimos las relaciones AQUÍ:
    # 1) "detalles" para las preguntas generadas
    # 2) "historial" para el registro del usuario (HistorialExamen)
    detalles = db.relationship("DetalleExamen", backref="examen", lazy=True)
    historial = db.relationship("HistorialExamen", backref="examen", lazy=True)


# ------------------ Modelo DetalleExamen ------------------ #
class DetalleExamen(db.Model):
    __tablename__ = "detalle_examen"

    id = db.Column(db.Integer, primary_key=True)
    examen_id = db.Column(db.Integer, db.ForeignKey("examenes.id"), nullable=False)

    pregunta = db.Column(db.Text, nullable=False)
    opcion_correcta = db.Column(db.Text, nullable=True)
    opcion_incorrecta1 = db.Column(db.Text, nullable=True)
    opcion_incorrecta2 = db.Column(db.Text, nullable=True)
    opcion_incorrecta3 = db.Column(db.Text, nullable=True)

    # NO definimos relationship con Examen aquí, porque
    # Examen ya definió "detalles = db.relationship(..., backref='examen')"


class HistorialExamen(db.Model):
    __tablename__ = "historial_examen"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    examen_id = db.Column(db.Integer, db.ForeignKey("examenes.id"), nullable=False)
    
    # ✅ Asegurar que la clave foránea apunta a `detalle_examen_respuesta`
    pregunta_id = db.Column(db.Integer, db.ForeignKey("detalle_examen_respuesta.id"), nullable=False)

    pregunta = db.Column(db.Text, nullable=False)
    respuesta_usuario = db.Column(db.Text, nullable=True)
    respuesta_correcta = db.Column(db.Text, nullable=False)
    es_correcta = db.Column(db.Boolean, default=False)

    fecha_realizacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    resultado = db.Column(db.Float, nullable=True)





############################################################
#                  LOGIN MANAGER                          #
############################################################

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


############################################################
#          FUNCIÓN PARA PROBAR CONEXIÓN A LA BD           #
############################################################

def probar_conexion():
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            print("✅ Conectado a PostgreSQL exitosamente")
    except Exception as e:
        print(f"❌ Error al conectar con PostgreSQL: {e}")


############################################################
#     CREAR LAS TABLAS AL EJECUTAR DIRECTAMENTE ESTE PY    #
############################################################

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()   # OPCIONAL en desarrollo: borra todo
        db.create_all() # Crea las tablas según estos modelos
        print("✅ Base de datos inicializada correctamente")
        probar_conexion()
