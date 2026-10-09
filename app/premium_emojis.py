"""Suporte centralizado a emojis premium/custom emoji do Telegram.

Edite somente o arquivo ``premium_emojis.json`` para trocar os IDs dos emojis
premium. Exemplo de entrada:

    "🛒": {
      "fallback": "🛒",
      "custom_emoji_id": "5312361253610475399"
    }

O módulo aplica duas estratégias diferentes, conforme o local:

* Mensagens HTML: troca o emoji por ``<tg-emoji emoji-id="...">fallback</tg-emoji>``.
* Botões: usa o campo oficial ``icon_custom_emoji_id`` em ``InlineKeyboardButton``
  e ``KeyboardButton``. Esse campo foi adicionado no Bot API 9.4. Como o projeto
  usa pyTelegramBotAPI 4.12.0, que ainda não serializa esse campo, este módulo
  adiciona compatibilidade por monkey patch em ``to_dict()``.
"""

from __future__ import annotations

import html as _html
import json
import os
import re
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "premium_emojis.json")

_CONFIG_CACHE: Dict[str, Any] | None = None
_CONFIG_MTIME: float | None = None
_EMOJI_PATTERN: re.Pattern[str] | None = None
_INSTALLED = False

_TG_EMOJI_TAG_RE = re.compile(r"<tg-emoji\b[^>]*>.*?</tg-emoji>", flags=re.IGNORECASE | re.DOTALL)


def _load_config() -> Dict[str, Any]:
    """Carrega o JSON e atualiza cache se o arquivo foi alterado."""
    global _CONFIG_CACHE, _CONFIG_MTIME, _EMOJI_PATTERN
    try:
        mtime = os.path.getmtime(CONFIG_PATH)
    except OSError:
        return {"enabled": False, "emojis": {}}

    if _CONFIG_CACHE is not None and _CONFIG_MTIME == mtime:
        return _CONFIG_CACHE

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as exc:
        print(f"[premium_emojis] Erro ao ler {CONFIG_PATH}: {exc}")
        cfg = {"enabled": False, "emojis": {}}

    emojis = cfg.get("emojis", {}) if isinstance(cfg.get("emojis", {}), dict) else {}
    keys = [k for k, v in emojis.items() if isinstance(k, str) and k and isinstance(v, dict)]
    keys.sort(key=len, reverse=True)
    _EMOJI_PATTERN = re.compile("|".join(re.escape(k) for k in keys)) if keys else None
    _CONFIG_CACHE = cfg
    _CONFIG_MTIME = mtime
    return cfg


def _valid_custom_id(value: Any) -> str:
    value = str(value or "").strip()
    return value if value.isdigit() else ""


def _emoji_data(emoji: str) -> Dict[str, Any]:
    cfg = _load_config()
    data = cfg.get("emojis", {}).get(emoji, {})
    return data if isinstance(data, dict) else {}


def custom_emoji_id(emoji: str) -> str:
    """Retorna o custom_emoji_id configurado para um emoji, ou string vazia."""
    return _valid_custom_id(_emoji_data(emoji).get("custom_emoji_id"))


def _emoji_html(emoji: str) -> str:
    data = _emoji_data(emoji)
    fallback = str(data.get("fallback") or emoji)
    cid = _valid_custom_id(data.get("custom_emoji_id"))
    if cid:
        return f'<tg-emoji emoji-id="{cid}">{_html.escape(fallback)}</tg-emoji>'
    return fallback


def _emoji_fallback(emoji: str) -> str:
    data = _emoji_data(emoji)
    return str(data.get("fallback") or emoji)


def _replace_outside_existing_tags(text: str, replace_segment: Callable[[str], str]) -> str:
    """Evita processar novamente emojis já convertidos em tags <tg-emoji>."""
    if "<tg-emoji" not in text.lower():
        return replace_segment(text)
    parts = []
    pos = 0
    for match in _TG_EMOJI_TAG_RE.finditer(text):
        parts.append(replace_segment(text[pos:match.start()]))
        parts.append(match.group(0))
        pos = match.end()
    parts.append(replace_segment(text[pos:]))
    return "".join(parts)


