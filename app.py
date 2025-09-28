from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend do salão rodando 🚀"

@app.route("/servicos")
def servicos():
    return jsonify({
        "servicos": [
            {"id": 1, "nome": "Corte de cabelo", "preco": 50},
            {"id": 2, "nome": "Trança", "preco": 80},
            {"id": 3, "nome": "Penteado social", "preco": 120}
        ]
    })

if __name__ == "__main__":
    # Para rodar localmente (http://127.0.0.1:5000)
    app.run(host="0.0.0.0", port=5000)
