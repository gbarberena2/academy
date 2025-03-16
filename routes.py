from flask import render_template, request, redirect, url_for, flash, jsonify
import random
from openai import OpenAI
from flask_login import login_user, logout_user, login_required, current_user
from config_db import app, db, bcrypt, Usuario, Pregunta, Respuesta,Examen,DetalleExamen,HistorialExamen,ConfigExamenML,DetalleExamenRespuesta,ResumenExamenResultados,Nota,EstadoExamen




from datetime import datetime  # <-- Agrega esta línea


import os
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la API key desde las variables de entorno
openai_api_key = os.getenv("OPENAI_API_KEY")

# Inicializar el cliente de OpenAI utilizando la clave obtenida
from openai import OpenAI
client = OpenAI(api_key=openai_api_key)

# Configuración de OpenAI
#client = OpenAI(api_key="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")



import random
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from config_db import db, Usuario, Pregunta, ConfigExamenML

def obtener_rango_nivel(nivel):
    if nivel == "Basico":
        return (2, 1000)
    elif nivel == "Basico II":
        return (1000, 3000)
    # ...
    elif nivel == "Avanzado II":
        return (9500, 10500)
    else:
        return (0, 0)  # o un rango inválido

import openai

def generar_opciones_multiple(texto_pregunta):
    # Asegúrate de haber configurado openai.api_key en tu .env o en el arranque
    prompt = (
        f"Genera 4 opciones de respuesta para la siguiente pregunta de Machine Learning. "
        f"Una debe ser correcta y las otras tres incorrectas. La dificultad debe ser alta.\n\n"
        f"Pregunta: {texto_pregunta}\n\n"
        "Formato de salida:\n"
        "Correcta: <respuesta correcta>\n"
        "Incorrecta1: <respuesta incorrecta 1>\n"
        "Incorrecta2: <respuesta incorrecta 2>\n"
        "Incorrecta3: <respuesta incorrecta 3>"
    )

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    contenido = response.choices[0].message.content
    # Parsear el texto devuelto para extraer las 4 opciones
    opciones = {}
    for linea in contenido.split("\n"):
        if linea.startswith("Correcta:"):
            opciones["correcta"] = linea.replace("Correcta:", "").strip()
        elif linea.startswith("Incorrecta1:"):
            opciones["incorrecta1"] = linea.replace("Incorrecta1:", "").strip()
        elif linea.startswith("Incorrecta2:"):
            opciones["incorrecta2"] = linea.replace("Incorrecta2:", "").strip()
        elif linea.startswith("Incorrecta3:"):
            opciones["incorrecta3"] = linea.replace("Incorrecta3:", "").strip()

    return opciones



from openai import OpenAI

def obtener_respuesta_gpt_ml(consulta):
    if not consulta.strip():
        return "Por favor, escribe una consulta."

    # Crea el cliente usando la clase OpenAI (API vieja)
    client = OpenAI(api_key=openai_api_key)

    # Llamada a la API antigua
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": consulta}],
        temperature=0.7
    )

    # Retorna el contenido de la primera respuesta
    return response.choices[0].message.content.strip()



@app.route("/ver_total_examenes")
@login_required
def ver_total_examenes():
    # Consulta todos los exámenes y los ordena por fecha de creación (descendente)
    examenes = Examen.query.order_by(Examen.fecha_creacion.desc()).all()
    return render_template("ver_total_examenes.html", examenes=examenes)




@app.route("/guardar_nota", methods=["POST"])
@login_required
def guardar_nota():
    data = request.get_json()  # <--- IMPORTANTE
    pregunta_id = data.get("pregunta_id")
    no_pregunta = data.get("no_pregunta")
    pagina = data.get("pagina")
    contenido = data.get("contenido")

    if not contenido or not pregunta_id:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    nueva_nota = Nota(
        usuario_id=current_user.id,
        pregunta_id=pregunta_id,
        no_pregunta=no_pregunta,
        pagina=pagina,
        contenido=contenido
    )
    db.session.add(nueva_nota)
    db.session.commit()

    return jsonify({"status": "ok"})






@app.route("/consulta_ayuda", methods=["POST"])
@login_required
def consulta_ayuda():
    data = request.get_json()
    pregunta_user = data.get("consulta", "")

    if not pregunta_user.strip():
        return jsonify({"respuesta": "Por favor, escribe una consulta."})

    # Llamar a la función que procesa la consulta con GPT
    respuesta_modelo = obtener_respuesta_gpt_ml(pregunta_user)

    return jsonify({"respuesta": respuesta_modelo})