def replace_emojis(text: Any, context: str = "message") -> Any:
    """Substitui emojis configurados por HTML premium em mensagens ou fallback em botões."""
    if not isinstance(text, str) or not text:
        return text
    cfg = _load_config()
    if not cfg.get("enabled", True):
        return text
    if context == "button" and not cfg.get("apply_to_buttons", True):
        return text
    if context == "message" and not cfg.get("apply_to_html_messages", True):
        return text
    pattern = _EMOJI_PATTERN
    if not pattern:
        return text

    if context == "button":
        return pattern.sub(lambda m: _emoji_fallback(m.group(0)), text)

    def repl(segment: str) -> str:
        return pattern.sub(lambda m: _emoji_html(m.group(0)), segment)

    return _replace_outside_existing_tags(text, repl)


def html_emoji(emoji: str) -> str:
    """Retorna manualmente o HTML premium de um emoji configurado."""
    return _emoji_html(emoji)


def button_emoji(emoji: str) -> str:
    """Retorna o fallback textual seguro para botões."""
    return _emoji_fallback(emoji)


def _find_button_icon(text: Any) -> Tuple[str, str]:
    """Localiza o primeiro emoji do texto que tem custom_emoji_id configurado.

    Retorna ``(emoji_unicode, custom_emoji_id)``. O Bot API aceita apenas um ícone
    premium por botão via ``icon_custom_emoji_id``; por isso usamos o primeiro
    emoji configurado encontrado no texto do botão.
    """
    if not isinstance(text, str) or not text:
        return "", ""
    cfg = _load_config()
    if not cfg.get("enabled", True) or not cfg.get("apply_to_buttons", True):
        return "", ""
    if not cfg.get("button_icon_custom_emoji", True):
        return "", ""
    pattern = _EMOJI_PATTERN
    if not pattern:
        return "", ""
    for match in pattern.finditer(text):
        emoji = match.group(0)
        cid = custom_emoji_id(emoji)
        if cid:
            return emoji, cid
    return "", ""


def _normalize_button_text(text: Any, icon_emoji: str = "") -> Any:
    """Normaliza o texto do botão e remove o emoji que virou ícone premium.

    Quando ``remove_icon_emoji_from_button_text`` está ativo, o emoji usado como
    ``icon_custom_emoji_id`` sai do texto para evitar duplicação visual. Se outros
    emojis sem ID existirem no botão, continuam como fallback Unicode.
    """
    if not isinstance(text, str) or not text:
        return text
    cfg = _load_config()
    result = replace_emojis(text, context="button")
    if icon_emoji and cfg.get("remove_icon_emoji_from_button_text", True):
        fallback = _emoji_fallback(icon_emoji)
        result = result.replace(fallback, "", 1)
        result = " ".join(result.split())
    return result


def _get_arg(args: Tuple[Any, ...], kwargs: Dict[str, Any], index: int, name: str) -> Any:
    if name in kwargs:
        return kwargs[name]
    if index >= 0 and len(args) > index:
        return args[index]
    return None


def _set_arg(args: Tuple[Any, ...], kwargs: Dict[str, Any], index: int, name: str, value: Any) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    if name in kwargs:
        kwargs[name] = value
        return args, kwargs
    if index >= 0 and len(args) > index:
        args_list = list(args)
        args_list[index] = value
        return tuple(args_list), kwargs
    kwargs[name] = value
    return args, kwargs


def _is_html_parse_mode(parse_mode: Any) -> bool:
    return isinstance(parse_mode, str) and parse_mode.lower() == "html"


