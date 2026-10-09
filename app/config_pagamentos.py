"""
=============================================================================
CONFIG_PAGAMENTOS.PY
=============================================================================
Arquivo centralizado para todas as configurações de pagamento do bot.
Mantém separado do bot.py para melhor organização e manutenção.

Gateways suportados:
- PromissePay
- MisticPay
- MercadoPago
=============================================================================
"""

import json
import os
from typing import Dict, Optional, Tuple

# ===== CONSTANTES DE CONFIGURAÇÃO =====

# IDs e URLs
ADMIN_ID_DEFAULT = None  # Será carregado do settings/credenciais.json
CANAL_ID = -1002787400901  # Canal para notificações de PIX gerado

# Timeouts
TIMEOUT_PIX_VERIFICACAO = 15 * 60  # 15 minutos em segundos
TIMEOUT_CONEXAO_API = 5  # segundos
TIMEOUT_LEITURA_API = 20  # segundos

# Retry
MAX_RETRIES_MISTICPAY = 3
RETRY_DELAY_MISTICPAY = 1  # segundos

# Limites padrão
DEPOSITO_MINIMO_PADRAO = 5.0  # R$
DEPOSITO_MAXIMO_PADRAO = 10000.0  # R$

# Arquivos de configuração
ARQUIVO_CREDENCIAIS = 'settings/credenciais.json'
ARQUIVO_PAGAMENTOS_PENDENTES = 'settings/pagamentos_pendentes.json'

# ===== FUNÇÕES DE CARREGAMENTO DE CONFIGURAÇÃO =====


def carregar_credenciais() -> Dict:
    """Carrega as credenciais do arquivo settings/credenciais.json"""
    try:
        with open(ARQUIVO_CREDENCIAIS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG] Erro ao carregar credenciais: {e}")
        return {}


def salvar_credenciais(cred: Dict) -> bool:
    """Salva as credenciais no arquivo settings/credenciais.json"""
    try:
        os.makedirs(os.path.dirname(ARQUIVO_CREDENCIAIS), exist_ok=True)
        with open(ARQUIVO_CREDENCIAIS, 'w', encoding='utf-8') as f:
            json.dump(cred, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"[CONFIG] Erro ao salvar credenciais: {e}")
        return False


def obter_gateway_ativo() -> str:
    """Retorna o gateway de pagamento ativo"""
    cred = carregar_credenciais()
    return cred.get('gateway_pagamento', {}).get('selecionada', 'promissepay')


def trocar_gateway(novo_gateway: str) -> bool:
    """Alterna entre gateways de pagamento"""
    if novo_gateway not in ['promissepay', 'misticpay', 'mercadopago']:
        print(f"[CONFIG] Gateway inválido: {novo_gateway}")
        return False
    
    cred = carregar_credenciais()
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay'}
    
    cred['gateway_pagamento']['selecionada'] = novo_gateway
    return salvar_credenciais(cred)


def troca_automatica_ativa() -> bool:
    """Verifica se a troca automática de gateway (failover) está ligada. Padrão: ligada."""
    cred = carregar_credenciais()
    return bool(cred.get('gateway_pagamento', {}).get('troca_automatica_ativa', True))


def alternar_troca_automatica() -> bool:
    """Liga/desliga a troca automática de gateway (failover). Retorna o novo status."""
    cred = carregar_credenciais()
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay'}

    atual = bool(cred['gateway_pagamento'].get('troca_automatica_ativa', True))
    novo_status = not atual
    cred['gateway_pagamento']['troca_automatica_ativa'] = novo_status
    salvar_credenciais(cred)
    return novo_status


# ===== CONFIGURAÇÕES DA TAXA DO INTERMEDIADOR =====

TAXA_VALOR_PADRAO = 0.50   # R$ 0,50
TAXA_LIMITE_ISENCAO = 50.0  # Acima deste valor de PIX, não cobra taxa


def taxa_intermediador_ativa() -> bool:
    """Verifica se a taxa fixa do intermediador está ativa. Padrão: ligada."""
    cred = carregar_credenciais()
    return bool(cred.get('gateway_pagamento', {}).get('taxa_intermediador', {}).get('ativa', True))


