import os
import urllib.parse
import pymysql
from flask import Flask, request, jsonify, session
from datetime import datetime, timedelta
from flask_cors import CORS  # Para permitir requisições do front-end hospedado em outro domínio

app = Flask(__name__)
CORS(app)  # Permite chamadas cross-origin

# ===========================================================
# CONFIGURAÇÕES SEGURAS
# ===========================================================
app.secret_key = os.getenv("SECRET_KEY", "chave_super_secreta_dev")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")
app.permanent_session_lifetime = timedelta(minutes=5)

# ===========================================================
# SERVIÇOS
# ===========================================================
SERVICOS = [
    {"id": 1, "nome": "Penteados sociais - Madrinhas", "preco": 70},
    {"id": 2, "nome": "Penteados sociais - Noivas", "preco": 70},
    {"id": 3, "nome": "Penteados sociais - Debutantes", "preco": 70},
    {"id": 4, "nome": "Tranças - Box Braids em geral", "preco": 125},
    {"id": 5, "nome": "Tranças - Nagô", "preco": 30},
    {"id": 6, "nome": "Mega Hair - Queratina", "preco": 450},
    {"id": 8, "nome": "Mega Hair - Micro link (por tela)", "preco": 30},
]

# ===========================================================
# CONEXÃO COM BANCO (HOSTINGER)
# ===========================================================
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "usuario"),
        password=os.getenv("DB_PASS", "senha"),
        database=os.getenv("DB_NAME", "banco"),
        cursorclass=pymysql.cursors.DictCursor
    )

# ===========================================================
# GERA HORÁRIOS AUTOMÁTICOS
# ===========================================================
def gerar_horarios(inicio_str, fim_str, intervalo_minutos):
    horarios = []
    hoje = datetime.today().date()
    inicio = datetime.strptime(inicio_str, "%H:%M").replace(year=hoje.year, month=hoje.month, day=hoje.day)
    fim = datetime.strptime(fim_str, "%H:%M").replace(year=hoje.year, month=hoje.month, day=hoje.day)
    atual = inicio
    while atual <= fim:
        horarios.append(atual.strftime("%H:%M"))
        atual += timedelta(minutes=intervalo_minutos)
    return horarios

HORARIOS = gerar_horarios("08:30", "18:00", 90)

# ===========================================================
# ROTAS API
# ===========================================================
@app.route('/api/servicos', methods=['GET'])
def api_servicos():
    return jsonify(SERVICOS)

@app.route('/api/horarios_disponiveis', methods=['GET'])
def api_horarios_disponiveis():
    data = request.args.get('data')
    servico_id = request.args.get('servico_id', type=int)
    if not data or not servico_id:
        return jsonify({"erro": "Data e serviço são obrigatórios"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT horario FROM agendamentos WHERE datas=%s", (data,))
            horarios_ocupados = [row['horario'] for row in cursor.fetchall()]
    finally:
        conn.close()

    horarios_livres = [h for h in HORARIOS if h not in horarios_ocupados]
    return jsonify({"horarios": horarios_livres})

@app.route('/api/agendar', methods=['POST'])
def api_agendar():
    data = request.json.get('data')
    horario = request.json.get('horario')
    servico_id = request.json.get('servico_id')
    cliente = request.json.get('cliente')
    telefone = request.json.get('telefone')

    if not all([data, horario, servico_id, cliente, telefone]):
        return jsonify({"erro": "Dados incompletos"}), 400

    try:
        servico_id = int(servico_id)
    except ValueError:
        return jsonify({"erro": "Serviço inválido"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as total FROM agendamentos WHERE datas=%s AND horario=%s",
                (data, horario)
            )
            if cursor.fetchone()['total'] > 0:
                return jsonify({"erro": "Horário já agendado!"}), 400

            cursor.execute(
                "INSERT INTO agendamentos (servico_id, datas, horario, cliente, telefone) VALUES (%s, %s, %s, %s, %s)",
                (servico_id, data, horario, cliente, telefone)
            )
            conn.commit()
    finally:
        conn.close()

    servico_nome = next((s['nome'] for s in SERVICOS if s['id'] == servico_id), "Serviço")
    mensagem = f"Olá, {cliente}! Seu agendamento para {servico_nome} foi confirmado para {data} às {horario}."
    mensagem_url = urllib.parse.quote(mensagem)
    numero_whatsapp = "55" + telefone
    link_whatsapp = f"https://api.whatsapp.com/send?phone={numero_whatsapp}&text={mensagem_url}"

    return jsonify({"mensagem": "Agendamento realizado com sucesso!", "link_whatsapp": link_whatsapp})

# ===========================================================
# RODANDO O SERVIDOR
# ===========================================================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
