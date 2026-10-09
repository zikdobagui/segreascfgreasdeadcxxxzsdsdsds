"""Rotinas agrupadas de interface."""

# ==================== MENUS ====================
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

import os
import json

def gerar_menu_principal(message):
    """Gera o markup para o MENU ÚNICO principal."""
    usar_categorias = True
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                usar_categorias = cfg.get("menu_categorias", True)
        except Exception:
            pass

    markup = InlineKeyboardMarkup()

    bt_ver_todos = InlineKeyboardButton('🛍️ VER PRODUTOS', callback_data='servicos')
    bt_contas = InlineKeyboardButton('🛒 CONTAS', callback_data='servicos_categoria conta')
    bt_telas = InlineKeyboardButton('📲 TELAS', callback_data='servicos_categoria tela')

    bt_carrinho  = InlineKeyboardButton('🛒 CARRINHO', callback_data='mostrar_carrinho')
    bt_perfil    = InlineKeyboardButton('ℹ️ MEU PERFIL', callback_data='perfil')
    bt_addsaldo  = InlineKeyboardButton('💰 RECARGA', callback_data='addsaldo')
    
    bt_ganhar   = InlineKeyboardButton('🎁 CENTRAL DE PRÊMIOS', callback_data='menu_premios')
    bt_suporte  = InlineKeyboardButton('📞 SUPORTE', url='https://t.me/Mobixsuporte')
    
    bt_rank     = InlineKeyboardButton('📊 RANKING', callback_data='ranking')
    bt_pesq     = InlineKeyboardButton('🔎 PESQUISAR', switch_inline_query_current_chat="buscar_loguin ")

    markup.row(bt_ver_todos)                      # 1
    markup.row(bt_carrinho)                       # 1 (Carrinho logo abaixo de Ver Produtos)

    if usar_categorias:
        markup.row(bt_contas, bt_telas)           # 2

    markup.row(bt_addsaldo, bt_perfil)            # 2
    markup.row(bt_ganhar)                         # 1
    markup.row(bt_suporte, bt_rank)               # 2
    markup.row(bt_pesq)                           # 1 (Pesquisar sozinho no final)

    return markup

def gerar_menu_premios():
    """Gera o submenu com todas as opções de ganhos e recompensas."""
    markup = InlineKeyboardMarkup()
    
    bt_caixa_misteriosa = InlineKeyboardButton('🎁 CAIXA MISTERIOSA', callback_data='comprar_caixa_misteriosa')
    bt_recompensa = InlineKeyboardButton('🔥 BÔNUS', callback_data='resgatar_recompensa')
    bt_promocoes = InlineKeyboardButton('🎉 PROMOÇÕES', callback_data='mostrar_promocoes')
    bt_revenda  = InlineKeyboardButton('👑 CASHBACK', callback_data='painel_revenda_vip')
    
    bt_voltar = InlineKeyboardButton('↩️ VOLTAR', callback_data='menu_start')

    # Seguindo o padrão: 1, 2, 1, 1 (último fica sozinho pois são 5 botões)
    markup.row(bt_caixa_misteriosa)               # 1
    markup.row(bt_recompensa, bt_promocoes)       # 2
    markup.row(bt_revenda)                        # 1
    markup.row(bt_voltar)                         # 1
    
    return markup