def alternar_taxa_intermediador() -> bool:
    """Liga/desliga a taxa fixa do intermediador. Retorna o novo status."""
    cred = carregar_credenciais()
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay'}
    if 'taxa_intermediador' not in cred['gateway_pagamento']:
        cred['gateway_pagamento']['taxa_intermediador'] = {'ativa': True, 'valor': TAXA_VALOR_PADRAO}

    atual = bool(cred['gateway_pagamento']['taxa_intermediador'].get('ativa', True))
    novo_status = not atual
    cred['gateway_pagamento']['taxa_intermediador']['ativa'] = novo_status
    salvar_credenciais(cred)
    return novo_status


def obter_valor_taxa_intermediador() -> float:
    """Obtém o valor fixo da taxa do intermediador (padrão R$ 0,50)."""
    cred = carregar_credenciais()
    return float(cred.get('gateway_pagamento', {}).get('taxa_intermediador', {}).get('valor', TAXA_VALOR_PADRAO))


def salvar_valor_taxa_intermediador(valor: float) -> bool:
    """Salva o novo valor fixo da taxa do intermediador (ex: 0.30, 0.50, 1.00)."""
    cred = carregar_credenciais()
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay'}
    if 'taxa_intermediador' not in cred['gateway_pagamento']:
        cred['gateway_pagamento']['taxa_intermediador'] = {'ativa': True, 'valor': TAXA_VALOR_PADRAO}

    cred['gateway_pagamento']['taxa_intermediador']['valor'] = float(valor)
    return salvar_credenciais(cred)


def obter_limite_isencao_taxa() -> float:
    """Obtém o valor de PIX a partir do qual a taxa do intermediador deixa de ser cobrada (padrão R$ 50,00)."""
    cred = carregar_credenciais()
    return float(cred.get('gateway_pagamento', {}).get('taxa_intermediador', {}).get('limite_isencao', TAXA_LIMITE_ISENCAO))


def salvar_limite_isencao_taxa(valor: float) -> bool:
    """Salva o novo valor de isenção da taxa do intermediador (ex: 30.00, 50.00, 100.00)."""
    cred = carregar_credenciais()
    if 'gateway_pagamento' not in cred:
        cred['gateway_pagamento'] = {'selecionada': 'promissepay'}
    if 'taxa_intermediador' not in cred['gateway_pagamento']:
        cred['gateway_pagamento']['taxa_intermediador'] = {'ativa': True, 'valor': TAXA_VALOR_PADRAO}

    cred['gateway_pagamento']['taxa_intermediador']['limite_isencao'] = float(valor)
    return salvar_credenciais(cred)


def calcular_taxa_pix(valor: float) -> float:
    """
    Calcula a taxa fixa do intermediador aplicada a um PIX de 'valor' reais.
    Regras: só cobra se a taxa estiver ativada E o valor do PIX for menor que
    o limite de isenção configurado (R$ 50 por padrão, mas ajustável pelo
    painel). Ponto único usado por todos os gateways (PromissePay, MisticPay,
    MercadoPago) e pela mensagem exibida ao cliente, para nunca ficar
    dessincronizado.
    """
    if not taxa_intermediador_ativa():
        return 0.0
    if float(valor) >= obter_limite_isencao_taxa():
        return 0.0
    return obter_valor_taxa_intermediador()


# ===== CONFIGURAÇÕES DO PROMISSEPAY =====

class ConfigPromissePay:
    """Configurações do PromissePay"""
    
    @staticmethod
    def obter_token() -> Optional[str]:
        """Obtém o token (API key) do PromissePay"""
        cred = carregar_credenciais()
        token = cred.get('gateway_pagamento', {}).get('promissepay', {}).get('token')
        if not token or not isinstance(token, str) or not token.strip():
            return None
        return token.strip()
    
    @staticmethod
    def salvar_token(token: str) -> bool:
        """Salva o token (API key) do PromissePay"""
        cred = carregar_credenciais()
        if 'gateway_pagamento' not in cred:
            cred['gateway_pagamento'] = {}
        if 'promissepay' not in cred['gateway_pagamento']:
            cred['gateway_pagamento']['promissepay'] = {}
        
        cred['gateway_pagamento']['promissepay']['token'] = str(token)
        return salvar_credenciais(cred)
    
    @staticmethod
    def esta_configurado() -> bool:
        """Verifica se o PromissePay está configurado"""
        return ConfigPromissePay.obter_token() is not None


# ===== CONFIGURAÇÕES DO MISTICPAY =====

