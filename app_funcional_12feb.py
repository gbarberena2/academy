from flask import Flask, render_template, request, jsonify
import csv
import random
from openai import OpenAI

# Configuración de OpenAI
client = OpenAI(api_key="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")

app = Flask(__name__)

def obtener_pregunta():
    """Lee el archivo CSV y selecciona una pregunta aleatoria."""
    with open("preguntas_01.csv", "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        preguntas = [row for row in reader if row["pregunta"] and not row["pregunta"].startswith("Pag=")]
    return random.choice(preguntas) if preguntas else None

def generar_opciones_multiple(pregunta):
    """Usa el modelo de OpenAI para generar opciones múltiples."""
    prompt = (
        f"Genera 4 opciones de respuesta para la siguiente pregunta de inteligencia artificial. "
        f"Una debe ser correcta y las otras tres incorrectas. La dificultad debe ser alta.\n\n"
        f"Pregunta: {pregunta}\n\n"
        "Formato de salida:\n"
        "Correcta: <respuesta correcta>\n"
        "Incorrecta1: <respuesta incorrecta 1>\n"
        "Incorrecta2: <respuesta incorrecta 2>\n"
        "Incorrecta3: <respuesta incorrecta 3>"
    )
    
    response = client.chat.completions.create(
        model="gpt-4",  # Usa el modelo que tengas disponible
        messages=[{"role": "user", "content": prompt}]
    )
    
    respuesta = response.choices[0].message.content
    opciones = {}
    for linea in respuesta.split("\n"):
        if linea.startswith("Correcta:"):
            opciones["correcta"] = linea.replace("Correcta:", "").strip()
        elif linea.startswith("Incorrecta1:"):
            opciones["incorrecta1"] = linea.replace("Incorrecta1:", "").strip()
        elif linea.startswith("Incorrecta2:"):
            opciones["incorrecta2"] = linea.replace("Incorrecta2:", "").strip()
        elif linea.startswith("Incorrecta3:"):
            opciones["incorrecta3"] = linea.replace("Incorrecta3:", "").strip()
    
    return opciones

@app.route("/")
def index():
    pregunta = obtener_pregunta()
    if pregunta:
        opciones = generar_opciones_multiple(pregunta["pregunta"])
        opciones_lista = [opciones["correcta"], opciones["incorrecta1"], opciones["incorrecta2"], opciones["incorrecta3"]]
        random.shuffle(opciones_lista)
        return render_template("index.html", pregunta=pregunta["pregunta"], opciones=opciones_lista, correcta=opciones["correcta"])
    else:
        return "No hay preguntas disponibles."

@app.route("/evaluar", methods=["POST"])
def evaluar():
    data = request.get_json()
    seleccion = data.get("respuesta")
    correcta = data.get("correcta")
    
    resultado = "Correcto! 🎉" if seleccion == correcta else "Incorrecto ❌. Inténtalo de nuevo."
    return jsonify({"resultado": resultado})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5516, debug=True)
