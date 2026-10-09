import os
import json
import random
import uuid
from telebot import types
from app import database # Certifique-se de que database.py tem get_user_balance e add_saldo

DB_FILE = 'caixa_misteriosa.json'

def create_default():
    """Cria a estrutura padrão de 3 caixas."""
    data = {
        "basica": {"preco": 2.0, "apps": []},
        "padrao": {"preco": 5.0, "apps": []},
        "premium": {"preco": 10.0, "apps": []}
    }
    save_data(data)
    return data

def load_data():
    """Carrega os dados da caixa misteriosa e converte formatos antigos se necessário."""
    if not os.path.exists(DB_FILE):
        return create_default()
        
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            # Sistema de segurança: se o ficheiro JSON for da versão antiga (1 caixa), ele converte para 3
            if "preco" in data:
                new_data = create_default()
                # Move os apps antigos para a caixa básica para não os perder
                new_data["basica"]["apps"] = data.get("apps", [])
                save_data(new_data)
                return new_data
            return data
        except json.JSONDecodeError:
            return create_default()

def save_data(data):
    """Salva os dados da caixa misteriosa."""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ==========================================
# ÁREA DO UTILIZADOR (USUÁRIO)
# ==========================================

def menu_caixa(message, bot):
    """Exibe o menu da caixa misteriosa para o utilizador final com as 3 opções."""
    data = load_data()
    
    preco_basica = data["basica"]["preco"]
    preco_padrao = data["padrao"]["preco"]
    preco_premium = data["premium"]["preco"]
    
    texto = (
        "🎁 <b>CAIXAS MISTERIOSAS</b> 🎁\n\n"
        "Tente a sorte! Abra uma das nossas caixas e ganhe um <b>Aplicativo Aleatório</b>.\n\n"
        f"📦 <b>Básica:</b> R$ {preco_basica:.2f}\n"
        f"📦 <b>Padrão:</b> R$ {preco_padrao:.2f}\n"
        f"📦 <b>Premium:</b> R$ {preco_premium:.2f}\n\n"
        "<i>Você tem coragem? Escolha a sua e descubra o que te aguarda!</i>"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_basica = types.InlineKeyboardButton(f"📦 Caixa Básica (R$ {preco_basica:.2f})", callback_data="caixa_confirmar_basica")
    btn_padrao = types.InlineKeyboardButton(f"📦 Caixa Padrão (R$ {preco_padrao:.2f})", callback_data="caixa_confirmar_padrao")
    btn_premium = types.InlineKeyboardButton(f"📦 Caixa Premium (R$ {preco_premium:.2f})", callback_data="caixa_confirmar_premium")
    
    # Botão de voltar configurado para ir para o menu de prêmios
    btn_voltar = types.InlineKeyboardButton("🔙 Voltar", callback_data="menu_premios") 
    
    markup.add(btn_basica, btn_padrao, btn_premium, btn_voltar)
    
    chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id

    try:
        try:
            # Apaga a mensagem anterior para não encher o chat
            bot.delete_message(chat_id, message.message_id)
        except:
            pass

        with open('1001420029.jpg', 'rb') as photo:
            bot.send_photo(
                chat_id,
                photo=photo,
                caption=texto,
                parse_mode='HTML',
                reply_markup=markup
            )
    except Exception as e:
        print(f"Erro ao enviar foto da caixa misteriosa: {e}")
        bot.send_message(chat_id, texto, reply_markup=markup, parse_mode='HTML')


def confirmar_compra_caixa(call, bot):
    """Exibe os detalhes da caixa e pede confirmação de compra com o visual de bloco."""
    tipo_caixa = call.data.split('_')[-1] # basica, padrao, premium
    data = load_data()
    
    if tipo_caixa not in data:
        bot.answer_callback_query(call.id, "Caixa não encontrada!", show_alert=True)
        return
        
    preco = data[tipo_caixa]["preco"]
    user_id = call.from_user.id
    saldo_atual = float(database.get_user_balance(user_id))
    
    nomes_caixas = {
        "basica": "🎁 CAIXA BÁSICA",
        "padrao": "🎁 CAIXA PADRÃO",
        "premium": "🎁 CAIXA PREMIUM"
    }
    
    descricoes = {
        "basica": "Descubra 1 aplicativo surpresa por um preço especial!\nO que você pode encontrar?\nServiços básicos como Amazon Prime, Crunchyroll e outros favoritos.",
        "padrao": "Descubra aplicativos incríveis com uma chance maior de pegar serviços intermediários e muito procurados!",
        "premium": "A melhor caixa! Chance de tirar os aplicativos mais caros e cobiçados do nosso catálogo como Netflix, Disney+ e muito mais."
    }
    
    nome_caixa = nomes_caixas.get(tipo_caixa, "CAIXA")
    descricao = descricoes.get(tipo_caixa, "Abra a caixa e ganhe um aplicativo surpresa.")
    
    # Formatação com "code" para ficar com a caixa preta
    texto = (
        f"<b>Caixa:</b> {nome_caixa}\n\n"
        f"<code>Valor: R$ {preco:.2f}</code>\n\n"
        f"<code>Seu saldo: R$ {saldo_atual:.2f}</code>\n\n"
        f"<code>Quantidade: 1\n"
        f"Sobre: {descricao}</code>"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_comprar = types.InlineKeyboardButton("🛒 Comprar Caixa", callback_data=f"caixa_abrir_{tipo_caixa}")
    
    # Botão de voltar configurado para ir para o menu de prêmios
    btn_voltar = types.InlineKeyboardButton("↩️ Voltar", callback_data="menu_premios") 
    
    markup.add(btn_comprar, btn_voltar)
    
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
        
    bot.send_message(call.message.chat.id, texto, parse_mode='HTML', reply_markup=markup)


def processar_abertura_caixa(call, bot):
    """Processa a compra e abertura das caixas após a confirmação."""
    user_id = call.from_user.id
    data = load_data()
    
    tipo_caixa = call.data.split('_')[-1]
    
    if tipo_caixa not in data:
        bot.answer_callback_query(call.id, "Caixa não encontrada!", show_alert=True)
        return

    preco = data[tipo_caixa]["preco"]
    apps = data[tipo_caixa]["apps"]
    
    if not apps:
        bot.answer_callback_query(call.id, f"A caixa {tipo_caixa.capitalize()} está vazia no momento!", show_alert=True)
        return

    # Verifica o saldo do utilizador
    saldo_atual = float(database.get_user_balance(user_id))
    
    if saldo_atual < preco:
        falta = preco - saldo_atual
        bot.answer_callback_query(
            call.id, 
            f"❌ Saldo Insuficiente!\n\n🎁 Caixa {tipo_caixa.capitalize()}: R${preco:.2f}\n💰 Seu Saldo: R${saldo_atual:.2f}\n🔻 Faltam: R${falta:.2f}\n\nPor favor, faça uma recarga.", 
            show_alert=True
        )
        return
        
    # Desconta o valor
    database.add_saldo(user_id, -preco) 
    
    # Sorteia um app específico desta caixa
    app_sorteado = random.choice(apps)
    
    texto_sucesso = (
        f"✅ <b>PAGAMENTO APROVADO!</b> ✅\n\n"
        f"🎉 <b>PARABÉNS! VOCÊ ABRIU A CAIXA {tipo_caixa.upper()}!</b> 🎉\n\n"
        f"📦 <b>Produto:</b> <code>{app_sorteado['nome']}</code>\n\n"
        f"👇 <b>SEUS DADOS DE ACESSO:</b> 👇\n"
        f"<code>{app_sorteado['conteudo']}</code>\n\n"
        f"<i>Aproveite o seu prêmio! Em caso de dúvidas, contate o suporte.</i>"
    )
    
    # Apaga o menu de confirmação
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    bot.send_message(user_id, texto_sucesso, parse_mode='HTML')
    bot.answer_callback_query(call.id, "Caixa aberta com sucesso!")


# ==========================================
# ÁREA DO ADMIN
# ==========================================

def painel_admin_caixa(message, bot):
    """Exibe o painel de gestão geral das 3 caixas."""
    data = load_data()
    
    texto = "⚙️ <b>GERIR CAIXAS MISTERIOSAS</b> ⚙️\n\n"
    
    # Exibe o status de cada caixa
    for tipo in ["basica", "padrao", "premium"]:
        preco = data[tipo]["preco"]
        apps_count = len(data[tipo]["apps"])
        texto += f"📦 <b>Caixa {tipo.capitalize()}</b> - R$ {preco:.2f} ({apps_count} apps)\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("💰 Alterar Preços", callback_data="admin_caixa_valores")
    b2 = types.InlineKeyboardButton("➕ Adicionar App", callback_data="admin_caixa_add")
    b3 = types.InlineKeyboardButton("❌ Remover App", callback_data="admin_caixa_rem")
    markup.add(b1)
    markup.add(b2, b3)
    
    chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id
    bot.send_message(chat_id, texto, reply_markup=markup, parse_mode='HTML')

def gerenciar_callbacks_admin(call, bot):
    """Gere os menus de opções do painel de admin."""
    
    # 1. MENU DE ALTERAR PREÇOS
    if call.data == "admin_caixa_valores":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🥉 Básica", callback_data="setpreco_basica"),
            types.InlineKeyboardButton("🥈 Padrão", callback_data="setpreco_padrao"),
            types.InlineKeyboardButton("🥇 Premium", callback_data="setpreco_premium")
        )
        bot.send_message(call.message.chat.id, "De qual caixa quer alterar o valor?", reply_markup=markup)

    elif call.data.startswith("setpreco_"):
        tipo = call.data.split('_')[1]
        msg = bot.send_message(call.message.chat.id, f"Digite o novo valor para a caixa <b>{tipo.capitalize()}</b> (ex: 5.00):", parse_mode='HTML')
        bot.register_next_step_handler(msg, step_alterar_valor, bot, tipo)

    # 2. MENU DE ADICIONAR APP
    elif call.data == "admin_caixa_add":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🥉 Básica", callback_data="addapp_basica"),
            types.InlineKeyboardButton("🥈 Padrão", callback_data="addapp_padrao"),
            types.InlineKeyboardButton("🥇 Premium", callback_data="addapp_premium")
        )
        bot.send_message(call.message.chat.id, "Em qual caixa quer adicionar o app?", reply_markup=markup)

    elif call.data.startswith("addapp_"):
        tipo = call.data.split('_')[1]
        msg = bot.send_message(call.message.chat.id, f"Digite o <b>NOME</b> do aplicativo para a caixa <b>{tipo.capitalize()}</b>:", parse_mode='HTML')
        bot.register_next_step_handler(msg, step_adicionar_app_nome, bot, tipo)

    # 3. MENU DE REMOVER APP
    elif call.data == "admin_caixa_rem":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🥉 Básica", callback_data="remapp_basica"),
            types.InlineKeyboardButton("🥈 Padrão", callback_data="remapp_padrao"),
            types.InlineKeyboardButton("🥇 Premium", callback_data="remapp_premium")
        )
        bot.send_message(call.message.chat.id, "De qual caixa quer remover o app?", reply_markup=markup)

    elif call.data.startswith("remapp_"):
        tipo = call.data.split('_')[1]
        data = load_data()
        apps = data[tipo].get("apps", [])
        
        if not apps:
            bot.answer_callback_query(call.id, f"A caixa {tipo.capitalize()} não tem apps!", show_alert=True)
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        for app in apps:
            markup.add(types.InlineKeyboardButton(f"❌ {app['nome']}", callback_data=f"delapp_{tipo}_{app['id']}"))
        bot.send_message(call.message.chat.id, f"Escolha qual app excluir da caixa {tipo.capitalize()}:", reply_markup=markup)

    # 4. EXCLUSÃO FINAL DO APP
    elif call.data.startswith("delapp_"):
        partes = call.data.split('_')
        tipo = partes[1]
        app_id = partes[2]
        processar_exclusao_app(call, bot, tipo, app_id)

