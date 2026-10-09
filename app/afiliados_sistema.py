"""
Sistema de Afiliados - Funcionalidades para o Bot
"""
from app import database
from app.central import SistemaAfiliados
import telebot
import html # <-- CORREÇÃO: Importação adicionada

# Estado global para captura de valor de indicação
admin_setting_valor_indicacao = {}

# --- INÍCIO DA FUNÇÃO HELPER ADICIONADA ---
def _get_display_name(bot, indicador_dict):
    """
    Busca o nome de exibição mais recente do usuário (Nome Sobrenome @username)
    usando bot.get_chat. Faz fallback para o username do banco.
    """
    # Tenta obter o ID do indicador.
    user_id = indicador_dict.get('id') or indicador_dict.get('user_id')
    
    if user_id:
        try:
            # Usar bot.get_chat para obter os dados mais recentes
            chat_info = bot.get_chat(user_id)
            
            # Construir o nome completo (Nome + Sobrenome)
            full_name_parts = [chat_info.first_name, chat_info.last_name]
            full_name = " ".join(part for part in full_name_parts if part)
            full_name = html.escape(full_name.strip()) # Limpar e escapar
            
            # Obter o username
            username_str = f"(@{chat_info.username})" if chat_info.username else ""
            
            # Combinar nome e username
            if full_name and username_str:
                return f"{full_name} {username_str}"
            elif full_name:
                return full_name
            elif chat_info.username: # Se SÓ tiver username
                return f"@{chat_info.username}"
            else:
                # Fallback se não tiver nem nome nem username (raro)
                return f"User {user_id}"
                
        except Exception:
            # Fallback se o bot.get_chat falhar (ex: usuário deletou a conta)
            # Usar o username salvo no banco
            return f"@{indicador_dict.get('username', f'User {user_id}')}"
    else:
        # Fallback se o 'indicador' não tiver 'id' (pior caso)
        return f"@{indicador_dict.get('username', 'Usuário Desconhecido')}"
# --- FIM DA FUNÇÃO HELPER ADICIONADA ---

def processar_comando_start_com_referencia(message, bot):
    """
    Processa comando /start com parâmetro de referência
    """
    try:
        # Extrair parâmetro do comando /start
        comando_parts = message.text.split()
        if len(comando_parts) > 1:
            param = comando_parts[1]
            # Suporta formatos: "ref_<id>" e "<id>"
            if param.startswith('ref_'):
                indicador_id = int(param.replace('ref_', ''))
            elif param.isdigit():
                indicador_id = int(param)
            else:
                return False
            user_id = message.from_user.id
            
            # Verificar se o sistema está ativo
            if not SistemaAfiliados.status_ativo():
                return False
            
            # Verificar se o usuário não está tentando se indicar
            if indicador_id == user_id:
                return False
            
            # Verificar se o usuário já foi indicado por alguém
            user_data = database.load_user_data(user_id)
            if user_data and user_data.get('indicado_por'):
                return False
            
            # Verificar se o indicador existe; se não existir, inicializar
            indicador_data = database.load_user_data(indicador_id)
            if not indicador_data:
                try:
                    indicador_data = database.initialize_user(indicador_id, username=message.from_user.username)
                except Exception:
                    indicador_data = {'username': f"User{indicador_id}"}
            
            # Registrar a indicação
            valor_indicacao = SistemaAfiliados.get_valor_indicacao()
            database.registrar_indicacao(indicador_id, user_id, valor_indicacao)
            
            # Notificar o indicador
            try:
                username = message.from_user.username or message.from_user.first_name or f"User{user_id}"
                bot.send_message(
                    indicador_id,
                    f"🎉 <b>Nova Indicação!</b>\n\n"
                    f"👤 <b>Usuário:</b> @{username}\n"
                    f"💰 <b>Você ganhou:</b> R$ {valor_indicacao:.2f}\n"
                    f"📊 <b>Seu saldo foi atualizado!</b>",
                    parse_mode='HTML'
                )
            except:
                pass  # Se não conseguir enviar, continua
            
            # Notificar o indicado
            try:
                indicador_username = indicador_data.get('username', f"User{indicador_id}")
                bot.send_message(
                    user_id,
                    f"✅ <b>Bem-vindo!</b>\n\n"
                    f"🎯 Você foi indicado por: @{indicador_username}\n"
                    f"🎁 Aproveite nossos serviços!",
                    parse_mode='HTML'
                )
            except:
                pass
            
            return True
    except:
        pass
    
    return False

