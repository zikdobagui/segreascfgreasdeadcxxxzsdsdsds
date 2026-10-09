"""
gerenciamento_logins.py

Sistema de gerenciamento do estoque de logins (contas/credenciais vendidas
aos clientes): adicionar, remover, renomear serviço, limpar duplicatas,
alterar valores e zerar o estoque.

Extraído de bot.py para deixar o arquivo principal mais limpo e organizado.

Uso em bot.py:
    import gerenciamento_logins
    logins_mgr = gerenciamento_logins.init_gerenciamento_logins(
        bot, api, is_admin_user, notify_subscribers
    )

    # depois, use logins_mgr.configurar_logins(...), logins_mgr.adicionar_login, etc.
"""
import os
import re
import json
import html
import traceback
from collections import Counter
from datetime import datetime, timedelta
import pytz
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def init_gerenciamento_logins(bot, api, is_admin_user, notify_subscribers):
    """
    Registra os handlers do sistema de estoque de logins no bot e devolve
    um objeto com as funções que bot.py ainda precisa chamar diretamente
    (menus, próximos passos etc).
    """

    # ==========================================================
    # LÓGICA DE ABASTECIMENTO EM MASSA
    # ==========================================================
    # Estado temporário do fluxo de abastecimento em massa
    admin_massa_temp = {}

    def receber_detalhes_massa(message):
        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")

    def processar_lista_massa(message):
        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")
    # ==========================================================


    def adicionar_login(message):

        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")

    # =================== INÍCIO DO NOVO BLOCO PARA ADICIONAR ===================

    import json
    import os
    import traceback # Certifique-se que esta importação está no topo do seu arquivo bot.py
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton # Garante importações
    from telebot import types # Garante importações

    # --- NOVO FLUXO INTERATIVO PARA REMOVER LOGIN (COM CONFIRMAÇÃO E BUSCA) ---

    def menu_remover_login(call):
        """
        Exibe o menu principal para a remoção de logins, com as opções de listar por serviço ou pesquisar por e-mail.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)


    def listar_servicos_para_remover(call):
        """
        Passo 1 (Listar por Serviço): Exibe botões com todos os serviços únicos que possuem estoque.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # ESTA É A VERSÃO CORRIGIDA da função selecionar_email_para_remover (mantida por compatibilidade)
    def selecionar_email_para_remover_v1(call):
        """
        Passo 2 (Listar por Serviço): Exibe botões com todos os e-mails disponíveis para aquele serviço.
        (VERSÃO CORRIGIDA COM ÍNDICE)
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)



    def executar_remocao_login_idx(call):
        """
        Passo 4: Executa a exclusão após a confirmação (via índice).
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # --- FIM DO FLUXO INTERATIVO ---

    # =================== FIM DO NOVO BLOCO PARA ADICIONAR ===================

    # --- FIM DO NOVO FLUXO ---       

    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
    # --- NOVO FLUXO INTERATIVO PARA REMOVER LOGIN ---

    def selecionar_servico_para_remover(call):
        """
        Passo 1: Exibe botões com todos os serviços únicos que possuem estoque.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def selecionar_email_para_remover(call):
        """
        Passo 2: Após selecionar um serviço, exibe botões com todos os e-mails disponíveis para aquele serviço.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def confirmar_remocao_login_idx(call):
        """
        Passo 3: Pergunta se o admin realmente quer excluir o login selecionado (via índice).
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # --- FIM DO NOVO FLUXO ---
    def remover_por_plataforma(message):
        # Listar plataformas disponíveis
        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")

    def confirmar_remover_plataforma(call):
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def remover_todos_plataforma(call):
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def mudar_valor_servico(message):
        if not is_admin_user(message.from_user.id):
            return bot.reply_to(message, 'Acesso restrito ao administrador.')
        try:
            sep = api.CredentialsChange.separador()
            txt = message.text.strip().split(f'{sep}')
            servico = txt[0]
            valor = float(txt[1].replace(',', '.'))
            if not api.ControleLogins.mudar_valor_por_nome(servico, valor):
                return bot.reply_to(message, 'Produto não encontrado ou preço inválido.')
            bot.reply_to(message, f"O servico {servico} teve seu valor mudado para R${valor:.2f}")
        except:
            bot.reply_to(message, 'Falha ao mudar os valores.')

    def mudar_valor_todos(message):
        if not is_admin_user(message.from_user.id):
            return bot.reply_to(message, 'Acesso restrito ao administrador.')
        try:
            valor = float(message.text.replace(',', '.'))
            if not api.ControleLogins.mudar_valor_de_todos(valor):
                return bot.reply_to(message, 'Catálogo vazio ou preço inválido.')
            bot.reply_to(message, "Valores alterados com sucesso")
        except:
            bot.reply_to(message, "Erro ao alterar valores.")

    # ==========================================================
    # [NOVO] FUNÇÕES DE RENOMEAR E LIMPEZA
    # ==========================================================

    # --- 1. LÓGICA DE RENOMEAR SERVIÇO ---
    def prompt_renomear_servico(call):
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def executar_renomeacao_servico(message):
        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")


    # --- 2. LÓGICA DE LIMPAR DUPLICATAS ---
    def prompt_limpar_duplicatas(call):
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def executar_limpeza_duplicatas(message):
        return bot.reply_to(message, "Estoque gerenciado pela API. Use o bot raiz.")

    def configurar_logins(message):
        texto = ('🌐 <b>ESTOQUE DA API</b>\n\n'
                 'Produtos e quantidades são consultados no fornecedor.\n'
                 'Email e senha são liberados somente após reservar a compra.\n'
                 'Reposições e remoções são feitas no bot raiz.')
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton('🌐 Configurar API', callback_data='stock_api_menu'))
        markup.row(InlineKeyboardButton('💸 Valor (Serviço)', callback_data='mudar_valor_servico'),
                   InlineKeyboardButton('💳 Valor (Todos)', callback_data='mudar_valor_todos'))
        markup.row(InlineKeyboardButton('📦 Consultar estoque', callback_data='estoque_menu'))
        markup.row(InlineKeyboardButton('↩ Voltar ao Painel', callback_data='voltar_paineladm'))
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                text=texto,
                message_id=message.message_id,
                reply_markup=markup,
                parse_mode='HTML'
            )
        except:
            bot.send_message(message.chat.id, texto, reply_markup=markup, parse_mode='HTML')

        # ======================= [INÍCIO] SISTEMA REMOVER E RECEBER =======================

    def menu_remover_receber(call):
        """
        Passo 1: Lista os serviços disponíveis para a função Remover e Receber.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # Estado temporário de seleção múltipla do fluxo Remover e Receber (por chat_id)
    remover_rec_estado = {}

    def _renderizar_lista_remover_receber(call, nome_servico):
        """
        Renderiza (ou re-renderiza) a lista de emails do serviço com checkboxes,
        refletindo o estado atual de seleção múltipla.
        """
        chat_id = call.message.chat.id
        estado = remover_rec_estado.setdefault(chat_id, {'servico': nome_servico, 'selecionados': set()})
        selecionados = estado['selecionados']

        try:
            todos_logins = api.ControleLogins.pegar_servicos()

            # Filtra e guarda o índice GLOBAL original para garantir remoção correta
            logins_do_servico = []
            for idx, s in enumerate(todos_logins):
                if s.get('nome') == nome_servico:
                    logins_do_servico.append((idx, s))

            if not logins_do_servico:
                remover_rec_estado.pop(chat_id, None)
                bot.edit_message_text(
                    f"Não há mais logins de '{nome_servico}'.",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("↩️ Voltar", callback_data='menu_remover_receber'))
                )
                return

            # Remove da seleção qualquer índice que não exista mais (ex: vendido nesse meio tempo)
            indices_validos = {idx for idx, _ in logins_do_servico}
            selecionados &= indices_validos

            markup = InlineKeyboardMarkup(row_width=1)
            for idx_global, login in logins_do_servico:
                email = login.get('email', 'Sem Email')
                email_display = (email[:30] + '...') if len(email) > 33 else email
                marcado = idx_global in selecionados
                prefixo = "☑️" if marcado else "⬜"
                markup.add(InlineKeyboardButton(f"{prefixo} {email_display}", callback_data=f"remover_rec_toggle|{idx_global}"))

            todos_marcados = len(selecionados) > 0 and selecionados == indices_validos
            markup.row(InlineKeyboardButton(
                "◻️ Desmarcar Todos" if todos_marcados else "☑️ Selecionar Todos",
                callback_data="remover_rec_toggle_todos"
            ))

            if selecionados:
                markup.row(InlineKeyboardButton(
                    f"✅ Confirmar Remoção ({len(selecionados)})",
                    callback_data="remover_rec_confirmar_multi"
                ))

            markup.row(InlineKeyboardButton("↩️ Voltar", callback_data='menu_remover_receber'))

            texto_qtd = f"\n\n🔢 {len(selecionados)} selecionado(s)." if selecionados else ""
            bot.edit_message_text(
                f"Selecione o(s) login(s) de <b>{nome_servico}</b> para remover e receber os dados "
                f"(toque para marcar/desmarcar — pode escolher vários de uma vez):{texto_qtd}",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode='HTML',
                reply_markup=markup
            )

        except Exception as e:
            print(f"Erro _renderizar_lista_remover_receber: {e}")
            bot.send_message(chat_id, "Erro ao listar emails.")

    def listar_emails_remover_receber(call):
        """
        Passo 2: Lista os emails do serviço selecionado, reiniciando a seleção múltipla.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def toggle_selecao_remover_receber(call):
        """
        Marca/desmarca um login individual na seleção múltipla.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def alternar_todos_remover_receber(call):
        """
        Seleciona ou desmarca todos os logins do serviço atual de uma vez.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def confirmar_remover_receber_multi(call):
        """
        Passo 2.5: Pede confirmação exibindo todos os emails selecionados antes de deletar.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def executar_remover_receber_multi(call):
        """
        Passo 3: Executa a remoção de todos os logins selecionados e entrega os dados ao admin.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # ======================= [FIM] SISTEMA REMOVER E RECEBER =======================
    def confirmar_zerar_estoque(call):
        """
        Confirmação antes de zerar o estoque.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    def zerar_estoque(call):
        """
        Zera completamente o estoque de logins.
        """
        return bot.answer_callback_query(call.id, "Estoque gerenciado pela API. Use o bot raiz.", show_alert=True)

    # ==========================================================
    # /estoque — visão do estoque.
    # Admin/dono: menu interativo (botões por plataforma, navegação, download).
    # Cliente comum: só o resumo em texto (valor, descrição, duração e
    # quantidade por serviço), sem nenhum botão.
    # ==========================================================
    def _montar_menu_estoque_texto_e_markup(user_id):
        resumo = api.ControleLogins.pegar_estoque_detalhado()  # HTML já pronto, com contagem por serviço

        if not is_admin_user(user_id):
            return resumo, None

        todos = api.ControleLogins.pegar_servicos() or []
        nomes_unicos = sorted({s.get('nome', '') for s in todos if s.get('nome')})

        markup = InlineKeyboardMarkup(row_width=2)
        if nomes_unicos:
            botoes = [InlineKeyboardButton(nome, callback_data=f'estoque_ver|{nome}|0') for nome in nomes_unicos]
            markup.add(*botoes)
        markup.row(InlineKeyboardButton('📄 Baixar tudo (.txt)', callback_data='estoque_baixar_txt'))
        markup.row(InlineKeyboardButton('↩ Voltar ao Painel', callback_data='voltar_paineladm'))

        texto = resumo
        if nomes_unicos:
            texto += (
                "\n\n👇 Toque em uma plataforma para consultar o produto. Credenciais só são liberadas após a reserva."
            )
        return texto, markup

    def comando_estoque(message):
        """/estoque — aberto a qualquer usuário. Admin/dono vê o menu
        interativo com email e senha de cada login; cliente comum só recebe
        o resumo em texto (sem botões)."""
        texto, markup = _montar_menu_estoque_texto_e_markup(message.from_user.id)
        bot.send_message(message.chat.id, texto, reply_markup=markup, parse_mode='HTML')

    def callback_estoque_menu(call):
        """Volta da tela de detalhe de um login para o menu de plataformas do /estoque.
        (Só é alcançável por admin/dono, já que cliente comum não recebe os botões.)"""
        texto, markup = _montar_menu_estoque_texto_e_markup(call.from_user.id)
        try:
            bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup, parse_mode='HTML')
        except Exception:
            bot.send_message(call.message.chat.id, texto, reply_markup=markup, parse_mode='HTML')
        bot.answer_callback_query(call.id)

    def callback_estoque_ver_plataforma(call):
        """Mostra, um por um (com Anterior/Próximo), os detalhes de cada login
        de uma plataforma. Email e senha só aparecem para admin/dono."""
        try:
            _, nome, pagina_str = call.data.split('|', 2)
            pagina = int(pagina_str)
        except Exception:
            return bot.answer_callback_query(call.id, "Erro ao processar essa plataforma.", show_alert=True)

        todos = api.ControleLogins.pegar_servicos() or []
        logins_da_plataforma = [s for s in todos if s.get('nome') == nome]
        total = len(logins_da_plataforma)
        if total == 0:
            bot.answer_callback_query(call.id, "⚠️ Não há mais estoque dessa plataforma.", show_alert=True)
            return callback_estoque_menu(call)

        pagina = max(0, min(pagina, total - 1))
        login = logins_da_plataforma[pagina]
        eh_admin = is_admin_user(call.from_user.id)
        texto = (
            f"📦 <b>{html.escape(str(nome))}</b>  ({pagina + 1}/{total})\n"
            f"➖➖➖➖➖➖➖➖➖➖➖\n"
            f"💲 <b>Valor:</b> R${html.escape(str(login.get('valor', 'N/A')))}\n"
            f"📝 <b>Descrição:</b> {html.escape(str(login.get('descricao', 'N/A')))}\n"
        )
        if eh_admin and not getattr(api.ControleLogins, "remoto", False):
            texto += (
                f"📧 <b>Email:</b> <code>{html.escape(str(login.get('email', 'N/A')))}</code>\n"
                f"🔑 <b>Senha:</b> <code>{html.escape(str(login.get('senha', 'N/A')))}</code>\n"
            )
        texto += f"⏳ <b>Duração:</b> {html.escape(str(login.get('duracao', 'N/A')))} dias"
        markup = InlineKeyboardMarkup()
        nav = []
        if pagina > 0:
            nav.append(InlineKeyboardButton('⬅ Anterior', callback_data=f'estoque_ver|{nome}|{pagina - 1}'))
        if pagina < total - 1:
            nav.append(InlineKeyboardButton('Próximo ➡', callback_data=f'estoque_ver|{nome}|{pagina + 1}'))
        if nav:
            markup.row(*nav)
        markup.row(InlineKeyboardButton('↩ Voltar à lista', callback_data='estoque_menu'))

        try:
            bot.edit_message_text(texto, chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   reply_markup=markup, parse_mode='HTML')
        except Exception:
            bot.send_message(call.message.chat.id, texto, reply_markup=markup, parse_mode='HTML')
        bot.answer_callback_query(call.id)

    def callback_estoque_baixar_txt(call):
        """Gera e envia um .txt com os detalhes completos de TODOS os logins em estoque.
        Fica restrito a admin/dono, pois inclui email e senha."""
        if not is_admin_user(call.from_user.id):
            return bot.answer_callback_query(call.id, "🚫 Sem permissão.", show_alert=True)
        bot.answer_callback_query(call.id, "Gerando arquivo...")
        try:
            ok = api.ControleLogins.criar_estoque_detalhado()
            if not ok:
                bot.send_message(call.message.chat.id, "⚠️ Estoque vazio ou houve um erro ao gerar o arquivo.")
                return
            with api.ControleLogins.arquivo_estoque_detalhado() as f:
                bot.send_document(
                    call.message.chat.id, f,
                    visible_file_name='estoque_detalhado.txt',
                    caption='📄 Catálogo do fornecedor (sem credenciais antes da reserva).'
                )
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Erro ao gerar/enviar o arquivo: {e}")

    bot.message_handler(commands=['estoque'])(comando_estoque)

    # ==========================================================
    # Registro dos handlers de callback (equivalente aos @bot.callback_query_handler
    # originais do bot.py)
    # ==========================================================
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_login_servico|'))(selecionar_email_para_remover_v1)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_login_confirmado_idx|'))(executar_remocao_login_idx)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_login_servico|'))(selecionar_email_para_remover)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_login_idx|'))(confirmar_remocao_login_idx)
    bot.callback_query_handler(func=lambda call: call.data.startswith('confirmar_remover_plat_'))(confirmar_remover_plataforma)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_todos_plat_'))(remover_todos_plataforma)
    bot.callback_query_handler(func=lambda call: call.data == 'renomear_servico_prompt')(prompt_renomear_servico)
    bot.callback_query_handler(func=lambda call: call.data == 'limpar_duplicatas_prompt')(prompt_limpar_duplicatas)
    bot.callback_query_handler(func=lambda call: call.data == 'menu_remover_receber')(menu_remover_receber)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_rec_serv|'))(listar_emails_remover_receber)
    bot.callback_query_handler(func=lambda call: call.data.startswith('remover_rec_toggle|'))(toggle_selecao_remover_receber)
    bot.callback_query_handler(func=lambda call: call.data == 'remover_rec_toggle_todos')(alternar_todos_remover_receber)
    bot.callback_query_handler(func=lambda call: call.data == 'remover_rec_confirmar_multi')(confirmar_remover_receber_multi)
    bot.callback_query_handler(func=lambda call: call.data == 'remover_rec_exec_multi')(executar_remover_receber_multi)
    bot.callback_query_handler(func=lambda call: call.data == 'confirmar_zerar_estoque')(confirmar_zerar_estoque)
    bot.callback_query_handler(func=lambda call: call.data == 'zerar_estoque')(zerar_estoque)
    bot.callback_query_handler(func=lambda call: call.data == 'estoque_menu')(callback_estoque_menu)
    bot.callback_query_handler(func=lambda call: call.data.startswith('estoque_ver|'))(callback_estoque_ver_plataforma)
    bot.callback_query_handler(func=lambda call: call.data == 'estoque_baixar_txt')(callback_estoque_baixar_txt)

    # ==========================================================
    # Funções que bot.py ainda chama diretamente (menus e próximos passos)
    # ==========================================================
    class _GerenciamentoLogins:
        pass

    modulo = _GerenciamentoLogins()
    modulo.configurar_logins = configurar_logins
    modulo.adicionar_login = adicionar_login
    modulo.receber_detalhes_massa = receber_detalhes_massa
    modulo.menu_remover_login = menu_remover_login
    modulo.listar_servicos_para_remover = listar_servicos_para_remover
    modulo.remover_por_plataforma = remover_por_plataforma
    modulo.mudar_valor_servico = mudar_valor_servico
    modulo.mudar_valor_todos = mudar_valor_todos
    modulo.comando_estoque = comando_estoque

    return modulo
