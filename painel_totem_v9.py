import pyautogui
import pyperclip
import time
import tkinter as tk
import os
import json
import pyscreeze
from PIL import Image
from datetime import datetime
import shutil
import subprocess  # Import necessário para executar o comando de ping
from pynput.keyboard import Key, Controller
from cryptography.fernet import Fernet
import threading

# Disable the fail-safe mechanism (not recommended)
pyautogui.FAILSAFE = False

# Função para gerar chave de encriptação se não existir
def generate_key():
    if not os.path.exists('key.key'):
        key = Fernet.generate_key()
        with open('key.key', 'wb') as key_file:
            key_file.write(key)

# Função para carregar chave de encriptação
def load_key():
    try:
        with open('key.key', 'rb') as key_file:
            return key_file.read()
    except FileNotFoundError:
        print("Erro: Arquivo de chave de encriptação não encontrado!")
        raise

# Função para encriptar dados
def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    return fernet.encrypt(json.dumps(data).encode())

# Função para desencriptar dados
def decrypt_data(encrypted_data):
    key = load_key()
    fernet = Fernet(key)
    return json.loads(fernet.decrypt(encrypted_data).decode())

# Função para carregar dados encriptados do comp.json
def load_encrypted_data(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'rb') as file:
            encrypted_data = file.read()
            return decrypt_data(encrypted_data)
    except Exception as e:
        print(f"Erro ao carregar dados encriptados: {e}")
        return []

# Função para salvar dados encriptados no comp.json
def save_encrypted_data(filepath, data):
    try:
        encrypted_data = encrypt_data(data)
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
    except Exception as e:
        print(f"Erro ao salvar dados encriptados: {e}")

# Função para registrar logs
def log_execution(name, ping_result=None, cycle_end=False, tempo_execucao=None):
    """Registra o nome, a data/hora e o resultado do ping em um arquivo de log."""
    log_path = os.path.join("static", "execution_log.txt")  # Alterado para salvar em /static/
    with open(log_path, "a", encoding="utf-8") as log_file:
        if not cycle_end:
            log_file.write(f"{datetime.now()}: Processado {name}")
            if ping_result is not None:
                log_file.write(f" - Ping: {ping_result}")
            log_file.write("\n")
        else:
            log_file.write("===================\n")
            if tempo_execucao is not None:
                log_file.write(f"Tempo de execução: {tempo_execucao}\n")

# Função para realizar teste de ping
def test_ping(hostname):
    try:
        response = subprocess.run(["ping", "-n", "1", hostname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "Sucesso" if response.returncode == 0 else "Falha"
    except Exception as e:
        print(f"Erro ao realizar ping: {e}")
        return "Erro"

# Função para fechar todas as janelas VNC
def close_all_vnc_windows():
    while True:
        try:
            pyautogui.getWindowsWithTitle("VNC Viewer")[0].close()
            time.sleep(0.5)
        except IndexError:
            break

# Função para executar o ciclo principal
def executar_ciclo():
    inicio = datetime.now()

    # Carregar dados do comp.json (encriptado)
    data = load_encrypted_data('comp.json')

    # Filtrar apenas os itens monitorados
    data = [record for record in data if record.get('monitorado')]

    contador = 0  # Inicializa o contador no início do ciclo

    for record in data:

        contador += 1  # Incrementa o contador a cada iteração
        print(f"{contador}: {record['nome']}")

        copied_text = record['nome']
        #print(copied_text)

        # Realizar teste de ping
        ping_result = test_ping(copied_text)

        # Registrar o nome, a data/hora e o resultado do ping
        log_execution(copied_text, ping_result)

        # Abrir o VNC
        #pyautogui.click(x=23, y=634)
        pyautogui.click(x=962, y=1052)
        
        #pyautogui.click(x=1036, y=1057)  # clica em vnc
        #pyautogui.click(x=487, y=738)  # clica em vnc
        #pyautogui.click(x=588, y=1061)  # clica em vnc
        #pyautogui.click(x=1023, y=1054)  # clica em VNC
                
        #pyautogui.hotkey('win')
        #time.sleep(1)
        #pyautogui.write('vncviewer')
        #pyautogui.press('enter')
        time.sleep(2)
        
        # Caminho para o executável do VNC Viewer
        #vnc_path = r"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe"

        # Executar o VNC Viewer com o hostname do painel/totem
        #subprocess.run([vnc_path, copied_text], check=True)
                
        
        # Digitar o hostname do painel/totem
        pyautogui.write(copied_text)
        pyautogui.press('enter')
        time.sleep(1)

        # Retirar erro da tela
        pyautogui.press('enter')
        pyautogui.press('enter')

        # Retorna ponteiro do mouse para a tela CMD
        pyautogui.click(x=2425, y=712)  # volta para tela

        # Fechar todas as janelas VNC após a pausa
        close_all_vnc_windows()

    fim = datetime.now()
    tempo_execucao = fim - inicio
    print(f"Tempo de execução do ciclo: {tempo_execucao}")

    # No final do ciclo
    log_execution("Fim do ciclo", cycle_end=True, tempo_execucao=tempo_execucao)

# Função para escutar Ctrl+P
def listen_for_ctrl_p():
    from pynput import keyboard

    def on_press(key):
        try:
            if key == keyboard.KeyCode.from_char('p') and ctrl_pressed[0]:
                print("Ctrl+P detectado. Encerrando o script.")
                os._exit(0)
            elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                ctrl_pressed[0] = True
        except Exception:
            pass

    def on_release(key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            ctrl_pressed[0] = False

    ctrl_pressed = [False]
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# Função para escutar Ctrl+Q
def listen_for_ctrl_q():
    from pynput import keyboard

    def on_press(key):
        try:
            # Ctrl+Q gera '\x11'
            if hasattr(key, 'char') and key.char == '\x11':
                print("Ctrl+Q detectado. Encerrando o script.")
                os._exit(0)
        except Exception:
            pass

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Função para escutar Ctrl+Shift+Q
def listen_for_ctrl_shift_q():
    from pynput import keyboard

    state = {"ctrl": False, "shift": False}

    def on_press(key):
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                state["ctrl"] = True
            elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                state["shift"] = True
            elif key == keyboard.KeyCode.from_char('q'):
                if state["ctrl"] and state["shift"]:
                    print("Ctrl+Shift+Q detectado. Encerrando o script.")
                    os._exit(0)
        except Exception:
            pass

    def on_release(key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            state["ctrl"] = False
        elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            state["shift"] = False

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# Inicializar chave de encriptação
#generate_key()

if __name__ == "__main__":
    try:
        listener_thread = threading.Thread(target=listen_for_ctrl_q, daemon=True)
        listener_thread.start()
        while True:
            executar_ciclo()
            log_execution(name=None, cycle_end=True)
            time.sleep(5)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")