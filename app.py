from flask import Flask, render_template, request, jsonify
import anthropic
import json
import os
from ddgs import DDGS

app = Flask(__name__)
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

system = """Eres Maximilian, un asistente sarcástico pero brillante.
Tienes memoria de conversaciones anteriores.
REGLA IMPORTANTE: Cuando recibas [Resultados de internet:] en el mensaje,
DEBES usar ESA información para responder. Resume los resultados de forma
útil con tu estilo sarcástico y menciona las fuentes."""

ARCHIVO_MEMORIA = "memoria.json"

def cargar_historial():
    if os.path.exists(ARCHIVO_MEMORIA):
        with open(ARCHIVO_MEMORIA, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_historial(historial):
    with open(ARCHIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

def buscar_en_internet(query):
    with DDGS() as ddgs:
        resultados = list(ddgs.text(query, max_results=8))
    texto = ""
    for r in resultados:
        texto += f"- {r['title']}: {r['body']}\n"
    return texto

def necesita_busqueda(mensaje):
    palabras_clave = [
        "busca", "buscar", "googlea", "qué es", "quién es",
        "cuánto cuesta", "precio", "hoy", "noticias", "último",
        "actualmente", "2024", "2025", "2026"
    ]
    return any(p in mensaje.lower() for p in palabras_clave)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    usuario = request.json.get("mensaje")
    historial = cargar_historial()

    if necesita_busqueda(usuario):
        resultados = buscar_en_internet(usuario)
        mensaje_con_contexto = f"{usuario}\n\n[Resultados de internet:]\n{resultados}"
    else:
        mensaje_con_contexto = usuario

    historial.append({"role": "user", "content": mensaje_con_contexto})

    respuesta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=historial
    )

    texto = respuesta.content[0].text
    historial.append({"role": "assistant", "content": texto})
    guardar_historial(historial)

    return jsonify({"respuesta": texto})

if __name__ == "__main__":
    app.run(debug=True)