# ==================== PERFIL_MANAGER ====================
# perfil_manager.py
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def exibir_perfil(message, bot, api, load_user_data_func):
    user_id = message.chat.id
    user = message.from_user
    
    # --- Coleta de Dados via API com proteção de erro ---
    try:
        saldo = api.InfoUser.saldo(user_id)
        total_compras = api.InfoUser.total_compras(user_id)
        pix_inseridos = api.InfoUser.pix_inseridos(user_id)
        gifts_resgatados = api.InfoUser.gifts_resgatados(user_id)
        indicados = api.InfoUser.quantidade_afiliados(user_id)
    except Exception as e:
        print(f"[Perfil] Erro ao carregar dados da API: {e}")
        saldo = total_compras = pix_inseridos = gifts_resgatados = indicados = 0.0

    # Carrega dados do arquivo JSON para detalhes adicionais
    try:
        user_data = load_user_data_func(user_id) or {}
    except Exception:
        user_data = {}
        
    compras = user_data.get("compras", [])

    # Calcula o total gasto de forma segura
    total_gasto = 0.0
    for compra in compras:
        try:
            total_gasto += float(compra.get("valor", 0))
        except (ValueError, TypeError):
            continue

    # Formata a última compra
    if compras:
        ultima_compra = compras[-1]
        servico_nome = ultima_compra.get('servico', 'N/A')
        data_compra = ultima_compra.get('data', 'N/A')
        ultima_compra_texto = f"🛍️ <b>{servico_nome}</b>\n   └─ 📅 <i>{data_compra}</i>"
    else:
        ultima_compra_texto = "<i>Nenhuma compra registrada.</i>"
        
    data_registro = user_data.get("data_registro", "Não informada")
    telefone = user_data.get("whatsapp", "Não informado")

    # Formatação do nome completo
    nome_completo = user.first_name
    if user.last_name:
        nome_completo += f" {user.last_name}"

    # --- Montagem do Texto do Perfil ---
    texto = f"""✌️ <b>OLÁ, {user.first_name.upper()}!</b>
<i>Aqui estão os detalhes completos da sua conta:</i>

👤 <b>DADOS DO USUÁRIO</b>
├─ <b>Nome:</b> {nome_completo}
├─ <b>Username:</b> @{user.username or 'Não definido'}
├─ <b>ID:</b> <code>{user_id}</code>
├─ <b>Telefone:</b> <code>{telefone}</code>
└─ <b>Registro:</b> {data_registro}

💰 <b>CARTEIRA & FINANCEIRO</b>
├─ <b>Saldo disponível:</b> R$ {saldo:.2f}
├─ <b>Total recarregado (PIX):</b> R$ {pix_inseridos:.2f}
├─ <b>Gifts resgatados:</b> R$ {gifts_resgatados:.2f}
└─ <b>Total gasto em compras:</b> R$ {total_gasto:.2f}

📈 <b>RESUMO DE ATIVIDADES</b>
├─ <b>Total de compras:</b> {total_compras}
└─ <b>Última Atividade:</b>
   {ultima_compra_texto}

🏆 <b>SISTEMA DE AFILIADOS</b>
├─ <b>Pessoas indicadas:</b> {indicados}
└─ <b>Seu link de indicação:</b>
   <code>https://t.me/{api.CredentialsChange.user_bot()}?start={user_id}</code>
"""

    markup = InlineKeyboardMarkup()
    
    # Adicionando botões de ação úteis no perfil
    markup.row(InlineKeyboardButton('🤖 ALUGAR ESSE BOT', url='https://t.me/Mobixsuporte'))
    markup.row(InlineKeyboardButton('❤️ FAVORITOS', callback_data='mostrar_favoritos'))
    markup.row(InlineKeyboardButton('📜 HISTÓRICO', callback_data='ver_historico_perfil'))
    markup.row(InlineKeyboardButton('🔄 RENOVAR APPS', callback_data='menu_renovacao'))
    markup.row(InlineKeyboardButton('↩️ Voltar ao Menu Principal', callback_data='menu_start'))

    from app import interface as fotos_menus
    if fotos_menus.exibir_com_foto_opcional(
        bot, message.chat.id, message.message_id, 'perfil', texto, reply_markup=markup
    ):
        return

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        if 'message is not modified' not in str(e).lower():
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception:
                pass
            bot.send_message(
                chat_id=message.chat.id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup,
                disable_web_page_preview=True
            )

# ==================== FOTOS_PRODUTOS ====================
import json
import os
from telebot import types
from app import central as api

ARQUIVO_FOTOS_PRODUTOS = 'database/fotos_produtos.json'

def is_admin_fotos_produtos(user_id):
    try:
        return api.Admin.verificar_admin(user_id) or str(user_id) == str(api.CredentialsChange.id_dono())
    except:
        return False

