from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort
from cryptography.fernet import Fernet
import json
import os
import threading
import subprocess

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

DATA_FILE = 'comp.json'
KEY_FILE = 'key.key'
USERS_FILE = 'usuarios.json'

# Função para carregar a chave de criptografia
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
    return key

# Função para criptografar os dados
def encrypt_data(data, key):
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode('utf-8'))

# Função para descriptografar os dados
def decrypt_data(encrypted_data, key):
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode('utf-8'))

# Função para carregar os dados do arquivo
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'rb') as file:
            encrypted_data = file.read()
        key = load_key()
        return decrypt_data(encrypted_data, key)
    except (json.JSONDecodeError, FileNotFoundError, Exception):
        return []

# Função para salvar os dados no arquivo
def save_data(data):
    key = load_key()
    encrypted_data = encrypt_data(data, key)
    with open(DATA_FILE, 'wb') as file:
        file.write(encrypted_data)

# Função para carregar os usuários
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    try:
        with open(USERS_FILE, 'rb') as f:
            encrypted_data = f.read()
        key = load_key()
        return decrypt_data(encrypted_data, key)
    except Exception:
        return []

# Função para salvar os usuários
def save_users(users):
    key = load_key()
    encrypted_data = encrypt_data(users, key)
    with open(USERS_FILE, 'wb') as f:
        f.write(encrypted_data)

# Função para verificar se o usuário é administrador
def is_admin():
    return session.get('user_tipo') == 'adm'

# Rota principal para exibir os registros
@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    sort_by = request.args.get('sort_by')
    monitorado_filter = request.args.get('monitorado')
    search = request.args.get('search', '').strip().lower()
    ativo = request.args.get('ativo')

    # Filtro por nome
    if search:
        data = [record for record in data if search in record.get('nome', '').lower()]

    # Filtro por monitorado
    if monitorado_filter == 'sim':
        data = [record for record in data if record.get('monitorado') is True]
    elif monitorado_filter == 'nao':
        data = [record for record in data if record.get('monitorado') is False]

    # Filtro por ativo
    if ativo == 'sim':
        data = [record for record in data if record.get('ativo') is True]
    elif ativo == 'nao':
        data = [record for record in data if record.get('ativo') is False]

    if sort_by in ['titulo', 'bloco', 'andar', 'nome']:
        data = sorted(data, key=lambda x: x.get(sort_by, ''))
    return render_template('index.html', records=data, log_viewer_url=url_for('execution_log_viewer'), sort_by=sort_by)

# Rota para adicionar um novo registro (apenas admin)
@app.route('/add', methods=['POST'])
def add_record():
    if not is_admin():
        abort(403)
    data = load_data()
    new_record = {
        "titulo": request.form['titulo'],
        "nome": request.form['nome'],
        "ativo": request.form.get('ativo') == 'on',
        "tipo": request.form['tipo'],
        "bloco": request.form['bloco'],
        "andar": request.form['andar'],
        "monitorado": request.form.get('monitorado') == 'on'
    }
    data.append(new_record)
    save_data(data)
    return redirect(url_for('index'))

# Rota para deletar um registro (apenas admin)
@app.route('/delete/<titulo>', methods=['POST'])
def delete(titulo):
    if not is_admin():
        abort(403)
    data = load_data()
    for i, record in enumerate(data):
        if record['titulo'] == titulo:
            del data[i]
            break
    save_data(data)
    return redirect(url_for('index'))

# Rota para atualizar um registro existente (apenas admin)
@app.route('/update/<titulo>', methods=['POST'])
def update_record(titulo):
    if not is_admin():
        abort(403)
    data = load_data()
    for record in data:
        if record['titulo'] == titulo:
            record.update({
                "titulo": request.form['titulo'],
                "nome": request.form['nome'],
                "ativo": request.form.get('ativo') == 'on',
                "tipo": request.form['tipo'],
                "bloco": request.form['bloco'],
                "andar": request.form['andar'],
                "monitorado": request.form.get('monitorado') == 'on'
            })
            break
    save_data(data)
    return redirect(url_for('index'))

# Rota para editar um registro
@app.route('/edit/<titulo>', methods=['GET'])
def edit(titulo):
    data = load_data()
    record = next((r for r in data if r['titulo'] == titulo), None)
    if not record:
        return "Registro não encontrado", 404
    return render_template('edit.html', record=record)

# Rota para alternar o estado de monitoramento de um registro (apenas admin)
@app.route('/toggle_monitorado/<titulo>', methods=['POST'])
def toggle_monitorado(titulo):
    if not is_admin():
        abort(403)
    data = load_data()
    for record in data:
        if record['titulo'] == titulo:
            record['monitorado'] = not record.get('monitorado', False)
            break
    save_data(data)
    return redirect(url_for('index'))

