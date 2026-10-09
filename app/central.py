import json
import time
import telebot
import uuid
import datetime
import random
import html
import pytz
import os
from datetime import timezone
from app.database import load_user_data, save_user_data, get_all_user_ids
from pytz import timezone


# Foto exibida no topo da mensagem de boas-vindas (menu principal / /start)
FOTO_MENU_PRINCIPAL = "https://i.ibb.co/wrSryC9T/IMG-20260901-052626-107.jpg"

def editar_menu_seguro(bot, chat_id, message_id, texto, reply_markup=None,
                        parse_mode='HTML', disable_web_page_preview=None):
    """
    Edita uma mensagem existente (menu) de forma segura. A foto de boas-vindas
    (FOTO_MENU_PRINCIPAL) deve aparecer APENAS no menu principal — então, se a
    mensagem atual for essa foto (não dá pra editar texto nela) e estamos
    indo para outro menu, a mensagem é apagada e uma nova SÓ DE TEXTO é
    enviada no lugar (sem foto).
    Retorna a mensagem enviada quando precisa recriar, ou None quando apenas
    editou a existente.
    """
    kwargs_text = dict(chat_id=chat_id, message_id=message_id, text=texto,
                        parse_mode=parse_mode, reply_markup=reply_markup)
    if disable_web_page_preview is not None:
        kwargs_text['disable_web_page_preview'] = disable_web_page_preview
    try:
        bot.edit_message_text(**kwargs_text)
        return None
    except Exception as e:
        msg = str(e).lower()
        if 'message is not modified' in msg:
            return None
        if 'no text in the message' not in msg and "there is no text" not in msg:
            print(f"[editar_menu_seguro] Falha ao editar texto, recriando mensagem: {e}")
        # A mensagem atual é a foto do menu principal (ou outro tipo não editável como texto).
        # Apaga e reenvia como mensagem de texto pura (sem foto), pois a foto é exclusiva do menu principal.
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        return bot.send_message(chat_id, texto, parse_mode=parse_mode,
                                 reply_markup=reply_markup)

def open_utf8(filepath, mode='r'):
    try:
        # Só usa encoding se não for modo binário
        if 'b' in mode:
            return open(filepath, mode)
        return open(filepath, mode, encoding='utf-8')
    except UnicodeDecodeError as e:
        print(f'[open_utf8] Erro de decode em {filepath} com utf-8: {e}. Tentando latin1...')
        if 'b' in mode:
            raise
        return open(filepath, mode, encoding='latin1')

class ViewTime():
    def data_atual():
        data_e_hora_atuais = datetime.datetime.now()
        data_e_hora_em_texto = data_e_hora_atuais.strftime('%d/%m/%Y')
        return data_e_hora_em_texto
    def hora_atual():
        data_e_hora_atuais = datetime.datetime.now()
        fuso_horario = timezone('America/Sao_Paulo')
        data_e_hora_sao_paulo = data_e_hora_atuais.astimezone(fuso_horario)
        hora_sao_paulo_em_texto = data_e_hora_sao_paulo.strftime('%H:%M:%S')
        # REMOVED: hora_sao_paulo = datetime.datetime.strptime(hora_sao_paulo_em_texto, '%H:%M:%S').time()
        return hora_sao_paulo_em_texto # Return the string directly
class CredentialsChange():
    def user_bot():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return str(data["user_bot"])
    def mudar_user_bot(user):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["user_bot"] = str(user)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    def token_bot():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return str(data["api-bot"])
    def mudar_token_bot(token):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["api-bot"] = str(token)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    def versao_bot():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return str(data["version"])
    def mudar_versao_bot(version):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["version"] = version
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    def verificar_premium():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        if int(data["premium"]) == 0:
            return False
        elif int(data["premium"]) == 1:
            return True
    def separador():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return str(data["separador"])
    def mudar_separador(separador):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["separador"] = separador
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    def status_manutencao():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        if data["maintance"] == 'on':
            return True
        else:
            return False
    def mudar_status_manutencao():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        if data["maintance"] == "on":
            data["maintance"] = "off"
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return
        else:
            data["maintance"] = "on"
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return
    def id_dono():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        dono_id = data["id_dono"]
        return int(dono_id)
    def mudar_dono(id):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["id_dono"] = int(id)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    class SuporteInfo():
        def link_suporte():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return str(data["link_suporte"])
        def mudar_link_suporte(link):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["link_suporte"] = str(link)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
    class StatusPix():
        def pix_manual():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if str(data["status_pix_manu"]) == 'on':
                return True
            else:
                return False
        def pix_auto():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if str(data["status_pix_auto"]) == 'on':
                return True
            else:
                return False
    class ChangeStatusPix():
        def change_pix_manual():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if str(data["status_pix_manu"]) == 'on':
                data["status_pix_manu"] = 'off'
                with open_utf8('settings/credenciais.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return
            else:
                data["status_pix_manu"] = 'on'
                with open_utf8('settings/credenciais.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return False
        def change_pix_auto():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if str(data["status_pix_auto"]) == 'on':
                data["status_pix_auto"] = 'off'
                with open_utf8('settings/credenciais.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return
            else:
                data["status_pix_auto"] = 'on'
                with open_utf8('settings/credenciais.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return False
    class BonusPix():
        def quantidade_bonus():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return int(data["bonus_pix"])
        def mudar_quantidade_bonus(porcentagem):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["bonus_pix"] = int(porcentagem)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return
        def valor_minimo_para_bonus():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return int(data["bonus_pix_min"])
        def mudar_valor_minimo_para_bonus(valor_min):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["bonus_pix_min"] = int(valor_min)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
    class BonusRegistro():
        def bonus():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return float(data["bonus_registro"])
        def mudar_bonus(novo_bonus):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["bonus_registro"] = float(novo_bonus)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
    class InfoPix():
        import json
        def token_promissepay():
            try:
                with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                token = data.get("gateway_pagamento", {}).get("promissepay", {}).get("token")
                if not token or not isinstance(token, str) or not token.strip():
                    raise ValueError("Token do PromissePay não configurado corretamente em settings/credenciais.json")
                return token.strip()
            except UnicodeDecodeError as e:
                raise RuntimeError(f"Erro de encoding ao ler settings/credenciais.json: {e}")
            except Exception as e:
                raise RuntimeError(f"Erro ao obter token do PromissePay: {e}")
        def mudar_token_promissepay(token):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if 'gateway_pagamento' not in data:
                data['gateway_pagamento'] = {}
            if 'promissepay' not in data['gateway_pagamento']:
                data['gateway_pagamento']['promissepay'] = {}
            data['gateway_pagamento']['promissepay']['token'] = str(token)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
        def token_mercadopago():
            try:
                with open('settings/credenciais.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                token = data.get("gateway_pagamento", {}).get("mercadopago", {}).get("token")
                if not token or not isinstance(token, str) or not token.strip():
                    raise ValueError("Token do Mercado Pago não configurado corretamente em settings/credenciais.json")
                return token.strip()
            except UnicodeDecodeError as e:
                raise RuntimeError(f"Erro de encoding ao ler settings/credenciais.json: {e}")
            except Exception as e:
                raise RuntimeError(f"Erro ao obter token do Mercado Pago: {e}")
        def mudar_token_mercadopago(token):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            if 'gateway_pagamento' not in data:
                data['gateway_pagamento'] = {}
            if 'mercadopago' not in data['gateway_pagamento']:
                data['gateway_pagamento']['mercadopago'] = {}
            data['gateway_pagamento']['mercadopago']['token'] = str(token)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
        def deposito_minimo_pix():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return float(data["min_pix"])
        def trocar_deposito_minimo_pix(min):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["min_pix"] = float(min)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return
        def deposito_maximo_pix():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return float(data["max_pix"])
        def trocar_deposito_maximo_pix(max):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["max_pix"] = float(max)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return
        def expiracao():
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            expiracao_time = data["expiracao_pix"]
            return int(expiracao_time)
        def mudar_expiracao(minutes):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["expiracao_pix"] = int(minutes)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
                return True

    class InfoMisticPay():
        """Gerencia credenciais do MisticPay (Client ID e Client Secret)"""
        import json
        
        def credenciais():
            try:
                with open_utf8('settings/credenciais.json', 'r') as f:
                    data = json.load(f)
                
                mistic = data.get("gateway_pagamento", {}).get("misticpay", {})
                client_id = mistic.get("client_id", "")
                client_secret = mistic.get("client_secret", "")
                
                if not client_id or not client_secret:
                    raise ValueError("Credenciais do MisticPay não configuradas")
                    
                return {"ci": client_id.strip(), "cs": client_secret.strip()}
            except Exception as e:
                raise RuntimeError(f"Erro ao obter credenciais do MisticPay: {e}")
        
        def mudar_credenciais(client_id, client_secret):
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
                
            if 'gateway_pagamento' not in data:
                data['gateway_pagamento'] = {}
            if 'misticpay' not in data['gateway_pagamento']:
                data['gateway_pagamento']['misticpay'] = {}
                
            data['gateway_pagamento']['misticpay']['client_id'] = str(client_id)
            data['gateway_pagamento']['misticpay']['client_secret'] = str(client_secret)
            
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return

    class RecompensaDiaria:
        """Gerencia o valor da recompensa diária por tarefas (comprar + recarregar)"""
        @staticmethod
        def valor() -> float:
            with open_utf8('settings/credenciais.json', 'r') as f:
                dados = json.load(f)
            # Busca o valor, com 1.0 como padrão se a chave não existir
            return float(dados.get('recompensa_diaria_valor', 1.0))

        @staticmethod
        def mudar_valor(novo_valor: float):
            with open_utf8('settings/credenciais.json', 'r') as f:
                dados = json.load(f)
            dados['recompensa_diaria_valor'] = float(novo_valor)
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
class AfiliadosInfo():
    def status_afiliado():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        if data["afiliados"] == 'on':
            return True
        else:
            return False
    def mudar_status_afiliado():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        if data["afiliados"] == 'on':
            data["afiliados"] = "off"
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
        else:
            data["afiliados"] = "on"
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
    def pontos_por_recarga():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return int(data["pontos_by_indicate_buy"])
    def mudar_pontos_por_recarga(pontos):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["pontos_by_indicate_buy"] = int(pontos)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
        return
    def minimo_pontos_pra_saldo():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return data["min_points_saldo"]
    def trocar_minimo_pontos_pra_saldo(min):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["min_points_saldo"] = int(min)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
    def multiplicador_pontos():
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return float(data["multiplicador_pontos"])
    def trocar_multiplicador_pontos(multiplicador):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        data["multiplicador_pontos"] = float(multiplicador)
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)

class SistemaAfiliados():
    """Classe para gerenciar o novo sistema de afiliados"""

    @staticmethod
    def status_ativo():
        """Verifica se o sistema de afiliados está ativo"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return data.get("afiliados_sistema", {}).get("ativo", False)

    @staticmethod
    def alternar_status():
        """Alterna o status do sistema de afiliados"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)

        if "afiliados_sistema" not in data:
            user_bot = data.get('user_bot', 'rlfornecedor_bot')
            data["afiliados_sistema"] = {
                "ativo": True,
                "valor_por_indicacao": 5.0
            }
        else:
            data["afiliados_sistema"]["ativo"] = not data["afiliados_sistema"]["ativo"]

        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return data["afiliados_sistema"]["ativo"]

    @staticmethod
    def get_valor_indicacao():
        """Retorna o valor por indicação"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
        return float(data.get("afiliados_sistema", {}).get("valor_por_indicacao", 5.0))

    @staticmethod
    def set_valor_indicacao(valor):
        """Define o valor por indicação"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)

        if "afiliados_sistema" not in data:
            data["afiliados_sistema"] = {
                "ativo": True,
                "valor_por_indicacao": float(valor)
            }
        else:
            data["afiliados_sistema"]["valor_por_indicacao"] = float(valor)

        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

class CanalObrigatorio():
    """Classe para gerenciar o sistema de canal obrigatório"""

    @staticmethod
    def status_ativo():
        """Verifica se o canal obrigatório está ativo"""
        try:
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return data.get("canal_obrigatorio", {}).get("ativo", True)
        except:
            return True

    @staticmethod
    def alternar_status():
        """Alterna o status do canal obrigatório"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)

        if "canal_obrigatorio" not in data:
            data["canal_obrigatorio"] = {
                "ativo": False,
                "id_canal": "-1002787400901",
                "link_canal": "https://t.me/+z06ZYa4CplVlMWMx"
            }
        else:
            data["canal_obrigatorio"]["ativo"] = not data["canal_obrigatorio"]["ativo"]

        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return data["canal_obrigatorio"]["ativo"]

    @staticmethod
    def get_id_canal():
        """Retorna o ID do canal"""
        try:
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return data.get("canal_obrigatorio", {}).get("id_canal", "-1002787400901")
        except:
            return "-1002787400901"

    @staticmethod
    def get_link_canal():
        """Retorna o link do canal"""
        try:
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            return data.get("canal_obrigatorio", {}).get("link_canal", "https://t.me/+z06ZYa4CplVlMWMx")
        except:
            return "https://t.me/+z06ZYa4CplVlMWMx"

    @staticmethod
    def set_id_canal(id_canal):
        """Define o ID do canal"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)

        if "canal_obrigatorio" not in data:
            data["canal_obrigatorio"] = {
                "ativo": True,
                "id_canal": str(id_canal),
                "link_canal": "https://t.me/+z06ZYa4CplVlMWMx"
            }
        else:
            data["canal_obrigatorio"]["id_canal"] = str(id_canal)

        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def set_link_canal(link_canal):
        """Define o link do canal"""
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)

        if "canal_obrigatorio" not in data:
            data["canal_obrigatorio"] = {
                "ativo": True,
                "id_canal": "-1002787400901",
                "link_canal": str(link_canal)
            }
        else:
            data["canal_obrigatorio"]["link_canal"] = str(link_canal)

        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

class Notificacoes():
    def modo_servico():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["tipo_texto"])
    def mudar_modo_servico():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        if data["tipo_texto"] == 0:
            data["tipo_texto"] = 1
        else:
            data["tipo_texto"] = 0
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def status_notificacoes():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        if data["status_notify"] == 'on':
            return True
        else:
            return False
    def mudar_status_notificacoes():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        if data["status_notify"] == 'on':
            data["status_notify"] = 'off'
            with open_utf8('settings/notify.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
        else:
            data["status_notify"] = 'on'
            with open_utf8('settings/notify.json', 'w') as f:
                json.dump(data, f, indent=4)
            return
    def id_grupo():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["id_grupo"])
    def trocar_id_grupo(id_grupo):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["id_grupo"] = int(id_grupo)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
        return
    def tempo_minimo_compras():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["time_min_compras"])
    def quantidade_de_servicos_pra_sortear():
        with open_utf8('settings/notificacao/servicos.txt', 'r') as f:
            file = f.read()
        quantidade = 0
        servicos = file.strip().split('\n')
        for servico in servicos:
            if len(servico) > 0:
                quantidade += 1
            pass
        return quantidade


    def pegar_servico_random():
        with open('settings/notificacao/servicos.txt', 'r', encoding='utf-8') as f:
            file = f.read()

        # Remove linhas em branco e espaços desnecessários
        file = [line.strip() for line in file.splitlines() if line.strip()]

        # Filtra as linhas que possuem 'R$' e exclui as que não seguem o formato
        valid_lines = [line for line in file if 'R$' in line]

        if not valid_lines:
            raise ValueError("Nenhuma linha válida com 'R$' foi encontrada no arquivo.")

        while True:
            servico = random.choice(valid_lines)
            try:
                # Divide o serviço pelo 'R$' para pegar nome e valor
                separar = servico.split('R$')
                servico_nome = separar[0].strip()
                valor = separar[1].strip()
                return servico_nome, f'R${valor}'
            except IndexError:
                print(f"Linha '{servico}' não contém o formato esperado 'R$'. Pulando...")

    # Teste
    # nome_servico, valor_servico = pegar_servico_random()
    # print(f"Serviço: {nome_servico}, Valor: {valor_servico}")

    def pegar_servicos_disponiveis():
        data = ControleLogins._load_acessos()
        nomes = []
        for acesso in data["acessos"]:
            if acesso["nome"] in nomes:
                pass
            nomes.append({"nome": acesso["nome"], "valor": acesso["valor"]})
        sort = random.choice(nomes)
        return sort["nome"], f'R${sort["valor"]:.2f}'
    def mudar_servicos_random(lista):
        with open_utf8('settings/notificacao/servicos.txt', 'w') as f:
            f.write(lista)
    def trocar_tempo_minimo_compras(min):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["time_min_compras"] = int(min)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def tempo_maximo_compras():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["time_max_compras"])
    def trocar_tempo_maximo_compras(max):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["time_max_compras"] = int(max)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def tempo_minimo_saldo():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["time_min_saldo"])
    def trocar_tempo_minimo_saldo(min):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["time_min_saldo"] = int(min)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def tempo_maximo_saldo():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return int(data["time_max_saldo"])
    def trocar_tempo_maximo_saldo(max):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["time_max_saldo"] = int(max)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def min_max_saldo():
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        return float(data["saldo_min"]), float(data["saldo_max"])
    def trocar_min_max_saldo(min, max):
        with open_utf8('settings/notify.json', 'r') as f:
            data = json.load(f)
        data["saldo_min"] = int(min)
        data["saldo_max"] = int(max)
        with open_utf8('settings/notify.json', 'w') as f:
            json.dump(data, f, indent=4)
    def pegar_texto_saldo():
        with open_utf8('settings/notificacao/saldo.txt', 'r') as f:
            return f.read()
    def mudar_texto_saldo(texto):
        with open_utf8('settings/notificacao/saldo.txt', 'w') as f:
            f.write(texto)
    def pegar_texto_compra():
        with open_utf8('settings/notificacao/compra.txt', 'r') as f:
            return f.read()
    def mudar_texto_compra(texto):
        with open_utf8('settings/notificacao/compra.txt', 'w') as f:
            f.write(texto)
    def texto_notificacao_saldo():
        texto = Notificacoes.pegar_texto_saldo()
        id = random.randint(898012903, 4290812093)
        saldo_min, saldo_max = Notificacoes.min_max_saldo()
        saldo =  random.randint(int(saldo_min), int(saldo_max))
        texto = texto.replace('{id}', f'{id}').replace('{saldo}', f'{saldo}')
        return texto
    def texto_notificacao_compra():
        texto = Notificacoes.pegar_texto_compra()
        id = random.randint(898012903, 4290812093)
        if Notificacoes.modo_servico() == 0:
            servico, valor = Notificacoes.pegar_servico_random()
        else:
            servico, valor = Notificacoes.pegar_servicos_disponiveis()
        texto = texto.replace('{id}', f'{id}').replace('{servico}', f'{servico}').replace('{valor}', f'{valor}')
        return texto