# --- FUNÇÃO MODIFICADA (PARA EDITAR MENSAGEM) ---
def comando_meu_link(message, bot):
    """
    Comando para o usuário obter seu link de indicação
    """
    # --- MODIFICAÇÃO: Usar message.chat.id ---
    user_id = message.chat.id
    
    # Verificar se o sistema está ativo
    if not SistemaAfiliados.status_ativo():
        # --- MODIFICAÇÃO: Tentar editar ou enviar ---
        try:
            bot.edit_message_text(
                "❌ <b>Sistema de Afiliados Desativado</b>\n\n"
                "O sistema de indicações está temporariamente desativado.",
                chat_id=user_id,
                message_id=message.message_id,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                user_id,
                "❌ <b>Sistema de Afiliados Desativado</b>\n\n"
                "O sistema de indicações está temporariamente desativado.",
                parse_mode='HTML'
            )
        return
    
    # --- (Lógica de busca de dados permanece a mesma) ---
    bot_username = bot.get_me().username
    link_indicacao = f"https://t.me/{bot_username}?start=ref_{user_id}"
    valor_por_indicacao = SistemaAfiliados.get_valor_indicacao()
    stats = database.get_user_indicacoes(user_id)
    texto = (
        f"🔗 <b>SEU LINK DE INDICAÇÃO</b>\n\n"
        f"📋 <b>Link:</b> <code>{link_indicacao}</code>\n\n"
        f"💰 <b>Valor por indicação:</b> R$ {valor_por_indicacao:.2f}\n"
        f"👥 <b>Total de indicações:</b> {stats['total_indicacoes']}\n"
        f"💵 <b>Total ganho:</b> R$ {stats['total_ganho']:.2f}\n\n"
        f"📢 <b>Como funciona:</b>\n"
        f"• Compartilhe seu link com amigos\n"
        f"• Quando alguém entrar pelo seu link, você ganha R$ {valor_por_indicacao:.2f}\n"
        f"• O valor é adicionado automaticamente ao seu saldo\n\n"
        f"🎯 <b>Dica:</b> Compartilhe em grupos e redes sociais!"
    )
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("📊 Minhas Indicações", callback_data="ver_indicacoes"),
        telebot.types.InlineKeyboardButton("🏆 Ranking", callback_data="ranking_indicadores")
    )
    
    # --- MODIFICAÇÃO: Tentar editar, se falhar, enviar ---
    try:
        bot.edit_message_text(
            text=texto,
            chat_id=user_id,
            message_id=message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=keyboard)
    # --- FIM DA MODIFICAÇÃO ---

# --- FUNÇÃO MODIFICADA (PARA EDITAR MENSAGEM) ---
def comando_minhas_indicacoes(message, bot):
    """
    Comando para ver as indicações do usuário
    """
    # --- MODIFICAÇÃO: Usar message.chat.id ---
    user_id = message.chat.id
    
    # Verificar se o sistema está ativo
    if not SistemaAfiliados.status_ativo():
        # --- MODIFICAÇÃO: Tentar editar ou enviar ---
        try:
            bot.edit_message_text(
                "❌ <b>Sistema de Afiliados Desativado</b>",
                chat_id=user_id,
                message_id=message.message_id,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                user_id,
                "❌ <b>Sistema de Afiliados Desativado</b>",
                parse_mode='HTML'
            )
        return
    
    # --- (Lógica de busca de dados permanece a mesma) ---
    stats = database.get_user_indicacoes(user_id)
    
    if stats['total_indicacoes'] == 0:
        texto = (
            f"📊 <b>SUAS INDICAÇÕES</b>\n\n"
            f"😔 Você ainda não possui indicações.\n\n"
            f"🔗 Use /meulink para obter seu link de indicação!"
        )
    else:
        texto = (
            f"📊 <b>SUAS INDICAÇÕES</b>\n\n"
            f"👥 <b>Total:</b> {stats['total_indicacoes']} indicações\n"
            f"💰 <b>Total ganho:</b> R$ {stats['total_ganho']:.2f}\n\n"
            f"📋 <b>Últimas indicações:</b>\n"
        )
        
        # Mostrar últimas 10 indicações
        indicacoes_recentes = stats['indicacoes'][-10:]
        for i, indicacao in enumerate(indicacoes_recentes, 1):
            user_indicado = database.load_user_data(indicacao['user_id'])
            username = user_indicado.get('username', f"User{indicacao['user_id']}") if user_indicado else f"User{indicacao['user_id']}"
            texto += f"{i}. @{username} - R$ {indicacao['valor_ganho']:.2f} ({indicacao['data']})\n"
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("🔗 Meu Link", callback_data="meu_link"),
        telebot.types.InlineKeyboardButton("🏆 Ranking", callback_data="ranking_indicadores")
    )
    
    # --- MODIFICAÇÃO: Tentar editar, se falhar, enviar ---
    try:
        bot.edit_message_text(
            text=texto,
            chat_id=user_id,
            message_id=message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=keyboard)
    # --- FIM DA MODIFICAÇÃO ---