# Rota para exibir o log de execução
@app.route('/execution_log_viewer')
def execution_log_viewer():
    return render_template('execution_log_viewer.html')

# Rota para adicionar um registro (GET e POST) (apenas admin)
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar():
    if not is_admin():
        abort(403)
    if request.method == 'POST':
        # Depuração: Imprimir os dados recebidos do formulário
        print("Dados recebidos do formulário:", request.form)

        # Carregar os dados existentes
        data = load_data()

        # Verificar se o título já existe
        titulo = request.form['titulo']
        if any(record['titulo'] == titulo for record in data):
            return "Erro: Um registro com este título já existe.", 400

        # Criar um novo registro com os dados do formulário
        new_record = {
            "titulo": titulo,
            "nome": request.form['nome'],
            "ativo": request.form.get('ativo') == 'on',
            "tipo": request.form['tipo'],
            "bloco": request.form['bloco'],
            "andar": request.form['andar'],
            "monitorado": request.form.get('monitorado') == 'on'
        }
        # Adicionar o novo registro à lista
        data.append(new_record)
        # Salvar os dados atualizados no arquivo
        save_data(data)
        # Redirecionar para a página inicial
        return redirect(url_for('index'))
    return render_template('adicionar.html')

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        users = load_users()
        matricula = request.form.get('matricula', '').strip()
        senha = request.form.get('password', '').strip()
        user = next((u for u in users if u['matricula'] == matricula and u['senha'] == senha), None)
        if user:
            session['user'] = user['nome']
            session['user_tipo'] = user['tipo']
            return redirect(url_for('index'))
        else:
            error = 'Usuário ou senha inválidos'
    return render_template('login.html', error=error)

# Rota para logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    session.pop('user_tipo', None)  # Remove o tipo de usuário da sessão
    return redirect(url_for('login'))

# Rota para executar o painel
@app.route('/executar_painel', methods=['POST'])
def executar_painel():
    try:
        # Altere o caminho conforme necessário
        subprocess.Popen(['python', 'painel_totem_v9.py'])
        return redirect(url_for('index'))
    except Exception as e:
        return f"Erro ao executar painel_totem_v9.py: {e}", 500

# Rota para abrir VNC
@app.route('/abrir_vnc/<nome>', methods=['POST'])
def abrir_vnc(nome):
    import subprocess
    # Substitua pelo comando real para abrir o VNC com o nome desejado
    subprocess.Popen(['python', 'seu_script_vnc.py', nome])
    return redirect(url_for('index'))

# Rota para gerenciar usuários
@app.route('/usuarios')
def usuarios():
    if not is_admin():
        abort(403)
    users = load_users()
    return render_template('usuarios.html', users=users)

# Rota para adicionar um novo usuário
@app.route('/usuarios/adicionar', methods=['GET', 'POST'])
def adicionar_usuario():
    if not is_admin():
        abort(403)
    if request.method == 'POST':
        users = load_users()
        novo = {
            "nome": request.form['nome'],
            "matricula": request.form['matricula'],
            "senha": request.form['senha'],  # Em produção, use hash!
            "tipo": request.form['tipo'],
            "obs": request.form['obs']
        }
        users.append(novo)
        save_users(users)
        return redirect(url_for('usuarios'))
    return render_template('usuario_form.html', user=None)

# Rota para editar um usuário existente
@app.route('/usuarios/editar/<matricula>', methods=['GET', 'POST'])
def editar_usuario(matricula):
    if not is_admin():
        abort(403)
    users = load_users()
    user = next((u for u in users if u['matricula'] == matricula), None)
    if not user:
        abort(404)
    if request.method == 'POST':
        user['nome'] = request.form['nome']
        user['senha'] = request.form['senha']
        user['tipo'] = request.form['tipo']
        user['obs'] = request.form['obs']
        save_users(users)
        return redirect(url_for('usuarios'))
    return render_template('usuario_form.html', user=user)

# Rota para excluir um usuário
@app.route('/usuarios/excluir/<matricula>', methods=['POST'])
def excluir_usuario(matricula):
    if not is_admin():
        abort(403)
    users = load_users()
    users = [u for u in users if u['matricula'] != matricula]
    save_users(users)
    return redirect(url_for('usuarios'))

# Função para escutar Ctrl+Q
def listen_for_ctrl_q():
    from pynput import keyboard

    def on_press(key):
        try:
            # Ctrl+Q gera '\x11'
            if hasattr(key, 'char') and key.char == '\x11':
                print("Ctrl+Q detectado. Encerrando o servidor Flask.")
                os._exit(0)
        except Exception:
            pass

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Inicialização do servidor Flask
if __name__ == '__main__':
    # Inicia o listener Ctrl+Q
    listener_thread = threading.Thread(target=listen_for_ctrl_q, daemon=True)
    listener_thread.start()
    app.run(debug=True, host='0.0.0.0', port=5031)