class InfoUser():
    def verificar_usuario(id):
        user_data = load_user_data(id)
        return user_data is not None

    def novo_afiliado(usuario, indicador):
        user_data_usuario = load_user_data(usuario)
        user_data_indicador = load_user_data(indicador)

        if user_data_usuario and user_data_indicador:
            if user_data_usuario.get("afiliado_por", 0) != 0: # Use .get for safety
                return
            user_data_usuario["afiliado_por"] = int(indicador)
            user_data_indicador["afiliacoes"] = user_data_indicador.get("afiliacoes", 0) + 1 # Use .get
            if "afiliados" not in user_data_indicador: # Initialize if not exists
                user_data_indicador["afiliados"] = []
            user_data_indicador["afiliados"].append({"id_afiliado": int(usuario)})

            save_user_data(usuario, user_data_usuario)
            save_user_data(indicador, user_data_indicador)

    def novo_usuario(id):

        user_data = {
            "id": int(id),
            "username": "",
            "banned": False, # Use boolean directly
            "invite_sent": False,
            "afiliado_por": 0,
            "saldo": 0.0,
            "gift_redeemed": 0.0,
            "total_compras": 0,
            "compras": [],
            "total_pagos": 0.0,
            "pagamentos": [],
            "pontos_indicado": 0,
            "afiliacoes": 0,
            "afiliados": [],
            "purchases": []
        }
        # Aplicar bônus de registro (idempotente)
        try:
            _bonus = float(CredentialsChange.BonusRegistro.bonus())
        except Exception:
            _bonus = 0.0
        if _bonus > 0 and float(user_data.get('gift_redeemed', 0.0)) <= 0.0:
            user_data['saldo'] = float(user_data.get('saldo', 0.0)) + _bonus
            user_data['gift_redeemed'] = float(_bonus)

            try:
                import telebot
                # Usa o token salvo nas credenciais para enviar o aviso de bônus
                token = CredentialsChange.token_bot()
                temp_bot = telebot.TeleBot(token)
                
                temp_bot.send_message(
                    int(id),
                    "🎉 Bem-vindo(a)!\n\n"
                    f"🎁 Você recebeu um bônus de R${_bonus:.2f} no seu saldo inicial.\n\n"
                    "✅ Já está disponível para usar."
                )
            except Exception as e:
                print(f"[ERROR] novo_usuario: Failed to send bonus message. Error: {e}")
                pass
        save_user_data(id, user_data)

    def verificar_ban(id):
        user_data = load_user_data(id)
        # Check against boolean True directly
        return user_data and user_data.get("banned", False) is True

    def dar_ban(id):
        user_data = load_user_data(id)
        if user_data:
            user_data["banned"] = True # Use boolean
            save_user_data(id, user_data)

    def tirar_ban(id):
        user_data = load_user_data(id)
        if user_data:
            user_data["banned"] = False # Use boolean
            save_user_data(id, user_data)

    def quantidade_afiliados(id):
        user_data = load_user_data(id)
        if user_data:
            return len(user_data.get("afiliados", []))
        return 0

    def saldo(id):
        user_data = load_user_data(id)
        if user_data:
            return float(user_data.get("saldo", 0))
        return 0

    def add_saldo(id, novo_saldo):
        user_data = load_user_data(id)
        if user_data:
            user_data["saldo"] = user_data.get("saldo", 0.0) + float(novo_saldo) # Use .get
            save_user_data(id, user_data)


    def tirar_saldo(id, novo_saldo):
        """Debita saldo do usuário. Retorna True se debitou, False se o saldo
        era insuficiente (evita saldo negativo em caso de compra duplicada/concorrente)."""
        user_data = load_user_data(id)
        if user_data:
            saldo = round(float(user_data.get("saldo", 0.0)), 2)
            valor = round(float(novo_saldo), 2)
            if saldo < valor:
                return False
            user_data["saldo"] = saldo - valor
            save_user_data(id, user_data)
            return True
        return False

    def mudar_saldo(id, novo_saldo):
        user_data = load_user_data(id)
        if user_data:
            user_data["saldo"] = float(novo_saldo)
            save_user_data(id, user_data)

    def gifts_resgatados(user_id: int) -> float:
        dados = load_user_data(user_id) or {}
        return float(dados.get("gift_redeemed", 0))


    def total_compras(id):
        user_data = load_user_data(id)
        if user_data:
            # More reliable: count the actual purchases list
            return len(user_data.get("compras", []))
        return 0

    def total_pagos(id):
        user_data = load_user_data(id)
        if user_data:
             # More reliable: count the actual payments list
            return len(user_data.get("pagamentos", []))
        return 0

    def pix_inseridos(id):
        user_data = load_user_data(id)
        if user_data:
            try:
                # Ensure values are floats before summing
                total_pix = sum(float(pagamento.get("valor", 0)) for pagamento in user_data.get("pagamentos", []))
                return total_pix
            except (ValueError, TypeError) as e:
                print(f"[ERROR] pix_inseridos: Error summing payments for user {id}. Error: {e}")
                return 0.0 # Return 0 if any value is invalid
        return 0.0

    def pontos_indicacao(id):
        user_data = load_user_data(id)
        if user_data:
            return user_data.get("pontos_indicado", 0)
        return 0

    def trocar_pontos(id):
        user_data = load_user_data(id)
        if user_data:
            pontos = user_data.get("pontos_indicado", 0)
            try:
                minimo = AfiliadosInfo.minimo_pontos_pra_saldo()
                multiplicador = AfiliadosInfo.multiplicador_pontos()
            except Exception as e:
                print(f"[ERROR] trocar_pontos: Failed to get affiliate settings. Error: {e}")
                return False

            if pontos >= minimo:
                saldo_novo = pontos * multiplicador
                user_data["pontos_indicado"] = 0
                user_data["saldo"] = user_data.get("saldo", 0.0) + saldo_novo # Use .get
                save_user_data(id, user_data)
                return True
        return False

    def fazer_txt_do_historico(id):
        user_data = load_user_data(id)
        # Check if user exists AND has purchases
        if not user_data or not user_data.get("compras"):
            print(f"[INFO] fazer_txt_do_historico: User {id} not found or has no purchase history.")
            return False # Indicate failure if no data or no purchases

        try:
            historico = f'HISTÓRICO DETALHADO @{CredentialsChange.user_bot()}\n_______________________\n\nCOMPRAS:\n'
            for compra in user_data.get("compras", []):
                servico = compra.get("servico", "N/A")
                valor = compra.get("valor", "N/A")
                email = compra.get("email", "N/A")
                senha = compra.get("senha", "N/A")
                data = compra.get("data", "N/A")
                historico += f'Serviço: {servico}\nValor: {valor}\nEmail: {email}\nSenha: {senha}\nData: {data}\n\n'

            historico += '_______________________\n\nPAGAMENTOS:\n'
            for pagamento in user_data.get("pagamentos", []):
                id_pagamento = pagamento.get("id_pagamento", pagamento.get("id", "N/A")) # Check both keys
                valor = pagamento.get("valor", "N/A")
                data = pagamento.get("data", "N/A")
                historico += f'Id pagamento: {id_pagamento}\nValor: {valor}\nData: {data}\n\n'

            # Ensure directory exists
            os.makedirs('historicos', exist_ok=True)
            with open_utf8(f'historicos/{id}.txt', 'w') as f:
                f.write(historico)
            print(f"[INFO] fazer_txt_do_historico: History file created for user {id}.")
            return True
        except Exception as e:
            print(f"[ERROR] fazer_txt_do_historico: Failed to generate history for user {id}. Error: {e}")
            return False # Indicate failure on error