# --- FUNÇÃO MODIFICADA (PARA EDITAR MENSAGEM E USAR NOMES) ---
def comando_ranking_indicadores(message, bot):
    """
    Comando para ver o ranking de indicadores
    """
    # --- MODIFICAÇÃO: Usar message.chat.id ---
    user_id = message.chat.id
    
    # Verificar se o sistema está ativo
    if not SistemaAfiliados.status_ativo():
        # --- MODIFICAÇÃO: Tentar editar ou enviar ---
        try:
            bot.edit_message_text(
                "❌ <b>Sistema de Afiliados Desativado</b>",
                chat_id=user_id,
                message_id=message.message_id,
                parse_mode='HTML'
            )
        except:
            bot.send_message(
                user_id,
                "❌ <b>Sistema de Afiliados Desativado</b>",
                parse_mode='HTML'
            )
        return
    
    # --- (Lógica de busca de dados permanece a mesma) ---
    top_indicadores = database.get_top_indicadores(10)
    
    if not top_indicadores:
        texto = (
            f"🏆 <b>RANKING DE INDICADORES</b>\n\n"
            f"😔 Ainda não há indicadores no ranking.\n\n"
            f"🔗 Seja o primeiro! Use /meulink"
        )
    else:
        texto = f"🏆 <b>TOP 10 INDICADORES</b>\n\n"
        
        for i, indicador in enumerate(top_indicadores, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            
            # --- CORREÇÃO DE NOME APLICADA ---
            display_name = _get_display_name(bot, indicador)
            
            texto += (
                f"{emoji} <b>{display_name}</b>\n"
                f"   👥 {indicador['total_indicacoes']} indicações | "
                f"💰 R$ {indicador['total_ganho']:.2f}\n\n"
            )
            # --- FIM DA CORREÇÃO DE NOME ---
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("🔗 Meu Link", callback_data="meu_link"),
        telebot.types.InlineKeyboardButton("📊 Minhas Indicações", callback_data="ver_indicacoes")
    )
    
    # --- MODIFICAÇÃO: Tentar editar, se falhar, enviar ---
    try:
        bot.edit_message_text(
            text=texto,
            chat_id=user_id,
            message_id=message.message_id,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except Exception as e:
        if 'message is not modified' not in str(e):
            bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=keyboard)
    # --- FIM DA MODIFICAÇÃO ---


