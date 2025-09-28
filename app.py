from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave_super_secreta_dev"
ADMIN_PASSWORD = "1234"

# ===========================================================
# HORÁRIOS FIXOS
# ===========================================================
HORARIOS = [
    "08:30", "10:00", "11:30",
    "13:00", "14:30", "16:00",
    "17:30", "18:00"
]

# ===========================================================
# AGENDAMENTOS EM MEMÓRIA
# ===========================================================
agendamentos = []

# ===========================================================
# ROTAS
# ===========================================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/agendamento')
def agendamento():
    hoje = datetime.today().isoformat()
    return render_template('agendamento.html', hoje=hoje, horarios=HORARIOS)

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
    data = request.form.get('data')
    horario = request.form.get('horario')
    cliente = request.form.get('cliente')
    telefone = request.form.get('telefone')

    if not all([data, horario, cliente, telefone]):
        return "Dados incompletos", 400

    # Verifica se já existe
    if any(a['data'] == data and a['horario'] == horario for a in agendamentos):
        return "Horário já agendado!", 400

    agendamentos.append({
        "data": data,
        "horario": horario,
        "cliente": cliente,
        "telefone": telefone
    })

    link_whatsapp = f"https://api.whatsapp.com/send?phone=55{telefone}&text=Olá, {cliente}! Seu agendamento foi confirmado para {data} às {horario}."
    return render_template('sucesso.html', link_whatsapp=link_whatsapp)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form.get('senha')
        if senha == ADMIN_PASSWORD:
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
    return render_template('admin.html', agendamentos=agendamentos)

@app.route('/admin/remover/<int:index>', methods=['POST'])
def admin_remover(index):
    if not session.get('logado'):
        return jsonify({"status": "erro", "mensagem": "Acesso negado"}), 403
    if 0 <= index < len(agendamentos):
        agendamentos.pop(index)
        return jsonify({"status": "sucesso"})
    return jsonify({"status": "erro", "mensagem": "Índice inválido"}), 400

# ===========================================================
# ROTA DE TESTE (SIMULA CONEXÃO DB)
# ===========================================================
@app.route("/teste_db")
def teste_db():
    return "Conexão simulada OK!"

# ===========================================================
# WSGI EM MODO DEBUG
# ===========================================================
if __name__ == "__main__":
    app.run(debug=True)