class ConfigMisticPay:
    """Configurações do MisticPay"""
    
    @staticmethod
    def obter_credenciais() -> Optional[Dict[str, str]]:
        """Obtém as credenciais do MisticPay (Client ID e Client Secret)"""
        cred = carregar_credenciais()
        mistic = cred.get('gateway_pagamento', {}).get('misticpay', {})
        client_id = mistic.get("client_id", "").strip()
        client_secret = mistic.get("client_secret", "").strip()
        
        if not client_id or not client_secret:
            return None
        
        return {"ci": client_id, "cs": client_secret}
    
    @staticmethod
    def salvar_credenciais(client_id: str, client_secret: str) -> bool:
        """Salva as credenciais do MisticPay"""
        cred = carregar_credenciais()
        if 'gateway_pagamento' not in cred:
            cred['gateway_pagamento'] = {}
        if 'misticpay' not in cred['gateway_pagamento']:
            cred['gateway_pagamento']['misticpay'] = {}
        
        cred['gateway_pagamento']['misticpay']['client_id'] = str(client_id)
        cred['gateway_pagamento']['misticpay']['client_secret'] = str(client_secret)
        return salvar_credenciais(cred)
    
    @staticmethod
    def esta_configurado() -> bool:
        """Verifica se o MisticPay está configurado"""
        return ConfigMisticPay.obter_credenciais() is not None


# ===== CONFIGURAÇÕES DO MERCADO PAGO =====

class ConfigMercadoPago:
    """Configurações do Mercado Pago"""

    @staticmethod
    def obter_token() -> Optional[str]:
        """Obtém o token (Access Token) do Mercado Pago"""
        cred = carregar_credenciais()
        token = cred.get('gateway_pagamento', {}).get('mercadopago', {}).get('token')
        if not token or not isinstance(token, str) or not token.strip():
            return None
        return token.strip()

    @staticmethod
    def salvar_token(token: str) -> bool:
        """Salva o token (Access Token) do Mercado Pago"""
        cred = carregar_credenciais()
        if 'gateway_pagamento' not in cred:
            cred['gateway_pagamento'] = {}
        if 'mercadopago' not in cred['gateway_pagamento']:
            cred['gateway_pagamento']['mercadopago'] = {}

        cred['gateway_pagamento']['mercadopago']['token'] = str(token)
        return salvar_credenciais(cred)

    @staticmethod
    def esta_configurado() -> bool:
        """Verifica se o Mercado Pago está configurado"""
        return ConfigMercadoPago.obter_token() is not None


# ===== CONFIGURAÇÕES DE PIX =====

class ConfigPix:
    """Configurações gerais de PIX"""
    
    @staticmethod
    def obter_deposito_minimo() -> float:
        """Obtém o depósito mínimo para PIX"""
        cred = carregar_credenciais()
        return float(cred.get('min_pix', DEPOSITO_MINIMO_PADRAO))
    
    @staticmethod
    def obter_deposito_maximo() -> float:
        """Obtém o depósito máximo para PIX"""
        cred = carregar_credenciais()
        return float(cred.get('max_pix', DEPOSITO_MAXIMO_PADRAO))
    
    @staticmethod
    def salvar_deposito_minimo(valor: float) -> bool:
        """Salva o depósito mínimo para PIX"""
        cred = carregar_credenciais()
        cred['min_pix'] = float(valor)
        return salvar_credenciais(cred)
    
    @staticmethod
    def salvar_deposito_maximo(valor: float) -> bool:
        """Salva o depósito máximo para PIX"""
        cred = carregar_credenciais()
        cred['max_pix'] = float(valor)
        return salvar_credenciais(cred)
    
    @staticmethod
    def obter_expiracao() -> int:
        """Obtém o tempo de expiração do PIX em minutos"""
        cred = carregar_credenciais()
        return int(cred.get('expiracao_pix', 15))
    
    @staticmethod
    def salvar_expiracao(minutos: int) -> bool:
        """Salva o tempo de expiração do PIX"""
        cred = carregar_credenciais()
        cred['expiracao_pix'] = int(minutos)
        return salvar_credenciais(cred)
    
    @staticmethod
    def pix_manual_ativo() -> bool:
        """Verifica se PIX manual está ativo"""
        cred = carregar_credenciais()
        return str(cred.get('status_pix_manu', 'on')) == 'on'
    
    @staticmethod
    def pix_automatico_ativo() -> bool:
        """Verifica se PIX automático está ativo"""
        cred = carregar_credenciais()
        return str(cred.get('status_pix_auto', 'on')) == 'on'
    
    @staticmethod
    def alternar_pix_manual() -> bool:
        """Alterna o status do PIX manual"""
        cred = carregar_credenciais()
        status_atual = str(cred.get('status_pix_manu', 'on'))
        novo_status = 'off' if status_atual == 'on' else 'on'
        cred['status_pix_manu'] = novo_status
        return salvar_credenciais(cred)
    
    @staticmethod
    def alternar_pix_automatico() -> bool:
        """Alterna o status do PIX automático"""
        cred = carregar_credenciais()
        status_atual = str(cred.get('status_pix_auto', 'on'))
        novo_status = 'off' if status_atual == 'on' else 'on'
        cred['status_pix_auto'] = novo_status
        return salvar_credenciais(cred)