class MudancaHistorico():
    def mudar_gift_resgatado(id, valor):
        user_data = load_user_data(id) # Load data directly
        if user_data:
            user_data["gift_redeemed"] = user_data.get("gift_redeemed", 0.0) + float(valor) # Use .get
            save_user_data(id, user_data) # Save data directly

    def add_compra(id, servico, valor, email, senha):
        user_data = load_user_data(id)
        if user_data:
            user_data["total_compras"] = user_data.get("total_compras", 0) + 1 # Use .get

            if "compras" not in user_data: # Initialize if not exists
                user_data["compras"] = []

            # Use correct format "dd/mm/yyyy HH:MM:SS"
            data_hora_formatada = f"{ViewTime.data_atual()} {ViewTime.hora_atual()}"

            user_data["compras"].append({
                "servico": servico,
                "valor": valor, # Keep original type (float expected)
                "email": email,
                "senha": senha,
                # "data": f"{ViewTime.data_atual()} às {ViewTime.hora_atual()}" # Old incorrect format
                "data": data_hora_formatada # Correct format
            })
            save_user_data(id, user_data)

    def add_pagamentos(id, valor, id_pag):
        user_data = load_user_data(id)
        if user_data:
            # Keep existing logic for total_pagos, add_saldo etc.
            user_data["total_pagos"] = user_data.get("total_pagos", 0) + 1 # Use .get

            # --- CORRECTION HERE ---
            # Create the correct date string format "dd/mm/yyyy HH:MM:SS"
            data_hora_formatada = f"{ViewTime.data_atual()} {ViewTime.hora_atual()}" # Use space, not ' as '
            # --- END CORRECTION ---

            if "pagamentos" not in user_data: # Initialize if not exists
                user_data["pagamentos"] = []

            user_data["pagamentos"].append({
                "id_pagamento": id_pag,
                "valor": valor, # Keep original type (float expected)
                # "data": f"{ViewTime.data_atual()} as {ViewTime.hora_atual()}" # Old incorrect line
                "data": data_hora_formatada # Use the corrected string
            })
            # Ensure InfoUser.add_saldo handles adding correctly
            try:
                InfoUser.add_saldo(id, valor)
            except Exception as e:
                 print(f"[ERROR] add_pagamentos: Failed to add balance via InfoUser.add_saldo. Error: {e}")

            save_user_data(id, user_data)

            afiliado_por = user_data.get("afiliado_por", 0) # Use .get for safety
            # Ensure AfiliadosInfo.status_afiliado() returns boolean True/False
            try:
                status_ativo = AfiliadosInfo.status_afiliado()
            except Exception as e:
                print(f"[ERROR] add_pagamentos: Failed to check affiliate status. Error: {e}")
                status_ativo = False

            if status_ativo and afiliado_por != 0:
                indicador_data = load_user_data(afiliado_por)
                if indicador_data:
                    # Ensure pontos_por_recarga returns an int/float
                    try:
                        pontos_a_adicionar = AfiliadosInfo.pontos_por_recarga()
                        indicador_data["pontos_indicado"] = indicador_data.get("pontos_indicado", 0) + pontos_a_adicionar
                        save_user_data(afiliado_por, indicador_data)
                    except Exception as e:
                        print(f"[ERROR] add_pagamentos: Failed to add affiliate points. Error: {e}")

    def zerar_pontos(id):
        user_data = load_user_data(id)
        if user_data:
            user_data["pontos_indicado"] = 0
            save_user_data(id, user_data)