@app.route("/procesar_examen/<int:config_id>", methods=["POST"])
@login_required
def procesar_examen(config_id):
    # 1. Obtener la configuración
    config = ConfigExamenML.query.get_or_404(config_id)

    # 2. Obtener las preguntas que se usaron en el template anterior.
    #    Normalmente ya las tenemos en la vista 'examen_ml.html'. 
    #    Si no guardaste esa lista en la BD, vuelve a consultar la tabla 'Pregunta'
    #    filtrando por el rango del nivel y la cantidad. 
    #    Pero lo más sencillo es guardar la "lista de preguntas" en la sesión o en la BD.
    #
    #    Aquí, a modo de ejemplo, se vuelve a consultar:
    rango = obtener_rango_nivel(config.nivel)  # Función que retorne (min, max) según nivel
    preguntas_disponibles = Pregunta.query.filter(
        Pregunta.no_pregunta >= rango[0],
        Pregunta.no_pregunta < rango[1]
    ).all()

    if not preguntas_disponibles:
        flash("No se encontraron preguntas para procesar.", "danger")
        return redirect(url_for("config_examen_ml"))

    # Seleccionar la misma cantidad que la config indica (o todas, si hay menos)
    cantidad_a_seleccionar = min(config.num_preguntas, len(preguntas_disponibles))
    preguntas_seleccionadas = random.sample(preguntas_disponibles, cantidad_a_seleccionar)

    # 3. Para cada pregunta, invocar GPT para generar las opciones y guardar en 'detalle_examen_respuesta'
    for pregunta in preguntas_seleccionadas:
        opciones = generar_opciones_multiple(pregunta.pregunta)  # ver función más abajo

        detalle = DetalleExamenRespuesta(
            config_id=config.id,
            pregunta_id=pregunta.id,
            pregunta_texto=pregunta.pregunta,
            opcion_correcta=opciones["correcta"],
            opcion_incorrecta1=opciones["incorrecta1"],
            opcion_incorrecta2=opciones["incorrecta2"],
            opcion_incorrecta3=opciones["incorrecta3"]
        )
        db.session.add(detalle)

    db.session.commit()

    flash("Examen procesado correctamente. Opciones múltiples generadas.", "success")
    # Podrías redirigir a otra página que muestre los resultados guardados:
    return redirect(url_for("ver_detalle_examen_respuesta", config_id=config.id))


@app.route("/ver_detalle_examen_respuesta/<int:config_id>")
@login_required
def ver_detalle_examen_respuesta(config_id):
    config = ConfigExamenML.query.get_or_404(config_id)
    # Aquí no consultamos DetalleExamenRespuesta, solo la configuración.
    return render_template("ver_detalle_examen_respuesta.html", config=config)




@app.route("/procesar_examen2/<int:config_id>", methods=["POST"])
@login_required
def procesar_examen2(config_id):
    # Obtener la configuración del examen
    config = ConfigExamenML.query.get_or_404(config_id)

    # Recuperar de la sesión los IDs de las preguntas seleccionadas
    preguntas_ids = session.get("preguntas_ids", [])
    if not preguntas_ids:
        flash("No hay preguntas seleccionadas en la sesión.", "danger")
        return redirect(url_for("config_examen_ml"))

    # Cargar las preguntas desde la base de datos
    preguntas = Pregunta.query.filter(Pregunta.id.in_(preguntas_ids)).all()

    # Para cada pregunta, se llama a GPT para generar las opciones múltiples y se guardan
    no_x=0
    for p in preguntas:
        
        print("x::"+str(no_x))

        # Puedes modificar el texto si deseas incluir más datos (como número o página)
        opciones = generar_opciones_multiple(p.pregunta)
        detalle = DetalleExamenRespuesta(
            config_id=config.id,
            pregunta_id=p.id,
            pregunta_texto=p.pregunta,
            opcion_correcta=opciones["correcta"],
            opcion_incorrecta1=opciones["incorrecta1"],
            opcion_incorrecta2=opciones["incorrecta2"],
            opcion_incorrecta3=opciones["incorrecta3"]
        )
        db.session.add(detalle)

    db.session.commit()

    flash("Examen procesado correctamente. Opciones múltiples generadas.", "success")
    return redirect(url_for("ver_detalle_examen_respuesta", config_id=config.id))


from flask import session, redirect, url_for, flash, render_template

