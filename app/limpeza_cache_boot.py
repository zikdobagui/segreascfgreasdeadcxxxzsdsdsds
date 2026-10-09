import sys
import time

def limpar_cache_boot(bot=None, admin_id=None):
    """
    Limpa os caches em memória no momento do boot e atualiza o admin em tempo real.
    """
    texto_status = "🧹 <b>Iniciando limpeza de cache do sistema...</b>\n\n"
    msg_id = None
    
    print("[LIMPEZA CACHE] Iniciando limpeza de caches do boot...")
    
    # Se recebeu o bot e o ID do admin, envia a primeira mensagem no Telegram
    if bot and admin_id:
        try:
            msg = bot.send_message(admin_id, texto_status, parse_mode='HTML')
            msg_id = msg.message_id
        except Exception as e:
            print(f"[LIMPEZA CACHE] Não foi possível enviar mensagem ao admin: {e}")

    bot_module = sys.modules.get('app.bot')
    
    if bot_module:
        caches_para_limpar = [
            'ultimo_menu',
            'user_access_notifications',
            'user_carts',
            'user_cart_msgs',
            'cart_timers',
            'pending_reminders',
            'username_cache',
            'admin_massa_temp'
        ]
        
        for nome_cache in caches_para_limpar:
            if hasattr(bot_module, nome_cache):
                try:
                    cache = getattr(bot_module, nome_cache)
                    if isinstance(cache, dict):
                        cache.clear()
                        log_linha = f"✅ Cache <code>{nome_cache}</code> limpo."
                        print(f" -> {log_linha}")
                        
                        # Atualiza a mensagem no Telegram em tempo real
                        if bot and admin_id and msg_id:
                            texto_status += log_linha + "\n"
                            try:
                                bot.edit_message_text(texto_status, chat_id=admin_id, message_id=msg_id, parse_mode='HTML')
                                time.sleep(0.3) # Efeito de carregamento em tempo real
                            except:
                                pass
                except Exception as e:
                    print(f" -> Erro ao limpar '{nome_cache}': {e}")

        # Limpar o cache de estatísticas do admin
        if hasattr(bot_module, 'admin_stats_cache'):
            try:
                bot_module.admin_stats_cache['data'] = None
                bot_module.admin_stats_cache['timestamp'] = 0
                log_linha = "✅ Cache <code>admin_stats_cache</code> limpo."
                print(f" -> {log_linha}")
                
                if bot and admin_id and msg_id:
                    texto_status += log_linha + "\n"
                    try:
                        bot.edit_message_text(texto_status, chat_id=admin_id, message_id=msg_id, parse_mode='HTML')
                        time.sleep(0.3)
                    except:
                        pass
            except Exception as e:
                print(f" -> Erro ao limpar 'admin_stats_cache': {e}")
                
    print("[LIMPEZA CACHE] Limpeza de boot concluída.")
    
    # Mensagem final no Telegram
    if bot and admin_id and msg_id:
        texto_status += "\n🚀 <b>Limpeza concluída com sucesso! Iniciando sistema...</b>"
        try:
            bot.edit_message_text(texto_status, chat_id=admin_id, message_id=msg_id, parse_mode='HTML')
        except:
            pass
