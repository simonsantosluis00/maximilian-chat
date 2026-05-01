from flask import Flask, render_template, request, jsonify
import anthropic
import json
import os
from ddgs import DDGS

app = Flask(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def cargar_clientes():
    with open("clientes.json", "r", encoding="utf-8") as f:
        return json.load(f)

def cargar_historial(cliente_id):
    archivo = f"historial_{cliente_id}.json"
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_historial(cliente_id, historial):
    archivo = f"historial_{cliente_id}.json"
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)

def buscar_en_internet(query):
    with DDGS() as ddgs:
        resultados = list(ddgs.text(query, max_results=5))
    texto = ""
    for r in resultados:
        texto += f"- {r['title']}: {r['body']}\n"
    return texto

def necesita_busqueda(mensaje):
    palabras_clave = ["busca", "buscar", "noticias", "hoy", "precio", "actualmente", "2026"]
    return any(p in mensaje.lower() for p in palabras_clave)

@app.route("/chat/<cliente_id>")
def chat(cliente_id):
    clientes = cargar_clientes()
    if cliente_id not in clientes:
        return "Cliente no encontrado", 404
    cliente = clientes[cliente_id]
    return render_template("chat.html", cliente=cliente, cliente_id=cliente_id)

@app.route("/mensaje/<cliente_id>", methods=["POST"])
def mensaje(cliente_id):
    clientes = cargar_clientes()
    if cliente_id not in clientes:
        return jsonify({"error": "Cliente no encontrado"}), 404

    cliente = clientes[cliente_id]
    usuario = request.json.get("mensaje")
    historial = cargar_historial(cliente_id)

    if necesita_busqueda(usuario):
        resultados = buscar_en_internet(usuario)
        mensaje_con_contexto = f"{usuario}\n\n[Resultados de internet:]\n{resultados}"
    else:
        mensaje_con_contexto = usuario

    historial.append({"role": "user", "content": mensaje_con_contexto})

    respuesta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=cliente["system"],
        messages=historial
    )

    texto = respuesta.content[0].text
    historial.append({"role": "assistant", "content": texto})
    guardar_historial(cliente_id, historial)

    return jsonify({"respuesta": texto})

@app.route("/")
def index():
    clientes = cargar_clientes()
    return render_template("index.html", clientes=clientes)

if __name__ == "__main__":
    app.run(debug=True)