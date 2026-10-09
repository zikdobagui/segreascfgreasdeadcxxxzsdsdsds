import json
import os
from datetime import datetime, timedelta
import pytz
import time
import threading
from app.database import get_all_user_ids

OFERTA_FILE = 'database/oferta_relampago.json'

# =======================================================================
# BANCO DE DADOS (agora suporta VÁRIAS ofertas ativas ao mesmo tempo)
# =======================================================================
def init_db():
    if not os.path.exists('database'):
        os.makedirs('database')
    if not os.path.exists(OFERTA_FILE):
        with open(OFERTA_FILE, 'w', encoding='utf-8') as f:
            json.dump({"ofertas": []}, f, indent=4)

def load_db():
    init_db()
    with open(OFERTA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Migração automática do formato antigo (uma oferta só) pro novo (lista)
    if "ofertas" not in data:
        migrada = {"ofertas": []}
        if data.get("ativa") and data.get("servico"):
            migrada["ofertas"].append({
                "servico": data.get("servico"),
                "preco_original": data.get("preco_original", 0),
                "preco_promocional": data.get("preco_promocional", 0),
                "fim_promocao": data.get("fim_promocao"),
                "limite_quantidade": data.get("limite_quantidade", 0),
            })
        data = migrada
        save_db(data)

    return data

def save_db(data):
    with open(OFERTA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_tz():
    return pytz.timezone('America/Sao_Paulo')

def limpar_texto_para_comparacao(txt):
    """Remove emojis e caracteres especiais para garantir que a comparação de nomes funcione."""
    return ''.join(c for c in str(txt) if c.isalnum()).lower()

def configurar_ofertas(lista_servicos, duracao_minutos=15, limite_quantidade=0):
    """
    Cria/atualiza uma oferta relâmpago para vários serviços de uma vez.
    lista_servicos: lista de dicts {"servico", "preco_original", "preco_promocional"}
    """
    db = load_db()
    agora = datetime.now(get_tz())
    fim = agora + timedelta(minutes=duracao_minutos)

    # Remove ofertas antigas dos mesmos serviços (pra evitar duplicidade)
    novos_nomes = {limpar_texto_para_comparacao(s['servico']) for s in lista_servicos}
    db["ofertas"] = [
        o for o in db["ofertas"]
        if limpar_texto_para_comparacao(o["servico"]) not in novos_nomes
    ]

    for s in lista_servicos:
        db["ofertas"].append({
            "servico": s['servico'],
            "preco_original": float(s['preco_original']),
            "preco_promocional": float(s['preco_promocional']),
            "fim_promocao": fim.isoformat(),
            "limite_quantidade": int(limite_quantidade),
        })

    save_db(db)
    return fim

def desativar_oferta(servico=None):
    """Se 'servico' for None, desativa TODAS as ofertas. Senão, desativa só a daquele serviço."""
    db = load_db()
    if servico is None:
        db["ofertas"] = []
    else:
        alvo = limpar_texto_para_comparacao(servico)
        db["ofertas"] = [
            o for o in db["ofertas"]
            if limpar_texto_para_comparacao(o["servico"]) != alvo
        ]
    save_db(db)

def _limpar_expiradas(db):
    """Remove do db as ofertas que já passaram do prazo. Retorna (db, expiradas)."""
    agora = datetime.now(get_tz())
    ativas, expiradas = [], []
    for o in db["ofertas"]:
        fim = datetime.fromisoformat(o["fim_promocao"])
        if agora > fim:
            expiradas.append(o)
        else:
            ativas.append(o)
    if expiradas:
        db["ofertas"] = ativas
        save_db(db)
    return db, expiradas

def verificar_ofertas_ativas():
    """Retorna a lista de ofertas atualmente ativas (já limpando as expiradas)."""
    db = load_db()
    db, _ = _limpar_expiradas(db)
    return db["ofertas"]

def verificar_oferta_ativa():
    """Mantido por compatibilidade: retorna (True/False, primeira_oferta_ativa)."""
    ofertas = verificar_ofertas_ativas()
    if ofertas:
        return True, ofertas[0]
    return False, None

def _achar_oferta(servico):
    alvo = limpar_texto_para_comparacao(servico)
    for o in verificar_ofertas_ativas():
        if limpar_texto_para_comparacao(o["servico"]) == alvo:
            return o
    return None

def verificar_preco(servico, preco_atual):
    oferta = _achar_oferta(servico)
    if oferta:
        return float(oferta["preco_promocional"])
    return float(preco_atual)

def obter_texto_contador(servico_solicitado):
    oferta = _achar_oferta(servico_solicitado)
    if not oferta:
        return ""

    fim = datetime.fromisoformat(oferta["fim_promocao"])
    agora = datetime.now(get_tz())
    restante = fim - agora
    minutos, segundos = divmod(restante.seconds, 60)
    horas, minutos = divmod(minutos, 60)

    if horas > 0:
        tempo_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    else:
        tempo_str = f"{minutos:02d}:{segundos:02d}"

    return f"⚡ <b>OFERTA RELÂMPAGO!</b> ⚡\n⏱️ Expira em: {tempo_str}\nDe R$ {oferta['preco_original']:.2f} por <b>R$ {oferta['preco_promocional']:.2f}</b>!\n\n"

# =======================================================================
# SISTEMA DE MONITORAMENTO E AVISO DO TÉRMINO DA OFERTA
# =======================================================================
def notificar_fim_oferta_broadcast(bot, servicos):
    """Envia a notificação de que a(s) oferta(s) acabou(aram) para o ADM e para todos os usuários."""
    if isinstance(servicos, str):
        servicos = [servicos]

    try:
        from app import central as api
        dono_id = api.CredentialsChange.id_dono()
    except Exception:
        dono_id = "7619679574"

    lista_servicos_txt = ", ".join(f"<b>{s}</b>" for s in servicos)

    try:
        bot.send_message(
            dono_id,
            f"⚠️ <b>AVISO DE SISTEMA:</b>\n\nA Oferta Relâmpago do(s) serviço(s) {lista_servicos_txt} chegou ao fim pelo tempo limite!",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Erro ao notificar ADM do fim da oferta: {e}")

    if len(servicos) == 1:
        corpo = f"A Oferta Relâmpago para <b>{servicos[0]}</b> foi encerrada."
    else:
        corpo = "As Ofertas Relâmpago para " + lista_servicos_txt + " foram encerradas."

    msg_todos = (
        f"⏳ <b>A OFERTA ACABOU!</b> ⏳\n\n"
        f"{corpo}\n\n"
        f"Fique de olho no bot para não perder as próximas promoções! 👀"
    )

    for user_id in get_all_user_ids():
        try:
            bot.send_message(chat_id=user_id, text=msg_todos, parse_mode="HTML")
            time.sleep(0.05)
        except Exception:
            pass

def monitor_ofertas_em_segundo_plano(bot):
    """Thread que roda a cada 60 segundos checando se alguma oferta expirou."""
    while True:
        time.sleep(60)
        db = load_db()
        db, expiradas = _limpar_expiradas(db)

        if expiradas:
            servicos_expirados = [o["servico"] for o in expiradas]
            notificar_fim_oferta_broadcast(bot, servicos_expirados)

# Variável de controle para garantir que o monitor inicie apenas uma vez
_monitor_iniciado = False

# Memória temporária para guardar os dados enquanto o admin configura a oferta
temp_oferta = {}

def setup_admin_handlers(bot, api):
    global _monitor_iniciado
    if not _monitor_iniciado:
        threading.Thread(target=monitor_ofertas_em_segundo_plano, args=(bot,), daemon=True).start()
        _monitor_iniciado = True

    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

    def texto_tempo(duracao_minutos):
        if duracao_minutos == 30:
            return "meia hora"
        elif duracao_minutos == 60:
            return "1 hora"
        elif duracao_minutos == 120:
            return "2 horas"
        elif duracao_minutos >= 1440:
            dias = duracao_minutos // 1440
            return f"{dias} dia(s)"
        return f"{duracao_minutos} minutos"

    def enviar_broadcast(lista_servicos, duracao_minutos):
        """lista_servicos: lista de dicts {"servico", "preco_atual", "preco_promocional"}"""
        tempo_texto = texto_tempo(duracao_minutos)

        if len(lista_servicos) == 1:
            s = lista_servicos[0]
            msg_todos = (
                f"⚡ <b>OFERTA RELÂMPAGO INICIADA!</b> ⚡\n\n"
                f"O serviço <b>{s['servico']}</b> está de R$ {s['preco_atual']:.2f} por apenas "
                f"<b>R$ {s['preco_promocional']:.2f}</b>!\n\nCorra, a oferta dura apenas {tempo_texto}!"
            )
        else:
            linhas = "\n".join(
                f"• <b>{s['servico']}</b>: R$ {s['preco_atual']:.2f} ➡️ <b>R$ {s['preco_promocional']:.2f}</b>"
                for s in lista_servicos
            )
            msg_todos = (
                f"⚡ <b>OFERTA RELÂMPAGO INICIADA!</b> ⚡\n\n"
                f"{linhas}\n\nCorra, a oferta dura apenas {tempo_texto}!"
            )

        markup_oferta = InlineKeyboardMarkup()
        for s in lista_servicos:
            markup_oferta.add(InlineKeyboardButton(f"🛒 Comprar {s['servico']}", callback_data=f"exibir_servico {s['servico']}"))

        for user_id in get_all_user_ids():
            try:
                bot.send_message(chat_id=user_id, text=msg_todos, parse_mode="HTML", reply_markup=markup_oferta)
                time.sleep(0.05)
            except Exception:
                pass

    def montar_texto_painel():
        ofertas = verificar_ofertas_ativas()
        texto = "⚡ <b>Painel Oferta Relâmpago</b>\n\n"

        if ofertas:
            agora = datetime.now(get_tz())
            texto += f"Status: 🟢 {len(ofertas)} ATIVA(S)\n\n"
            for o in ofertas:
                fim = datetime.fromisoformat(o["fim_promocao"])
                restante = fim - agora
                minutos, segundos = divmod(restante.seconds, 60)
                horas, minutos = divmod(minutos, 60)
                dias = restante.days
                if dias > 0:
                    tempo_str = f"{dias}d {horas:02d}:{minutos:02d}:{segundos:02d}"
                elif horas > 0:
                    tempo_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
                else:
                    tempo_str = f"{minutos:02d}:{segundos:02d}"

                texto += (
                    f"🔹 <b>{o['servico']}</b>\n"
                    f"   R$ {o['preco_original']:.2f} ➡️ R$ {o['preco_promocional']:.2f}\n"
                    f"   ⏱️ Restante: {tempo_str}\n\n"
                )
        else:
            texto += "Status: 🔴 INATIVA"

        return texto, ofertas

    @bot.callback_query_handler(func=lambda call: call.data == 'admin_oferta_relampago')
    def painel_oferta(call):
        texto, ofertas = montar_texto_painel()

        markup = InlineKeyboardMarkup()
        if ofertas:
            for o in ofertas:
                markup.row(InlineKeyboardButton(f"🛑 Desativar {o['servico']}", callback_data=f"oferta_desativar_{o['servico']}"))
            if len(ofertas) > 1:
                markup.row(InlineKeyboardButton("🛑 Desativar TODAS", callback_data="oferta_desativar_todas"))
            markup.row(InlineKeyboardButton("➕ Adicionar mais produtos", callback_data="oferta_iniciar"))
        else:
            markup.row(InlineKeyboardButton("⚡ Iniciar Nova Oferta", callback_data="oferta_iniciar"))

        markup.row(InlineKeyboardButton("↩ Voltar", callback_data="voltar_paineladm"))

        bot.edit_message_text(texto, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == 'oferta_desativar_todas')
    def desativar_todas(call):
        desativar_oferta(None)
        bot.answer_callback_query(call.id, "Todas as ofertas foram desativadas!")
        painel_oferta(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('oferta_desativar_') and call.data != 'oferta_desativar_todas')
    def desativar_uma(call):
        servico = call.data.replace('oferta_desativar_', '')
        desativar_oferta(servico)
        bot.answer_callback_query(call.id, f"Oferta de {servico} desativada!")
        painel_oferta(call)

    # -------------------------------------------------------------
    # FLUXO DE CRIAÇÃO: agora com seleção MÚLTIPLA de produtos
    # -------------------------------------------------------------
    def montar_markup_selecao(chat_id):
        nomes_unicos = temp_oferta[chat_id]['nomes_disponiveis']
        selecionados = temp_oferta[chat_id]['selecionados']

        markup = InlineKeyboardMarkup()
        for idx, nome in enumerate(nomes_unicos):
            marcado = "✅" if idx in selecionados else "⬜"
            markup.add(InlineKeyboardButton(f"{marcado} {nome}", callback_data=f"oferta_toggle_{idx}"))

        qtd = len(selecionados)
        if qtd > 0:
            markup.row(InlineKeyboardButton(f"➡️ Confirmar Seleção ({qtd})", callback_data="oferta_confirmar_selecao"))
        markup.row(InlineKeyboardButton("❌ Cancelar", callback_data="admin_oferta_relampago"))
        return markup

    @bot.callback_query_handler(func=lambda call: call.data == 'oferta_iniciar')
    def iniciar(call):
        servicos = api.ControleLogins.pegar_servicos()
        nomes_unicos = sorted(list(set([s['nome'] for s in servicos])))

        if not nomes_unicos:
            bot.answer_callback_query(call.id, "Sem serviços em estoque!", show_alert=True)
            return

        temp_oferta[call.message.chat.id] = {
            "nomes_disponiveis": nomes_unicos,
            "selecionados": set(),
        }

        bot.edit_message_text(
            "Selecione UM ou VÁRIOS serviços para a oferta (toque para marcar/desmarcar):",
            call.message.chat.id, call.message.message_id,
            reply_markup=montar_markup_selecao(call.message.chat.id)
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('oferta_toggle_'))
    def toggle_selecao(call):
        chat_id = call.message.chat.id
        if chat_id not in temp_oferta:
            bot.answer_callback_query(call.id, "Sessão expirada. Tente novamente.", show_alert=True)
            return

        idx = int(call.data.replace('oferta_toggle_', ''))
        selecionados = temp_oferta[chat_id]['selecionados']
        if idx in selecionados:
            selecionados.discard(idx)
        else:
            selecionados.add(idx)

        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=montar_markup_selecao(chat_id))

    @bot.callback_query_handler(func=lambda call: call.data == 'oferta_confirmar_selecao')
    def confirmar_selecao(call):
        chat_id = call.message.chat.id
        if chat_id not in temp_oferta or not temp_oferta[chat_id]['selecionados']:
            bot.answer_callback_query(call.id, "Nenhum serviço selecionado.", show_alert=True)
            return

        nomes_unicos = temp_oferta[chat_id]['nomes_disponiveis']
        idxs = sorted(temp_oferta[chat_id]['selecionados'])
        nomes_selecionados = [nomes_unicos[i] for i in idxs]

        servicos_api = api.ControleLogins.pegar_servicos()
        precos_atuais = {}
        for s in servicos_api:
            if s['nome'] in nomes_selecionados and s['nome'] not in precos_atuais:
                precos_atuais[s['nome']] = float(s['valor'])

        temp_oferta[chat_id] = {
            "itens": [{"servico": nome, "preco_atual": precos_atuais.get(nome, 0)} for nome in nomes_selecionados]
        }

        if len(nomes_selecionados) == 1:
            item = temp_oferta[chat_id]["itens"][0]
            msg = bot.send_message(
                chat_id,
                f"Serviço: <b>{item['servico']}</b>\nPreço atual: R$ {item['preco_atual']:.2f}\n\nDigite o <b>novo preço promocional</b> (Ex: 10.50):",
                parse_mode="HTML",
                reply_markup=ForceReply()
            )
            bot.register_next_step_handler(msg, processar_preco_unico)
        else:
            lista_txt = "\n".join(f"• {it['servico']}: R$ {it['preco_atual']:.2f}" for it in temp_oferta[chat_id]["itens"])
            msg = bot.send_message(
                chat_id,
                f"Serviços selecionados:\n{lista_txt}\n\n"
                f"Digite o <b>percentual de desconto</b> a aplicar em todos (Ex: 30 para 30% OFF):",
                parse_mode="HTML",
                reply_markup=ForceReply()
            )
            bot.register_next_step_handler(msg, processar_desconto_percentual)

    def processar_preco_unico(message):
        chat_id = message.chat.id
        try:
            preco_promocional = float(message.text.replace(',', '.'))
        except ValueError:
            bot.reply_to(message, "❌ Valor numérico inválido. A oferta foi cancelada.")
            return

        if chat_id not in temp_oferta:
            return
        temp_oferta[chat_id]["itens"][0]["preco_promocional"] = preco_promocional
        pedir_limite(message)

    def processar_desconto_percentual(message):
        chat_id = message.chat.id
        try:
            desconto = float(message.text.replace(',', '.').replace('%', ''))
            if not (0 < desconto < 100):
                raise ValueError
        except ValueError:
            bot.reply_to(message, "❌ Percentual inválido. Use um número entre 1 e 99. Oferta cancelada.")
            return

        if chat_id not in temp_oferta:
            return

        for item in temp_oferta[chat_id]["itens"]:
            preco_promo = round(item["preco_atual"] * (1 - desconto / 100), 2)
            item["preco_promocional"] = preco_promo

        resumo = "\n".join(
            f"• {it['servico']}: R$ {it['preco_atual']:.2f} ➡️ R$ {it['preco_promocional']:.2f}"
            for it in temp_oferta[chat_id]["itens"]
        )
        bot.reply_to(message, f"✅ Desconto de {desconto:.0f}% aplicado:\n{resumo}", parse_mode="HTML")
        pedir_limite(message)

    def pedir_limite(message):
        msg = bot.reply_to(
            message,
            "🔢 <b>Digite o LIMITE MÁXIMO de compras por pessoa (vale para todos os itens selecionados):</b>\n<i>(Envie 0 se quiser que seja ILIMITADO)</i>",
            parse_mode="HTML",
            reply_markup=ForceReply()
        )
        bot.register_next_step_handler(msg, processar_limite_oferta)

    def processar_limite_oferta(message):
        chat_id = message.chat.id
        try:
            limite_quantidade = int(message.text.strip())

            if chat_id not in temp_oferta:
                return

            temp_oferta[chat_id]["limite_quantidade"] = limite_quantidade

            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("15 Min", callback_data="oferta_tempo_15"),
                       InlineKeyboardButton("30 Min", callback_data="oferta_tempo_30"))
            markup.row(InlineKeyboardButton("1 Hora", callback_data="oferta_tempo_60"),
                       InlineKeyboardButton("2 Horas", callback_data="oferta_tempo_120"))
            markup.row(InlineKeyboardButton("1 Dia", callback_data="oferta_tempo_1440"),
                       InlineKeyboardButton("2 Dias", callback_data="oferta_tempo_2880"))
            markup.row(InlineKeyboardButton("7 Dias", callback_data="oferta_tempo_10080"))
            markup.row(InlineKeyboardButton("❌ Cancelar", callback_data="admin_oferta_relampago"))

            bot.reply_to(message, "⏱️ <b>Selecione a duração da oferta:</b>", parse_mode="HTML", reply_markup=markup)
        except ValueError:
            bot.reply_to(message, "❌ Quantidade inválida. Use apenas números. Oferta cancelada.")

    @bot.callback_query_handler(func=lambda call: call.data.startswith('oferta_tempo_'))
    def definir_tempo_e_iniciar(call):
        duracao_minutos = int(call.data.split('_')[2])
        chat_id = call.message.chat.id

        if chat_id not in temp_oferta or "itens" not in temp_oferta[chat_id]:
            bot.answer_callback_query(call.id, "Sessão expirada. Tente novamente.", show_alert=True)
            return

        dados = temp_oferta[chat_id]
        itens = dados['itens']
        limite_quantidade = dados.get('limite_quantidade', 0)

        lista_para_salvar = [
            {"servico": it['servico'], "preco_original": it['preco_atual'], "preco_promocional": it['preco_promocional']}
            for it in itens
        ]
        fim = configurar_ofertas(lista_para_salvar, duracao_minutos, limite_quantidade)

        del temp_oferta[chat_id]

        resumo = "\n".join(f"• {it['servico']}: R$ {it['preco_promocional']:.2f}" for it in itens)
        bot.edit_message_text(
            f"✅ <b>Oferta iniciada com sucesso!</b>\n\n{resumo}\n\nVálida até: {fim.strftime('%H:%M:%S')}\n\n<i>Disparando aviso para os usuários...</i>",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        # 'itens' já tem exatamente as chaves que enviar_broadcast espera (servico, preco_atual, preco_promocional)
        threading.Thread(target=enviar_broadcast, args=(itens, duracao_minutos)).start()