@app.route("/iniciar_examen_ml/<int:config_id>")
@login_required
def iniciar_examen_ml(config_id):
    config = ConfigExamenML.query.get_or_404(config_id)
    
    # Asegúrate de que config.examen_id no sea None
    if not config.examen_id:
        flash("No se encontró examen asociado a esta configuración.", "danger")
        return redirect(url_for("dashboard"))

    examen_id = config.examen_id  # El ID real del examen en la tabla `examenes`
    
    # Obtener los detalles de la configuración
    detalles = DetalleExamenRespuesta.query.filter_by(config_id=config_id).all()
    if not detalles:
        flash("No hay preguntas procesadas para este examen.", "danger")
        return redirect(url_for("ver_detalle_examen_respuesta", config_id=config_id))
    
    # Buscar si ya existe un estado en progreso para este usuario y examen
    estado = EstadoExamen.query.filter_by(
        usuario_id=current_user.id,
        examen_id=examen_id,
        status="in_progress"
    ).first()
    
    if not estado:
        # Crear un nuevo estado
        estado = EstadoExamen(
            usuario_id=current_user.id,
            examen_id=examen_id,  # OJO: aquí va el examen_id real
            current_index=0,
            answers={}
        )
        db.session.add(estado)
        db.session.commit()
        print(f"DEBUG: Nuevo estado creado con id: {estado.id}, examen_id={examen_id}")
    else:
        print(f"DEBUG: Estado existente con id: {estado.id}, examen_id={examen_id}")

    # Redirigir a la primera pregunta (índice guardado en el estado)
    return redirect(url_for("mostrar_pregunta_ml", config_id=config_id, idx=estado.current_index))




@app.route("/iniciar_examen_ml/<int:config_id>/pregunta/<int:idx>", methods=["GET", "POST"])
@login_required
def mostrar_pregunta_ml(config_id, idx):
    config = ConfigExamenML.query.get_or_404(config_id)
    if not config.examen_id:
        flash("No se encontró examen asociado a esta configuración.", "danger")
        return redirect(url_for("dashboard"))

    examen_id = config.examen_id
    print(f"DEBUG: mostrar_pregunta_ml => config_id={config_id}, examen_id={examen_id}")

    estado = EstadoExamen.query.filter_by(
        usuario_id=current_user.id,
        examen_id=examen_id,
        status="in_progress"
    ).first()
    print("DEBUG: Estado obtenido:", estado)

    if not estado:
        flash("No has iniciado este examen o ya fue finalizado.", "warning")
        return redirect(url_for("ver_detalle_examen_respuesta", config_id=config_id))

    # Cargar todas las preguntas para este config
    detalles = DetalleExamenRespuesta.query.filter_by(config_id=config_id).all()
    print(f"DEBUG: Total de preguntas cargadas: {len(detalles)}")
    if idx < 0 or idx >= len(detalles):
        flash("Índice de pregunta inválido.", "danger")
        return redirect(url_for("ver_detalle_examen_respuesta", config_id=config_id))

    detalle_id = detalles[idx].id
    pregunta_actual = DetalleExamenRespuesta.query.get_or_404(detalle_id)

    # Obtener la "pregunta base" (información extra, ej. número, página, etc.)
    pregunta_base = Pregunta.query.get(pregunta_actual.pregunta_id)

    if request.method == "POST":
        respuesta_usuario = request.form.get("opcion")
        print("DEBUG: respuesta_usuario recibida =", respuesta_usuario)
        if not respuesta_usuario or respuesta_usuario.strip() == "":
            flash("No seleccionaste ninguna opción.", "warning")
            return redirect(url_for("mostrar_pregunta_ml", config_id=config_id, idx=idx))
        
        # Guardamos la respuesta en el diccionario de estado usando el id del detalle
        estado.answers[str(detalle_id)] = respuesta_usuario
        print("DEBUG: Diccionario answers actualizado =", estado.answers)
        
        # Actualizamos el índice de la siguiente pregunta
        estado.current_index = idx + 1
        db.session.commit()
        print("DEBUG: Estado guardado en BD:", estado.answers)

        if estado.current_index < len(detalles):
            print("DEBUG: Redirigiendo a la pregunta con idx =", estado.current_index)
            return redirect(url_for("mostrar_pregunta_ml", config_id=config_id, idx=estado.current_index))
        else:
            print("DEBUG: Se contestaron todas las preguntas. Redirigiendo a finalizar_examen_ml.")
            return redirect(url_for("finalizar_examen_ml", config_id=config_id))

    # Para GET: se mezclan las opciones antes de mostrar la plantilla
    opciones = [
        pregunta_actual.opcion_correcta,
        pregunta_actual.opcion_incorrecta1,
        pregunta_actual.opcion_incorrecta2,
        pregunta_actual.opcion_incorrecta3
    ]
    random.shuffle(opciones)
    print("DEBUG: Opciones a mostrar:", opciones)

    return render_template(
        "mostrar_pregunta_ml.html",
        pregunta=pregunta_actual,
        pregunta_base=pregunta_base,
        opciones=opciones,
        idx=idx,
        total=len(detalles),
        config_id=config_id
    )