class GiftCard():
    def validar_gift(codigo):
        try:
            with open_utf8("database/gift_card.json", 'r') as f:
                data = json.load(f)
            for gift in data.get('gift', []): # Use .get for safety
                if gift.get("codigo") == codigo: # Use .get
                    valor = float(gift.get("valor", 0)) # Use .get and default
                    return True, valor
        except FileNotFoundError:
            print("[WARN] validar_gift: gift_card.json not found.")
        except json.JSONDecodeError:
            print("[ERROR] validar_gift: Error decoding gift_card.json.")
        except Exception as e:
            print(f"[ERROR] validar_gift: Unexpected error: {e}")
        return False, 0

    def listar_gift():
        msg = ''
        try:
            with open_utf8('database/gift_card.json', 'r') as f:
                data = json.load(f)
            for gift in data.get("gift", []): # Use .get
                try:
                    # Format value safely
                    valor_str = f"{float(gift.get('valor', 0)):.2f}"
                    msg += f"<code>{html.escape(str(gift.get('codigo', 'N/A')))}</code> R${valor_str}\n" # Escape code
                except (ValueError, TypeError, KeyError):
                    continue # Skip invalid entries
        except FileNotFoundError:
            print("[WARN] listar_gift: gift_card.json not found.")
        except json.JSONDecodeError:
            print("[ERROR] listar_gift: Error decoding gift_card.json.")
        except Exception as e:
            print(f"[ERROR] listar_gift: Unexpected error: {e}")
        return msg if msg else "Nenhum gift card encontrado."

    def create_gift(codigo, valor):
        try:
            with open_utf8("database/gift_card.json", 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
             # Initialize if file doesn't exist or is invalid
            data = {"gift": []}

        if "gift" not in data or not isinstance(data["gift"], list):
            data["gift"] = [] # Ensure 'gift' is a list

        try:
             # Ensure value is float
            data["gift"].append({"codigo": str(codigo), "valor": float(valor)})
            with open_utf8("database/gift_card.json", 'w') as j:
                json.dump(data, j, indent=4)
            return True
        except (ValueError, TypeError) as e:
             print(f"[ERROR] create_gift: Invalid value provided. Error: {e}")
             return False
        except Exception as e:
            print(f"[ERROR] create_gift: Failed to save gift card. Error: {e}")
            return False

    def del_gift(codigo):
        updated = False
        try:
            with open_utf8("database/gift_card.json", 'r') as f:
                data = json.load(f)
            if "gift" not in data or not isinstance(data["gift"], list):
                 return False # Nothing to delete

            # Filter out the gift card with the matching code
            original_len = len(data["gift"])
            data["gift"] = [gift for gift in data["gift"] if gift.get("codigo") != codigo]
            updated = len(data["gift"]) < original_len

            if updated:
                with open_utf8("database/gift_card.json", 'w') as f:
                    json.dump(data, f, indent=4)
                return True
        except FileNotFoundError:
            print("[WARN] del_gift: gift_card.json not found.")
        except json.JSONDecodeError:
            print("[ERROR] del_gift: Error decoding gift_card.json.")
        except Exception as e:
             print(f"[ERROR] del_gift: Failed to delete gift card. Error: {e}")
        return False


class FuncaoTransmitir():
    # Keep the static variables for simplicity in this context
    _foto = None
    _texto = None
    _markup = None
    _video = None

    @staticmethod
    def formatar_html(texto, entities):
        # Implementation depends on the 're' module, ensure it's imported
        import re
        padrao_tags_html = r"<\/?[a-zA-Z]+[^>]*>"
        tags_encontradas = re.findall(padrao_tags_html, texto or "") # Handle None case
        if tags_encontradas:
            return texto or "" # Return empty string if input is None

        tags_html = {
            'bold': ('<b>', '</b>'),
            'italic': ('<i>', '</i>'),
            'code': ('<code>', '</code>'),
            'pre': ('<pre>', '</pre>'), # Added pre format
            'text_link': ('<a href="{url}">', '</a>') # Added link format
        }
        formatted_text = texto or "" # Handle None case
        offset_adjustment = 0

        # Ensure entities is a list and sort safely
        safe_entities = sorted(entities or [], key=lambda e: e.get("offset", 0), reverse=True)

        for entity in safe_entities:
            entity_type = entity.get("type")
            start_offset = entity.get("offset", 0) + offset_adjustment
            length = entity.get("length", 0)
            end_offset = start_offset + length

            if entity_type in tags_html:
                if entity_type == 'text_link':
                    url = entity.get('url', '#') # Default URL if missing
                    tag_abertura, tag_fechamento = tags_html[entity_type]
                    tag_abertura = tag_abertura.format(url=html.escape(url))
                else:
                    tag_abertura, tag_fechamento = tags_html[entity_type]

                # Boundary checks to prevent index errors
                if 0 <= start_offset <= end_offset <= len(formatted_text):
                    formatted_text = (
                        formatted_text[:start_offset] +
                        tag_abertura +
                        formatted_text[start_offset:end_offset] +
                        tag_fechamento +
                        formatted_text[end_offset:]
                    )
                    offset_adjustment += len(tag_abertura) + len(tag_fechamento)
                else:
                     print(f"[WARN] formatar_html: Invalid entity offsets skipped. Entity: {entity}, Text len: {len(formatted_text)}")

        return formatted_text

    @staticmethod
    def pegar_foto():
        return FuncaoTransmitir._foto

    @staticmethod
    def pegar_texto():
        return FuncaoTransmitir._texto

    @staticmethod
    def pegar_markup():
        # Returns the internal representation (needs conversion for API)
        return FuncaoTransmitir._markup

    @staticmethod
    def adicionar_foto(photo):
         # Expects a file path or file_id string
        FuncaoTransmitir._foto = photo

    @staticmethod
    def adicionar_texto(txt):
        FuncaoTransmitir._texto = txt

    @staticmethod
    def adicionar_video(video):
        FuncaoTransmitir._video = video

    @staticmethod
    def pegar_video():
        return FuncaoTransmitir._video

    @staticmethod
    def adicionar_entitie(ent):
        # Applies formatting directly to the stored text
        if FuncaoTransmitir._texto and ent:
            try:
                # Assuming 'ent' is a list of entity objects from pyTelegramBotAPI
                entities_list = [e.to_dict() for e in ent if hasattr(e, 'to_dict')]
                FuncaoTransmitir._texto = FuncaoTransmitir.formatar_html(FuncaoTransmitir._texto, entities_list)
            except Exception as e:
                print(f"[ERROR] adicionar_entitie: Failed to format text. Error: {e}")

    @staticmethod
    def adicionar_markup(markup):
        # Armazena o objeto InlineKeyboardMarkup diretamente, sem convertê-lo
        # para uma lista de dicts. A conversão anterior quebrava o envio em massa,
        # pois bot.send_message/send_photo/send_video exigem um objeto
        # InlineKeyboardMarkup em reply_markup, não uma lista crua.
        FuncaoTransmitir._markup = markup


    @staticmethod
    def zerar_infos():
        FuncaoTransmitir._texto = None
        FuncaoTransmitir._foto = None
        FuncaoTransmitir._markup = None
        FuncaoTransmitir._video = None # Also clear video


# Outras classes ou funções podem continuar aqui...

class ControleLogins():

    @staticmethod
    def _load_acessos():
        """Loads data from acessos.json safely."""
        try:
            with open_utf8('database/acessos.json', 'r') as f:
                data = json.load(f)
            # Ensure the structure is correct
            if not isinstance(data, dict): data = {"acessos": []}
            if "acessos" not in data or not isinstance(data["acessos"], list):
                 data["acessos"] = []
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {"acessos": []} # Return default structure on error
        except Exception as e:
            print(f"[ERROR] _load_acessos: Unexpected error loading acessos.json: {e}")
            return {"acessos": []}

    @staticmethod
    def _save_acessos(data):
        """Saves data to acessos.json safely."""
        try:
            # Ensure the directory exists
            os.makedirs('database', exist_ok=True)
            with open_utf8('database/acessos.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"[ERROR] _save_acessos: Failed to save acessos.json: {e}")
            return False

    @classmethod
    def peek_primeiro_disponivel(cls, servico: str):
        """Finds the first available login without removing it."""
        data = cls._load_acessos()
        servico_lower = servico.lower() # Compare case-insensitive

        for acesso in data.get("acessos", []):
            # Safe access using .get() with defaults
            if acesso.get("nome", "").lower() == servico_lower:
                return (
                    acesso.get("nome"),
                    acesso.get("valor"),
                    acesso.get("email"),
                    acesso.get("senha"),
                    acesso.get("descricao"),
                    acesso.get("duracao")
                )
        return None # Return None if not found


    @classmethod
    def add_login(cls, nome, valor, descricao, email, senha, duracao):
        """Adds a new login."""
        data = cls._load_acessos()
        try:
            # Basic validation
            if not all([nome, valor, email, senha, duracao]):
                 print("[WARN] add_login: Missing required fields.")
                 return False

            data["acessos"].append({
                "nome": str(nome),
                "valor": float(valor), # Ensure value is float
                "descricao": str(descricao or "-"), # Default description
                "email": str(email),
                "senha": str(senha),
                "duracao": int(duracao) # Ensure duration is int
            })
            return cls._save_acessos(data)
        except (ValueError, TypeError) as e:
             print(f"[ERROR] add_login: Invalid data type provided. Error: {e}")
             return False
        except Exception as e:
            print(f"[ERROR] add_login: Unexpected error: {e}")
            return False

    @classmethod
    def remover_login(cls, nome, email):
        """Removes a specific login by name and email."""
        data = cls._load_acessos()
        original_len = len(data["acessos"])
        nome_lower = nome.lower()
        email_lower = email.lower()

        # Filter out the matching login
        data["acessos"] = [
            acesso for acesso in data["acessos"]
            if not (acesso.get("nome", "").lower() == nome_lower and acesso.get("email", "").lower() == email_lower)
        ]

        if len(data["acessos"]) < original_len:
            return cls._save_acessos(data)
        return False # Return False if nothing was removed


    @classmethod
    def pegar_servicos(cls):
        """Obtém a lista completa de todas as entradas de login disponíveis.""" # Docstring atualizado
        data = cls._load_acessos()
        # Retorna a lista inteira de logins, incluindo duplicatas
        return data.get("acessos", [])


    @classmethod
    def estoque_total(cls):
        """Counts the total number of logins."""
        data = cls._load_acessos()
        return len(data.get("acessos", []))

    @classmethod
    def pegar_estoque(cls, nome):
        """Counts the stock for a specific service name."""
        data = cls._load_acessos()
        nome_lower = nome.lower()
        quantidade = 0
        for acesso in data.get("acessos", []):
            if acesso.get("nome", "").lower() == nome_lower:
                quantidade += 1
        return quantidade

    @classmethod
    def pegar_estoque_detalhado(cls):
        """Gets detailed stock count for each service."""
        data = cls._load_acessos()
        estoque_map = {}
        for acesso in data.get("acessos", []):
            nome = acesso.get("nome")
            if nome:
                estoque_map[nome] = estoque_map.get(nome, 0) + 1

        if not estoque_map:
             return "<b>ESTOQUE VAZIO</b>"

        montagem = "<b>ACESSOS EM ESTOQUE:</b>\n\n"
        logins = ''
        # Sort alphabetically for consistent output
        for nome, quantidade in sorted(estoque_map.items()):
            logins += f'{html.escape(nome)}: {quantidade}\n' # Escape names

        montagem += f"<code>{logins.strip()}</code>" # Use code block for alignment
        return montagem

    @classmethod
    def criar_estoque_detalhado(cls):
        """Creates a detailed stock report file."""
        data = cls._load_acessos()
        if not data.get("acessos"):
            print("[INFO] criar_estoque_detalhado: No stock to create report.")
            return False

        mensagem = "ACESSOS EM ESTOQUE DETALHADO:\n" + "="*30 + "\n\n"
        for acesso in data["acessos"]:
            try:
                 mensagem += (
                    f'Nome: {acesso.get("nome", "N/A")}\n'
                    f'Valor: {acesso.get("valor", "N/A")}\n'
                    f'Descricao: {acesso.get("descricao", "N/A")}\n'
                    f'Email: {acesso.get("email", "N/A")}\n'
                    f'Senha: {acesso.get("senha", "N/A")}\n'
                    f'Duracao: {acesso.get("duracao", "N/A")} dias\n'
                    + "-"*30 + "\n\n"
                 )
            except Exception as e:
                print(f"[WARN] criar_estoque_detalhado: Skipping invalid record. Error: {e}")
                continue

        try:
            os.makedirs('historicos', exist_ok=True)
            with open_utf8('historicos/estoque_detalhado.txt', 'w') as f:
                f.write(mensagem)
            return True
        except Exception as e:
            print(f"[ERROR] criar_estoque_detalhado: Failed to write report file. Error: {e}")
            return False


    @staticmethod
    def arquivo_estoque_detalhado():
        """Provides the detailed stock report file object (read-binary)."""
        # This method assumes the file exists. Error handling should be done by the caller.
        try:
            return open_utf8('historicos/estoque_detalhado.txt', 'rb')
        except FileNotFoundError:
            print("[ERROR] arquivo_estoque_detalhado: Report file not found.")
            raise # Re-raise the error for the caller to handle
        except Exception as e:
            print(f"[ERROR] arquivo_estoque_detalhado: Error opening report file: {e}")
            raise

    @classmethod
    def remover_por_nome(cls, nome):
        """Removes all logins matching a specific service name."""
        data = cls._load_acessos()
        acessos_antes = len(data["acessos"])
        nome_lower = nome.lower()

        # Keep only logins that DO NOT match the name
        data["acessos"] = [
            acesso for acesso in data["acessos"]
            if acesso.get("nome", "").lower() != nome_lower
        ]

        acessos_depois = len(data["acessos"])
        removidos = acessos_antes - acessos_depois

        if removidos > 0:
            cls._save_acessos(data)

        return removidos


    @classmethod
    def zerar_estoque(cls):
        """Removes all logins from the stock."""
        data = {"acessos": []} # Create a new empty structure
        return cls._save_acessos(data)


    @classmethod
    def mudar_valor_por_nome(cls, nome, novo_valor):
        """Changes the price for all logins of a specific service."""
        data = cls._load_acessos()
        nome_lower = nome.lower()
        changed = False
        try:
            valor_float = float(novo_valor) # Validate and convert once
            for acesso in data.get("acessos", []):
                if acesso.get("nome", "").lower() == nome_lower:
                    acesso["valor"] = valor_float
                    changed = True
            if changed:
                return cls._save_acessos(data)
            return False # Return False if name not found or no change made
        except (ValueError, TypeError) as e:
            print(f"[ERROR] mudar_valor_por_nome: Invalid new value '{novo_valor}'. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] mudar_valor_por_nome: Unexpected error: {e}")
            return False


    @classmethod
    def mudar_valor_de_todos(cls, valor):
        """Changes the price for ALL logins in stock."""
        data = cls._load_acessos()
        try:
            valor_float = float(valor) # Validate and convert once
            if not data.get("acessos"): return False # Nothing to change

            for acesso in data["acessos"]:
                acesso["valor"] = valor_float
            return cls._save_acessos(data)
        except (ValueError, TypeError) as e:
            print(f"[ERROR] mudar_valor_de_todos: Invalid value '{valor}'. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] mudar_valor_de_todos: Unexpected error: {e}")
            return False


    @classmethod
    def pegar_info(cls, nome):
        """Gets info for the first login matching the name."""
        data = cls._load_acessos()
        nome_lower = nome.lower()
        for acesso in data.get("acessos", []):
            if acesso.get("nome", "").lower() == nome_lower:
                # Return tuple with defaults for missing keys
                return (
                    acesso.get("nome"),
                    acesso.get("valor"),
                    acesso.get("descricao"),
                    acesso.get("duracao"),
                    acesso.get("email")
                )
        return None, None, None, None, None # Return tuple of Nones if not found


    @classmethod
    def entregar_acesso(cls, nome, email):
        """Gets info for a specific login (name and email), DOES NOT REMOVE."""
        # Note: This seems redundant with pegar_info_entrega. Consider merging.
        data = cls._load_acessos()
        nome_lower = nome.lower()
        email_lower = email.lower()
        for acesso in data.get("acessos", []):
            if acesso.get("nome", "").lower() == nome_lower and acesso.get("email", "").lower() == email_lower:
                return (
                    acesso.get("nome"),
                    acesso.get("valor"),
                    acesso.get("email"),
                    acesso.get("senha"),
                    acesso.get("descricao"),
                    acesso.get("duracao")
                )
        return None # Return None if not found


    @classmethod
    def pegar_info_entrega(cls, nome, email):
        """Gets the full dict for a specific login (name and email), DOES NOT REMOVE."""
        data = cls._load_acessos()
        nome_lower = nome.lower()
        email_lower = email.lower()
        for acesso in data.get("acessos", []):
             if acesso.get("nome", "").lower() == nome_lower and acesso.get("email", "").lower() == email_lower:
                return acesso # Return the whole dictionary
        return None # Return None if not found


    @classmethod
    def pegar_primeiro_disponivel(cls, servico: str):
        """
        Finds, removes, and returns the first available login for a service.
        Returns tuple: (nome, valor, email, senha, descricao, duracao) or None.
        """
        data = cls._load_acessos()
        servico_lower = servico.lower()
        found_acesso = None
        found_index = -1

        # Find the first matching login
        for i, acesso in enumerate(data.get("acessos", [])):
            if acesso.get("nome", "").lower() == servico_lower:
                found_acesso = acesso
                found_index = i
                break # Stop after finding the first one

        if found_acesso:
            # Remove the found login from the list *by index*
            del data["acessos"][found_index]

            # Save the updated list back to the file
            if cls._save_acessos(data):
                # Return the details of the removed login
                return (
                    found_acesso.get("nome"),
                    found_acesso.get("valor"),
                    found_acesso.get("email"),
                    found_acesso.get("senha"),
                    found_acesso.get("descricao"),
                    found_acesso.get("duracao")
                )
            else:
                 # Should ideally handle save failure (e.g., log error, maybe try to re-add?)
                 print(f"[CRITICAL] pegar_primeiro_disponivel: Failed to save acessos.json after removing login for '{servico}'. Potential data loss!")
                 return None
        else:
            # Service not found or out of stock
            return None




# Todas as consultas e reservas usam exclusivamente o fornecedor remoto.
from app.estoque_api import criar_controle
ControleLogins = criar_controle(ControleLogins)

class Admin():
    def total_users():
        try:
            # Conta os usuários registrados no PostgreSQL (antes contava arquivos
            # em database/users, pasta que ficou vazia após a migração para o banco).
            return len(get_all_user_ids())
        except Exception as e:
            print(f"[ERROR] total_users: Failed to count users. Error: {e}")
            return 0 # Return 0 on error


    def verificar_vencimento():
        try:
            time_left = Admin.tempo_ate_o_vencimento()
            # Handle potential None return from tempo_ate_o_vencimento
            return time_left is not None and int(time_left) <= 0
        except Exception as e:
            print(f"[ERROR] verificar_vencimento: Error checking expiration. Error: {e}")
            return True # Assume expired if check fails

    def data_vencimento():
        try:
            # --- PATCH ALUGUEL START ---
            import os, datetime
            caminho_aluguel = os.path.join(os.getcwd(), 'settings', 'aluguel_config.json')
            if os.path.exists(caminho_aluguel):
                try:
                    with open(caminho_aluguel, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        data_criacao = datetime.datetime.strptime(dados.get('data_criacao'), "%Y-%m-%d %H:%M:%S")
                        dias_comprados = int(dados.get('dias_vencimento', 30))
                        data_venc = data_criacao + datetime.timedelta(days=dias_comprados)
                        return data_venc.strftime('%d/%m/%Y')
                except Exception:
                    pass
            # --- PATCH ALUGUEL END ---

            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            # Use .get with a default fallback date
            return str(data.get("vencimento_bot", "01/01/1970"))
        except Exception as e:
            print(f"[ERROR] data_vencimento: Failed to read expiration date. Error: {e}")
            return "01/01/1970" # Fallback date

    def tempo_ate_o_vencimento():
        try:
            # --- PATCH ALUGUEL START ---
            import os, datetime
            caminho_aluguel = os.path.join(os.getcwd(), 'settings', 'aluguel_config.json')
            if os.path.exists(caminho_aluguel):
                try:
                    with open(caminho_aluguel, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        data_criacao = datetime.datetime.strptime(dados.get('data_criacao'), "%Y-%m-%d %H:%M:%S").date()
                        dias_comprados = int(dados.get('dias_vencimento', 30))
                        data_venc = data_criacao + datetime.timedelta(days=dias_comprados)
                        data_atual = datetime.datetime.now().date()
                        return (data_venc - data_atual).days
                except Exception:
                    pass
            # --- PATCH ALUGUEL END ---

            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data_vencimento_str = data.get('vencimento_bot')
            if not data_vencimento_str: return 0 # Return 0 if date is missing

            data_vencimento = datetime.datetime.strptime(data_vencimento_str, '%d/%m/%Y').date()
            data_atual = datetime.datetime.now().date()
            diferenca = data_vencimento - data_atual
            return diferenca.days
        except (ValueError, TypeError) as e:
            print(f"[ERROR] tempo_ate_o_vencimento: Invalid date format in credenciais.json. Error: {e}")
            return 0 # Return 0 if date format is wrong
        except Exception as e:
            print(f"[ERROR] tempo_ate_o_vencimento: Failed to calculate days left. Error: {e}")
            return 0 # Return 0 on other errors

    def aumentar_vencimento(dias):
        try:
            # --- PATCH ALUGUEL START ---
            import os
            caminho_aluguel = os.path.join(os.getcwd(), 'settings', 'aluguel_config.json')
            if os.path.exists(caminho_aluguel):
                try:
                    with open(caminho_aluguel, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    dados['dias_vencimento'] = int(dados.get('dias_vencimento', 30)) + int(dias)
                    with open(caminho_aluguel, 'w', encoding='utf-8') as f:
                        json.dump(dados, f, indent=4)
                    return True
                except Exception:
                    pass
            # --- PATCH ALUGUEL END ---

            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            vencimento_dias = int(dias) # Ensure dias is int
            vencimento_bot_str = data.get('vencimento_bot', datetime.datetime.now().strftime('%d/%m/%Y')) # Default to today if missing

            vencimento_bot = datetime.datetime.strptime(vencimento_bot_str, '%d/%m/%Y')
            nova_data = vencimento_bot + datetime.timedelta(days=vencimento_dias)
            data["vencimento_bot"] = nova_data.strftime('%d/%m/%Y')
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except (ValueError, TypeError) as e:
            print(f"[ERROR] aumentar_vencimento: Invalid input or date format. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] aumentar_vencimento: Failed to update expiration date. Error: {e}")
            return False


    def diminuir_vencimento(days):
        try:
            # --- PATCH ALUGUEL START ---
            import os
            caminho_aluguel = os.path.join(os.getcwd(), 'settings', 'aluguel_config.json')
            if os.path.exists(caminho_aluguel):
                try:
                    with open(caminho_aluguel, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    dados['dias_vencimento'] = int(dados.get('dias_vencimento', 30)) - int(days)
                    with open(caminho_aluguel, 'w', encoding='utf-8') as f:
                        json.dump(dados, f, indent=4)
                    return True
                except Exception:
                    pass
            # --- PATCH ALUGUEL END ---

            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            vencimento_dias = int(days) # Ensure days is int
            vencimento_str = data.get("vencimento_bot", datetime.datetime.now().strftime('%d/%m/%Y')) # Default to today

            vencimento_bot = datetime.datetime.strptime(vencimento_str, '%d/%m/%Y')
            nova_data = vencimento_bot - datetime.timedelta(days=vencimento_dias)
            data["vencimento_bot"] = nova_data.strftime('%d/%m/%Y')
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except (ValueError, TypeError) as e:
            print(f"[ERROR] diminuir_vencimento: Invalid input or date format. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] diminuir_vencimento: Failed to update expiration date. Error: {e}")
            return False


    def zerar_vencimento():
        try:
            # --- PATCH ALUGUEL START ---
            import os
            caminho_aluguel = os.path.join(os.getcwd(), 'settings', 'aluguel_config.json')
            if os.path.exists(caminho_aluguel):
                try:
                    with open(caminho_aluguel, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                    dados['dias_vencimento'] = 0
                    with open(caminho_aluguel, 'w', encoding='utf-8') as f:
                        json.dump(dados, f, indent=4)
                    return True
                except Exception:
                    pass
            # --- PATCH ALUGUEL END ---

            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["vencimento_bot"] = '01/01/1970' # Use a past date
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"[ERROR] zerar_vencimento: Failed to reset expiration date. Error: {e}")
            return False

    def receita_total():
        receita = 0.0
        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] receita_total: Failed to fetch user ids. Error: {e}")
            return 0.0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id)
                if not user_data: continue

                # Sum payments safely
                for pagamento in user_data.get("pagamentos", []):
                    try:
                        receita += float(pagamento.get("valor", 0))
                    except (ValueError, TypeError, KeyError):
                        print(f"[WARN] receita_total: Skipping invalid payment value for user {user_id}: {pagamento.get('valor')}")
                        continue
            except Exception as e:
                print(f"[ERROR] receita_total: Failed to process user {user_id}. Error: {e}")
                continue
        return receita


    def receita_hoje():
        receita_dia = 0.0
        tz = pytz.timezone('America/Sao_Paulo')
        today_str = datetime.datetime.now(tz).strftime('%d/%m/%Y')
        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] receita_hoje: Failed to fetch user ids. Error: {e}")
            return 0.0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id)
                if not user_data: continue

                for pagamento in user_data.get("pagamentos", []):
                    try:
                        # Check if payment date matches today's date string
                        if str(pagamento.get('data', '').split(' ')[0]) == today_str:
                             receita_dia += float(pagamento.get('valor', 0))
                    except (ValueError, TypeError, KeyError, IndexError) as e:
                        print(f"[WARN] receita_hoje: Skipping invalid payment record for user {user_id}: {pagamento}. Error: {e}")
                        continue # Skip invalid payment records
            except Exception as e:
                print(f"[ERROR] receita_hoje: Failed to process user {user_id}. Error: {e}")
                continue
        return receita_dia


    def acessos_vendidos():
        quantidade = 0
        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] acessos_vendidos: Failed to fetch user ids. Error: {e}")
            return 0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id)
                if user_data:
                    # Count the length of the 'compras' list
                    quantidade += len(user_data.get("compras", []))
            except Exception as e:
                 print(f"[ERROR] acessos_vendidos: Failed to process user {user_id}. Error: {e}")
                 continue
        return quantidade


    def acessos_vendidos_hoje():
        quantidade = 0
        tz = pytz.timezone('America/Sao_Paulo')
        today_str = datetime.datetime.now(tz).strftime('%d/%m/%Y')
        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] acessos_vendidos_hoje: Failed to fetch user ids. Error: {e}")
            return 0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id)
                if not user_data: continue

                for compra in user_data.get("compras", []):
                    try:
                         # Check if purchase date string matches today
                        if compra.get("data", "").split(' ')[0] == today_str:
                            quantidade += 1
                    except (AttributeError, IndexError, KeyError):
                         # Handle cases where 'data' might be missing or malformed
                         print(f"[WARN] acessos_vendidos_hoje: Skipping invalid purchase record for user {user_id}: {compra}")
                         continue
            except Exception as e:
                print(f"[ERROR] acessos_vendidos_hoje: Failed to process user {user_id}. Error: {e}")
                continue
        return quantidade


    def verificar_admin(id):
        try:
            with open_utf8('database/admins.json', 'r') as f:
                data = json.load(f)
            # Use .get for safer access
            for admin in data.get("admins", []):
                # Ensure comparison is between integers
                if int(admin.get("id", -1)) == int(id):
                    return True
        except (FileNotFoundError, json.JSONDecodeError):
             print("[ERROR] verificar_admin: admins.json not found or corrupted.")
             return False # Assume not admin if file is missing/invalid
        except (ValueError, TypeError) as e:
             print(f"[ERROR] verificar_admin: Invalid ID format in admins.json or input. Error: {e}")
             return False # Invalid ID format
        except Exception as e:
            print(f"[ERROR] verificar_admin: Unexpected error: {e}")
            return False
        return False


    def add_admin(id):
        try:
            admin_id = int(id) # Validate ID format early
            try:
                with open_utf8('database/admins.json', 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"admins": []} # Initialize if file missing/invalid

            if "admins" not in data or not isinstance(data["admins"], list):
                data["admins"] = [] # Ensure structure

            # Check if admin already exists
            if any(admin.get("id") == admin_id for admin in data["admins"]):
                print(f"[INFO] add_admin: Admin {admin_id} already exists.")
                return True # Already exists, consider it success

            data["admins"].append({"id": admin_id})

            # Ensure directory exists before saving
            os.makedirs('database', exist_ok=True)
            with open_utf8('database/admins.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except (ValueError, TypeError) as e:
            print(f"[ERROR] add_admin: Invalid ID provided '{id}'. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] add_admin: Failed to add admin {id}. Error: {e}")
            return False


    def quantidade_admin():
        try:
            with open_utf8('database/admins.json', 'r') as f:
                data = json.load(f)
            # Safely count the list length
            return len(data.get("admins", []))
        except (FileNotFoundError, json.JSONDecodeError):
            return 0 # Return 0 if file missing/invalid
        except Exception as e:
            print(f"[ERROR] quantidade_admin: Error reading admins file: {e}")
            return 0


    def listar_admins():
        adm_list = '<b>👮 LISTA DE ADMINS:</b> 🚨\n\n'
        found_admins = False
        try:
            with open_utf8('database/admins.json', 'r') as f:
                data = json.load(f)
            # Safely iterate through admins
            for admin in data.get("admins", []):
                try:
                    admin_id = int(admin.get("id", "N/A")) # Get ID safely
                    adm_list += f'<b>ADMIN ID</b>: <code>{admin_id}</code>\n'
                    found_admins = True
                except (ValueError, TypeError, KeyError):
                    adm_list += '<b>ADMIN ID</b>: <code>INVALID_ENTRY</code>\n' # Mark invalid entries
                    continue
        except (FileNotFoundError, json.JSONDecodeError):
            adm_list += "<i>Arquivo de admins não encontrado ou corrompido.</i>"
        except Exception as e:
            print(f"[ERROR] listar_admins: Error reading admins file: {e}")
            adm_list += f"<i>Erro ao ler a lista: {e}</i>"

        if not found_admins and "Erro" not in adm_list and "não encontrado" not in adm_list:
             adm_list += "<i>Nenhum administrador cadastrado.</i>"

        return adm_list


    def obter_ids_admins():
        """Retorna uma lista com os IDs de todos os admins"""
        ids = []
        try:
            with open_utf8('database/admins.json', 'r') as f:
                data = json.load(f)
            for admin in data.get("admins", []):
                 try:
                    ids.append(int(admin["id"])) # Ensure ID is integer
                 except (ValueError, TypeError, KeyError):
                     continue # Skip invalid entries
        except (FileNotFoundError, json.JSONDecodeError):
            pass # Return empty list if file issues
        except Exception as e:
            print(f"[ERROR] obter_ids_admins: Error reading admin IDs: {e}")
        return ids


    def remover_admin(id):
        updated = False
        try:
            admin_id_to_remove = int(id) # Validate ID format
            try:
                with open_utf8('database/admins.json', 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return False # Nothing to remove

            if "admins" not in data or not isinstance(data["admins"], list):
                return False # Nothing to remove

            original_len = len(data["admins"])
            # Filter out the admin to remove
            data["admins"] = [
                admin for admin in data["admins"]
                if admin.get("id") != admin_id_to_remove
            ]
            updated = len(data["admins"]) < original_len

            if updated:
                with open_utf8('database/admins.json', 'w') as f:
                    json.dump(data, f, indent=4)
                return True
        except (ValueError, TypeError) as e:
             print(f"[ERROR] remover_admin: Invalid ID provided '{id}'. Error: {e}")
             return False
        except Exception as e:
             print(f"[ERROR] remover_admin: Failed to remove admin {id}. Error: {e}")
             return False
        return False # Return False if not found or not updated


    def receita_semana():
        receita = 0.0
        tz = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.datetime.now(tz)
        # Use floor division for days of week to start on Monday (0)
        # Calculate days since Monday
        days_since_monday = hoje.weekday()
        # Subtract those days to get the start of the current week (Monday 00:00:00)
        inicio_semana = hoje - datetime.timedelta(days=days_since_monday,
                                                  hours=hoje.hour,
                                                  minutes=hoje.minute,
                                                  seconds=hoje.second,
                                                  microseconds=hoje.microsecond)

        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] receita_semana: Failed to fetch user ids. Error: {e}")
            return 0.0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id) # Use your existing function
                if not user_data: continue

                # Check total_pagos using .get for safety
                if user_data.get("total_pagos", 0) > 0:
                    for pagamento in user_data.get("pagamentos", []):
                        try:
                            data_pagamento_str = pagamento.get('data', '')
                            if not data_pagamento_str: continue

                            data_pagamento_naive = None
                            # Tenta analisar os formatos possíveis (incluindo o formato corrompido 'Ã s')
                            for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y às %H:%M:%S", "%d/%m/%Y as %H:%M:%S", "%d/%m/%Y Ã s %H:%M:%S"):
                                try:
                                    data_pagamento_naive = datetime.datetime.strptime(data_pagamento_str, fmt)
                                    break # Sai do loop se encontrar um formato válido
                                except ValueError:
                                    continue # Tenta o próximo formato

                            # Se nenhum formato funcionou, loga o erro e pula
                            if data_pagamento_naive is None:
                                raise ValueError(f"Formato de data desconhecido ou inválido: '{data_pagamento_str}'")

                            # Localiza o objeto datetime
                            data_pagamento = tz.localize(data_pagamento_naive)

                        except ValueError as e:
                            # Loga o erro se o formato for realmente inválido ou desconhecido
                            print(f"[WARN] receita_semana: Skipping payment for user {user_id} due to date format error. Date: '{data_pagamento_str}'. Error: {e}")
                            continue # Skip this payment record
                        except Exception as e:
                            # Log other unexpected errors during date processing
                            print(f"[ERROR] receita_semana: Unexpected date processing error for user {user_id}: '{pagamento}'. Error: {e}")
                            continue # Skip this payment record

                        # Compare timezone-aware datetimes
                        if data_pagamento >= inicio_semana:
                            try:
                                # Ensure valor is treated as float before adding
                                receita += float(pagamento['valor'])
                            except (ValueError, TypeError, KeyError) as val_err:
                                # Log error if value is invalid
                                print(f"[WARN] receita_semana: Skipping payment for user {user_id} due to invalid value '{pagamento.get('valor')}'. Error: {val_err}")
                                continue
            except Exception as outer_e:
                 # Log error if processing a whole user fails
                 print(f"[ERROR] receita_semana: Failed to process user {user_id}. Error: {outer_e}")
                 continue # Skip this user entirely on major error

        return receita # Return the calculated weekly revenue


    def acessos_vendidos_semana():
        quantidade = 0
        tz = pytz.timezone('America/Sao_Paulo')
        hoje = datetime.datetime.now(tz)
        # Correctly calculate the start of the week (Monday 00:00:00)
        days_since_monday = hoje.weekday()
        inicio_semana = hoje - datetime.timedelta(days=days_since_monday,
                                                  hours=hoje.hour,
                                                  minutes=hoje.minute,
                                                  seconds=hoje.second,
                                                  microseconds=hoje.microsecond)
        # Migrado para SQLite: 'database/users' não existe mais após a migração para o banco.
        try:
            user_ids = get_all_user_ids()
        except Exception as e:
            print(f"[ERROR] acessos_vendidos_semana: Failed to fetch user ids. Error: {e}")
            return 0

        for user_id in user_ids:
            try:
                user_data = load_user_data(user_id)
                if not user_data: continue

                # Check total_compras using .get for safety
                if user_data.get("total_compras", 0) > 0:
                    for compra in user_data.get("compras", []):
                        try:
                            data_compra_str = compra.get('data', '')
                            if not data_compra_str: continue

                            data_compra_naive = None
                            # Tenta analisar os formatos possíveis (incluindo o formato corrompido 'Ã s')
                            for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y às %H:%M:%S", "%d/%m/%Y as %H:%M:%S", "%d/%m/%Y Ã s %H:%M:%S"):
                                try:
                                    data_compra_naive = datetime.datetime.strptime(data_compra_str, fmt)
                                    break # Sai do loop se encontrar um formato válido
                                except ValueError:
                                    continue # Tenta o próximo formato

                            # Se nenhum formato funcionou, loga o erro e pula
                            if data_compra_naive is None:
                                raise ValueError(f"Formato de data desconhecido ou inválido: '{data_compra_str}'")

                            # Localiza o objeto datetime
                            data_compra = tz.localize(data_compra_naive)

                        except ValueError as e:
                            # Loga o erro se o formato for realmente inválido ou desconhecido
                            print(f"[WARN] acessos_vendidos_semana: Skipping purchase for user {user_id} due to date format error. Date: '{data_compra_str}'. Error: {e}")
                            continue
                        except Exception as e:
                            print(f"[ERROR] acessos_vendidos_semana: Unexpected date processing error for user {user_id}: '{compra}'. Error: {e}")
                            continue

                        # Compare timezone-aware dates
                        if data_compra >= inicio_semana:
                            quantidade += 1
            except Exception as outer_e:
                print(f"[ERROR] acessos_vendidos_semana: Failed to process user {user_id}. Error: {outer_e}")
                continue
        return quantidade