# --- Funções de passos do Admin ---

def step_alterar_valor(message, bot, tipo):
    try:
        novo_valor = float(message.text.replace(',', '.'))
        data = load_data()
        data[tipo]['preco'] = novo_valor
        save_data(data)
        bot.send_message(message.chat.id, f"✅ Valor da caixa <b>{tipo.capitalize()}</b> atualizado para <b>R$ {novo_valor:.2f}</b>!", parse_mode='HTML')
    except ValueError:
        bot.send_message(message.chat.id, "❌ Valor inválido. Tente novamente.")

def step_adicionar_app_nome(message, bot, tipo):
    nome_app = message.text
    msg = bot.send_message(message.chat.id, "Envie agora o <b>Link</b> ou <b>Texto/Arquivo</b> que o utilizador vai receber ao ganhar esse app:", parse_mode='HTML')
    bot.register_next_step_handler(msg, step_adicionar_app_conteudo, bot, tipo, nome_app)

def step_adicionar_app_conteudo(message, bot, tipo, nome_app):
    conteudo = message.text 
    if not conteudo:
        bot.send_message(message.chat.id, "❌ Precisa de ser um texto ou link válido.")
        return
        
    data = load_data()
    novo_app = {
        "id": str(uuid.uuid4())[:8],
        "nome": nome_app,
        "conteudo": conteudo
    }
    data[tipo]["apps"].append(novo_app)
    save_data(data)
    
    bot.send_message(message.chat.id, f"✅ App <b>{nome_app}</b> adicionado à caixa <b>{tipo.capitalize()}</b> com sucesso!", parse_mode='HTML')

