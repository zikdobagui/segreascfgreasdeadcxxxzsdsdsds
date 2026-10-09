import os
from html import escape
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def registrar_handlers(bot, api):
    
    @bot.callback_query_handler(func=lambda call: call.data == 'editar_textos_bot')
    def handle_editar_textos_menu(call):
        bot.answer_callback_query(call.id)
        exibir_menu_edicao_texto(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('edit_text_'))
    def handle_iniciar_edicao(call):
        bot.answer_callback_query(call.id)
        tipo_texto = call.data.replace('edit_text_', '')
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        iniciar_edicao_texto(bot, api, call.message, tipo_texto)


def exibir_menu_edicao_texto(bot, message):
    texto = "<b>📝 Sistema de Edição de Textos e Mídia</b>\n\nSelecione qual mensagem do bot você deseja personalizar:"
    
    botoes = [
        ('🏠 Menu Inicial', 'start'),
        ('👤 Perfil', 'perfil'),
        ('💰 Adicionar Saldo', 'add_saldo'),
        ('💠 PIX Manual', 'pix_manual'),
        ('🤖 PIX Automático', 'pix_auto'),
        ('❌ Pagamento Expirado', 'pag_expirado'),
        ('✅ Pagamento Aprovado', 'pag_aprovado'),
        ('🛍️ Menu Comprar', 'menu_comprar'),
        ('🔍 Exibir Serviço', 'exibir_servico'),
        ('✨ Mensagem de Compra', 'mensagem_comprou'),
        ('🎁 Gift Card', 'giftcard'),
        ('📥 PIX Gerado (Inline)', 'pix_gerado_inline'),
        ('✅ Aprovado (Inline)', 'aprovado_inline'),
        ('📂 Categorias', 'categoriasservicos'),
        ('🤖 Alugar Bot', 'alugar_bot')
    ]

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(*[InlineKeyboardButton(nome, callback_data=f'edit_text_{chave}') for nome, chave in botoes])
    markup.row(InlineKeyboardButton('🔙 Voltar ao Painel', callback_data='voltar_paineladm'))

    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception:
        bot.send_message(
            message.chat.id,
            text=texto,
            parse_mode='HTML',
            reply_markup=markup
        )


