"""
admin.py
════════════════════════════════════════════════════════════════════
Professional Coder-Themed Animated Admin Panel
for SARKER Hosting Bot.

Extends main.py WITHOUT modifying it.

How it works:
  • Imports main.py (registers all handlers, starts daemon threads).
  • Renders a terminal-style animated admin panel.
  • Overrides ONLY main.show_admin_panel at runtime.
  • All callbacks (admin_force_menu, admin_maintenance, ...) are still
    handled by main.py's original callback_listener — nothing changed.
"""

import os
import sys
import time
import threading
import shutil

import main

from main import (
    bot,
    cfg,
    is_admin,
    load_meta,
    styled_button,
    bot_send_message,
    bot_edit_message,
    get_force_channels,
    report_enabled,
    active_project_count,
    get_project_status,
    project_is_expired,
    BOT_STARTED_AT,
)

try:
    import psutil
except ImportError:
    psutil = None

import telebot.types as types


# ────────────────────────────────────────────────────────────────
#  UI CONSTANTS
# ────────────────────────────────────────────────────────────────

BAR_WIDTH  = 10
BAR_FILLED = "▰"
BAR_EMPTY  = "▱"

SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

SEP_THICK = "━" * 34

BOOT_STEPS = [
    "[ 0.000 ] boot: initializing admin terminal",
    "[ 0.042 ] kernel: loading modules",
    "[ 0.091 ] fs: mounting virtual storage",
    "[ 0.145 ] net: verifying telegram channel",
    "[ 0.203 ] auth: validating owner token",
    "[ 0.267 ] ui: rendering console",
    "[ 0.312 ] done.",
]


# ────────────────────────────────────────────────────────────────
#  HELPERS
# ────────────────────────────────────────────────────────────────

def _bar(percent, width=BAR_WIDTH):
    try:
        p = max(0.0, min(100.0, float(percent)))
    except Exception:
        p = 0.0
    filled = int(round(width * p / 100.0))
    return BAR_FILLED * filled + BAR_EMPTY * (width - filled)