def carregar_fotos_produtos():
    if not os.path.exists('database'):
        os.makedirs('database')
    if os.path.exists(ARQUIVO_FOTOS_PRODUTOS):
        try:
            with open(ARQUIVO_FOTOS_PRODUTOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def salvar_foto_produto(nome_produto, file_id):
    fotos = carregar_fotos_produtos()
    fotos[nome_produto.lower().strip()] = file_id
    with open(ARQUIVO_FOTOS_PRODUTOS, 'w', encoding='utf-8') as f:
        json.dump(fotos, f, indent=4, ensure_ascii=False)

def obter_foto_customizada(nome_produto):
    fotos = carregar_fotos_produtos()
    return fotos.get(nome_produto.lower().strip())

def registrar_fotos_produtos(bot):
    @bot.message_handler(commands=['setfoto'])
    def cmd_setfoto(message):
        if not is_admin_fotos_produtos(message.from_user.id):
            return bot.reply_to(message, "🚫 Acesso Negado!")
        
        msg = bot.send_message(
            message.chat.id, 
            "📸 <b>DEFINIR FOTO DO PRODUTO</b>\n\nDigite o <b>NOME EXATO</b> do produto que deseja adicionar/alterar a foto:", 
            parse_mode='HTML', 
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, processar_nome_foto, bot)

    def processar_nome_foto(message, bot):
        if message.text.lower() in ['/cancel', 'cancelar']:
            return bot.reply_to(message, "Operação cancelada.")
            
        nome_produto = message.text.strip()
        msg = bot.send_message(
            message.chat.id, 
            f"✅ Produto selecionado: <b>{nome_produto}</b>\n\nAgora, envie a <b>IMAGEM (FOTO)</b> que aparecerá para os clientes.", 
            parse_mode='HTML', 
            reply_markup=types.ForceReply()
        )
        bot.register_next_step_handler(msg, processar_imagem_foto, bot, nome_produto)

    def processar_imagem_foto(message, bot, nome_produto):
        if not message.photo:
            bot.send_message(message.chat.id, "❌ Você não enviou uma foto válida. Use o comando /setfoto novamente.")
            return
            
        file_id = message.photo[-1].file_id
        salvar_foto_produto(nome_produto, file_id)
        
        bot.send_message(
            message.chat.id, 
            f"✅ <b>Sucesso!</b> A foto do produto <b>{nome_produto}</b> foi salva e já aparecerá no menu e na entrega.", 
            parse_mode='HTML'
        )

# ==================== FOTOS_MENUS ====================
import json
import os
from telebot import types
from app import central as api
from app import premium_emojis

ARQUIVO_FOTOS_MENUS = 'database/fotos_menus.json'

# Menus que já têm um ponto de exibição integrado (aparecem no /setfotomenu
# com o aviso de que já funcionam). Para adicionar um novo menu à lista,
# basta chamar exibir_com_foto_opcional(...) no ponto onde ele é mostrado
# (veja o exemplo em bot.py -> addsaldo()
# e em bot.py -> cart_show_products()).
MENUS_DISPONIVEIS = [
    ('🛍️ Ver Produtos', 'servicos'),
    ('🛒 Carrinho', 'carrinho'),
    ('🛒📲 Categorias (Contas/Telas)', 'servicos_categoria'),
    ('💰 Adicionar Saldo / Recarga', 'addsaldo'),
    ('👤 Perfil', 'perfil'),
    ('🎁 Central de Prêmios', 'menu_premios'),
    ('📊 Ranking', 'ranking'),
    ('🏠 Menu Inicial (/start)', 'start'),
    ('🛍️ Menu Comprar', 'menu_comprar'),
    ('💠 PIX Manual', 'pix_manual'),
    ('🎁 Gift Card', 'giftcard'),
]


def is_admin_fotos_menus(user_id):
    try:
        return api.Admin.verificar_admin(user_id) or str(user_id) == str(api.CredentialsChange.id_dono())
    except Exception:
        return False


def carregar_fotos_menus():
    if not os.path.exists('database'):
        os.makedirs('database')
    if os.path.exists(ARQUIVO_FOTOS_MENUS):
        try:
            with open(ARQUIVO_FOTOS_MENUS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salvar_foto_menu(chave, file_id):
    fotos = carregar_fotos_menus()
    fotos[chave] = file_id
    if not os.path.exists('database'):
        os.makedirs('database')
    with open(ARQUIVO_FOTOS_MENUS, 'w', encoding='utf-8') as f:
        json.dump(fotos, f, indent=4, ensure_ascii=False)


def remover_foto_menu(chave):
    fotos = carregar_fotos_menus()
    if chave in fotos:
        del fotos[chave]
        with open(ARQUIVO_FOTOS_MENUS, 'w', encoding='utf-8') as f:
            json.dump(fotos, f, indent=4, ensure_ascii=False)
        return True
    return False


def obter_foto_menu(chave):
    foto = carregar_fotos_menus().get(chave)
    if isinstance(foto, str) and foto.startswith('assets/'):
        from pathlib import Path
        assets = (Path(__file__).resolve().parent.parent / 'assets').resolve()
        caminho = (Path(__file__).resolve().parent.parent / foto).resolve()
        if caminho.is_relative_to(assets) and caminho.is_file():
            return caminho.read_bytes()
    return foto


def exibir_com_foto(bot, chat_id, message_id, foto, texto, reply_markup=None, parse_mode='HTML'):
    """
    Exibe 'foto' (file_id de upload OU uma URL) com 'texto' como legenda,
    no lugar da mensagem 'message_id'. SEMPRE força a foto certa, mesmo que
    a mensagem atual já seja uma foto de OUTRO menu (evita herdar a imagem
    errada ao trocar de tela).
    Retorna:
      - True        -> editou a mensagem existente com sucesso (mesmo message_id)
      - Message     -> precisou apagar e mandar mensagem nova (pegue .message_id)
      - None        -> falhou completamente
    """
    # bot.edit_message_media() não passa pelos patches de premium_emojis.py
    # (que só cobrem send_message/send_photo/edit_message_text/edit_message_caption),
    # então sem isso os emojis premium viravam o emoji padrão toda vez que o
    # menu era trocado usando essa função (ex: botão "Voltar").
    if isinstance(parse_mode, str) and parse_mode.lower() == 'html':
        texto = premium_emojis.replace_emojis(texto, context="message")
    legenda = texto if len(texto) <= 1024 else texto[:1021] + '...'

    # 1ª tentativa: TROCAR a mídia da mensagem atual (funciona mesmo se a
    # mensagem já for uma foto de outro menu — troca pela foto certa).
    try:
        media = types.InputMediaPhoto(foto, caption=legenda, parse_mode=parse_mode)
        bot.edit_message_media(media, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        return True
    except Exception:
        pass

    # 2ª tentativa: apaga a mensagem atual (texto) e envia a foto no lugar
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass
    try:
        return bot.send_photo(chat_id, foto, caption=legenda, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        print(f"[fotos_menus] Erro ao exibir foto: {e}")
        return None


def exibir_com_foto_opcional(bot, chat_id, message_id, chave, texto, reply_markup=None, parse_mode='HTML'):
    """
    Se houver uma foto customizada salva para 'chave' (via /setfotomenu),
    tenta exibir essa foto no lugar da mensagem 'message_id', usando 'texto'
    como legenda. Retorna True se conseguiu (o chamador não precisa fazer
    mais nada). Retorna False se não há foto customizada para essa chave
    (o chamador deve seguir com o fluxo normal em texto).
    """
    file_id = obter_foto_menu(chave)
    if not file_id:
        return False
    resultado = exibir_com_foto(bot, chat_id, message_id, file_id, texto, reply_markup=reply_markup, parse_mode=parse_mode)
    return resultado is not None


def _montar_menu_selecao():
    markup = types.InlineKeyboardMarkup(row_width=1)
    fotos_atuais = carregar_fotos_menus()
    for nome, chave in MENUS_DISPONIVEIS:
        marcador = ' ✅' if chave in fotos_atuais else ''
        markup.add(types.InlineKeyboardButton(f"{nome}{marcador}", callback_data=f'setfotomenu_escolher_{chave}'))
    return markup


def registrar_fotos_menus(bot):
    @bot.message_handler(commands=['setfotomenu'])
    def cmd_setfotomenu(message):
        if not is_admin_fotos_menus(message.from_user.id):
            return bot.reply_to(message, "🚫 Acesso Negado!")
        bot.send_message(
            message.chat.id,
            "📸 <b>FOTO DOS MENUS</b>\n\n"
            "Escolha para qual menu você quer definir (ou trocar) a foto.\n"
            "Os menus com ✅ já têm uma foto customizada salva.",
            parse_mode='HTML',
            reply_markup=_montar_menu_selecao()
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('setfotomenu_escolher_'))
    def cb_escolher_menu(call):
        if not is_admin_fotos_menus(call.from_user.id):
            return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
        bot.answer_callback_query(call.id)
        chave = call.data.replace('setfotomenu_escolher_', '')
        nome_exibicao = dict((c, n) for n, c in MENUS_DISPONIVEIS).get(chave, chave)

        markup = types.InlineKeyboardMarkup()
        if obter_foto_menu(chave):
            markup.add(types.InlineKeyboardButton('🗑️ Remover foto atual', callback_data=f'setfotomenu_remover_{chave}'))
        markup.add(types.InlineKeyboardButton('❌ Cancelar', callback_data='setfotomenu_cancelar'))

        msg = bot.send_message(
            call.message.chat.id,
            f"✅ Menu selecionado: <b>{nome_exibicao}</b>\n\n"
            f"Agora, envie a <b>foto</b> (imagem) que deve aparecer nesse menu.\n"
            f"Basta enviar a foto pelo chat, sem precisar de link.",
            parse_mode='HTML',
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, _processar_imagem_menu, bot, chave, nome_exibicao)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('setfotomenu_remover_'))
    def cb_remover_menu(call):
        if not is_admin_fotos_menus(call.from_user.id):
            return bot.answer_callback_query(call.id, "🚫 Acesso Negado!", show_alert=True)
        chave = call.data.replace('setfotomenu_remover_', '')
        removeu = remover_foto_menu(chave)
        bot.answer_callback_query(call.id, "✅ Foto removida!" if removeu else "Nenhuma foto encontrada.", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data == 'setfotomenu_cancelar')
    def cb_cancelar_menu(call):
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass

    def _processar_imagem_menu(message, bot, chave, nome_exibicao):
        if message.text and message.text.lower() in ['/cancel', 'cancelar']:
            return bot.reply_to(message, "Operação cancelada.")
        if not message.photo:
            bot.send_message(message.chat.id, "❌ Você não enviou uma foto válida. Use o comando /setfotomenu novamente.")
            return

        file_id = message.photo[-1].file_id
        salvar_foto_menu(chave, file_id)

        bot.send_message(
            message.chat.id,
            f"✅ <b>Sucesso!</b> A foto do menu <b>{nome_exibicao}</b> foi salva e já aparecerá "
            f"da próxima vez que esse menu for aberto.",
            parse_mode='HTML'
        )

# ==================== RANKINGS ====================
"""
rankings.py — versão otimizada.

get_most_active_users_last_30_days ainda depende do campo 'compras'
armazenado no blob JSON de cada usuário (para casar user_id -> nome),
mas as agregações pesadas (top depositors, top products, top recent,
top gifts, top indicações) agora usam índices/consultas SQL do
database.py em vez de varrer arquivos .json da pasta database/users
(pasta que não existe mais após a migração para SQLite).

registrar_handlers(bot) e o cache de 5 min do menu (ranking_cache)
foram mantidos exatamente como no original — só a leitura de dados
por trás das funções acima mudou.
"""

import os
import json
import time
from datetime import datetime, timedelta
from collections import Counter
from telebot import types

from app import database
from app import central as api

# --- VARIÁVEIS PARA O CACHE DO RANKING (mantidas) ---
ranking_cache = {}
RANKING_CACHE_TTL = 300  # Cache de 5 minutos
username_cache = {}


def valor_aproximado(valor):
    """Arredonda um valor pra baixo, pro múltiplo de 10 mais próximo, e formata
    como faixa aproximada (ex: R$ 47,32 -> 'R$ 40+'). Usado nos rankings
    públicos pra não expor o valor exato de saldo/recarga/gift de ninguém."""
    valor = float(valor or 0.0)
    faixa = int(valor // 10) * 10
    return f"R$ {faixa}+"


def get_top_users_by_balance(limit=10):
    return database.get_top_users(top_n=limit)


def get_top_depositors(limit=10):
    return database.get_top_depositors(top_n=limit)


def get_top_products_last_30_days(limit=10):
    rows = database.get_top_products_last_30_days(top_n=limit)
    # mantém o formato original: lista de tuplas (produto, vendas)
    return [(r["produto"], r["vendas"]) for r in rows]


def get_top_recent_depositors(limit=10, days=30):
    return database.get_top_recent_depositors(top_n=limit, days=days)


def get_most_active_users_last_30_days(limit=10):
    conn = database._connect()
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """
        SELECT c.user_id AS user_id, COALESCE(u.username, 'User'||c.user_id) AS username,
               COUNT(*) AS recent_purchases_count
        FROM compras c
        LEFT JOIN users u ON u.user_id = c.user_id
        WHERE c.data >= ?
        GROUP BY c.user_id
        ORDER BY recent_purchases_count DESC
        LIMIT ?
        """,
        (cutoff, limit),
    ).fetchall()
    return [
        {
            "id": r["user_id"],
            "username": r["username"],
            "recent_purchases_count": r["recent_purchases_count"],
        }
        for r in rows
    ]


def registrar_rankings(bot):
    """Registra os comandos e botões do ranking interativo no bot."""

    def get_username_with_cache(user_id):
        user_id_str = str(user_id)
        if user_id_str in username_cache:
            return username_cache[user_id_str]
        
        try:
            chat_info = bot.get_chat(user_id)
            display_name = (chat_info.first_name or "") + (" " + chat_info.last_name if chat_info.last_name else "")
            if not display_name and chat_info.username:
                 display_name = chat_info.username
            if not display_name:
                 display_name = str(user_id)
            
            parts = display_name.split(" ")
            anonymized_parts = []
            for part in parts:
                if len(part) <= 2:
                    anonymized_parts.append(part)
                elif len(part) <= 4:
                    anonymized_parts.append(part[0] + "..." + part[-1])
                else:
                    anonymized_parts.append(part[0] + "..." + part[-3:])

            final_anonymized_name = " ".join(anonymized_parts)
            username_cache[user_id_str] = final_anonymized_name
            return final_anonymized_name
        except Exception:
            fallback_name = f"Utilizador {user_id_str[-3:]}"
            username_cache[user_id_str] = fallback_name
            return fallback_name

    def gerar_menu_rankings(ranking_selecionado=None):
        tipos_rankings = [
            ('rank_products', ' Serviços'),
            ('rank_depositors', ' Recargas'),
            ('rank_top_spenders', ' Compras'),
            ('rank_gifts', ' Gift Card'),
            ('rank_balance', ' Saldo'),
            ('rank_indicacoes', ' Indicações')
        ]
        
        icone_selecionado = '✅'
        icone_nao_selecionado = '✔️'

        botoes = []
        linha = []
        for codigo, descricao in tipos_rankings:
            icone = icone_selecionado if codigo == ranking_selecionado else icone_nao_selecionado
            botao = types.InlineKeyboardButton(f"{icone}{descricao}", callback_data=codigo)
            linha.append(botao)
            if len(linha) >= 2:
                botoes.append(linha)
                linha = []
        if linha:
            botoes.append(linha)

        bt_back = types.InlineKeyboardButton('↩️ Voltar', callback_data='menu_start')
        botoes.append([bt_back])
        markup = types.InlineKeyboardMarkup(botoes)
        return markup

    def atualizar_mensagem_rank(call, ranking_selecionado):
        global ranking_cache
        agora = time.time()
        
        if ranking_selecionado in ranking_cache:
            dados_cacheados, timestamp = ranking_cache[ranking_selecionado]
            if agora - timestamp < RANKING_CACHE_TTL:
                conteudo = dados_cacheados
                markup = gerar_menu_rankings(ranking_selecionado)
                from app import interface as fotos_menus
                if fotos_menus.exibir_com_foto_opcional(
                    bot, call.message.chat.id, call.message.message_id, 'ranking', conteudo, reply_markup=markup
                ):
                    return
                try:
                    api.editar_menu_seguro(
                        bot,
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        texto=conteudo,
                        reply_markup=markup,
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    print(f"Erro ao editar mensagem com cache: {e}")
                return 

        conteudo = "Selecione um tipo de ranking para visualizar."
        footer = "\n\nSe mantenha em 1º no ranking e ganhe uma coca e duas pamonhas!"

        if ranking_selecionado == 'rank_products':
            top_products = get_top_products_last_30_days()
            titulo = "🏆 Ranking de serviços mais vendidos (deste mês)"
            linhas = []
            for idx, (produto, vendas) in enumerate(top_products):
                pos = f"{idx+1}º)"
                if idx < 3:
                    linhas.append(f"{pos} - {produto} - {['🥇', '🥈', '🥉'][idx]} - Com {vendas} pedidos.")
                else:
                    linhas.append(f"{pos} - {produto} - Com {vendas} pedidos.")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer if linhas else "Sem dados ainda."

        elif ranking_selecionado == 'rank_depositors':
            top_depositors = get_top_recent_depositors()
            titulo = "🏆 Ranking de utilizadores que mais recarregaram (deste mês)"
            linhas = []
            for idx, user in enumerate(top_depositors):
                pos = f"{idx+1}º)"
                username = get_username_with_cache(user.get('id')).replace('@', '')
                valor_str = valor_aproximado(user.get('total_recent_pagos', 0.0))
                if idx < 3:
                    linhas.append(f"{pos} - {username} - {['🥇', '🥈', '🥉'][idx]} - Com {valor_str} em recargas.")
                else:
                    linhas.append(f"{pos} - {username} - Com {valor_str} em recargas.")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer if linhas else "Sem dados ainda."

        elif ranking_selecionado == 'rank_top_spenders':
            top_spenders = get_most_active_users_last_30_days()
            titulo = "🏆 Ranking de utilizadores que mais compraram (deste mês)"
            linhas = []
            for idx, user in enumerate(top_spenders):
                pos = f"{idx+1}º)"
                username = get_username_with_cache(user.get('id')).replace('@', '')
                compras = user.get('recent_purchases_count', 0)
                if idx < 3:
                    linhas.append(f"{pos} - {username} - {['🥇', '🥈', '🥉'][idx]} - Com {int(compras)} compras.")
                else:
                    linhas.append(f"{pos} - {username} - Com {int(compras)} compras.")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer if linhas else "Sem dados ainda."

        elif ranking_selecionado == 'rank_balance':
            top_users = get_top_users_by_balance(limit=10)
            titulo = "🏆 Ranking de utilizadores com maior saldo"
            linhas = []
            for idx, user in enumerate(top_users):
                pos = f"{idx+1}º)"
                username = get_username_with_cache(user.get('id')).replace('@', '')
                valor_str = valor_aproximado(user.get('saldo', 0.0))
                if idx < 3:
                    linhas.append(f"{pos} - {username} - {['🥇', '🥈', '🥉'][idx]} - Com {valor_str} em saldo.")
                else:
                    linhas.append(f"{pos} - {username} - Com {valor_str} em saldo.")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer if linhas else "Sem dados ainda."

        elif ranking_selecionado == 'rank_gifts':
            titulo = "🏆 Ranking de utilizadores que mais resgataram gift (prazo total)"
            top_gifts = []
            # CORREÇÃO: varria database/users/*.json, pasta que não existe mais
            # após a migração para SQLite. Agora usa database.get_all_user_ids().
            for uid in database.get_all_user_ids():
                try:
                    ud = database.load_user_data(uid) or {}

                    # Soma os valores da lista historico_gifts
                    historico = ud.get('historico_gifts', [])
                    resgatados = sum(float(g.get('valor', 0.0)) for g in historico if isinstance(g, dict))

                    # Fallback para chaves diretas caso existam no blob salvo
                    if resgatados == 0:
                        resgatados = float(ud.get('gift_redeemed') or ud.get('gifts_resgatados') or 0.0)

                    if resgatados > 0:
                        top_gifts.append({'id': ud.get('id', uid), 'gifts_resgatados': resgatados})
                except Exception:
                    pass
            top_gifts = sorted(top_gifts, key=lambda k: k['gifts_resgatados'], reverse=True)[:10]
            
            linhas = []
            for idx, user in enumerate(top_gifts):
                pos = f"{idx+1}º)"
                username = get_username_with_cache(user.get('id')).replace('@', '')
                valor_str = valor_aproximado(user.get('gifts_resgatados', 0.0))
                if idx < 3:
                    linhas.append(f"{pos} - {username} - {['🥇', '🥈', '🥉'][idx]} - Com {valor_str} resgatados.")
                else:
                    linhas.append(f"{pos} - {username} - Com {valor_str} resgatados.")
            if not linhas:
                linhas.append("<i>Nenhum resgate encontrado.</i>")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer

        elif ranking_selecionado == 'rank_indicacoes':
            titulo = "🏆 Ranking de utilizadores que mais indicaram (prazo total)"
            # CORREÇÃO: antes lia ud['afiliacoes']/ud['afiliados'], campos que o
            # fluxo de indicação em uso (afiliados_sistema.py -> database.
            # registrar_indicacao) nunca preenche — ele grava em
            # user_data['indicacoes'] e na tabela SQL 'indicacoes'. Por isso
            # esse ranking sempre aparecia vazio, mesmo com indicações reais
            # acontecendo. Agora usa database.get_top_indicadores(), que já
            # agrega a partir da tabela indexada 'indicacoes'.
            top_indicacoes = database.get_top_indicadores(top_n=10)
            linhas = []
            for idx, user in enumerate(top_indicacoes):
                pos = f"{idx+1}º)"
                username = get_username_with_cache(user.get('id')).replace('@', '')
                indicacoes = int(user.get('total_indicacoes', 0))
                if idx < 3:
                    linhas.append(f"{pos} - {username} - {['🥇', '🥈', '🥉'][idx]} - {indicacoes} indicações.")
                else:
                    linhas.append(f"{pos} - {username} - {indicacoes} indicações.")
            if not linhas:
                linhas.append("<i>Nenhuma indicação encontrada.</i>")
            conteudo = f"<b>{titulo}</b>\n\n" + "\n".join(linhas) + footer

        ranking_cache[ranking_selecionado] = (conteudo, agora)
        markup = gerar_menu_rankings(ranking_selecionado)

        from app import interface as fotos_menus
        if fotos_menus.exibir_com_foto_opcional(
            bot, call.message.chat.id, call.message.message_id, 'ranking', conteudo, reply_markup=markup
        ):
            return

        try:
            api.editar_menu_seguro(
                bot,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                texto=conteudo,
                reply_markup=markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Erro ao editar mensagem: {e}")

    # ===== ROTAS DO BOT (COMANDOS E BOTÕES) =====

    @bot.message_handler(commands=['ranking'])
    def comando_ranking(message):
        # Aqui também abre direto nos produtos se o utilizador usar o comando /ranking
        class DummyCall:
            def __init__(self, msg):
                self.message = msg
        
        dummy_call = DummyCall(message)
        # Envia uma mensagem em branco primeiro só para ter o message_id para o edit_message_text funcionar
        sent_msg = bot.send_message(chat_id=message.chat.id, text="A carregar rankings...")
        dummy_call.message = sent_msg
        
        atualizar_mensagem_rank(dummy_call, 'rank_products')


    # Intercepta os cliques nos botões do ranking interativo
    @bot.callback_query_handler(func=lambda call: call.data in [
        'ranking', 'rank_products', 'rank_depositors', 'rank_top_spenders', 
        'rank_gifts', 'rank_balance', 'rank_indicacoes'
    ])
    def callback_ranking_menu(call):
        try:
            bot.answer_callback_query(call.id)
        except:
            pass
        
        if call.data == 'ranking':
            # AGORA ABRE DIRETO NOS PRODUTOS/APLICATIVOS
            atualizar_mensagem_rank(call, 'rank_products')
        else:
            atualizar_mensagem_rank(call, call.data)

# ==================== SISTEMA_FAVORITOS ====================
import os
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

PASTA_FAVORITOS = os.path.join('database', 'favoritos')

def _garantir_pasta():
    """Garante que a pasta de favoritos exista."""
    if not os.path.exists(PASTA_FAVORITOS):
        os.makedirs(PASTA_FAVORITOS)

def carregar_favoritos(user_id):
    """Carrega a lista de favoritos do usuário."""
    _garantir_pasta()
    caminho = os.path.join(PASTA_FAVORITOS, f"{user_id}.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_favoritos(user_id, favoritos):
    """Salva a lista de favoritos do usuário."""
    _garantir_pasta()
    caminho = os.path.join(PASTA_FAVORITOS, f"{user_id}.json")
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(favoritos, f, ensure_ascii=False, indent=4)

def registrar_favoritos(bot, api):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('fav_toggle|'))
    def handle_fav_toggle(call):
        user_id = call.from_user.id
        servico = call.data.split('|')[1]
        favoritos = carregar_favoritos(user_id)
        
        if servico in favoritos:
            favoritos.remove(servico)
            mensagem = f"💔 {servico} foi removido!"
            novo_texto = "❤️ FAVORITAR"
        else:
            favoritos.append(servico)
            mensagem = f"❤️ {servico} salvo com sucesso!"
            novo_texto = "💔 DESFAVORITAR"
            
        salvar_favoritos(user_id, favoritos)
        
        # Envia o balãozinho pop-up
        bot.answer_callback_query(call.id, mensagem, show_alert=True)
        
        # Atualiza o texto do botão na mesma hora sem recarregar a mensagem inteira
        if call.message and call.message.reply_markup:
            markup = call.message.reply_markup
            for row in markup.keyboard:
                for btn in row:
                    if btn.callback_data == call.data:
                        btn.text = novo_texto
            try:
                bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id, 
                    message_id=call.message.message_id, 
                    reply_markup=markup
                )
            except Exception:
                pass

    @bot.callback_query_handler(func=lambda call: call.data == 'mostrar_favoritos')
    def handle_mostrar_favoritos(call):
        user_id = call.from_user.id
        favoritos = carregar_favoritos(user_id)
        
        if not favoritos:
            bot.answer_callback_query(call.id, "💔 Seu painel de favoritos está vazio.", show_alert=True)
            # Atualiza a tela informando que esvaziou a lista
            markup_vazio = InlineKeyboardMarkup()
            markup_vazio.add(InlineKeyboardButton("🔙 Voltar", callback_data="perfil"))
            try:
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="💔 <b>Seu painel de favoritos está vazio.</b>\n\nAdicione novos produtos navegando pela nossa loja!",
                    parse_mode='HTML',
                    reply_markup=markup_vazio
                )
            except:
                pass
            return
            
        texto = "❤️ <b>Seus Produtos Favoritos:</b>\n\n👇 Clique em um produto abaixo para visualizar:"
        markup = InlineKeyboardMarkup(row_width=1)
        
        for servico in favoritos:
            try:
                estoque = int(api.ControleLogins.pegar_estoque(servico))
            except Exception:
                estoque = 0
            
            if estoque > 0:
                texto_botao = f"⭐ {servico}"
                cb_data = f"exibir_servico {servico}" # Abre o produto
            else:
                texto_botao = f"❌ {servico} [ESGOTADO]"
                cb_data = f"fav_esgotado|{servico}" # Abre menu de remoção rápida
            
            markup.add(InlineKeyboardButton(texto_botao, callback_data=cb_data))
            
        markup.add(InlineKeyboardButton("🔙 Voltar", callback_data="perfil"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
            bot.answer_callback_query(call.id)
        except Exception:
            bot.send_message(call.message.chat.id, texto, parse_mode='HTML', reply_markup=markup)

    # NOVO: Handler que barra a abertura do produto esgotado
    @bot.callback_query_handler(func=lambda call: call.data.startswith('fav_esgotado|'))
    def handle_fav_esgotado(call):
        servico = call.data.split('|')[1]
        texto = (
            f"⚠️ <b>O produto {servico} está atualmente ESGOTADO!</b>\n\n"
            f"Você deseja removê-lo da sua lista de favoritos ou mantê-lo para quando o estoque for reposto?"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🗑️ Remover dos Favoritos", callback_data=f"fav_del_return|{servico}"))
        markup.row(InlineKeyboardButton("🔙 Manter e Voltar", callback_data="mostrar_favoritos"))
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    # NOVO: Handler que deleta o produto e retorna pra lista
    @bot.callback_query_handler(func=lambda call: call.data.startswith('fav_del_return|'))
    def handle_fav_del_return(call):
        user_id = call.from_user.id
        servico = call.data.split('|')[1]
        favoritos = carregar_favoritos(user_id)
        
        if servico in favoritos:
            favoritos.remove(servico)
            salvar_favoritos(user_id, favoritos)
            bot.answer_callback_query(call.id, f"🗑️ {servico} foi removido!", show_alert=True)
        else:
            bot.answer_callback_query(call.id)
            
        # Chama a função principal de favoritos de novo para atualizar a tela automaticamente
        handle_mostrar_favoritos(call)