def _can_auto_html(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    # Evita quebrar mensagens que já contenham markup ou caracteres que exigem escape em HTML.
    return "<" not in text and ">" not in text and "&" not in text


def _wrap_text_method(original: Callable[..., Any], text_index: int, text_name: str, parse_index: int = -1) -> Callable[..., Any]:
    @wraps(original)
    def wrapper(self, *args, **kwargs):
        text = _get_arg(args, kwargs, text_index, text_name)
        cfg = _load_config()
        parse_mode = _get_arg(args, kwargs, parse_index, "parse_mode") if parse_index >= 0 else kwargs.get("parse_mode")
        effective_parse_mode = parse_mode or getattr(self, "parse_mode", None)

        should_replace = _is_html_parse_mode(effective_parse_mode)
        if not should_replace and cfg.get("auto_html_parse_mode", False) and _can_auto_html(text):
            should_replace = True
            if parse_index >= 0:
                args, kwargs = _set_arg(args, kwargs, parse_index, "parse_mode", "HTML")
            else:
                kwargs.setdefault("parse_mode", "HTML")

        if should_replace:
            args, kwargs = _set_arg(args, kwargs, text_index, text_name, replace_emojis(text, context="message"))
        return original(self, *args, **kwargs)
    return wrapper


def _wrap_button_init(original: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(original)
    def wrapper(self, *args, **kwargs):
        explicit_icon = _valid_custom_id(kwargs.pop("icon_custom_emoji_id", ""))
        text = _get_arg(args, kwargs, 0, "text")
        icon_emoji, detected_icon = _find_button_icon(text)
        icon_id = explicit_icon or detected_icon
        normalized_text = _normalize_button_text(text, icon_emoji if detected_icon else "")
        args, kwargs = _set_arg(args, kwargs, 0, "text", normalized_text)
        original(self, *args, **kwargs)
        if icon_id:
            setattr(self, "icon_custom_emoji_id", icon_id)
        return None
    return wrapper


def _wrap_button_to_dict(original: Callable[..., Dict[str, Any]]) -> Callable[..., Dict[str, Any]]:
    @wraps(original)
    def wrapper(self, *args, **kwargs):
        data = original(self, *args, **kwargs)
        icon_id = _valid_custom_id(getattr(self, "icon_custom_emoji_id", ""))
        if icon_id:
            data["icon_custom_emoji_id"] = icon_id
        return data
    return wrapper


def install() -> None:
    """Instala patches globais no pyTelegramBotAPI."""
    global _INSTALLED
    if _INSTALLED:
        return
    try:
        import telebot
        from telebot import types
    except Exception as exc:
        print(f"[premium_emojis] pyTelegramBotAPI não disponível: {exc}")
        return

    # Métodos com texto principal.
    telebot.TeleBot.send_message = _wrap_text_method(telebot.TeleBot.send_message, 1, "text", 2)
    telebot.TeleBot.edit_message_text = _wrap_text_method(telebot.TeleBot.edit_message_text, 0, "text", 4)

    # Métodos comuns com caption. Os índices seguem as assinaturas do pyTelegramBotAPI 4.x.
    for method_name, caption_index, parse_index in (
        ("send_photo", 2, 5),
        ("send_document", 2, 5),
        ("send_video", 2, 5),
        ("send_animation", 2, 5),
        ("edit_message_caption", 0, 4),
    ):
        original = getattr(telebot.TeleBot, method_name, None)
        if original is not None and not getattr(original, "_premium_emoji_text_wrapped", False):
            wrapped = _wrap_text_method(original, caption_index, "caption", parse_index)
            setattr(wrapped, "_premium_emoji_text_wrapped", True)
            setattr(telebot.TeleBot, method_name, wrapped)

    # InlineKeyboardButton e KeyboardButton: suporte ao campo icon_custom_emoji_id.
    for class_name in ("InlineKeyboardButton", "KeyboardButton"):
        cls = getattr(types, class_name, None)
        if cls is None:
            continue
        if hasattr(cls, "__init__") and not getattr(cls.__init__, "_premium_emoji_button_wrapped", False):
            wrapped_init = _wrap_button_init(cls.__init__)
            setattr(wrapped_init, "_premium_emoji_button_wrapped", True)
            cls.__init__ = wrapped_init
        if hasattr(cls, "to_dict") and not getattr(cls.to_dict, "_premium_emoji_to_dict_wrapped", False):
            wrapped_to_dict = _wrap_button_to_dict(cls.to_dict)
            setattr(wrapped_to_dict, "_premium_emoji_to_dict_wrapped", True)
            cls.to_dict = wrapped_to_dict

    _INSTALLED = True
    print("[premium_emojis] Sistema de emojis premium carregado com suporte a icon_custom_emoji_id nos botões.")