# ===== CONFIGURAÇÕES DE BONUS =====

class ConfigBonus:
    """Configurações de bônus para PIX"""
    
    @staticmethod
    def obter_percentual_bonus() -> int:
        """Obtém o percentual de bônus para PIX"""
        cred = carregar_credenciais()
        return int(cred.get('bonus_pix', 0))
    
    @staticmethod
    def salvar_percentual_bonus(percentual: int) -> bool:
        """Salva o percentual de bônus para PIX"""
        cred = carregar_credenciais()
        cred['bonus_pix'] = int(percentual)
        return salvar_credenciais(cred)
    
    @staticmethod
    def obter_valor_minimo_bonus() -> float:
        """Obtém o valor mínimo para aplicar bônus"""
        cred = carregar_credenciais()
        return float(cred.get('bonus_pix_min', 0))
    
    @staticmethod
    def salvar_valor_minimo_bonus(valor: float) -> bool:
        """Salva o valor mínimo para aplicar bônus"""
        cred = carregar_credenciais()
        cred['bonus_pix_min'] = float(valor)
        return salvar_credenciais(cred)


# ===== UTILITÁRIOS =====

def validar_valor_pix(valor: float) -> Tuple[bool, str]:
    """Valida se o valor está dentro dos limites de PIX"""
    minimo = ConfigPix.obter_deposito_minimo()
    maximo = ConfigPix.obter_deposito_maximo()
    
    if valor < minimo:
        return False, f"Valor mínimo é R$ {minimo:.2f}"
    if valor > maximo:
        return False, f"Valor máximo é R$ {maximo:.2f}"
    
    return True, "OK"


def obter_info_pagamentos() -> Dict:
    """Retorna um dicionário com todas as informações de pagamento"""
    return {
        'gateway_ativo': obter_gateway_ativo(),
        'troca_automatica_ativa': troca_automatica_ativa(),
        'taxa_intermediador_ativa': taxa_intermediador_ativa(),
        'taxa_intermediador_valor': obter_valor_taxa_intermediador(),
        'taxa_intermediador_limite_isencao': obter_limite_isencao_taxa(),
        'promissepay': {
            'configurado': ConfigPromissePay.esta_configurado(),
            'token': ConfigPromissePay.obter_token() or 'Não configurado'
        },
        'misticpay': {
            'configurado': ConfigMisticPay.esta_configurado(),
            'client_id': ConfigMisticPay.obter_credenciais().get('ci') if ConfigMisticPay.obter_credenciais() else 'Não configurado'
        },
        'mercadopago': {
            'configurado': ConfigMercadoPago.esta_configurado(),
            'token': ConfigMercadoPago.obter_token() or 'Não configurado'
        },
        'pix': {
            'manual_ativo': ConfigPix.pix_manual_ativo(),
            'automatico_ativo': ConfigPix.pix_automatico_ativo(),
            'deposito_minimo': ConfigPix.obter_deposito_minimo(),
            'deposito_maximo': ConfigPix.obter_deposito_maximo(),
            'expiracao_minutos': ConfigPix.obter_expiracao(),
            'bonus_percentual': ConfigBonus.obter_percentual_bonus(),
            'bonus_valor_minimo': ConfigBonus.obter_valor_minimo_bonus()
        }
    }


if __name__ == "__main__":
    # Teste das configurações
    print("=== INFORMAÇÕES DE PAGAMENTO ===")
    import pprint
    pprint.pprint(obter_info_pagamentos())
    