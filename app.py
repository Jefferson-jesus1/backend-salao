from flask import Flask, request, jsonify, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_super_secreta_dev"
ADMIN_PASSWORD = "1234"

# Horários fixos
HORARIOS = [
    "08:30", "10:00", "11:30",
    "13:00", "14:30", "16:00",
    "17:30", "18:00"
]

# Agendamentos em memória
agendamentos = []

# ===========================================================
# ROTAS PÚBLICAS
# ===========================================================
@app.route('/horarios_disponiveis')
def horarios_disponiveis():
    data = request.args.get('data')
    if not data:
        return jsonify({"erro": "Data é obrigatória"}), 400

    horarios_ocupados = [a['horario'] for a in agendamentos if a['data'] == data]
    horarios_livres = [h for h in HORARIOS if h not in horarios_ocupados]
    return jsonify({"horarios": horarios_livres})

@app.route('/agendar', methods=['POST'])
def agendar():
    data = request.json.get('data')
    horario = request.json.get('horario')
    cliente = request.json.get('cliente')
    telefone = request.json.get('telefone')

    if not all([data, horario, cliente, telefone]):
        return jsonify({"erro": "Dados incompletos"}), 400

    if any(a['data'] == data and a['horario'] == horario for a in agendamentos):
        return jsonify({"erro": "Horário já agendado!"}), 400

    agendamentos.append({
        "data": data,
        "horario": horario,
        "cliente": cliente,
        "telefone": telefone
    })

    link_whatsapp = f"https://api.whatsapp.com/send?phone=55{telefone}&text=Olá, {cliente}! Seu agendamento foi confirmado para {data} às {horario}."
    return jsonify({"status": "sucesso", "link_whatsapp": link_whatsapp})

@app.route("/teste_db")
def teste_db():
    return jsonify({"status": "OK", "mensagem": "Simulação de conexão com o banco"})

# ===========================================================
# ROTAS ADMIN
# ===========================================================
@app.route('/login', methods=['POST'])
def login():
    senha = request.json.get('senha')
    if senha == ADMIN_PASSWORD:
        session['logado'] = True
        return jsonify({"status": "sucesso"})
    return jsonify({"erro": "Senha incorreta!"}), 401

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"status": "logout_ok"})

@app.route('/admin/agendamentos')
def admin_agendamentos():
    if not session.get('logado'):
        return jsonify({"erro": "Acesso negado"}), 403
    return jsonify({"agendamentos": agendamentos})

@app.route('/admin/remover/<int:index>', methods=['POST'])
def admin_remover(index):
    if not session.get('logado'):
        return jsonify({"erro": "Acesso negado"}), 403
    if 0 <= index < len(agendamentos):
        agendamentos.pop(index)
        return jsonify({"status": "sucesso"})
    return jsonify({"erro": "Índice inválido"}), 400

# ===========================================================
# WSGI EM MODO DEBUG
# ===========================================================
if __name__ == "__main__":
    app.run(debug=True)
