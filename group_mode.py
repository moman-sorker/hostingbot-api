"""
group_mode.py
════════════════════════════════════════════════════════════════════
Group / Channel support for SARKER Hosting Bot.

Design:
  • Whitelisted group IDs only.
  • Regular users in group → can send /start (bot replies "go to DM").
  • Owner in group → /admin sends admin panel to owner's DM.
  • Everything else in group → silent.
  • DM behavior is completely unchanged.

main.py is NOT modified.
"""

import main
from main import bot, is_admin, cfg

import telebot.types as types


# ────────────────────────────────────────────────────────────────
#  CONFIG
# ────────────────────────────────────────────────────────────────

def _load_allowed_groups():
    """Read allowed_group_ids from config.json (list of negative ints)."""
    raw = cfg("allowed_group_ids", []) or []
    result = set()
    for x in raw:
        try:
            result.add(int(x))
        except Exception:
            pass
    return result


ALLOWED_GROUPS = _load_allowed_groups()


# ────────────────────────────────────────────────────────────────
#  HELPERS
# ────────────────────────────────────────────────────────────────

def _is_allowed_group(chat):
    if chat is None:
        return False
    chat_type = getattr(chat, "type", None)
    if chat_type not in ("group", "supergroup"):
        return False
    return chat.id in ALLOWED_GROUPS


def _bot_username():
    try:
        return bot.get_me().username or "your_bot"
    except Exception:
        return "your_bot"


# ────────────────────────────────────────────────────────────────
#  HANDLERS
# ────────────────────────────────────────────────────────────────

def _install_group_handlers():
    before = len(bot.message_handlers)

    # ── /start in group ──
    @bot.message_handler(
        commands=["start"],
        func=lambda m: _is_allowed_group(m.chat)
    )
    def _group_start(message):
        uname = _bot_username()
        text = (
            "⚡ ꜱᴀʀᴋᴇʀ ʜᴏꜱᴛɪɴɢ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "👋 ᴡᴇʟᴄᴏᴍᴇ!\n\n"
            "ᴛʜɪꜱ ʙᴏᴛ ᴏᴘᴇʀᴀᴛᴇꜱ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ᴏɴʟʏ.\n\n"
            f"👉 ᴏᴘᴇɴ ᴅᴍ: @{uname}\n"
            "ᴛʜᴇɴ ꜱᴇɴᴅ /start ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴀꜱʜʙᴏᴀʀᴅ."
        )
        try:
            bot.reply_to(message, text)
        except Exception as e:
            print(f"[GroupMode] group_start reply failed: {e}")

    @bot.message_handler(func=lambda m: m.chat and m.chat.type in ("group","supergroup"))
    def _debug_group(message):
        print(f"[Debug] Group ID: {message.chat.id} | Title: {message.chat.title}")

    # ── /admin in group ──
    @bot.message_handler(
        commands=["admin"],
        func=lambda m: _is_allowed_group(m.chat)
    )
    def _group_admin(message):
        sender = getattr(message, "from_user", None)
        if sender is None:
            return
        if not is_admin(sender.id):
            try:
                bot.reply_to(message, "⛔ ᴀᴅᴍɪɴ ᴏɴʟʏ.")
            except Exception:
                pass
            return

        # Send the admin panel to the owner's DM, not the group.
        try:
            bot.send_message(
                sender.id,
                "👑 ᴀᴅᴍɪɴ ᴛᴇʀᴍɪɴᴀʟ ᴏᴘᴇɴᴇᴅ ꜰʀᴏᴍ ɢʀᴏᴜᴘ\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "ᴀʟʟ ᴀᴄᴛɪᴏɴꜱ ᴡɪʟʟ ʜᴀᴘᴘᴇɴ ʜᴇʀᴇ ɪɴ ᴅᴍ."
            )
            main.show_admin_panel(sender.id)
        except Exception as e:
            try:
                bot.reply_to(
                    message,
                    "❌ ᴄᴏᴜʟᴅ ɴᴏᴛ ꜱᴇɴᴅ ᴘᴀɴᴇʟ ᴛᴏ ʏᴏᴜʀ ᴅᴍ.\n"
                    "ᴘʟᴇᴀꜱᴇ ᴏᴘᴇɴ ᴀ ᴅᴍ ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ ꜰɪʀꜱᴛ, "
                    "ᴛʜᴇɴ ꜱᴇɴᴅ /admin ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ᴀɢᴀɪɴ."
                )
            except Exception:
                pass
            print(f"[GroupMode] group_admin DM failed: {e}")

    # ── Move new handlers to the FRONT of the list ──
    new = bot.message_handlers[before:]
    old = bot.message_handlers[:before]
    bot.message_handlers = new + old

    print(f"[GroupMode] {len(new)} group handler(s) registered at front.")
    print(f"[GroupMode] Allowed group IDs: {sorted(ALLOWED_GROUPS) or '(none)'}")


# ────────────────────────────────────────────────────────────────
#  INSTALL
# ────────────────────────────────────────────────────────────────

def install():
    _install_group_handlers()
    print("[GroupMode] ✅ Group/channel support installed.")


install()