@app.route("/show_questions")
@login_required
def show_questions():
    # Consulta el historial de exámenes para el usuario actual, ordenado por fecha (más reciente primero)
    historial = HistorialExamen.query.filter_by(usuario_id=current_user.id).order_by(HistorialExamen.fecha_realizacion.desc()).all()
    return render_template("show_questions.html", historial=historial)



from datetime import datetime

@app.route("/finalizar_examen_ml/<int:config_id>")
@login_required
def finalizar_examen_ml(config_id):
    config = ConfigExamenML.query.get_or_404(config_id)
    if not config.examen_id:
        flash("No se encontró el examen correspondiente.", "danger")
        return redirect(url_for("dashboard"))

    examen_id = config.examen_id
    estado = EstadoExamen.query.filter_by(
        usuario_id=current_user.id,
        examen_id=examen_id,
        status="in_progress"
    ).first()

    if not estado:
        flash("No tienes un examen activo para finalizar.", "danger")
        return redirect(url_for("ver_detalle_examen_respuesta", config_id=config_id))

    answers = estado.answers
    correctas = 0
    total = len(answers)

    for detalle_id_str, respuesta_usuario in answers.items():
        detalle = DetalleExamenRespuesta.query.get(int(detalle_id_str))
        if not detalle:
            continue
        es_correcta = (respuesta_usuario == detalle.opcion_correcta)
        if es_correcta:
            correctas += 1
        
        # Guardar en HistorialExamen si quieres
        nuevo_historial = HistorialExamen(
            usuario_id=current_user.id,
            examen_id=examen_id,
            pregunta_id=detalle.id,
            pregunta=detalle.pregunta_texto,
            respuesta_usuario=respuesta_usuario,
            respuesta_correcta=detalle.opcion_correcta,
            es_correcta=es_correcta,
            fecha_realizacion=datetime.now()
        )
        db.session.add(nuevo_historial)

    porcentaje = (correctas / total * 100) if total else 0

    # Marcar el examen como finalizado
    examen = Examen.query.get(examen_id)
    if examen:
        examen.fecha_realizacion = datetime.now()
        examen.resultado = porcentaje

    # Marcar el estado como terminado
    estado.status = "finished"
    db.session.commit()

    return render_template(
        "finalizar_examen_ml.html",
        config_id=config_id,
        total=total,
        correctas=correctas,
        porcentaje=porcentaje
    )








@app.route("/ver_graph_ml")
@login_required
def ver_graph_ml():
    # 1. Consultar la tabla con los resultados
    #    Opcional: filtrar solo por el usuario actual, si quieres.
    resultados = ResumenExamenResultados.query.filter_by(usuario_id=current_user.id).order_by(ResumenExamenResultados.fecha_finalizacion).all()

    if not resultados:
        flash("No hay resultados registrados aún.", "warning")
        return redirect(url_for("dashboard"))

    # 2. Extraer los datos para la gráfica
    fechas = [r.fecha_finalizacion for r in resultados]
    porcentajes = [r.porcentaje for r in resultados]

    # 3. Crear la gráfica con matplotlib
    import matplotlib.pyplot as plt
    import io
    import base64

    # Crear figura y eje
    fig, ax = plt.subplots(figsize=(8,4))
    # Trazar la línea con marcadores
    ax.plot(fechas, porcentajes, marker="o", linestyle="-", label="Resultado (%)")

    # Configurar ejes y título
    ax.set_xlabel("Fecha de Finalización")
    ax.set_ylabel("Porcentaje de Aciertos")
    ax.set_title("Evolución de Resultados de Examen")
    ax.grid(True)
    ax.legend()

    # Rotar las etiquetas de fecha si lo deseas
    fig.autofmt_xdate()

    # 4. Convertir la gráfica a base64 para mostrarla en la plantilla
    png_image = io.BytesIO()
    plt.savefig(png_image, format="png", bbox_inches="tight")
    png_image.seek(0)
    graph_url = base64.b64encode(png_image.getvalue()).decode()

    plt.close(fig)  # Cerrar la figura en memoria

    # 5. Renderizar la plantilla con la imagen embebida
    return render_template("ver_graph_ml.html", graph_url=graph_url)


