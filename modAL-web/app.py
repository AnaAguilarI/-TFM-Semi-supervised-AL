from flask import Flask, request, jsonify, render_template
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import json
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling
from sklearn.datasets import load_digits
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Configuración inicial
app = Flask(__name__, static_url_path="/static")

# Cargar datos y preparar modelo
n_initial = 100
X, y = load_digits(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Inicialización del pool de datos
initial_idx = np.random.choice(range(len(X_train)), size=n_initial, replace=False)
X_initial, y_initial = X_train[initial_idx], y_train[initial_idx]
X_pool, y_pool = np.delete(X_train, initial_idx, axis=0), np.delete(y_train, initial_idx, axis=0)

# Configurar el modelo ActiveLearner
learner = ActiveLearner(
    estimator=RandomForestClassifier(),
    query_strategy=uncertainty_sampling,
    X_training=X_initial,
    y_training=y_initial
)

# Variables globales
current_query_idx = None
query_inst = None
history = []
accuracy_scores = []


# Ruta principal para el frontend
@app.route("/")
def index():
    return render_template("index.html")


# Ruta para obtener la imagen actual en formato base64
@app.route("/api/current-image", methods=["GET"])
def get_current_image():
    global current_query_idx, query_inst, X_pool

    if X_pool.shape[0] == 0:
        return jsonify({"error": "No more data to query."}), 400

    # Realizar consulta al modelo
    current_query_idx, query_inst = learner.query(X_pool)

    # Convertir imagen a base64
    image_array = query_inst.reshape(8, 8) * 255  # Convertir a escala de grises
    img = Image.fromarray(image_array.astype("uint8"))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return jsonify({"image": img_str})


@app.route("/api/accuracy-scores", methods=["GET"])
def get_accuracy_scores():
    global accuracy_scores

    # Si `accuracy_scores` no está inicializado, devolvemos un mensaje de error
    if not accuracy_scores:
        return jsonify({"error": "No accuracy scores available."}), 404

    # Devolvemos las métricas como una lista
    return jsonify(accuracy_scores)



# Ruta para recibir y guardar la etiqueta
@app.route("/api/submit-label", methods=["POST"])
def submit_label():
    global current_query_idx, X_pool, y_pool, history, accuracy_scores

    # Obtener la etiqueta del usuario
    data = request.get_json()
    label = int(data["label"])

    # Entrenar el modelo con el nuevo dato etiquetado
    learner.teach(query_inst.reshape(1, -1), np.array([label], dtype=int))

    # Actualizar el pool
    X_pool = np.delete(X_pool, current_query_idx, axis=0)
    y_pool = np.delete(y_pool, current_query_idx, axis=0)

    # Guardar en el historial
    history.append({
        "image": query_inst.tolist(),
        "label": label
    })

    # Actualizar métricas
    accuracy_scores.append(learner.score(X_test, y_test))

    return jsonify({"success": True, "message": "Label submitted successfully."})



# Ruta para obtener las últimas 5 imágenes etiquetadas
@app.route("/api/history", methods=["GET"])
def get_history():
    global history

    # Limitar a las últimas 5 entradas
    last_5 = history[-5:]
    processed_history = []

    for item in last_5:
        try:
            # Convertir imagen a base64
            image_array = np.array(item["image"]).reshape(8, 8) * 255
            img = Image.fromarray(image_array.astype("uint8"))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            processed_history.append({"image": image_base64, "label": item["label"]})
        except Exception as e:
            print(f"Error processing history item: {e}")

    return jsonify(processed_history)


# Ejecutar la aplicación
if __name__ == "__main__":
    app.run(debug=True)