def _uptime_str(seconds):
    seconds = max(0, int(seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h:02d}h {m:02d}m"
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def _bool_dot(flag):
    return "🟢" if flag else "🔴"


# ────────────────────────────────────────────────────────────────
#  LIVE STATS COLLECTORS
# ────────────────────────────────────────────────────────────────

def _collect_system_stats():
    data = {
        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
        "free_gb": 0.0, "total_gb": 0.0,
        "load": "N/A",
        "pid": os.getpid(),
        "threads": threading.active_count(),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "bot_uptime": time.time() - BOT_STARTED_AT,
    }
    if psutil:
        try:
            data["cpu"] = round(psutil.cpu_percent(interval=None), 1)
        except Exception:
            pass
        try:
            data["ram"] = round(psutil.virtual_memory().percent, 1)
        except Exception:
            pass
        try:
            du = shutil.disk_usage("/")
            data["disk"] = round((du.used / du.total) * 100, 1) if du.total else 0.0
            data["free_gb"] = round(du.free / (1024 ** 3), 2)
            data["total_gb"] = round(du.total / (1024 ** 3), 2)
        except Exception:
            pass
        try:
            data["load"] = f"{os.getloadavg()[0]:.2f}"
        except Exception:
            pass
    return data


def _collect_hosting_stats():
    meta = load_meta()
    projects = {
        k: v for k, v in meta.items()
        if not str(k).startswith("_") and isinstance(v, dict)
    }
    settings = meta.get("_settings", {}) if isinstance(meta.get("_settings", {}), dict) else {}
    registry = settings.get("users", {}) if isinstance(settings.get("users", {}), dict) else {}

    project_user_ids = {
        str(v.get("chat_id")) for v in projects.values()
        if v.get("chat_id") is not None
    }
    total_users = len(set(registry.keys()) | project_user_ids)

    running = crashed = expired = 0
    for pid, pdata in projects.items():
        try:
            status = get_project_status(pid, pdata)
            if status.startswith("🟢"):
                running += 1
            elif "CRASHED" in status:
                crashed += 1
            if project_is_expired(pdata):
                expired += 1
        except Exception:
            pass

    queued = len(settings.get("start_queue", []) or [])

    return {
        "users": total_users,
        "projects": len(projects),
        "running": running,
        "crashed": crashed,
        "expired": expired,
        "queued": queued,
        "active": active_project_count(),
        "max_concurrent": int(cfg("max_concurrent_projects", 8)),
    }


# ────────────────────────────────────────────────────────────────
#  PANEL RENDERER
# ────────────────────────────────────────────────────────────────

def render_panel():
    s = _collect_system_stats()
    h = _collect_hosting_stats()

    maintenance   = bool(cfg("maintenance_mode", False))
    deploy        = bool(cfg("deploy_enabled", True))
    auto_restart  = bool(cfg("auto_restart_default", True))
    queue         = bool(cfg("queue_enabled", True))
    force_targets = len(get_force_channels())
    report        = report_enabled()

    L = []
    L.append(SEP_THICK)
    L.append("  ⚡ SARKER — ADMIN TERMINAL v2.0")
    L.append(SEP_THICK)
    L.append("")
    L.append("  `$ sudo system --status --verbose`")
    L.append("")
    L.append("  ◆ RESOURCES")
    L.append(f"    CPU   `{_bar(s['cpu'])}`  {s['cpu']:>5}%")
    L.append(f"    RAM   `{_bar(s['ram'])}`  {s['ram']:>5}%")
    L.append(f"    DISK  `{_bar(s['disk'])}`  {s['disk']:>5}%")
    L.append(f"    FREE  {s['free_gb']} GB / {s['total_gb']} GB")
    L.append(f"    LOAD  {s['load']}")
    L.append("")
    L.append("  ◆ RUNTIME")
    L.append(f"    Uptime   : {_uptime_str(s['bot_uptime'])}")
    L.append(f"    PID      : {s['pid']}")
    L.append(f"    Threads  : {s['threads']}")
    L.append(f"    Python   : {s['python']}")
    L.append("")
    L.append("  ◆ HOSTING METRICS")
    L.append(f"    Users     : {h['users']}")
    L.append(f"    Projects  : {h['projects']}")
    L.append(f"    Running   : {h['running']}")
    L.append(f"    Crashed   : {h['crashed']}")
    L.append(f"    Expired   : {h['expired']}")
    L.append(f"    Queued    : {h['queued']}")
    L.append(f"    Capacity  : {h['active']} / {h['max_concurrent']}")
    L.append("")
    L.append("  ◆ STATUS")
    L.append(f"    {_bool_dot(not maintenance)} Maintenance  : {'ON' if maintenance else 'OFF'}")
    L.append(f"    {_bool_dot(deploy)} Deploy       : {'ON' if deploy else 'OFF'}")
    L.append(f"    {_bool_dot(auto_restart)} AutoRestart  : {'ON' if auto_restart else 'OFF'}")
    L.append(f"    {_bool_dot(queue)} Queue        : {'ON' if queue else 'OFF'}")
    L.append(f"    {_bool_dot(force_targets > 0)} ForceJoin    : {force_targets} target(s)")
    L.append(f"    {_bool_dot(report)} ReportGroup  : {'ON' if report else 'OFF'}")
    L.append("")
    L.append(SEP_THICK)
    L.append("  > select a module below")
    return "\n".join(L)


def build_panel_markup():
    m = types.InlineKeyboardMarkup(row_width=2)

    maintenance_label = (
        "🛡️ MAINTENANCE • ON"
        if bool(cfg("maintenance_mode", False))
        else "🛡️ MAINTENANCE • OFF"
    )
    deploy_label = (
        "🚀 DEPLOY • ON"
        if bool(cfg("deploy_enabled", True))
        else "🚀 DEPLOY • OFF"
    )

    m.add(
        styled_button("📡 JOIN CONTROL",  callback_data="admin_force_menu"),
        styled_button(maintenance_label,  callback_data="admin_maintenance"),
    )
    m.add(
        styled_button(deploy_label,       callback_data="admin_deploy_toggle"),
        styled_button("♻️ AUTO RESTART",  callback_data="admin_autorestart_default"),
    )
    m.add(
        styled_button("👤 USER LIMITS",   callback_data="admin_limit"),
        styled_button("⌛ DEFAULT TIME",  callback_data="admin_days"),
    )
    m.add(
        styled_button("📊 SYSTEM STATS",  callback_data="admin_stats"),
        styled_button("🧠 START QUEUE",   callback_data="admin_queue"),
    )
    m.add(
        styled_button("⏳ EXPIRY GRACE",  callback_data="admin_grace"),
        styled_button("👥 MANAGE USERS",  callback_data="admin_user_control"),
    )
    m.add(
        styled_button("📢 BROADCAST",     callback_data="admin_broadcast_menu"),
        styled_button("📬 NOTIFY GROUP",  callback_data="admin_report_menu"),
    )
    m.add(
        styled_button("📥 JSON STORE",    callback_data="admin_download_json",
                      style="success"),
    )
    m.add(
        styled_button("🚫 SUSPEND USER",  callback_data="admin_suspend_user",
                      style="danger"),
        styled_button("🧹 CLEAR EXPIRED", callback_data="admin_cleanup"),
    )
    m.add(
        styled_button("↻ REFRESH",        callback_data="admin_panel"),
        styled_button("⌂ MAIN MENU",      callback_data="btn_back_home"),
    )
    return m


# ────────────────────────────────────────────────────────────────
#  ANIMATION HELPERS
# ────────────────────────────────────────────────────────────────

def _play_boot(chat_id, message_id):
    if not bool(cfg("dynamic_animation_enabled", True)):
        return

    shown = []
    for idx, step in enumerate(BOOT_STEPS):
        shown.append(step)
        pct = int(((idx + 1) / len(BOOT_STEPS)) * 100)
        body = "\n".join(shown)
        try:
            bot_edit_message(
                "╔═══════════════════════════════════╗\n"
                "║  ⚡ ADMIN TERMINAL BOOT SEQUENCE  ║\n"
                "╚═══════════════════════════════════╝\n\n"
                f"```\n{body}\n```\n"
                f"`{_bar(pct, 10)}`  {pct}%",
                chat_id, message_id,
                parse_mode="Markdown",
            )
            time.sleep(0.16)
        except Exception:
            pass


def _flash_refresh(chat_id, message_id):
    if not bool(cfg("dynamic_animation_enabled", True)):
        return
    for frame in SPINNER[:4]:
        try:
            bot_edit_message(
                f"`{frame}`  refreshing panel...",
                chat_id, message_id, parse_mode="Markdown",
            )
            time.sleep(0.07)
        except Exception:
            break


# ────────────────────────────────────────────────────────────────
#  PUBLIC ENTRYPOINT — drop-in replacement
# ────────────────────────────────────────────────────────────────

def show_admin_panel(chat_id, message_id=None):
    """
    Signature matches main.show_admin_panel(chat_id, message_id=None)
    so it can be installed as a drop-in replacement.
    """
    if not is_admin(chat_id):
        return

    if message_id is None:
        try:
            msg = bot_send_message(
                chat_id,
                "```\n$ booting admin terminal...\n```",
                parse_mode="Markdown",
            )
            _play_boot(chat_id, msg.message_id)
            bot_edit_message(
                render_panel(),
                chat_id, msg.message_id,
                parse_mode="Markdown",
                reply_markup=build_panel_markup(),
            )
        except Exception as e:
            print(f"[Admin] first render failed: {e}")
        return

    _flash_refresh(chat_id, message_id)
    try:
        bot_edit_message(
            render_panel(),
            chat_id, message_id,
            parse_mode="Markdown",
            reply_markup=build_panel_markup(),
        )
    except Exception as e:
        print(f"[Admin] refresh failed: {e}")


# ────────────────────────────────────────────────────────────────
#  INSTALL PATCH (auto-runs on import)
# ────────────────────────────────────────────────────────────────

def install():
    main.show_admin_panel = show_admin_panel
    print("[Admin] ✅ Enhanced coder-themed admin panel installed.")


install()