def painel_admin_afiliados(message, bot):
    """
    Painel administrativo para gerenciar o sistema de afiliados
    """
    user_id = message.chat.id
    
    # Verificar se é admin (você deve implementar esta verificação)
    # if not is_admin(user_id):
    #     return
    
    status = "🟢 ATIVO" if SistemaAfiliados.status_ativo() else "🔴 INATIVO"
    valor_indicacao = SistemaAfiliados.get_valor_indicacao()
    
    # Estatísticas gerais
    top_indicadores = database.get_top_indicadores(5)
    total_indicadores = len(top_indicadores)
    
    texto = (
        f"⚙️ <b>PAINEL ADMIN - AFILIADOS</b>\n\n"
        f"📊 <b>Status:</b> {status}\n"
        f"💰 <b>Valor por indicação:</b> R$ {valor_indicacao:.2f}\n"
        f"👥 <b>Total de indicadores:</b> {total_indicadores}\n\n"
        f"🏆 <b>Top 3 Indicadores:</b>\n"
    )
    
    for i, indicador in enumerate(top_indicadores[:3], 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        
        # --- CORREÇÃO DE NOME APLICADA ---
        display_name = _get_display_name(bot, indicador)
        texto += f"{emoji} {display_name} - {indicador['total_indicacoes']} indicações\n"
        # --- FIM DA CORREÇÃO DE NOME ---
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    
    # Botão para ativar/desativar
    status_btn_text = "🔴 Desativar" if SistemaAfiliados.status_ativo() else "🟢 Ativar"
    keyboard.row(
        telebot.types.InlineKeyboardButton(status_btn_text, callback_data="admin_toggle_afiliados")
    )
    
    keyboard.row(
        telebot.types.InlineKeyboardButton("💰 Alterar Valor", callback_data="admin_alterar_valor_indicacao"),
        telebot.types.InlineKeyboardButton("📊 Estatísticas", callback_data="admin_stats_afiliados")
    )
    
    keyboard.row(
        telebot.types.InlineKeyboardButton("🔄 Atualizar", callback_data="admin_refresh_afiliados"),
        telebot.types.InlineKeyboardButton("↩ Voltar", callback_data="voltar_paineladm")
    )
    
    # Editar mensagem existente em vez de enviar nova
    try:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=texto,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except:
        # Se não conseguir editar, envia nova mensagem
        bot.send_message(user_id, texto, parse_mode='HTML', reply_markup=keyboard)

# --- FUNÇÃO MODIFICADA (PARA DE USAR FAKE_MESSAGE) ---
def handle_callback_afiliados(call, bot):
    """
    Handler para callbacks do sistema de afiliados
    """
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data == "ver_indicacoes":
            bot.answer_callback_query(call.id)
            # --- MODIFICAÇÃO: Passar a mensagem real ---
            comando_minhas_indicacoes(call.message, bot)
        
        elif data == "ranking_indicadores":
            bot.answer_callback_query(call.id)
            # --- MODIFICAÇÃO: Passar a mensagem real ---
            comando_ranking_indicadores(call.message, bot)
        
        elif data == "meu_link":
            bot.answer_callback_query(call.id)
            # --- MODIFICAÇÃO: Passar a mensagem real ---
            comando_meu_link(call.message, bot)
        
        elif data == "admin_toggle_afiliados":
            # Verificar se é admin
            from app import central as api
            if not (api.Admin.verificar_admin(user_id) or int(user_id) == int(api.CredentialsChange.id_dono())):
                bot.answer_callback_query(call.id, "❌ Acesso negado!", show_alert=True)
                return
                
            novo_status = SistemaAfiliados.alternar_status()
            status_text = "ativado" if novo_status else "desativado"
            bot.answer_callback_query(call.id, f"Sistema {status_text}!")
            painel_admin_afiliados(call.message, bot)
        
        elif data == "admin_refresh_afiliados":
            bot.answer_callback_query(call.id, "Painel atualizado!")
            painel_admin_afiliados(call.message, bot)
        
        elif data == "admin_alterar_valor_indicacao":
            from app import central as api
            if not (api.Admin.verificar_admin(user_id) or int(user_id) == int(api.CredentialsChange.id_dono())):
                bot.answer_callback_query(call.id, "❌ Acesso negado!", show_alert=True)
                return
                
            bot.answer_callback_query(call.id)
            # Ativar estado para capturar próxima mensagem
            admin_setting_valor_indicacao[user_id] = True
            bot.send_message(
                user_id,
                "💰 <b>Alterar Valor por Indicação</b>\n\n"
                "Digite o novo valor (exemplo: 10.50):",
                parse_mode='HTML'
            )
        
        elif data == "admin_stats_afiliados":
            bot.answer_callback_query(call.id)
            # Mostrar estatísticas detalhadas
            mostrar_estatisticas_detalhadas(call.message, bot)
            
    except Exception as e:
        print(f"Erro no callback afiliados: {e}")
        bot.answer_callback_query(call.id, "❌ Erro interno", show_alert=True)

def mostrar_estatisticas_detalhadas(message, bot):
    """
    Mostra estatísticas detalhadas do sistema de afiliados
    """
    try:
        # Obter todos os indicadores
        top_indicadores = database.get_top_indicadores(20)
        
        if not top_indicadores:
            texto = (
                "📊 <b>ESTATÍSTICAS DETALHADAS</b>\n\n"
                "😔 Ainda não há dados de indicações no sistema."
            )
        else:
            total_indicacoes = sum(ind['total_indicacoes'] for ind in top_indicadores)
            total_pago = sum(ind['total_ganho'] for ind in top_indicadores)
            
            texto = (
                f"📊 <b>ESTATÍSTICAS DETALHADAS</b>\n\n"
                f"👥 <b>Total de indicadores:</b> {len(top_indicadores)}\n"
                f"🎯 <b>Total de indicações:</b> {total_indicacoes}\n"
                f"💰 <b>Total pago em recompensas:</b> R$ {total_pago:.2f}\n"
                f"📈 <b>Média por indicador:</b> {total_indicacoes/len(top_indicadores):.1f} indicações\n\n"
                f"🏆 <b>TOP 10 INDICADORES:</b>\n"
            )
            
            for i, indicador in enumerate(top_indicadores[:10], 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                # --- CORREÇÃO DE NOME APLICADA ---
                display_name = _get_display_name(bot, indicador)
                texto += (
                    f"{emoji} {display_name}\n"
                    f"   👥 {indicador['total_indicacoes']} indicações | "
                    f"💰 R$ {indicador['total_ganho']:.2f}\n"
                )
                # --- FIM DA CORREÇÃO DE NOME ---
        
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("🔄 Atualizar", callback_data="admin_stats_afiliados"),
            telebot.types.InlineKeyboardButton("↩ Voltar", callback_data="admin_refresh_afiliados")
        )
        
        # Editar mensagem existente
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=texto,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except:
            # Se não conseguir editar, envia nova mensagem
            bot.send_message(message.chat.id, texto, parse_mode='HTML', reply_markup=keyboard)
            
    except Exception as e:
        print(f"Erro ao mostrar estatísticas: {e}")
        bot.send_message(message.chat.id, "❌ Erro ao carregar estatísticas.", parse_mode='HTML')