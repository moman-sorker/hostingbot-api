"""
run.py
════════════════════════════════════════════════════════════════════
Enhanced entry point for SARKER Hosting Bot.

Loads:
  • main.py        → original bot (untouched)
  • admin.py       → coder-themed Telegram admin terminal
  • welcome.py     → coder-themed /start message
  • web_panel.py   → Flask web admin panel (SAME process → shared state)

Use this file instead of `python main.py`:

    python run.py
"""

import time
import admin        # noqa: F401  (patches main.show_admin_panel)
import welcome      # noqa: F401  (patches main.send_welcome)
import web_panel    # NEW: web admin panel (Flask)
import group_mode
import main

if __name__ == "__main__":
    print("=" * 56)
    print("  SARKER HOSTING HUB — ENHANCED + WEB CONSOLE")
    print("=" * 56)
    print("  • main.py       : untouched")
    print("  • admin.py      : Telegram admin terminal UI")
    print("  • welcome.py    : /start message UI")
    print("  • web_panel.py  : Web admin panel (Flask)")
    print("  • config.json   : untouched")
    print("=" * 56)

    # Start the web panel FIRST so it's live even if Telegram init is slow.
    try:
        web_panel.start_web_panel()
    except Exception as e:
        print(f"[WebPanel] Failed to start: {type(e).__name__}: {e}")

    try:
        main.bot.remove_webhook()
        time.sleep(1)
        me = main.bot.get_me()
        print(f"[Telegram] Connected as @{getattr(me, 'username', '') or 'unknown'} "
              f"(ID: {getattr(me, 'id', 'unknown')})")
        print("[Telegram] Polling started. Send /start or /admin to your bot.")
    except Exception as e:
        print(f"[Telegram Startup Warning] {type(e).__name__}: {e}")

    while True:
        try:
            main.bot.infinity_polling(timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"[Polling Error] {type(e).__name__}: {e}. Reconnecting in 3s...")
            time.sleep(3)