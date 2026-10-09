# recompensas.py
import json
import os
from datetime import datetime
import pytz
from app.database import load_user_data, save_user_data, add_saldo
from app import central

# Variável global para armazenar a instância do bot
bot = None

def setup(bot_instance):
    """Salva a instância do bot para uso interno."""
    global bot
    bot = bot_instance
    print("[Recompensas] Sistema de recompensas diárias iniciado.")

def _get_today_obj():
    """Retorna o objeto datetime.date de hoje para America/Sao_Paulo."""
    try:
        tz = pytz.timezone('America/Sao_Paulo')
        return datetime.now(tz).date()
    except Exception:
        return datetime.now().date() # Fallback para o fuso do servidor

def _parse_data_compra(data_str):
    """Converte a string de data 'dd/mm/YYYY HH:MM:SS' para um objeto date."""
    try:
        # Pega apenas a parte da data
        data_apenas = data_str.split(' ')[0]
        dt_obj = datetime.strptime(data_apenas, "%d/%m/%Y")
        return dt_obj.date()
    except (ValueError, IndexError, TypeError):
        return None

def _parse_data_pagamento(data_str):
    """Converte a string de data 'dd/mm/YYYY às HH:MM:SS' para um objeto date."""
    try:
        # Pega apenas a parte da data
        data_apenas = data_str.split(' ')[0]
        dt_obj = datetime.strptime(data_apenas, "%d/%m/%Y")
        return dt_obj.date()
    except (ValueError, IndexError, TypeError):
        return None

def _check_compra_hoje(user_data, hoje):
    """Verifica se o usuário fez alguma compra hoje."""
    compras = user_data.get('compras', [])
    for compra in compras:
        data_compra = _parse_data_compra(compra.get('data'))
        if data_compra and data_compra == hoje:
            return True
    return False

def _check_recarga_hoje(user_data, hoje):
    """Verifica se o usuário fez alguma recarga hoje."""
    pagamentos = user_data.get('pagamentos', [])
    for pag in pagamentos:
        data_pag = _parse_data_pagamento(pag.get('data'))
        if data_pag and data_pag == hoje:
            return True
    return False

def _check_recompensa_ja_resgatada(user_data, hoje_str):
    """Verifica se a recompensa de hoje já foi resgatada."""
    last_claim = user_data.get('last_daily_reward_claim')
    return last_claim == hoje_str

def get_valor_recompensa():
    """Pega o valor da recompensa das configurações."""
    try:
        # Usa a nova classe que adicionaremos em central.py
        return central.CredentialsChange.RecompensaDiaria.valor()
    except Exception as e:
        print(f"[Recompensas] Erro ao ler valor da recompensa: {e}")
        return 0.0

def resgatar_recompensa(user_id):
    """
    Função principal para verificar e conceder a recompensa.
    Retorna uma tupla (codigo_status, dados_adicionais).
    """
    try:
        user_data = load_user_data(user_id)
        if not user_data:
            return ("erro", "Usuário não encontrado.")

        hoje_obj = _get_today_obj()
        hoje_str = hoje_obj.isoformat() # Formato YYYY-MM-DD

        # 1. Verificar se já resgatou
        if _check_recompensa_ja_resgatada(user_data, hoje_str):
            return ("ja_resgatado", None)

        valor_recompensa = get_valor_recompensa()
        if valor_recompensa <= 0:
            return ("desativado", None)

        # 2. Verificar condições
        comprou = _check_compra_hoje(user_data, hoje_obj)
        recarregou = _check_recarga_hoje(user_data, hoje_obj)

        if comprou and recarregou:
            # 3. Conceder recompensa
            try:
                # 1. Modifica o saldo e a data de resgate no mesmo objeto
                saldo_atual = user_data.get('saldo', 0.0)
                user_data['saldo'] = saldo_atual + float(valor_recompensa)
                user_data['last_daily_reward_claim'] = hoje_str
                
                # 2. Salva o arquivo UMA VEZ com ambas as alterações
                save_user_data(user_id, user_data)
                
                # --- [INÍCIO] NOVO BLOCO DE NOTIFICAÇÃO DO ADMIN ---
                try:
                    admin_id = central.CredentialsChange.id_dono()
                    novo_saldo = user_data['saldo'] # Saldo *depois* da recompensa
                    
                    # Obter informações do usuário (nome, username)
                    try:
                        chat_info = bot.get_chat(user_id)
                        user_display_name = chat_info.first_name or "Usuário"
                        username = f"@{chat_info.username}" if chat_info.username else "Não definido"
                    except Exception as e:
                        print(f"[Recompensas] Erro ao buscar info do usuário {user_id} para log: {e}")
                        user_display_name = "Usuário"
                        username = "Não definido"

                    # Obter data/hora formatada
                    try:
                        tz = pytz.timezone('America/Sao_Paulo')
                        agora = datetime.now(tz)
                    except Exception:
                        agora = datetime.now()
                    data_hora_formatada = agora.strftime("%d/%m/%Y às %H:%M:%S")

                    # Montar a mensagem
                    texto_notificacao = (
                        f"<b>🎁 Recompensa Diária Resgatada! (Tarefas)</b>\n\n"
                        f"👤 <b>Usuário:</b> {user_display_name}\n"
                        f"   - <b>Username:</b> {username}\n"
                        f"   - <b>ID:</b> <code>{user_id}</code>\n\n"
                        f"💰 <b>Detalhes do Bônus:</b>\n"
                        f"   - <b>Valor da Recompensa:</b> R${valor_recompensa:,.2f}\n"
                        f"   - <b>Saldo Anterior:</b> R${saldo_atual:,.2f}\n"
                        f"   - <b>Saldo Atual:</b> R${novo_saldo:,.2f}\n\n"
                        f"🕐 <b>Data/Hora:</b> {data_hora_formatada}"
                    )
                    
                    # Enviar a notificação
                    bot.send_message(
                        admin_id,
                        texto_notificacao,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"[Recompensas] Erro ao notificar admin sobre resgate: {e}")
                # --- [FIM] NOVO BLOCO DE NOTIFICAÇÃO DO ADMIN ---

                # 3. Retorna o sucesso para o usuário
                return ("sucesso", valor_recompensa)
                
            except Exception as e:
                print(f"[Recompensas] Erro ao adicionar saldo para {user_id}: {e}")
                return ("erro", str(e))
        else:
            # 4. Não cumpriu as condições
            return ("nao_cumpriu", {'comprou': comprou, 'recarregou': recarregou})

    except Exception as e:
        print(f"[Recompensas] Erro fatal em resgatar_recompensa para {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return ("erro", "Erro interno no sistema de recompensas.")
        