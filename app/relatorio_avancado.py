import os
import json
from datetime import datetime, timedelta
import pytz
from app import database


def calcular_top_stats(api=None):
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    hoje = agora.date()
    semana_passada = hoje - timedelta(days=7)
    mes_passado = hoje - timedelta(days=30)

    top_comprador_hoje = {'nome': 'Ninguém', 'valor': 0.0}
    top_comprador_semana = {'nome': 'Ninguém', 'valor': 0.0}
    top_comprador_mes = {'nome': 'Ninguém', 'valor': 0.0}

    top_depositante_hoje = {'nome': 'Ninguém', 'valor': 0.0}
    top_depositante_semana = {'nome': 'Ninguém', 'valor': 0.0}
    top_depositante_mes = {'nome': 'Ninguém', 'valor': 0.0}
    
    # NOVOS PARA GIFTS
    top_gift_hoje = {'nome': 'Ninguém', 'valor': 0.0}
    top_gift_semana = {'nome': 'Ninguém', 'valor': 0.0}
    top_gift_mes = {'nome': 'Ninguém', 'valor': 0.0}
    
    total_gifts_hoje = 0.0
    total_gifts_semana = 0.0
    total_gifts_mes = 0.0
    total_gifts_all = 0.0

    # CORREÇÃO: esta função varria database/users/*.json, pasta que não
    # existe mais após a migração para SQLite (o relatório sempre voltava
    # zerado). Agora usa database.get_all_user_ids()/load_user_data().
    user_ids = database.get_all_user_ids()

    for uid in user_ids:
        try:
            ud = database.load_user_data(uid) or {}
        except Exception:
            continue

        username = ud.get('username', uid)
        nome_display = f"@{username}" if not str(username).isdigit() else f"ID: {username}"

        # --- COMPRAS ---
        compras = ud.get('compras', []) + ud.get('purchases', [])
        gasto_hoje = 0.0
        gasto_semana = 0.0
        gasto_mes = 0.0

        for c in compras:
            data_str = c.get('data_compra', c.get('data', ''))
            valor = float(c.get('valor') or 0)
            try:
                data_limpa = data_str.split(' ')[0].replace('às', '').strip()
                if '-' in data_limpa:
                    dt_obj = datetime.fromisoformat(data_str[:10]).date()
                else:
                    dt_obj = datetime.strptime(data_limpa, "%d/%m/%Y").date()
                
                if dt_obj == hoje: gasto_hoje += valor
                if dt_obj >= semana_passada: gasto_semana += valor
                if dt_obj >= mes_passado: gasto_mes += valor
            except: pass

        if gasto_hoje > top_comprador_hoje['valor']: top_comprador_hoje = {'nome': nome_display, 'valor': gasto_hoje}
        if gasto_semana > top_comprador_semana['valor']: top_comprador_semana = {'nome': nome_display, 'valor': gasto_semana}
        if gasto_mes > top_comprador_mes['valor']: top_comprador_mes = {'nome': nome_display, 'valor': gasto_mes}

        # --- DEPÓSITOS (PIX) ---
        pagamentos = ud.get('pagamentos', [])
        dep_hoje = 0.0
        dep_semana = 0.0
        dep_mes = 0.0

        for p in pagamentos:
            data_str = p.get('data', '')
            valor = float(p.get('valor') or 0)
            try:
                data_limpa = data_str.split(' ')[0].replace('às', '').strip()
                if '-' in data_limpa:
                    dt_obj = datetime.fromisoformat(data_str[:10]).date()
                else:
                    dt_obj = datetime.strptime(data_limpa, "%d/%m/%Y").date()
                
                if dt_obj == hoje: dep_hoje += valor
                if dt_obj >= semana_passada: dep_semana += valor
                if dt_obj >= mes_passado: dep_mes += valor
            except: pass
        
        if dep_hoje > top_depositante_hoje['valor']: top_depositante_hoje = {'nome': nome_display, 'valor': dep_hoje}
        if dep_semana > top_depositante_semana['valor']: top_depositante_semana = {'nome': nome_display, 'valor': dep_semana}
        if dep_mes > top_depositante_mes['valor']: top_depositante_mes = {'nome': nome_display, 'valor': dep_mes}

        # --- GIFTS RESGATADOS (Com datas) ---
        # Procura por listas de histórico de gifts no JSON
        historico_gifts = ud.get('historico_gifts', ud.get('gifts', ud.get('gifts_resgatados_historico', [])))
        user_gift_hoje = 0.0
        user_gift_semana = 0.0
        user_gift_mes = 0.0

        if isinstance(historico_gifts, list):
            for g in historico_gifts:
                if isinstance(g, dict):
                    data_str = g.get('data', g.get('data_resgate', ''))
                    valor = float(g.get('valor') or 0)
                    try:
                        data_limpa = data_str.split(' ')[0].replace('às', '').strip()
                        if '-' in data_limpa:
                            dt_obj = datetime.fromisoformat(data_str[:10]).date()
                        else:
                            dt_obj = datetime.strptime(data_limpa, "%d/%m/%Y").date()
                        
                        if dt_obj == hoje: user_gift_hoje += valor
                        if dt_obj >= semana_passada: user_gift_semana += valor
                        if dt_obj >= mes_passado: user_gift_mes += valor
                    except: pass
        
        total_gifts_hoje += user_gift_hoje
        total_gifts_semana += user_gift_semana
        total_gifts_mes += user_gift_mes

        if user_gift_hoje > top_gift_hoje['valor']: top_gift_hoje = {'nome': nome_display, 'valor': user_gift_hoje}
        if user_gift_semana > top_gift_semana['valor']: top_gift_semana = {'nome': nome_display, 'valor': user_gift_semana}
        if user_gift_mes > top_gift_mes['valor']: top_gift_mes = {'nome': nome_display, 'valor': user_gift_mes}

        # --- GIFTS RESGATADOS TOTAL HISTÓRICO ---
        try:
            if api and hasattr(api, 'InfoUser') and hasattr(api.InfoUser, 'gifts_resgatados'):
                gifts_user = api.InfoUser.gifts_resgatados(uid)
                total_gifts_all += float(gifts_user or 0)
        except:
            pass
        
    return {
        'top_comp_hoje': top_comprador_hoje, 'top_comp_semana': top_comprador_semana, 'top_comp_mes': top_comprador_mes,
        'top_dep_hoje': top_depositante_hoje, 'top_dep_semana': top_depositante_semana, 'top_dep_mes': top_depositante_mes,
        'top_gift_hoje': top_gift_hoje, 'top_gift_semana': top_gift_semana, 'top_gift_mes': top_gift_mes,
        'total_gifts_hoje': total_gifts_hoje, 'total_gifts_semana': total_gifts_semana, 'total_gifts_mes': total_gifts_mes,
        'total_gifts_all': total_gifts_all
    }
