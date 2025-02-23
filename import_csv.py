import csv
from config_db import app, db, Pregunta  # Importa el modelo ya definido
from sqlalchemy.exc import SQLAlchemyError

def importar_preguntas(csv_file):
    """
    Importa preguntas desde un archivo CSV a la tabla 'preguntas' en PostgreSQL.
    Se omiten las filas cuyo contenido en 'pregunta' empiece por 'Pag='.
    """
    with app.app_context():
        try:
            with open(csv_file, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    # Saltar filas que indiquen la página (ej. "Pag=1")
                    if row["pregunta"].startswith("Pag="):
                        continue

                    nueva_pregunta = Pregunta(
                        no_pregunta=int(row["no_pregunta"]),
                        pregunta=row["pregunta"],
                        pagina=int(row["pagina"]) if row["pagina"] else None
                    )
                    db.session.add(nueva_pregunta)
                    
                db.session.commit()
                print("✅ Preguntas importadas correctamente en la base de datos.")
                
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"❌ Error al importar preguntas: {e}")

if __name__ == "__main__":
    importar_preguntas("preguntas_01.csv")
