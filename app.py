import os
import urllib.parse
import pymysql
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta

app = Flask(__name__)

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
# CONEXÃO COM BANCO (HOSTINGER REMOTO)
# ===========================================================
def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "srv1965.hstgr.io"),        # Host remoto
        user=os.getenv("DB_USER", "u855521630_jefferson"),      # Usuário do banco
        password=os.getenv("DB_PASS", "Jefferson7-"),    # Senha do banco
        database=os.getenv("DB_NAME", "u855521630_salao"),    # Nome do banco
        port=int(os.getenv("DB_PORT", 3306)),          # Porta
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/teste_db")
def teste_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            hora = cursor.fetchone()
        return f"Conexão OK! Hora do banco: {hora['NOW()']}"
    except Exception as e:
        return f"Erro na conexão: {e}"
    finally:
        conn.close()


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
# ROTAS
# ===========================================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/agendamento')
def agendamento():
    hoje = datetime.today().isoformat()
    return render_template('agendamento.html', servicos=SERVICOS, hoje=hoje)

@app.route('/horarios_disponiveis')
def horarios_disponiveis():
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

@app.route('/agendar', methods=['POST'])
def agendar():
    data = request.form.get('data')
    horario = request.form.get('horario')
    servico_id_str = request.form.get('servico_id')
    cliente = request.form.get('cliente')
    telefone = request.form.get('telefone')

    if not all([data, horario, servico_id_str, cliente, telefone]):
        return "Dados incompletos", 400

    try:
        servico_id = int(servico_id_str)
    except ValueError:
        return "Serviço inválido", 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as total FROM agendamentos WHERE datas=%s AND horario=%s",
                (data, horario)
            )
            if cursor.fetchone()['total'] > 0:
                return "Horário já agendado!", 400

            cursor.execute(
                "INSERT INTO agendamentos (servico_id, datas, horario, cliente, telefone) VALUES (%s, %s, %s, %s, %s)",
                (servico_id, data, horario, cliente, telefone)
            )
            conn.commit()
    finally:
        conn.close()

    servico_nome = next((s['nome'] for s in SERVICOS if s['id'] == servico_id), "Serviço")
    mensagem = f"Olá, {cliente}! Seu agendamento para *{servico_nome}* foi confirmado para {data} às {horario}."
    mensagem_url = urllib.parse.quote(mensagem)
    numero_whatsapp = "55" + telefone
    link_whatsapp = f"https://api.whatsapp.com/send?phone={numero_whatsapp}&text={mensagem_url}"

    return render_template('sucesso.html', link_whatsapp=link_whatsapp)

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == ADMIN_PASSWORD:
            session.permanent = True
            session['logado'] = True
            return redirect(url_for('admin'))
        return "Senha incorreta!"
    return '''
        <form method="post">
            <input type="password" name="senha" placeholder="Digite a senha">
            <button type="submit">Entrar</button>
        </form>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            hoje = datetime.today().date()
            cursor.execute("DELETE FROM agendamentos WHERE datas < %s", (hoje,))
            conn.commit()
            cursor.execute("SELECT * FROM agendamentos ORDER BY datas, horario")
            agendamentos = cursor.fetchall()
    finally:
        conn.close()

    servico_dict = {s["id"]: s["nome"] for s in SERVICOS}
    for ag in agendamentos:
        ag["servico"] = servico_dict.get(ag["servico_id"], "Serviço desconhecido")

    return render_template('admin.html', agendamentos=agendamentos)

@app.route('/admin/remover/<int:id>', methods=['POST'])
def admin_remover(id):
    if not session.get('logado'):
        return jsonify({"status": "erro", "mensagem": "Acesso negado"}), 403
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM agendamentos WHERE id = %s", (id,))
            conn.commit()
    finally:
        conn.close()
    return jsonify({"status": "sucesso"})

# ===========================================================
# ROTA DE TESTE DE CONEXÃO (opcional)
# ===========================================================
@app.route("/teste_db")
def teste_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            hora = cursor.fetchone()
        return f"Conexão OK! Hora do banco: {hora['NOW()']}"
    except Exception as e:
        return f"Erro na conexão: {e}"
    finally:
        conn.close()

# ===========================================================
# WSGI
# ===========================================================
if __name__ == "__main__":
    app.run()