@app.route("/config_examen_ml", methods=["GET", "POST"])
@login_required
def config_examen_ml():
    if request.method == "POST":
        # Recibir datos del formulario
        nivel = request.form.get("nivel")
        num_preguntas_input = request.form.get("num_preguntas")
        aleatorio = request.form.get("aleatorio")  # Si está marcado, su valor puede ser "on" o similar

        # Determinar la cantidad de preguntas a utilizar (máximo 50)
        if aleatorio:
            num_preguntas = random.randint(1, 50)
        else:
            try:
                num_preguntas = int(num_preguntas_input)
                if num_preguntas > 50:
                    num_preguntas = 50
            except ValueError:
                flash("Número de preguntas inválido, se usará un valor por defecto.", "warning")
                num_preguntas = 10

        # Guardar la configuración en la tabla config_examen_ml
        config = ConfigExamenML(
            usuario_id=current_user.id,
            nivel=nivel,
            num_preguntas=num_preguntas
        )
        db.session.add(config)
        db.session.commit()

        # ✅ Crear un nuevo examen en `examenes` y asociarlo a la configuración
        nuevo_examen = Examen(
            tema="Machine Learning",
            nivel=nivel,
            sistema="multiple"
        )
        db.session.add(nuevo_examen)
        db.session.commit()

        # Asociar el ID del examen creado con la configuración
        config.examen_id = nuevo_examen.id
        db.session.commit()

        # Seleccionar preguntas
        rango = obtener_rango_nivel(nivel)
        preguntas_disponibles = Pregunta.query.filter(
            Pregunta.no_pregunta >= rango[0],
            Pregunta.no_pregunta < rango[1]
        ).all()

        if not preguntas_disponibles:
            flash("No se encontraron preguntas para el nivel seleccionado.", "danger")
            return redirect(url_for("config_examen_ml"))

        cantidad_a_seleccionar = min(num_preguntas, len(preguntas_disponibles))
        preguntas_seleccionadas = random.sample(preguntas_disponibles, cantidad_a_seleccionar)

        # Guardar en la sesión los IDs de las preguntas seleccionadas
        session["preguntas_ids"] = [p.id for p in preguntas_seleccionadas]

        return render_template("examen_ml.html", config=config, examen_id=nuevo_examen.id)

    niveles = [
        "Basico", "Basico II", "Basico III",
        "Intermedio", "Intermedio II", "Intermedio III",
        "Avanzado I", "Avanzado II"
    ]
    return render_template("config_examen_ml.html", niveles=niveles)





@app.route("/ver_examen/<int:examen_id>")
@login_required
def ver_examen(examen_id):
    examen = Examen.query.get_or_404(examen_id)
    return render_template("ver_examen.html", examen=examen)




@app.route("/ver_examenes")
@login_required
def ver_examenes():
    """
    Muestra una lista de todos los exámenes realizados.
    Solo muestra exámenes que tienen historial registrado.
    """
    examenes = Examen.query.join(HistorialExamen).filter(
        HistorialExamen.usuario_id == current_user.id
    ).distinct().all()

    return render_template("ver_examenes.html", examenes=examenes)



@app.route("/finalizar_examen/<int:examen_id>")
@login_required
def finalizar_examen(examen_id):
    exam_progress = session.get("exam_progress")
    if not exam_progress or exam_progress.get("examen_id") != examen_id:
        flash("No has iniciado este examen o ya se ha finalizado.", "warning")
        return redirect(url_for("dashboard"))

    examen = Examen.query.get_or_404(examen_id)
    preguntas = examen.detalles  
    respuestas_usuario = exam_progress["answers"]  

    correctas = 0
    total = len(preguntas)

    if examen.sistema == "multiple":
        for pregunta_detalle in preguntas:
            respuesta = respuestas_usuario.get(str(pregunta_detalle.id))
            if respuesta == pregunta_detalle.opcion_correcta:
                correctas += 1

    porcentaje = (correctas / total) * 100 if total > 0 else 0
    aprobado = porcentaje >= 90

    # ✅ SÓLO actualiza Examen (resumen global)
    examen.fecha_realizacion = datetime.now()
    examen.resultado = porcentaje
    db.session.commit()

    # Limpia la sesión para evitar que el usuario repita el examen
    session.pop("exam_progress", None)

    return render_template(
        "finalizar_examen.html",
        examen=examen,
        correctas=correctas,
        total=total,
        porcentaje=porcentaje,
        aprobado=aprobado
    )




import matplotlib.pyplot as plt
import io
import base64