def iniciar_edicao_texto(bot, api, message, tipo_texto):
    caminho_arquivo = f'textos/{tipo_texto}.txt'
    
    # Dicionário informando quais variáveis são suportadas em cada menu
    # (mantido em sincronia com as classes Textos/TextoInline em central.py)
    variaveis_por_tipo = {
        'start': "Nenhuma variável específica além das universais.",
        'perfil': (
            "<code>{pontos_indicacao}</code>, <code>{quantidade_afiliados}</code>, "
            "<code>{quantidade_compras}</code>, <code>{pix_inseridos}</code>, "
            "<code>{gifts_resgatados}</code>"
        ),
        'add_saldo': "Nenhuma variável específica além das universais (usa <code>{saldo}</code>).",
        'pix_manual': "<code>{deposito_minimo}</code>",
        'pix_auto': (
            "<code>{valor}</code>, <code>{pix_copia_cola}</code>, <code>{id_pagamento}</code>, "
            "<code>{expiracao}</code>, <code>{deposito_minimo}</code>"
        ),
        'pag_expirado': "<code>{id_pagamento}</code>, <code>{valor}</code>",
        'pag_aprovado': "<code>{id_pagamento}</code>, <code>{valor}</code>",
        'menu_comprar': "Nenhuma variável específica além das universais (usa <code>{saldo}</code>).",
        'exibir_servico': (
            "<code>{nome_servico}</code>, <code>{valor}</code>, <code>{descricao}</code>, "
            "<code>{estoque}</code>, <code>{duracao}</code>"
        ),
        'mensagem_comprou': (
            "<code>{nome}</code>, <code>{valor}</code>, <code>{email}</code>, <code>{senha}</code>, "
            "<code>{duracao}</code>, <code>{descricao}</code>"
        ),
        'giftcard': "<code>{codigo}</code>, <code>{quantidade}</code>, <code>{valor}</code>",
        'pix_gerado_inline': (
            "<code>{valor}</code>, <code>{id_pagamento}</code>, <code>{pix_copia_cola}</code>, "
            "<code>{expiracao}</code>\n"
            "⚠️ <i>Este texto é gerado sem contexto de usuário — variáveis universais "
            "(nome, saldo, etc.) ficam vazias.</i>"
        ),
        'aprovado_inline': "<code>{valor}</code>, <code>{id_pagamento}</code>",
        'categoriasservicos': (
            "Nenhuma variável — este texto não passa por formatação de variáveis.\n"
            "⚠️ <i>Formato de imagem diferente: aqui a 1ª linha deve ser a URL direta "
            "do GIF/imagem (sem o truque de link invisível).</i>"
        ),
        'alugar_bot': "Nenhuma variável. <i>(Texto salvo, mas ainda não exibido em nenhum ponto do bot.)</i>",
    }

    vars_especificas = variaveis_por_tipo.get(tipo_texto, "Nenhuma variável extra.")

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            texto_atual = f.read()

        instrucoes_vars = (
            "<b>Variáveis Universais</b> (disponíveis sempre que houver um usuário no contexto):\n"
            "<code>{first_name}</code> - Nome\n"
            "<code>{username}</code> - @User\n"
            "<code>{id}</code> - ID do Telegram\n"
            "<code>{saldo}</code> - Saldo atual\n"
            "<code>{link_afiliado}</code> - Link de Afiliado\n\n"
            f"<b>Específicas para este menu:</b>\n{vars_especificas}\n"
        )
        
        # Instrução detalhada de como colocar uma FOTO usando o truque de HTML invisível
        # (não se aplica a 'categoriasservicos', que usa formato próprio - ver aviso acima)
        instrucoes_img = (
            "\n<b>🖼️ COMO COLOCAR UMA FOTO NO TOPO:</b>\n"
            "Coloque o código abaixo exatamente na <b>primeira linha</b> da sua mensagem:\n\n"
            "<code>&lt;a href=\"SEU_LINK_AQUI\"&gt;&#8204;&lt;/a&gt;</code>\n\n"
            "<i>(Substitua SEU_LINK_AQUI pelo link da imagem, ex: https://i.imgur.com/suafoto.png)</i>"
            if tipo_texto != 'categoriasservicos' else
            "\n<b>🖼️ COMO COLOCAR UM GIF/IMAGEM:</b>\n"
            "Coloque a <b>URL direta</b> da imagem/GIF sozinha na <b>primeira linha</b>, "
            "e o texto normalmente a partir da segunda linha."
        )
            
        texto_prompt = (
            f"<b>📝 Editando '{tipo_texto.replace('_', ' ').title()}'</b>\n\n"
            f"<b>Texto Atual:</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{escape(texto_atual)}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"Envie o <b>novo texto</b> agora. Você pode usar formatação HTML.\n\n"
            f"{instrucoes_vars}"
            f"{instrucoes_img}"
        )
        
        # Opcional: botão para cancelar a edição
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("❌ Cancelar", callback_data="editar_textos_bot"))
        
        msg_enviada = bot.send_message(message.chat.id, texto_prompt, parse_mode='HTML', disable_web_page_preview=True, reply_markup=markup)
        bot.register_next_step_handler(msg_enviada, salvar_novo_texto, bot, api, tipo_texto)

    except FileNotFoundError:
        bot.reply_to(message, f"❌ Arquivo de texto não encontrado: `{caminho_arquivo}`", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ Erro ao carregar o texto: {str(e)}")


def salvar_novo_texto(message, bot, api, tipo_texto):
    # Proteção caso o usuário desista e dê /start ou /cancelar
    if not message.text or message.text.lower() in ['/start', '/cancelar', 'cancelar']:
        bot.reply_to(message, "❌ Edição cancelada.")
        exibir_menu_edicao_texto(bot, message)
        return

    novo_texto = message.text
    
    metodos_salvar = {
        'start': api.MudarTexto.start,
        'perfil': api.MudarTexto.perfil,
        'add_saldo': api.MudarTexto.adicionar_saldo,
        'pix_manual': api.MudarTexto.pix_manual,
        'pix_auto': api.MudarTexto.pix_automatico,
        'pag_expirado': api.MudarTexto.pagamento_expirado,
        'pag_aprovado': api.MudarTexto.pagamento_aprovado,
        'menu_comprar': api.MudarTexto.menu_comprar,
        'exibir_servico': api.MudarTexto.exibir_servico,
        'mensagem_comprou': api.MudarTexto.mensagem_comprou,
        'giftcard': api.MudarTexto.giftcard,
        'pix_gerado_inline': api.MudarTexto.pix_gerado_inline,
        'aprovado_inline': api.MudarTexto.aprovado_inline,
        'categoriasservicos': api.MudarTexto.categoriasservicos,
        'alugar_bot': api.MudarTexto.alugar_bot
    }

    metodo_salvar = metodos_salvar.get(tipo_texto)

    if callable(metodo_salvar):
        try:
            metodo_salvar(novo_texto)
            bot.reply_to(message, "✅ <b>Texto e mídia atualizados com sucesso!</b>\nAs alterações já estão no ar.", parse_mode="HTML")
            exibir_menu_edicao_texto(bot, message)
        except Exception as e:
            bot.reply_to(message, f"❌ Erro ao salvar o novo texto: {str(e)}")
    else:
        bot.reply_to(message, f"❌ Erro interno: método para salvar '{tipo_texto}' não foi encontrado.")
