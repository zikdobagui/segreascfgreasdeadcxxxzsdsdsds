import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from app import central as api # Importa a sua API central para mexer nos dias

# ==========================================
# CONFIGURAÇÕES
# ==========================================
# O token da PromissePay NÃO fica mais fixo no código: ele é lido de
# settings/credenciais.json (mesmo local usado pelo restante do bot),
# através do config_pagamentos.py. Configure/atualize o token pelo
# painel de pagamentos do bot (⚙️ Configuração de Pagamentos).

PLANOS = {
    "renovar_1": {"meses": 1, "valor": 30.00, "texto": "1 Mês - R$ 30,00"},
    "renovar_2": {"meses": 2, "valor": 50.00, "texto": "2 Meses - R$ 50,00"},
    "renovar_3": {"meses": 3, "valor": 70.00, "texto": "3 Meses - R$ 70,00"}
}

# ==========================================
# LÓGICA DE SOMA (CORRIGIDA COM A CENTRAL)
# ==========================================
def adicionar_dias_bot(user_id, meses):
    """
    Usa a função aumentar_vencimento da central para somar os dias.
    """
    try:
        # Garante que os meses viram inteiros (ex: 1 mês = 30 dias)
        dias_comprados = int(meses) * 30
        
        # 1. Verifica como está a situação do bot hoje
        dias_atuais = api.Admin.tempo_ate_o_vencimento()
        
        # 2. Se o bot já estiver vencido (ex: -5 dias), compensamos o tempo negativo 
        # para garantir que ele ganhe os 30 dias limpos a partir de HOJE.
        if dias_atuais is not None and dias_atuais < 0:
            dias_para_adicionar = abs(dias_atuais) + dias_comprados
        else:
            # Se já tem saldo positivo (ex: 30), ele só adiciona os novos (ex: +30)
            dias_para_adicionar = dias_comprados
            
        # 3. Usa a função NATIVA do seu central.py que soma os dias na data!
        sucesso = api.Admin.aumentar_vencimento(dias_para_adicionar)
        
        if sucesso:
            # Pega o novo total atualizado para mostrar na mensagem
            novo_total = api.Admin.tempo_ate_o_vencimento()
            print(f"[SUCESSO] Renovação aplicada! O bot agora tem {novo_total} dias de validade.")
            return novo_total
        else:
            return None

    except Exception as e:
        print(f"Erro ao adicionar dias com a central: {e}")
        return None

# ==========================================
# FUNÇÃO QUE EXIBE O AVISO INICIAL DE BLOQUEIO
# ==========================================
def ver_se_expirou(bot, chat_id):
    """
    Função para enviar a mensagem de bloqueio quando o bot estiver inativo.
    """
    markup_vencido = InlineKeyboardMarkup()
    markup_vencido.add(InlineKeyboardButton('♻️ RENOVAR AGORA', callback_data='renovar_bot'))
    
    try:
        bot.send_message(
            chat_id=chat_id,
            text="⚠️ <b>OPSS, O PLANO DO SEU BOT VENCEU ELE ESTA INATIVO. RENOVE-O AGORA!</b>",
            reply_markup=markup_vencido,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Erro ao enviar mensagem de vencimento: {e}")

# ==========================================
# LÓGICA DA PROMISSEPAY E BOT
# ==========================================
def exibir_planos_renovacao(message, bot):
    """Gera o menu com os botões dos planos."""
    # row_width=1 coloca todos os botões em um único menu, sem dividir
    markup = InlineKeyboardMarkup(row_width=1)
    
    for callback_data, plano in PLANOS.items():
        btn = InlineKeyboardButton(text=plano["texto"], callback_data=callback_data)
        markup.add(btn)
        
    # Adicionando o botão de voltar igual ao da foto
    markup.add(InlineKeyboardButton('↩️ VOLTAR', callback_data='voltar_vencido'))
        
    texto = (
        "🔄 <b>Renovação do Bot</b>\n\n"
        "Escolha um dos planos abaixo. O tempo será <b>SOMADO</b> aos seus dias atuais!\n\n"
        "👇 <b>Escolha seu Plano:</b>"
    )
    
    try:
        # Edita a mensagem atual em vez de enviar uma nova, dando aquele efeito rápido
        bot.edit_message_text(
            chat_id=message.chat.id, 
            message_id=message.message_id,
            text=texto, 
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception:
        # Fallback caso a edição falhe por algum motivo
        bot.send_message(
            message.chat.id, 
            texto, 
            reply_markup=markup,
            parse_mode="HTML"
        )

def gerar_pagamento_pix(valor, descricao):
    """Comunica com a PromissePay para gerar o PIX de renovação."""
    payment = api.CriarPixPromissePay.gerar(valor, "renovacao_bot")
    return {
        "id": payment["id"],
        "copia_cola": payment["qr_code"],
    }

def monitorar_pagamento(payment_id, chat_id, message_id, meses, bot):
    """Roda em segundo plano verificando se o PIX foi pago."""
    tempo_maximo = 15 * 60 
    intervalo_checagem = 10 
    tempo_decorrido = 0
    
    while tempo_decorrido < tempo_maximo:
        try:
            resposta = api.CriarPixPromissePay.consultar(payment_id)
            status = str(resposta.get("status", "")).upper()
            
            if status == "PAID":
                # Pagamento aprovado! Chama a função que SOMA os dias
                novo_vencimento = adicionar_dias_bot(chat_id, meses)
                
                if novo_vencimento is not None:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=f"✅ <b>Pagamento Aprovado!</b>\n\nA sua renovação de <b>{meses} mês(es)</b> foi concluída.\n\n📅 Novo vencimento: <b>{novo_vencimento} dias</b>",
                        parse_mode="HTML"
                    )
                else:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text="✅ <b>Pagamento Aprovado!</b>\n\nMas ocorreu um erro ao actualizar os dias. Contacte o suporte.",
                        parse_mode="HTML"
                    )
                return 
            
        except Exception as e:
            print(f"Erro ao checar pagamento: {e}")
            
        time.sleep(intervalo_checagem)
        tempo_decorrido += intervalo_checagem
        
    try:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text="❌ <b>Tempo expirado.</b>", parse_mode="HTML")
    except: pass