@app.route("/graficar_examenes")
@login_required
def graficar_examenes():
    # Consultar los exámenes finalizados (con fecha_realizacion)
    examenes = Examen.query.filter(Examen.fecha_realizacion.isnot(None)).order_by(Examen.fecha_realizacion).all()

    if not examenes:
        flash("Aún no hay exámenes con resultados.", "warning")
        return redirect(url_for("dashboard"))

    # Extraer datos para la gráfica: se formatea la fecha con hora, minuto y segundo
    fechas = [examen.fecha_realizacion.strftime("%Y-%m-%d %H:%M:%S") for examen in examenes]
    resultados = [examen.resultado for examen in examenes]

    import matplotlib.pyplot as plt
    import io
    import base64

    plt.figure(figsize=(10, 5))
    plt.plot(fechas, resultados, marker="o", linestyle="-", label="Resultado del Examen")
    plt.axhline(y=90, color="r", linestyle="--", label="Línea de Aprobación (90%)")
    plt.xlabel("Fecha y Hora")
    plt.ylabel("Resultado (%)")
    plt.title("Evolución de Exámenes Realizados")
    plt.xticks(rotation=45)
    plt.ylim(0, 100)  # Opcional: fijar el rango del eje Y de 0 a 100
    plt.legend()
    plt.grid(True)

    # Guardar la imagen en memoria y convertirla a base64
    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    img_url = base64.b64encode(img.getvalue()).decode()

    return render_template("graficar_examenes.html", img_url=img_url)





@app.route("/examen/<int:examen_id>/pregunta/<int:idx>", methods=["GET", "POST"])
@login_required
def mostrar_pregunta(examen_id, idx):
    exam_progress = session.get("exam_progress")
    if not exam_progress or exam_progress.get("examen_id") != examen_id:
        flash("No has iniciado este examen o ya terminó.", "warning")
        return redirect(url_for("dashboard"))

    print("examen_id-->"+str(examen_id))

    # Obtenemos el examen y su lista de preguntas
    examen = Examen.query.get_or_404(examen_id)
    preguntas = examen.detalles  # Lista de DetalleExamen
    total_preguntas = len(preguntas)
    print("total:"+str(total_preguntas))

    # Validar que idx está en rango
    if idx < 0 or idx >= total_preguntas:
        flash("Índice de pregunta inválido.", "danger")
        return redirect(url_for("dashboard"))

    pregunta_actual = preguntas[idx]

    if request.method == "POST":
        # Guardar la respuesta elegida (si es multiple)
        respuesta_usuario = request.form.get("opcion")
        
        # Determinar si es correcta
        es_correcta = (respuesta_usuario == pregunta_actual.opcion_correcta)

        # Guardar en HistorialExamen
        #nuevo_historial = HistorialExamen(
        #    usuario_id=current_user.id,
        #    examen_id=examen_id,
        #    pregunta_id=pregunta_actual.id,
        #    pregunta=pregunta_actual.pregunta,
        #    respuesta_usuario=respuesta_usuario,
        #    respuesta_correcta=pregunta_actual.opcion_correcta,
        #    es_correcta=es_correcta
        #)
        #db.session.add(nuevo_historial)
        #db.session.commit()

        # Almacenar en session["answers"][pregunta_id] = respuesta
        exam_progress["answers"][str(pregunta_actual.id)] = respuesta_usuario
        session["exam_progress"] = exam_progress

        # Ir a la siguiente pregunta
        next_idx = idx + 1
        if next_idx < total_preguntas:
            return redirect(url_for("mostrar_pregunta", examen_id=examen_id, idx=next_idx))
        else:
            return redirect(url_for("finalizar_examen", examen_id=examen_id))

    # Si es GET, mezclamos las opciones si es multiple
    all_options = []
    if examen.sistema == "multiple":
        all_options = [
            pregunta_actual.opcion_correcta,
            pregunta_actual.opcion_incorrecta1,
            pregunta_actual.opcion_incorrecta2,
            pregunta_actual.opcion_incorrecta3
        ]
        random.shuffle(all_options)

    return render_template(
        "mostrar_pregunta.html",
        examen=examen,
        pregunta=pregunta_actual,
        idx=idx,
        total=total_preguntas,
        all_options=all_options  # Pasamos la lista mezclada al template
    )



@app.route("/historial_examen/<int:examen_id>")
@login_required
def historial_examen(examen_id):
    examen = Examen.query.get_or_404(examen_id)
    historial = HistorialExamen.query.filter_by(examen_id=examen_id, usuario_id=current_user.id).all()
    
    return render_template("historial_examen.html", examen=examen, historial=historial)



import json
import re

def fix_json_string(s):
    # Corrige "\u" incompleto (no seguido de 4 hex)
    s = re.sub(r'\\u(?![0-9A-Fa-f]{4})', r'\\\\u', s)
    # Duplica los backslashes que no formen parte de secuencias de escape válidas
    return re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', s)