def processar_exclusao_app(call, bot, tipo, app_id):
    data = load_data()
    apps_iniciais = len(data[tipo]["apps"])
    data[tipo]["apps"] = [app for app in data[tipo]["apps"] if app["id"] != app_id]
    
    if len(data[tipo]["apps"]) < apps_iniciais:
        save_data(data)
        bot.answer_callback_query(call.id, "✅ App removido com sucesso!", show_alert=True)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Erro: App não encontrado.", show_alert=True)


# ==========================================
# REGISTRO DE HANDLERS (LIGAÇÃO COM O BOT)
# ==========================================
def registrar_handlers(bot, api, painel_admin_func=None):
    
    # --- Lógica do Utilizador (Menu da Loja) ---
    @bot.callback_query_handler(func=lambda call: call.data == 'comprar_caixa_misteriosa')
    def handler_menu_caixas(call):
        menu_caixa(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('caixa_confirmar_'))
    def handler_confirmar_caixa(call):
        confirmar_compra_caixa(call, bot)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('caixa_abrir_'))
    def handler_abrir_caixa(call):
        processar_abertura_caixa(call, bot)

    # --- Lógica do Admin (Painel Admin) ---
    @bot.callback_query_handler(func=lambda call: call.data == 'admin_menu_caixa')
    def handler_painel_admin_caixa(call):
        try:
            # Mantém a sua segurança antiga para que apenas admins abram o painel
            if not (api.Admin.verificar_admin(call.message.chat.id) or int(call.message.chat.id) == int(api.CredentialsChange.id_dono())):
                return bot.answer_callback_query(call.id, "Sem permissão.", show_alert=True)
        except:
            pass
        painel_admin_caixa(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data in ["admin_caixa_valores", "admin_caixa_add", "admin_caixa_rem"] or call.data.startswith(("setpreco_", "addapp_", "remapp_", "delapp_")))
    def handler_callbacks_admin(call):
        gerenciar_callbacks_admin(call, bot)