def registrar_handlers_renovacao(bot):
    """Registra as ações dos botões para o bot principal."""
    
    # ==========================================
    # 1. GATILHO PARA ABRIR O MENU DE PLANOS
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data == 'renovar_bot')
    def abrir_menu_renovacao(call):
        # Responde ao Telegram para tirar o ícone de "a carregar" do botão
        bot.answer_callback_query(call.id) 
        
        # Chama a função que monta e envia o menu de planos editando a mensagem atual
        exibir_planos_renovacao(call.message, bot)

    @bot.callback_query_handler(func=lambda call: call.data == 'voltar_vencido')
    def voltar_vencido_callback(call):
        """Retorna para a mensagem de bloqueio sem burlar o sistema."""
        bot.answer_callback_query(call.id)
        markup_vencido = InlineKeyboardMarkup([[InlineKeyboardButton('♻️ RENOVAR AGORA', callback_data='renovar_bot')]])
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="⚠️ <b>OPSS, O PLANO DO SEU BOT VENCEU ELE ESTA INATIVO. RENOVE-O AGORA!</b>",
                reply_markup=markup_vencido,
                parse_mode="HTML"
            )
        except Exception:
            pass

    # ==========================================
    # 2. GATILHO DE QUANDO ELE ESCOLHE UM PLANO
    # ==========================================
    @bot.callback_query_handler(func=lambda call: call.data in ['renovar_1', 'renovar_2', 'renovar_3'])
    def processar_escolha_plano(call):
        # Essa linha avisa o Telegram que o botão foi clicado, removendo o carregamento "aba"
        bot.answer_callback_query(call.id, "Gerando PIX, aguarde...")
        
        # Identifica o plano com base no botão clicado
        if call.data == 'renovar_1':
            valor = 30.00
            meses = 1
            texto = "1 Mês"
        elif call.data == 'renovar_2':
            valor = 50.00
            meses = 2
            texto = "2 Meses"
        elif call.data == 'renovar_3':
            valor = 70.00
            meses = 3
            texto = "3 Meses"
            
        pagamento = gerar_pagamento_pix(valor, f"Renovacao Bot - {meses} Meses")
        
        if "id" not in pagamento:
            bot.send_message(call.message.chat.id, "❌ Erro ao gerar pagamento.")
            return
            
        payment_id = pagamento["id"]
        copia_cola = pagamento["copia_cola"]
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🔄 <b>Pagamento de Renovação</b>\n\nPlano: {texto}\n\n<code>{copia_cola}</code>\n\n⏳ A aguardar aprovação automática...",
            parse_mode="HTML"
        )
        
        threading.Thread(
            target=monitorar_pagamento, 
            args=(payment_id, call.message.chat.id, call.message.message_id, meses, bot)
        ).start()