def generar_preguntas_gpt(tema, nivel, sistema):
    """
    Genera un conjunto de preguntas basadas en el tema, nivel y sistema 
    usando la API GPT. Devuelve una lista de dict con la estructura necesaria.
    Las fórmulas matemáticas se solicitarán en LaTeX (delimitadas con '$').
    """

    import random

    aleatorio = random.randint(10, 20)

    

    if sistema == "multiple":
        prompt = (
            f"Genera {aleatorio} preguntas  de opción múltiple sobre el tema '{tema}' "
            f"con un nivel de dificultad '{nivel}'. Considera que si el nivel es avanzado, las preguntas deberán ser "
            f"extremadamente difíciles, al igual que las opciones múltiples. "
            f"Para todas las fórmulas matemáticas (incluyendo las opciones), utiliza LaTeX delimitado con '$'. "
            f"**Importante**: Para exponentes que sean fracciones, utiliza siempre la notación con llaves, por ejemplo, "
            f"escribe 'x^{{\\frac{{a}}{{b}}}}' en lugar de 'x^\\frac{{a}}{{b}}'. "
            f"Cada pregunta debe tener 4 opciones: 1 correcta y 3 incorrectas. "
            f"Devuelve sólo JSON con la siguiente estructura:\n"
            f"[\n"
            f"  {{\n"
            f"    \"pregunta\": \"...\",\n"
            f"    \"correcta\": \"...\",\n"
            f"    \"incorrecta1\": \"...\",\n"
            f"    \"incorrecta2\": \"...\",\n"
            f"    \"incorrecta3\": \"...\"\n"
            f"  }},\n"
            f"  ...\n"
            f"]"
        )
    else:
        prompt = (
            f"Genera 5 preguntas abiertas sobre el tema '{tema}' con nivel '{nivel}'. "
            f"Devuelve sólo JSON con la siguiente estructura:\n"
            f"[\n"
            f"  {{ \"pregunta\": \"...\" }},\n"
            f"  ...\n"
            f"]"
        )


    print("voy a consultar el modelo ....")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    contenido = response.choices[0].message.content.strip()
    print(contenido)  # Para depuración

      # Solución: duplicar todos los backslashes
    contenido_fixed = contenido.replace('\\', '\\\\')


    # Corregir problemas de escape en la cadena JSON
    #contenido_fixed = fix_json_string(contenido)

    try:
        preguntas_list = json.loads(contenido_fixed)
    except Exception as e:
        print("hubo un error al jsonear contenido:", e)
        preguntas_list = []
    
    return preguntas_list




@app.route("/preparar_examen", methods=["GET", "POST"])
@login_required
def preparar_examen():
    if request.method == "POST":
        # 1. Recibir datos del formulario
        tema = request.form.get("tema")
        nivel = request.form.get("nivel")
        sistema = request.form.get("sistema")  # "multiple" o "texto"

        # 2. Crear el registro en la tabla Examen
        nuevo_examen = Examen(tema=tema, nivel=nivel, sistema=sistema)
        db.session.add(nuevo_examen)
        db.session.commit()  # ya tenemos nuevo_examen.id

        # 3. Llamar a GPT para generar preguntas
        preguntas_generadas = generar_preguntas_gpt(tema, nivel, sistema)
        
        # 4. Guardar las preguntas en "detalle_examen"
        for p in preguntas_generadas:
            if sistema == "multiple":
                detalle = DetalleExamen(
                    examen_id=nuevo_examen.id,
                    pregunta=p.get("pregunta", ""),
                    opcion_correcta=p.get("correcta", ""),
                    opcion_incorrecta1=p.get("incorrecta1", ""),
                    opcion_incorrecta2=p.get("incorrecta2", ""),
                    opcion_incorrecta3=p.get("incorrecta3", "")
                )
            else:  # sistema == "texto"
                detalle = DetalleExamen(
                    examen_id=nuevo_examen.id,
                    pregunta=p.get("pregunta", "")
                )
            db.session.add(detalle)
        
        db.session.commit()

        # 5. Redirigir a la ruta que muestra el resumen de este examen
        # (en lugar de volver al dashboard)
        return redirect(url_for("ver_examen", examen_id=nuevo_examen.id))

    # GET -> mostrar formulario
    return render_template("preparar_examen.html")




from flask import session

@app.route("/iniciar_examen/<int:examen_id>")
@login_required
def iniciar_examen(examen_id):
    examen = Examen.query.get_or_404(examen_id)
    
    # 1. Inicializar en session el estado del examen
    session["exam_progress"] = {
        "examen_id": examen.id,
        "current_index": 0,
        "answers": {}  # aquí guardaremos las respuestas del usuario
    }
    
    # 2. Redirigir a la primera pregunta
    return redirect(url_for("mostrar_pregunta", examen_id=examen.id, idx=0))


