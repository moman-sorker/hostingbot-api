"""
welcome.py
════════════════════════════════════════════════════════════════════
Professional Coder-Themed /start Message
for SARKER Hosting Bot.

Extends main.py WITHOUT modifying it.

NOTE about handler order:
  main.py registers a catch-all handler
  (`@bot.message_handler(func=lambda m: True)`) AFTER /start.
  Since Telegram dispatches to the FIRST matching handler only,
  we must replace the /start function IN-PLACE rather than
  removing and re-appending — otherwise /start lands after the
  catch-all and never fires.
"""

import re
import main
from main import (
    bot,
    cfg,
    is_admin,
    is_private_chat,
    register_user_profile,
    force_join_check,
    get_user_limit,
    get_project_status,
    load_meta,
    styled_button,
    bot_send_message,
)
import telebot.types as types


# ──────────────── HELPERS ────────────────

def _safe_name(name, fallback="user"):
    """Strip chars that could break Telegram legacy Markdown."""
    text = str(name or "").strip()
    text = re.sub(r"[`*_\[\]]", "", text)
    text = text[:20].strip()
    return text or fallback


def _build_welcome_text(name, project_count, running, limit_str, user_id):
    is_adm = is_admin(user_id)
    role = "👑 ADMIN" if is_adm else "👤 USER"

    lines = [
        "⚡  SARKER HOSTING CONSOLE",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
        f"$ login --user {name}",
        "$ status --user",
        "",
        f"  ◆ Projects  : {project_count} / {limit_str}",
        f"  ◆ Running   : {running}",
        "  ◆ Service   : 🟢 ONLINE",
        "  ◆ Access    : 🔒 PRIVATE",
        f"  ◆ Role      : {role}",
        "",
        "$ capabilities --list",
        "",
        "  › deploy     push a new project",
        "  › files      browse & edit code",
        "  › logs       live terminal feed",
        "  › monitor    cpu · ram · uptime",
        "  › backup     export project zip",
    ]
    if is_adm:
        lines.append("  › admin      open control terminal")

    lines.extend([
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "> select a module below.",
    ])
    return "\n".join(lines)


def _build_welcome_markup(user_id):
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        styled_button("🚀 ᴅᴇᴘʟᴏʏ ɴᴇᴡ",    callback_data="btn_deploy"),
        styled_button("📁 ᴍʏ ᴘʀᴏᴊᴇᴄᴛꜱ",   callback_data="btn_my_files"),
    )
    m.add(
        styled_button("🖥️ ꜱᴇʀᴠᴇʀ ꜱᴛᴀᴛᴜꜱ", callback_data="btn_server_status"),
        styled_button("💡 ʜᴇʟᴘ",            callback_data="btn_help"),
    )
    if is_admin(user_id):
        m.add(styled_button("👑 ᴀᴅᴍɪɴ ᴛᴇʀᴍɪɴᴀʟ", callback_data="admin_panel"))
    return m


# ──────────────── REPLACEMENT send_welcome ────────────────

def enhanced_welcome(message):
    if not is_private_chat(message.chat):
        return

    chat_id = message.chat.id
    user_id = chat_id  # private chat: chat_id == user_id

    sender = getattr(message, "from_user", None)
    if sender is not None and getattr(sender, "id", None) == chat_id:
        try:
            register_user_profile(sender)
        except Exception:
            pass

    if not force_join_check(chat_id, user_id):
        return

    if bool(cfg("maintenance_mode", False)) and not is_admin(user_id):
        bot_send_message(
            chat_id,
            "🛠  ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "The service is being updated.\n"
            "Please check back shortly.",
        )
        return

    meta = load_meta()
    user_projects = [
        k for k, v in meta.items()
        if isinstance(v, dict) and v.get("chat_id") == chat_id
    ]

    running = 0
    for pid in user_projects:
        try:
            if get_project_status(pid, meta[pid]).startswith("🟢"):
                running += 1
        except Exception:
            pass

    raw_name = ""
    if sender is not None:
        raw_name = getattr(sender, "first_name", "") or ""
    name = _safe_name(raw_name, fallback="user")

    limit = get_user_limit(chat_id)
    limit_str = "∞" if limit == float("inf") else str(limit)

    text = _build_welcome_text(name, len(user_projects), running, limit_str, user_id)
    markup = _build_welcome_markup(user_id)

    bot_send_message(chat_id, text, reply_markup=markup)


# ──────────────── IN-PLACE /start HANDLER REPLACEMENT ────────────────

def _install_start_handler():
    """
    Replace the /start handler's FUNCTION in-place, preserving its
    position in bot.message_handlers.

    Why in-place: main.py registers a catch-all handler
    (@bot.message_handler(func=lambda m: True)) AFTER /start.
    If we remove + re-append /start, it lands after the catch-all
    and never fires.
    """
    replaced = 0
    for h in getattr(bot, "message_handlers", []):
        try:
            filters = h.get("filters") or {}
            cmds = filters.get("commands") or []
            if "start" in cmds:
                h["function"] = enhanced_welcome
                replaced += 1
        except Exception:
            pass

    if replaced == 0:
        @bot.message_handler(commands=["start"], func=lambda m: is_private_chat(m.chat))
        def _start_handler(message):
            enhanced_welcome(message)
        print("[Welcome] ⚠️ No existing /start handler found — registered new one.")

    print(f"[Welcome] /start handler replaced in-place ({replaced})")


# ──────────────── INSTALL PATCHES ────────────────

def install():
    _install_start_handler()
    main.send_welcome = enhanced_welcome
    print("[Welcome] ✅ Enhanced /start message installed.")


install()