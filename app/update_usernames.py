import os
import json
import time
import threading
from telebot import TeleBot

from app import database

time.sleep(1)

# Carregar o token do arquivo de credenciais
def get_bot_token():
    try:
        with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
            cred = json.load(f)
            return cred.get('api-bot', '')
    except Exception as e:
        print(f"Erro ao carregar token: {e}")
        return None

BOT_TOKEN = get_bot_token()

if not BOT_TOKEN:
    print("ERRO: Token do bot não encontrado no arquivo de credenciais!")
    exit(1)

# Inicializar o bot
bot = TeleBot(BOT_TOKEN, parse_mode=None)

def get_username_by_id(user_id):
    """
    Obtém o username (@) ou o nome do Telegram a partir do ID do usuário.
    """
    try:
        user = bot.get_chat(user_id)
        if user.username:
            return f"{user.username}"  # Retorna o @username se disponível
        elif user.first_name:
            return user.first_name  # Retorna o nome se o @username não estiver disponível
        else:
            return f"Usuario sem @"  # Caso nenhuma informação esteja disponível
    except Exception as e:
        print(f"Erro ao obter informações para ID {user_id}: {e}")
        return None

def process_user(user_id):
    """
    Processa um usuário do banco SQLite para atualizar o username ou nome.
    """
    try:
        user_data = database.load_user_data(user_id)
    except Exception as e:
        print(f"Erro ao carregar usuário {user_id}: {e}")
        return

    if not user_data:
        print(f"Usuário {user_id} não encontrado no banco.")
        return

    print(f"Processando usuário ID: {user_id}")
    novo_username = get_username_by_id(user_id)
    if novo_username is None:
        # Falha de consulta não significa que o usuário perdeu seu username.
        return

    if novo_username != user_data.get('username'):
        user_data['username'] = novo_username
        try:
            database.save_user_data(user_id, user_data)
            print(f"Username atualizado para {novo_username} (usuário {user_id}).")
        except Exception as e:
            print(f"Erro ao salvar o usuário {user_id}: {e}")
    else:
        print(f"Username já está atualizado para {novo_username} (usuário {user_id}).")

def update_usernames():
    """
    Atualiza os usernames ou nomes dos usuários cadastrados no banco SQLite,
    consultando o Telegram para pegar o valor mais recente.
    """
    # CORREÇÃO: este script lia/gravava arquivos database/users/<id>.json,
    # pasta que não existe mais após a migração para SQLite — o processo
    # rodava indefinidamente (via start.py) sem atualizar nada. Agora usa
    # database.get_all_user_ids()/load_user_data()/save_user_data().
    try:
        user_ids = database.get_all_user_ids()
    except Exception as e:
        print(f"Erro ao listar usuários do banco: {e}")
        return

    threads = []

    for user_id in user_ids:
        # Criar uma thread para cada usuário
        thread = threading.Thread(target=process_user, args=(user_id,))
        threads.append(thread)
        thread.start()

        # Limitar o número de threads simultâneas para evitar sobrecarga
        while len(threads) >= 10:  # Ajuste o limite de threads conforme necessário
            threads = [t for t in threads if t.is_alive()]
            time.sleep(0.1)

    # Garantir que todas as threads tenham terminado
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    while True:
        print("Iniciando atualização dos usernames...")
        update_usernames()
        print("Atualização concluída. Aguardando 24 horas para a próxima execução...")
        time.sleep(86400)  # 24 horas em segundos