@app.route("/dashboard")
@login_required
def dashboard():
    # Cantidad de preguntas resueltas por el usuario
    solved_count = HistorialExamen.query.filter_by(usuario_id=current_user.id).count()
    # Total de preguntas
    total_questions = Pregunta.query.count()
    # Porcentaje
    percentage = (solved_count / total_questions * 100) if total_questions > 0 else 0

    # Cantidad total de usuarios (para tu nuevo icono)
    total_users = Usuario.query.count()

    return render_template("dashboard.html",
                           solved_count=solved_count,
                           total_questions=total_questions,
                           percentage=percentage,
                           total_users=total_users)



@app.route("/admin")
@login_required
def admin():    
    return render_template("admin.html")

@app.route("/bat01")
@login_required
def bat01():    
    return render_template("bat01.html")



@app.route("/")
def home():
    return redirect(url_for("dashboard"))



@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        # Verificar si el usuario ya existe
        existing_user = Usuario.query.filter_by(email=email).first()
        if existing_user:
            flash("Este correo ya está registrado. Usa otro.", "danger")
            return redirect(url_for("register"))

        # Encriptar la contraseña
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Crear nuevo usuario
        new_user = Usuario(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")
    #return render_template("login.html")



#from flask_limiter import Limiter
#from flask_limiter.util import get_remote_address

# Limitar intentos de login
#limiter = Limiter(get_remote_address, app=app)

@app.route("/login", methods=["GET", "POST"])
#@limiter.limit("5 per minute")  # Máximo 5 intentos por IP cada minuto
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = Usuario.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Inicio de sesión exitoso", "success")
            #return redirect(url_for("index"))
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template("login.html")




# 📌 2️⃣ Ruta de LOGOUT
@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()  # Limpia toda la sesión, incluidos los flashes pendientes
    flash("Sesión cerrada correctamente", "info")
    return redirect(url_for("login"))



# 📌 3️⃣ Obtener una pregunta aleatoria desde PostgreSQL
def obtener_pregunta():
    """Obtiene una pregunta aleatoria desde la base de datos."""
    pregunta = Pregunta.query.order_by(db.func.random()).first()
    
    print("pregunta::"+str(pregunta))

    return pregunta if pregunta else None


# 📌 4️⃣ Generar opciones múltiples con OpenAI
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
        model="gpt-3.5-turbo",
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


# 📌 5️⃣ Ruta protegida "/" (Solo accesible con sesión iniciada)
@app.route("/practicar")
@login_required
def index():
    pregunta = obtener_pregunta()
    if pregunta:
        opciones = generar_opciones_multiple(pregunta.pregunta)
        opciones_lista = [opciones["correcta"], opciones["incorrecta1"], opciones["incorrecta2"], opciones["incorrecta3"]]
        random.shuffle(opciones_lista)
        return render_template("index.html", pregunta=pregunta.pregunta, opciones=opciones_lista, correcta=opciones["correcta"], pregunta_id=pregunta.id)
    else:
        return "No hay preguntas disponibles."


# 📌 6️⃣ Ruta "/evaluar" para guardar respuestas
@app.route("/evaluar", methods=["POST"])
def evaluar():
    data = request.get_json()

    seleccion = data.get("respuesta")
    correcta = data.get("correcta")
    pregunta_id = data.get("pregunta_id")
    
    opcion_correcta = data.get("opcion_correcta")
    opcion_incorrecta1 = data.get("opcion_incorrecta1")
    opcion_incorrecta2 = data.get("opcion_incorrecta2")
    opcion_incorrecta3 = data.get("opcion_incorrecta3")

    # Validar que pregunta_id no sea None
    if not pregunta_id:
        return jsonify({"error": "pregunta_id no recibido"}), 400

    es_correcta = seleccion == correcta
    usuario_id = current_user.id if current_user.is_authenticated else None

    nueva_respuesta = Respuesta(
        usuario_id=usuario_id,
        pregunta_id=int(pregunta_id),
        respuesta_usuario=seleccion,
        es_correcta=es_correcta,
        opcion_correcta=opcion_correcta,
        opcion_incorrecta1=opcion_incorrecta1,
        opcion_incorrecta2=opcion_incorrecta2,
        opcion_incorrecta3=opcion_incorrecta3
    )

    db.session.add(nueva_respuesta)
    db.session.commit()

    resultado = "Correcto! 🎉" if es_correcta else "Incorrecto ❌. Inténtalo de nuevo."
    return jsonify({"resultado": resultado})