class Textos():
    @staticmethod
    def _read_text_file(filename):
        """Safely reads a text file from the 'textos' directory."""
        filepath = os.path.join('textos', f"{filename}.txt")
        try:
            with open_utf8(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[WARN] Text file not found: {filepath}")
            return f"<{filename.upper()} TEXT MISSING>" # Fallback text
        except Exception as e:
            print(f"[ERROR] Failed to read text file {filepath}: {e}")
            return f"<ERROR READING {filename.upper()}>"

    @staticmethod
    def _format_text(template, message=None, **kwargs):
        """Formats the text template with provided data."""
        data = {}
        # Get data from message if provided
        if message:
            user_id = message.chat.id
            if str(user_id).startswith('-'): # Group message scenario
                 user_id = message.from_user.id
                 first_name = message.from_user.first_name or "User"
                 username = message.from_user.username or f"user_{user_id}"
            else:
                 first_name = message.chat.first_name or "User"
                 username = message.chat.username or f"user_{user_id}"

            data['first_name'] = first_name
            data['username'] = username
            data['id'] = user_id
            data['link_afiliado'] = f'https://t.me/{CredentialsChange.user_bot()}?start={user_id}'

            # Safely get user stats
            try: data['saldo'] = f'{InfoUser.saldo(user_id):.2f}'
            except: data['saldo'] = '0.00'
            try: data['pontos_indicacao'] = str(InfoUser.pontos_indicacao(user_id))
            except: data['pontos_indicacao'] = '0'
            try: data['quantidade_afiliados'] = str(InfoUser.quantidade_afiliados(user_id))
            except: data['quantidade_afiliados'] = '0'
            try: data['quantidade_compras'] = str(InfoUser.total_compras(user_id))
            except: data['quantidade_compras'] = '0'
            try: data['pix_inseridos'] = f'{InfoUser.pix_inseridos(user_id):.2f}'
            except: data['pix_inseridos'] = '0.00'
            try: data['gifts_resgatados'] = f'{InfoUser.gifts_resgatados(user_id):.2f}'
            except: data['gifts_resgatados'] = '0.00'
            try:
                _bonus_pct = CredentialsChange.BonusPix.quantidade_bonus()
                if _bonus_pct and _bonus_pct > 0:
                    try:
                        _bonus_min = CredentialsChange.BonusPix.valor_minimo_para_bonus()
                        _bonus_min_txt = f'{_bonus_min:.2f}'
                    except:
                        _bonus_min_txt = '0.00'
                    data['bonus_pix_status'] = f'✅ Ativado ({_bonus_pct}% a partir de R${_bonus_min_txt})'
                else:
                    data['bonus_pix_status'] = '❌ Desativado'
            except: data['bonus_pix_status'] = '❌ Desativado'
        else:
            # Provide default empty strings if no message context
            data = {
                'first_name': '', 'username': '', 'id': '', 'link_afiliado': '',
                'saldo': '0.00', 'pontos_indicacao': '0', 'quantidade_afiliados': '0',
                'quantidade_compras': '0', 'pix_inseridos': '0.00', 'gifts_resgatados': '0.00',
                'bonus_pix_status': '❌ Desativado'
            }


        # Add specific kwargs passed to the method
        data.update(kwargs)

        # Format the template using .format_map for missing key safety
        return template.format_map(data)

    # Specific text methods
    @classmethod
    def start(cls, message):
        template = cls._read_text_file('start')
        return cls._format_text(template, message)

    @classmethod
    def perfil(cls, message):
        template = cls._read_text_file('perfil')
        return cls._format_text(template, message)

    @classmethod
    def adicionar_saldo(cls, message):
        template = cls._read_text_file('adicionar_saldo')
        return cls._format_text(template, message)

    @classmethod
    def pix_manual(cls, message):
        template = cls._read_text_file('pix_manual')
        try: deposito_minimo = f'{CredentialsChange.InfoPix.deposito_minimo_pix():.2f}'
        except: deposito_minimo = 'N/A'
        return cls._format_text(template, message, deposito_minimo=deposito_minimo)

    @classmethod
    def pix_automatico(cls, message, pix_copia_cola, expiracao, id_pagamento, valor):
        template = cls._read_text_file('pix_automatico')
        try: deposito_minimo = f'{CredentialsChange.InfoPix.deposito_minimo_pix():.2f}'
        except: deposito_minimo = 'N/A'
        return cls._format_text(template, message,
                                pix_copia_cola=pix_copia_cola,
                                expiracao=expiracao,
                                id_pagamento=id_pagamento,
                                valor=valor,
                                deposito_minimo=deposito_minimo)

    @classmethod
    def pagamento_expirado(cls, message, id_pagamento, valor):
        template = cls._read_text_file('pagamento_expirado')
        return cls._format_text(template, message, id_pagamento=id_pagamento, valor=valor)

    @classmethod
    def pagamento_aprovado(cls, message, id_pagamento, valor):
        template = cls._read_text_file('pagamento_aprovado')
        return cls._format_text(template, message, id_pagamento=id_pagamento, valor=valor)

    @classmethod
    def menu_comprar(cls, message):
        template = cls._read_text_file('menu_comprar')
        return cls._format_text(template, message)

    @classmethod
    def exibir_servico(cls, message, nome):
        template = cls._read_text_file('exibir_servico')
        user_id = message.chat.id
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'

        try:
            nome_servico, valor, descricao, duracao, email = ControleLogins.pegar_info(nome)
            # Ensure safe formatting and defaults
            valor_fmt = f'{float(valor):.2f}' if valor is not None else 'N/A'
            descricao = descricao or "Sem descrição"
            duracao = str(duracao) if duracao is not None else 'N/A'
            estoque = str(ControleLogins.pegar_estoque(nome))
        except Exception as e:
            print(f"[ERROR] exibir_servico: Failed to get service info for '{nome}'. Error: {e}")
            nome_servico, valor_fmt, descricao, duracao, estoque, email = nome, 'Erro', 'Erro ao buscar detalhes', 'N/A', 'N/A', None

        # Format text and return email separately
        texto = cls._format_text(template, message,
                                 nome_servico=nome_servico,
                                 valor=valor_fmt,
                                 descricao=descricao,
                                 saldo=saldo, # Saldo was already formatted
                                 estoque=estoque,
                                 duracao=duracao)
        return texto, email # Return email for potential use elsewhere

    @classmethod
    def mensagem_comprou(cls, message, nome, valor, email, senha, descricao, duracao):
        template = cls._read_text_file('mensagem_comprou')
        user_id = message.chat.id
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'
        # Format values safely
        valor_fmt = f'{float(valor):.2f}' if valor is not None else 'N/A'
        duracao = str(duracao) if duracao is not None else 'N/A'
        descricao = descricao or "-"

        return cls._format_text(template, message,
                                nome=nome, valor=valor_fmt, saldo=saldo,
                                email=email, senha=senha, duracao=duracao,
                                descricao=descricao)

    @classmethod
    def mensagem_comprou_inline(cls, user_id, nome, valor, email, senha, descricao, duracao):
        """ Inline version without message object. """
        # --- Imports necessários (verifique se já existem no topo do central.py) ---
        import datetime
        import pytz
        # --------------------------------------------------------------------------

        template = cls._read_text_file('mensagem_comprou')
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'
        valor_fmt = f'{float(valor):.2f}' if valor is not None else 'N/A'
        duracao = str(duracao) if duracao is not None else 'N/A'
        descricao = descricao or "-"

        # Need basic user info if template uses {first_name} etc. - fetch if necessary
        first_name = f"User {user_id}" # Placeholder
        username = f"user_{user_id}"   # Placeholder

        # --- ADICIONADO: Obter data atual formatada sem horário ---
        tz = pytz.timezone('America/Sao_Paulo')
        agora = datetime.datetime.now(tz)
        data_atual_sem_horario = agora.strftime("%d/%m/%Y")
        data_atual_com_horario = agora.strftime("%d/%m/%Y %H:%M:%S") # Para compatibilidade, caso use {data_atual}
        try:
             # Calcula data de vencimento também
             data_venc = agora + datetime.timedelta(days=int(duracao))
             data_venc_formatada = data_venc.strftime("%d/%m/%Y")
        except:
             data_venc_formatada = "N/A"
        # -----------------------------------------------------------

        # Format using a dictionary for safety
        data = {
            'first_name': first_name, 'username': username, 'id': user_id,
            'link_afiliado': f'https://t.me/{CredentialsChange.user_bot()}?start={user_id}',
            'saldo': saldo, 'pontos_indicacao': '0', 'quantidade_afiliados': '0', # Default stats
            'quantidade_compras': '0', 'pix_inseridos': '0.00', 'gifts_resgatados': '0.00',
            'nome': nome, 'valor': valor_fmt, 'email': email, 'senha': senha,
            'duracao': duracao, 'descricao': descricao,
            # --- CHAVE ADICIONADA ---
            'data_sem_horario': data_atual_sem_horario,
            # --- Adicionado para garantir compatibilidade com a função entregar original ---
            'data_atual': data_atual_com_horario, # Se o template usar {data_atual}
            'data_vencimento': data_venc_formatada # Se o template usar {data_vencimento}
            # --------------------------------------------------------------------------
        }
        return template.format_map(data)


from app.suporte import log_info, log_error # Assuming logger.py exists

class MudarTexto():
    @staticmethod
    def _save_text_file(filename, texto):
        """Safely saves text to a file in the 'textos' directory."""
        filepath = os.path.join('textos', f"{filename}.txt")
        try:
            # Ensure directory exists
            os.makedirs('textos', exist_ok=True)
            with open_utf8(filepath, 'w') as f:
                f.write(texto)
            log_info(f"Texto {filename} atualizado com sucesso")
            return True
        except Exception as e:
            log_error(f"Erro ao atualizar {filename}: {str(e)}")
            # raise # Optionally re-raise the exception
            return False

    # Static methods for each text type
    @staticmethod
    def alugar_bot(texto): return MudarTexto._save_text_file('alugar_bot', texto)
    @staticmethod
    def start(texto): return MudarTexto._save_text_file('start', texto)
    @staticmethod
    def perfil(texto): return MudarTexto._save_text_file('perfil', texto)
    @staticmethod
    def adicionar_saldo(texto): return MudarTexto._save_text_file('adicionar_saldo', texto)
    @staticmethod
    def pix_manual(texto): return MudarTexto._save_text_file('pix_manual', texto)
    @staticmethod
    def pix_automatico(texto): return MudarTexto._save_text_file('pix_automatico', texto)
    @staticmethod
    def pagamento_expirado(texto): return MudarTexto._save_text_file('pagamento_expirado', texto)
    @staticmethod
    def pagamento_aprovado(texto): return MudarTexto._save_text_file('pagamento_aprovado', texto)
    @staticmethod
    def menu_comprar(texto): return MudarTexto._save_text_file('menu_comprar', texto)
    @staticmethod
    def exibir_servico(texto): return MudarTexto._save_text_file('exibir_servico', texto)
    @staticmethod
    def mensagem_comprou(texto): return MudarTexto._save_text_file('mensagem_comprou', texto)
    @staticmethod
    def giftcard(texto): return MudarTexto._save_text_file('giftcard', texto)
    @staticmethod
    def pix_gerado_inline(texto): return MudarTexto._save_text_file('pix_gerado_inline', texto)
    @staticmethod
    def aprovado_inline(texto): return MudarTexto._save_text_file('aprovado_inline', texto)
    @staticmethod
    def categoriasservicos(texto): return MudarTexto._save_text_file('categoriasservicos', texto)




class Log():
    @staticmethod
    def _read_log_template(filename):
        """Safely reads a log template file."""
        filepath = os.path.join('log', f"{filename}.txt")
        try:
            with open_utf8(filepath, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[WARN] Log template not found: {filepath}")
            return f"<LOG TEMPLATE {filename.upper()} MISSING>"
        except Exception as e:
            print(f"[ERROR] Failed to read log template {filepath}: {e}")
            return f"<ERROR READING LOG {filename.upper()}>"

    @staticmethod
    def _get_user_info(message):
        """Extracts user info safely from message object."""
        user_info = {'id': 'N/A', 'name': 'N/A', 'username': 'N/A', 'link': '#'}
        try:
            if str(message.chat.id).startswith('-'): # Group
                 user = message.from_user
            else: # Private chat
                 user = message.chat

            user_info['id'] = user.id
            user_info['name'] = user.first_name or f"User_{user.id}"
            user_info['username'] = user.username or f"user_{user.id}"
            user_info['link'] = f'https://t.me/{user.username}' if user.username else f'tg://user?id={user.id}'
        except AttributeError:
             print("[WARN] _get_user_info: Message object missing expected attributes.")
        except Exception as e:
             print(f"[ERROR] _get_user_info: Unexpected error: {e}")
        return user_info

    @staticmethod
    def id_log_destino():
        try:
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            # Use .get with default and ensure it's an int
            return int(data.get("destino_log", CredentialsChange.id_dono())) # Default to owner ID
        except (ValueError, TypeError) as e:
             print(f"[ERROR] id_log_destino: Invalid ID format in credenciais.json. Error: {e}")
             return CredentialsChange.id_dono() # Fallback to owner ID
        except Exception as e:
            print(f"[ERROR] id_log_destino: Error reading log destination: {e}")
            return CredentialsChange.id_dono() # Fallback to owner ID

    @staticmethod
    def mudar_destino_logs(id):
        try:
            log_dest_id = int(id) # Validate ID
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            data["destino_log"] = log_dest_id
            with open_utf8('settings/credenciais.json', 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except (ValueError, TypeError) as e:
            print(f"[ERROR] mudar_destino_logs: Invalid ID provided '{id}'. Error: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] mudar_destino_logs: Error saving log destination: {e}")
            return False

    @classmethod
    def log_registro(cls, message):
        txt = cls._read_log_template('registro')
        if message is None: return txt

        user_info = cls._get_user_info(message)
        # Safely format using .format_map
        return txt.format_map(user_info).replace('\\n', '\n')

    @classmethod
    def log_compra(cls, message, servico, email, senha, valor, descricao):
        txt = cls._read_log_template('compra')
        if message is None: return txt

        user_info = cls._get_user_info(message)
        user_id = user_info['id'] # Get ID for saldo lookup

        data = ViewTime.data_atual()
        hora = ViewTime.hora_atual() # Assumes ViewTime.hora_atual returns string
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'
        descricao = descricao or "-"

        # Combine all data and format
        log_data = {
            **user_info, # Includes id, name, username, link
            'data': data,
            'hora': hora,
            'email': email or "N/A",
            'senha': senha or "N/A",
            'valor': valor_fmt,
            'servico': servico or "N/A",
            'saldo': saldo,
            'descricao': descricao
        }
        return txt.format_map(log_data).replace('\\n', '\n')

    @classmethod
    def log_recarga(cls, message, id_pagamento, valor):
        txt = cls._read_log_template('recarga')
        if message is None: return txt

        user_info = cls._get_user_info(message)
        user_id = user_info['id']

        data = ViewTime.data_atual()
        hora = ViewTime.hora_atual()
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'

        log_data = {
            **user_info,
            'data': data,
            'hora': hora,
            'id_pagamento': id_pagamento or "N/A",
            'valor': valor_fmt,
            'saldo': saldo
        }
        return txt.format_map(log_data).replace('\\n', '\n')

    @classmethod
    def log_compra_inline(cls, user_id, nome, email, senha, valor, descricao):
        """ Inline log version without message object. """
        txt = cls._read_log_template('compra')
        # Fetch minimal user info needed for the log
        # (Could fetch from DB or use defaults)
        user_info = {'id': user_id, 'name': f"User_{user_id}", 'username': f"user_{user_id}", 'link': f'tg://user?id={user_id}'}
        # In a real scenario, you might fetch real name/username if available in your DB

        data = ViewTime.data_atual()
        hora = ViewTime.hora_atual()
        try: saldo = f'{InfoUser.saldo(user_id):.2f}'
        except: saldo = '0.00'
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'
        descricao = descricao or "-"

        log_data = {
            **user_info,
            'data': data, 'hora': hora, 'email': email or "N/A", 'senha': senha or "N/A",
            'valor': valor_fmt, 'servico': nome or "N/A", 'saldo': saldo, 'descricao': descricao
        }
        return txt.format_map(log_data).replace('\\n', '\n')


class MudarLog():
    @staticmethod
    def _save_log_template(filename, txt):
        """Safely saves text to a log template file."""
        filepath = os.path.join('log', f"{filename}.txt")
        try:
            os.makedirs('log', exist_ok=True) # Ensure directory exists
            with open_utf8(filepath, 'w') as f:
                f.write(txt)
            log_info(f"Template de log {filename} atualizado.") # Assumes logger
            return True
        except Exception as e:
            log_error(f"Erro ao salvar template de log {filename}: {e}") # Assumes logger
            return False

    @staticmethod
    def log_registro(txt): return MudarLog._save_log_template('registro', txt)
    @staticmethod
    def log_compra(txt): return MudarLog._save_log_template('compra', txt)
    @staticmethod
    def log_recarga(txt): return MudarLog._save_log_template('recarga', txt)

class TextoInline():
    @staticmethod
    def giftcard(message, codigo, quantidade, valor):
        template = Textos._read_text_file('giftcard') # Reuse safe reader
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'
        quantidade = str(quantidade) if quantidade is not None else 'N/A'
        codigo = codigo or "N/A"
        # Format using message context (if available) and specific args
        return Textos._format_text(template, message, codigo=codigo, quantidade=quantidade, valor=valor_fmt)

    @staticmethod
    def pix_gerado_inline(valor, pix_copia_cola, id_pagamento):
        template = Textos._read_text_file('pix_gerado_inline')
        try: expiracao = str(CredentialsChange.InfoPix.expiracao())
        except: expiracao = 'N/A'
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'
        pix_copia_cola = pix_copia_cola or "N/A"
        id_pagamento = id_pagamento or "N/A"
        # Format without message context, only specific args
        return Textos._format_text(template, None,
                                   valor=valor_fmt,
                                   id_pagamento=id_pagamento,
                                   pix_copia_cola=pix_copia_cola,
                                   expiracao=expiracao)

    @staticmethod
    def pagamento_aprovado(message, valor, id_pagamento):
        template = Textos._read_text_file('aprovado_inline') # Filename mismatch? Assuming aprovado_inline.txt
        try: valor_fmt = f'{float(valor):.2f}'
        except: valor_fmt = 'N/A'
        id_pagamento = id_pagamento or "N/A"
        # Format with message context and specific args
        return Textos._format_text(template, message, valor=valor_fmt, id_pagamento=id_pagamento)

class MudarTextoInline():
    # Reuse MudarTexto's safe saver
    @staticmethod
    def mudar_giftcar(txt): return MudarTexto._save_text_file('giftcard', txt)
    @staticmethod
    def mudar_pix_gerado(txt): return MudarTexto._save_text_file('pix_gerado_inline', txt)
    @staticmethod
    def mudar_pagamento_aprovado(txt): return MudarTexto._save_text_file('aprovado_inline', txt) # Filename mismatch?


_promissepay_session = None
_promissepay_session_lock = None


def _get_promissepay_session():
    """Obtém ou cria uma sessão HTTP reutilizável para o PromissePay."""
    global _promissepay_session, _promissepay_session_lock
    import threading
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    if _promissepay_session_lock is None:
        _promissepay_session_lock = threading.Lock()

    with _promissepay_session_lock:
        if _promissepay_session is None:
            _promissepay_session = requests.Session()
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],  # 429 é tratado manualmente (rate limit da PromissePay)
                allowed_methods=["POST", "GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            _promissepay_session.mount("http://", adapter)
            _promissepay_session.mount("https://", adapter)

    return _promissepay_session


class CriarPixPromissePay():
    """Cria cobranças PIX via PromissePay (POST /transactions)."""
    BASE_URL = "https://api.promisse.com.br"

    @staticmethod
    def gerar(valor, id_or_context):
        """Gera uma cobrança PIX na PromissePay e retorna id, copia-e-cola e QR Code."""
        import requests

        try:
            token = CredentialsChange.InfoPix.token_promissepay()

            user_id = id_or_context if isinstance(id_or_context, (int, str)) else getattr(id_or_context, 'chat', {}).get('id', 'UnknownUser')

            from app.config_pagamentos import calcular_taxa_pix
            taxa_fixa = calcular_taxa_pix(valor)
            valor_com_taxa = float(valor) + taxa_fixa
            # PromissePay trabalha em centavos (inteiro), com mínimo de 50 centavos
            amount_centavos = int(round(valor_com_taxa * 100))

            payload = {"amount": amount_centavos}

            headers = {
                "Authorization": token,
                "Content-Type": "application/json",
            }

            session = _get_promissepay_session()
            print(f"[DEBUG] CriarPixPromissePay.gerar: Criando cobrança de {amount_centavos} centavos (User: {user_id})")

            response = session.post(
                f"{CriarPixPromissePay.BASE_URL}/transactions",
                headers=headers,
                json=payload,
                timeout=(5, 20)
            )

            try:
                data = response.json()
            except ValueError:
                raise ConnectionError(f"Resposta inválida da PromissePay (não é JSON): {response.text[:200]}")

            if response.status_code == 429:
                raise ConnectionError("PromissePay: limite de 45 cobranças por minuto excedido (429).")

            if response.status_code not in (200, 201) or "id" not in data:
                erro = data.get("message", "Erro desconhecido")
                raise ConnectionError(f"PromissePay API error: {erro} (Status: {response.status_code})")

            qr_base64 = data.get("qrCodeBase64", "")
            if "base64," in qr_base64:
                qr_base64 = qr_base64.split("base64,")[1]

            print(f"[DEBUG] CriarPixPromissePay.gerar: Cobrança criada (ID: {data['id']})")

            return {
                "id": str(data["id"]),
                "qr_code": data.get("copyPaste", ""),
                "qr_code_base64": qr_base64,
            }

        except ValueError as e:
            print(f"[ERROR] CriarPixPromissePay.gerar: Valor ou configuração inválidos. Valor='{valor}'. Erro: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] CriarPixPromissePay.gerar: Falha de rede ao falar com a PromissePay. Erro: {e}")
            raise ConnectionError(f"Failed to communicate with PromissePay: {e}")
        except Exception as e:
            print(f"[ERROR] CriarPixPromissePay.gerar: Falha ao criar cobrança PIX. Erro: {e}")
            raise ConnectionError(f"Failed to communicate with PromissePay: {e}")

    @staticmethod
    def consultar(transaction_id):
        """Consulta uma cobrança pelo ID (GET /transactions/:id). Retorna o status em maiúsculas (ex.: 'PAID')."""
        import requests

        token = CredentialsChange.InfoPix.token_promissepay()
        headers = {"Authorization": token}
        session = _get_promissepay_session()

        response = session.get(
            f"{CriarPixPromissePay.BASE_URL}/transactions/{transaction_id}",
            headers=headers,
            timeout=(5, 20)
        )
        data = response.json()
        if response.status_code != 200:
            raise ConnectionError(f"PromissePay API error ao consultar {transaction_id}: {data.get('message', 'Erro desconhecido')} (Status: {response.status_code})")
        return data

# Alias for backward compatibility
def novo_usuario(id):
    return InfoUser.novo_usuario(id)

# ===== INTEGRAÇÃO MISTICPAY =====
class InfoMisticPay():
    """Gerencia credenciais do MisticPay (Client ID e Client Secret)"""
    import json
    
    def credenciais():
        try:
            with open_utf8('settings/credenciais.json', 'r') as f:
                data = json.load(f)
            
            mistic = data.get("gateway_pagamento", {}).get("misticpay", {})
            client_id = mistic.get("client_id", "")
            client_secret = mistic.get("client_secret", "")
            
            if not client_id or not client_secret:
                raise ValueError("Credenciais do MisticPay não configuradas")
                
            return {"ci": client_id.strip(), "cs": client_secret.strip()}
        except Exception as e:
            raise RuntimeError(f"Erro ao obter credenciais do MisticPay: {e}")
    
    def mudar_credenciais(client_id, client_secret):
        with open_utf8('settings/credenciais.json', 'r') as f:
            data = json.load(f)
            
        if 'gateway_pagamento' not in data:
            data['gateway_pagamento'] = {}
        if 'misticpay' not in data['gateway_pagamento']:
            data['gateway_pagamento']['misticpay'] = {}
            
        data['gateway_pagamento']['misticpay']['client_id'] = str(client_id)
        data['gateway_pagamento']['misticpay']['client_secret'] = str(client_secret)
        
        with open_utf8('settings/credenciais.json', 'w') as f:
            json.dump(data, f, indent=4)
        return


# ===== POOL DE SESSÕES HTTP PARA MISTICPAY =====
_misticpay_session = None
_misticpay_session_lock = None

def _get_misticpay_session():
    """Obtém ou cria uma sessão HTTP reutilizável para MisticPay"""
    global _misticpay_session, _misticpay_session_lock
    import threading
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    if _misticpay_session_lock is None:
        _misticpay_session_lock = threading.Lock()
    
    with _misticpay_session_lock:
        if _misticpay_session is None:
            _misticpay_session = requests.Session()
            
            # Configurar retry strategy
            retry_strategy = Retry(
                total=3,  # Total de tentativas
                backoff_factor=0.5,  # Aguarda 0.5s, 1s, 2s entre tentativas
                status_forcelist=[429, 500, 502, 503, 504],  # Retry em erros de servidor
                allowed_methods=["POST", "GET"]  # Métodos que podem ser retentados
            )
            
            # Montar adaptador HTTP com retry
            adapter = HTTPAdapter(max_retries=retry_strategy)
            _misticpay_session.mount("http://", adapter)
            _misticpay_session.mount("https://", adapter)
            
            # Configurar timeouts e pool de conexões
            _misticpay_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
    
    return _misticpay_session


class CriarPixMisticPay():
    """Cria transações PIX via MisticPay com retry automático e gerenciamento de conexão"""
    @staticmethod
    def gerar(valor, user_id, nome="Cliente", cpf="00000000000"):
        import requests
        import uuid
        import time
        from requests.exceptions import ConnectionError, Timeout, RequestException
        from urllib3.exceptions import MaxRetryError, ProtocolError
        
        MAX_RETRIES = 3
        RETRY_DELAY = 1  # segundos
        
        try:
            creds = CredentialsChange.InfoMisticPay.credenciais()
            
            import base64
            auth_str = base64.b64encode(f"{creds['ci']}:{creds['cs']}".encode()).decode()
            
            url = "https://api.misticpay.com/api/transactions/create"
            
            headers = {
                "Authorization": f"Basic {auth_str}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            from app.config_pagamentos import calcular_taxa_pix
            taxa_fixa = calcular_taxa_pix(valor)
            valor_com_taxa = float(valor) + taxa_fixa
            desc_taxa = f" (Taxa R$ {taxa_fixa:.2f})" if taxa_fixa > 0 else ""

            # Obter sessão com retry automático
            session = _get_misticpay_session()
            
            # Tentativas manuais com backoff exponencial
            last_error = None
            for attempt in range(MAX_RETRIES):
                # Gera um ID de transação NOVO a cada tentativa. Importante: se uma
                # tentativa anterior deu timeout de LEITURA, a transação pode já ter
                # sido criada do lado do MisticPay mesmo sem termos recebido a
                # resposta — reusar o mesmo transactionId nesse caso faz a tentativa
                # seguinte falhar com "transactionId duplicado" e mascarar o erro real.
                tx_id = f"bot_{user_id}_{uuid.uuid4().hex[:8]}"
                payload = {
                    "amount": valor_com_taxa,
                    "payerName": nome,
                    "payerDocument": cpf,
                    "transactionId": tx_id,
                    "description": f"Recarga Bot - User {user_id}{desc_taxa}"
                }
                try:
                    print(f"[MisticPay] Tentativa {attempt + 1}/{MAX_RETRIES} para gerar PIX (User: {user_id}, Valor: R${valor:.2f})")
                    
                    # Timeout aumentado para 20s (conexão + leitura)
                    response = session.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=(5, 20)  # (connection_timeout, read_timeout)
                    )
                    
                    # Verificar se a resposta é válida
                    try:
                        data = response.json()
                    except ValueError as e:
                        raise Exception(f"Resposta inválida do MisticPay (não é JSON): {response.text[:200]}")
                    
                    if response.status_code in [200, 201] and "data" in data:
                        qr_base64 = data["data"].get("qrCodeBase64", "")
                        copy_paste = data["data"].get("copyPaste", "")
                        transaction_id = data["data"].get("transactionId", tx_id)
                        
                        # Remove o prefixo "data:image/png;base64," se existir
                        if "base64," in qr_base64:
                            qr_base64 = qr_base64.split("base64,")[1]
                        
                        print(f"[MisticPay] ✅ PIX gerado com sucesso (ID: {transaction_id})")
                        
                        return {
                            "id": str(transaction_id),
                            "qr_code": copy_paste,
                            "qr_code_base64": qr_base64
                        }
                    elif response.status_code in [429, 500, 502, 503, 504]:
                        # Erros que justificam retry
                        raise ConnectionError(f"Servidor MisticPay retornou {response.status_code}: {data.get('message', 'Erro desconhecido')}")
                    else:
                        raise Exception(f"Erro MisticPay ({response.status_code}): {data.get('message', 'Erro desconhecido')}")
                        
                except (ConnectionError, Timeout, ConnectionResetError, MaxRetryError, ProtocolError) as e:
                    last_error = e
                    error_type = type(e).__name__
                    error_msg = str(e)[:100]
                    print(f"[MisticPay] ⚠️ Erro de conexão (tentativa {attempt + 1}/{MAX_RETRIES}): {error_type}: {error_msg}")
                    
                    # Se for MaxRetryError, extrair a causa raiz
                    if isinstance(e, MaxRetryError) and e.reason:
                        print(f"[MisticPay]    Causa: {type(e.reason).__name__}: {str(e.reason)[:100]}")
                    
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (2 ** attempt)  # Backoff exponencial
                        print(f"[MisticPay] Aguardando {wait_time}s antes de tentar novamente...")
                        time.sleep(wait_time)
                    else:
                        raise Exception(f"Falha ao gerar PIX após {MAX_RETRIES} tentativas: {str(last_error)}")
                        
                except RequestException as e:
                    # Outros erros de request (não devem ser retentados)
                    raise Exception(f"Erro na requisição MisticPay: {str(e)[:200]}")
                    
        except Exception as e:
            error_msg = f"[ERROR] CriarPixMisticPay.gerar: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)


# ===== POOL DE SESSÕES HTTP PARA MERCADO PAGO =====
_mercadopago_session = None
_mercadopago_session_lock = None


def _get_mercadopago_session():
    """Obtém ou cria uma sessão HTTP reutilizável para o Mercado Pago"""
    global _mercadopago_session, _mercadopago_session_lock
    import threading
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    if _mercadopago_session_lock is None:
        _mercadopago_session_lock = threading.Lock()

    with _mercadopago_session_lock:
        if _mercadopago_session is None:
            _mercadopago_session = requests.Session()

            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],  # 429 é tratado manualmente (rate limit do Mercado Pago)
                allowed_methods=["POST", "GET"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            _mercadopago_session.mount("http://", adapter)
            _mercadopago_session.mount("https://", adapter)

    return _mercadopago_session


class CriarPixMercadoPago():
    """Cria cobranças PIX via Mercado Pago (POST /v1/payments)."""
    BASE_URL = "https://api.mercadopago.com/v1"

    @staticmethod
    def gerar(valor, id_or_context):
        """Gera uma cobrança PIX no Mercado Pago e retorna id, copia-e-cola e QR Code."""
        import requests
        import uuid

        try:
            token = CredentialsChange.InfoPix.token_mercadopago()

            user_id = id_or_context if isinstance(id_or_context, (int, str)) else getattr(id_or_context, 'chat', {}).get('id', 'UnknownUser')

            from app.config_pagamentos import calcular_taxa_pix
            taxa_fixa = calcular_taxa_pix(valor)
            valor_com_taxa = round(float(valor) + taxa_fixa, 2)
            # Valor mínimo de cobrança do Mercado Pago é R$ 0,50
            if valor_com_taxa < 0.50:
                valor_com_taxa = 0.50

            payload = {
                "transaction_amount": valor_com_taxa,
                "description": f"Recarga Bot - User {user_id}",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"user{user_id}@lulostore.com",
                    "first_name": "Cliente",
                    "last_name": str(user_id),
                },
            }

            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                # Chave de idempotência: evita cobrança duplicada em caso de retry
                "X-Idempotency-Key": f"bot_{user_id}_{uuid.uuid4().hex[:12]}",
            }

            session = _get_mercadopago_session()
            print(f"[DEBUG] CriarPixMercadoPago.gerar: Criando cobrança de R$ {valor_com_taxa:.2f} (User: {user_id})")

            response = session.post(
                f"{CriarPixMercadoPago.BASE_URL}/payments",
                headers=headers,
                json=payload,
                timeout=(5, 20)
            )

            try:
                data = response.json()
            except ValueError:
                raise ConnectionError(f"Resposta inválida do Mercado Pago (não é JSON): {response.text[:200]}")

            if response.status_code == 429:
                raise ConnectionError("Mercado Pago: muitas requisições em um curto espaço de tempo (429).")

            if response.status_code not in (200, 201) or "id" not in data:
                erro = data.get("message", data.get("cause", "Erro desconhecido"))
                raise ConnectionError(f"Mercado Pago API error: {erro} (Status: {response.status_code})")

            poi = data.get("point_of_interaction", {}) or {}
            transaction_data = poi.get("transaction_data", {}) or {}
            qr_base64 = transaction_data.get("qr_code_base64", "")
            if "base64," in qr_base64:
                qr_base64 = qr_base64.split("base64,")[1]

            print(f"[DEBUG] CriarPixMercadoPago.gerar: Cobrança criada (ID: {data['id']})")

            return {
                "id": str(data["id"]),
                "qr_code": transaction_data.get("qr_code", ""),
                "qr_code_base64": qr_base64,
            }

        except ValueError as e:
            print(f"[ERROR] CriarPixMercadoPago.gerar: Valor ou configuração inválidos. Valor='{valor}'. Erro: {e}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] CriarPixMercadoPago.gerar: Falha de rede ao falar com o Mercado Pago. Erro: {e}")
            raise ConnectionError(f"Failed to communicate with MercadoPago: {e}")
        except Exception as e:
            print(f"[ERROR] CriarPixMercadoPago.gerar: Falha ao criar cobrança PIX. Erro: {e}")
            raise ConnectionError(f"Failed to communicate with MercadoPago: {e}")

    @staticmethod
    def consultar(transaction_id):
        """Consulta uma cobrança pelo ID (GET /v1/payments/:id). Retorna o status em maiúsculas
        normalizado ao padrão usado pelo restante do bot (ex.: 'PAID')."""
        import requests

        token = CredentialsChange.InfoPix.token_mercadopago()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        session = _get_mercadopago_session()

        response = session.get(
            f"{CriarPixMercadoPago.BASE_URL}/payments/{transaction_id}",
            headers=headers,
            timeout=(5, 20)
        )
        data = response.json()
        if response.status_code != 200:
            raise ConnectionError(f"Mercado Pago API error ao consultar {transaction_id}: {data.get('message', 'Erro desconhecido')} (Status: {response.status_code})")

        # Normaliza o status do Mercado Pago para o vocabulário usado pelo restante do bot
        status_mp = str(data.get("status", "")).lower()
        mapa_status = {
            "approved": "PAID",
            "rejected": "FAILED",
            "cancelled": "CANCELLED",
            "refunded": "CANCELLED",
            "charged_back": "CANCELLED",
        }
        data["status"] = mapa_status.get(status_mp, status_mp.upper())
        return data


