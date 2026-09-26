"""
web_panel.py
════════════════════════════════════════════════════════════════════
Web Admin Panel for SARKER Hosting Bot.

Runs Flask in a DAEMON THREAD inside the SAME process as the bot,
so it shares main.active_processes, projects_meta.json, and CONFIG.

Result: Telegram panel & Web panel are ALWAYS in sync (same memory).

main.py is NOT modified.
"""

import os
import time
import json
import shutil
import functools
import threading

try:
    from flask import (
        Flask, request, session, redirect, url_for,
        jsonify, render_template_string,
    )
    FLASK_OK = True
except ImportError:
    Flask = None
    FLASK_OK = False

import main
from main import (
    cfg,
    load_meta,
    save_meta,
    set_cfg,
    stop_project_process,
    request_project_start,
    get_project_status,
    process_resource_stats,
    active_processes,
    report_enabled,
    get_force_channels,
    BOT_STARTED_AT,
)

try:
    import psutil
except ImportError:
    psutil = None


# ────────────────────────────────────────────────────────────────
#  CONFIG
# ────────────────────────────────────────────────────────────────

WEB_HOST     = os.getenv("WEB_PANEL_HOST") or str(cfg("web_panel_host", "0.0.0.0"))
WEB_PORT     = int(os.getenv("WEB_PANEL_PORT") or cfg("web_panel_port", 12549))
WEB_PASSWORD = os.getenv("WEB_PANEL_PASSWORD") or str(cfg("web_panel_password", "sarker123"))
WEB_SECRET   = os.getenv("WEB_PANEL_SECRET") or "sarker-hosting-change-me-please"


# ────────────────────────────────────────────────────────────────
#  APP
# ────────────────────────────────────────────────────────────────

if FLASK_OK:
    app = Flask(__name__)
    app.secret_key = WEB_SECRET


def login_required(f):
    @functools.wraps(f)
    def wrap(*a, **kw):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrap


# ────────────────────────────────────────────────────────────────
#  STATS HELPERS
# ────────────────────────────────────────────────────────────────

def _system_stats():
    s = {
        "cpu": 0.0, "ram": 0.0, "disk": 0.0,
        "uptime": time.time() - BOT_STARTED_AT,
        "pid": os.getpid(),
        "threads": threading.active_count(),
    }
    if psutil:
        try:
            s["cpu"] = round(psutil.cpu_percent(interval=None), 1)
        except Exception:
            pass
        try:
            s["ram"] = round(psutil.virtual_memory().percent, 1)
        except Exception:
            pass
        try:
            du = shutil.disk_usage("/")
            s["disk"] = round((du.used / du.total) * 100, 1) if du.total else 0.0
        except Exception:
            pass
    return s


def _projects_payload():
    meta = load_meta()
    rows = []
    running_count = 0
    for pid, pdata in meta.items():
        if str(pid).startswith("_") or not isinstance(pdata, dict):
            continue
        try:
            status = get_project_status(pid, pdata)
        except Exception:
            status = "🔴 STOPPED"
        if status.startswith("🟢"):
            running_count += 1
        try:
            cpu, ram, up = process_resource_stats(pid)
        except Exception:
            cpu, ram, up = 0.0, 0.0, 0
        rows.append({
            "id": pid,
            "name": pdata.get("name", pid),
            "chat_id": pdata.get("chat_id"),
            "user_name": pdata.get("user_name", "Unknown"),
            "username": pdata.get("username", ""),
            "main_file": pdata.get("main_file") or "",
            "port": pdata.get("port") or "",
            "status": status,
            "cpu": cpu,
            "ram": ram,
            "uptime": up,
            "auto_restart": bool(pdata.get("auto_restart", False)),
        })
    rows.sort(key=lambda r: (not r["status"].startswith("🟢"), r["name"].lower()))
    return rows, running_count


# ────────────────────────────────────────────────────────────────
#  ROUTES — AUTH
# ────────────────────────────────────────────────────────────────

if FLASK_OK:

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = ""
        if request.method == "POST":
            if request.form.get("password") == WEB_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("dashboard"))
            error = "Access denied."
        return render_template_string(LOGIN_HTML, error=error)


    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))


    @app.route("/")
    @login_required
    def dashboard():
        return render_template_string(DASHBOARD_HTML)


    # ──────────── ROUTES — API ────────────

    @app.route("/api/stats")
    @login_required
    def api_stats():
        s = _system_stats()
        _, running = _projects_payload()
        meta = load_meta()
        total = sum(
            1 for k, v in meta.items()
            if not str(k).startswith("_") and isinstance(v, dict)
        )
        s.update({"ok": True, "projects": total, "running": running})
        return jsonify(s)


    @app.route("/api/projects")
    @login_required
    def api_projects():
        rows, _ = _projects_payload()
        return jsonify({"ok": True, "projects": rows})


    @app.route("/api/projects/<proj_id>/start", methods=["POST"])
    @login_required
    def api_start(proj_id):
        meta = load_meta()
        if proj_id not in meta:
            return jsonify({"ok": False, "error": "Project not found"}), 404
        stop_project_process(proj_id, notify=False)
        ok, msg = request_project_start(proj_id, meta[proj_id])
        return jsonify({"ok": ok, "message": str(msg)})


    @app.route("/api/projects/<proj_id>/stop", methods=["POST"])
    @login_required
    def api_stop(proj_id):
        stop_project_process(proj_id, notify=True)
        return jsonify({"ok": True})


    @app.route("/api/projects/<proj_id>/restart", methods=["POST"])
    @login_required
    def api_restart(proj_id):
        meta = load_meta()
        if proj_id not in meta:
            return jsonify({"ok": False, "error": "Project not found"}), 404
        stop_project_process(proj_id, notify=False)
        ok, msg = request_project_start(proj_id, meta[proj_id])
        return jsonify({"ok": ok, "message": str(msg)})


    @app.route("/api/projects/<proj_id>/delete", methods=["POST"])
    @login_required
    def api_delete(proj_id):
        meta = load_meta()
        if proj_id not in meta:
            return jsonify({"ok": False, "error": "Project not found"}), 404
        stop_project_process(proj_id, notify=False)
        try:
            shutil.rmtree(meta[proj_id].get("dir", ""), ignore_errors=True)
        except Exception:
            pass
        del meta[proj_id]
        save_meta(meta)
        return jsonify({"ok": True})


    @app.route("/api/projects/<proj_id>/logs")
    @login_required
    def api_logs(proj_id):
        meta = load_meta()
        pdata = meta.get(proj_id)
        if not pdata:
            return jsonify({"ok": False, "error": "Project not found"}), 404
        log_path = os.path.join(pdata.get("dir", ""), "output.log")
        if not os.path.exists(log_path):
            return jsonify({"ok": True, "logs": "(no log file yet)"})
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            return jsonify({"ok": True, "logs": content[-9000:]})
        except Exception as e:
            return jsonify({"ok": False, "logs": f"read error: {e}"})


    @app.route("/api/settings", methods=["GET", "POST"])
    @login_required
    def api_settings():
        if request.method == "GET":
            return jsonify({
                "ok": True,
                "maintenance_mode": bool(cfg("maintenance_mode", False)),
                "deploy_enabled": bool(cfg("deploy_enabled", True)),
                "auto_restart_default": bool(cfg("auto_restart_default", True)),
                "queue_enabled": bool(cfg("queue_enabled", True)),
                "report_group_enabled": bool(cfg("report_group_enabled", False)),
                "force_join_enabled": bool(cfg("force_join_enabled", False)),
                "force_targets": len(get_force_channels()),
            })

        data = request.get_json(silent=True) or {}
        allowed = {
            "maintenance_mode", "deploy_enabled", "auto_restart_default",
            "queue_enabled", "report_group_enabled", "force_join_enabled",
            "max_concurrent_projects", "default_project_limit",
            "default_online_days", "expiry_grace_hours",
        }
        for k, v in data.items():
            if k in allowed:
                try:
                    set_cfg(k, v)
                except Exception:
                    pass
        return jsonify({"ok": True})


# ────────────────────────────────────────────────────────────────
#  HTML — LOGIN
# ────────────────────────────────────────────────────────────────

LOGIN_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SARKER Admin — Login</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    font-family:'JetBrains Mono',ui-monospace,'Fira Code',monospace;
    background:radial-gradient(circle at 15% 15%,#0a0e17,#05070b 60%);
    color:#e6edf3;min-height:100vh;
    display:flex;align-items:center;justify-content:center;padding:20px;
  }
  form{
    background:#0d1117;border:1px solid #1f2937;border-radius:14px;
    padding:42px 36px;width:100%;max-width:420px;
    box-shadow:0 30px 80px rgba(0,0,0,.7),0 0 0 1px rgba(34,197,94,.08);
  }
  .logo{
    font-size:22px;font-weight:800;
    background:linear-gradient(90deg,#22c55e,#3b82f6);
    -webkit-background-clip:text;background-clip:text;color:transparent;
    margin-bottom:6px;letter-spacing:.5px;
  }
  .sub{color:#6b7280;font-size:12px;margin-bottom:32px}
  label{display:block;font-size:11px;color:#9ca3af;margin-bottom:8px;
        text-transform:uppercase;letter-spacing:1.5px}
  input{
    width:100%;padding:13px 15px;background:#05070b;
    border:1px solid #1f2937;color:#e6edf3;border-radius:8px;
    font-family:inherit;font-size:14px;outline:none;transition:border-color .2s;
  }
  input:focus{border-color:#22c55e;box-shadow:0 0 0 3px rgba(34,197,94,.1)}
  button{
    width:100%;margin-top:22px;padding:13px;
    background:linear-gradient(90deg,#22c55e,#16a34a);border:none;
    color:#fff;font-family:inherit;font-weight:700;font-size:13px;
    border-radius:8px;cursor:pointer;letter-spacing:1px;
    transition:transform .1s,box-shadow .2s;
  }
  button:hover{box-shadow:0 0 24px rgba(34,197,94,.4)}
  button:active{transform:scale(.98)}
  .error{color:#ef4444;font-size:13px;margin-top:16px;text-align:center}
  .blink{animation:blink 1s infinite}
  @keyframes blink{50%{opacity:0}}
</style>
</head>
<body>
  <form method="POST">
    <div class="logo">⚡ SARKER ADMIN</div>
    <div class="sub">$ authenticate --secure <span class="blink">▊</span></div>
    <label>Access Password</label>
    <input type="password" name="password" autofocus required autocomplete="off">
    <button type="submit">▶ AUTHENTICATE</button>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
  </form>
</body>
</html>
"""


# ────────────────────────────────────────────────────────────────
#  HTML — DASHBOARD
# ────────────────────────────────────────────────────────────────

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SARKER — Web Console</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#05070b;--panel:#0d1117;--border:#1f2937;--border2:#2d3748;
    --text:#e6edf3;--muted:#6b7280;
    --green:#22c55e;--red:#ef4444;--blue:#3b82f6;--amber:#f59e0b;--purple:#a78bfa;
  }
  html,body{height:100%}
  body{
    font-family:'JetBrains Mono',ui-monospace,'Fira Code',monospace;
    background:var(--bg);color:var(--text);min-height:100vh;
    padding:18px;font-size:13px;line-height:1.5;
  }
  .topbar{
    display:flex;align-items:center;justify-content:space-between;
    padding:14px 20px;background:var(--panel);border:1px solid var(--border);
    border-radius:12px;margin-bottom:16px;
  }
  .brand{
    font-weight:800;font-size:15px;letter-spacing:.5px;
    background:linear-gradient(90deg,#22c55e,#3b82f6);
    -webkit-background-clip:text;background-clip:text;color:transparent;
  }
  .topbar-right{display:flex;gap:14px;align-items:center}
  .live{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--muted)}
  .dot{width:8px;height:8px;border-radius:50%;background:var(--green);
       box-shadow:0 0 10px var(--green);animation:pulse 1.6s infinite}
  @keyframes pulse{50%{opacity:.35}}
  .logout{
    color:var(--muted);text-decoration:none;font-size:11px;
    padding:6px 12px;border:1px solid var(--border);border-radius:6px;
    letter-spacing:1px;transition:all .2s;
  }
  .logout:hover{color:var(--red);border-color:var(--red)}

  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));
        gap:12px;margin-bottom:16px}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;
        padding:16px 18px;transition:border-color .2s,transform .2s}
  .card:hover{border-color:var(--border2)}
  .card-label{font-size:10px;color:var(--muted);text-transform:uppercase;
              letter-spacing:1.5px;margin-bottom:10px}
  .card-value{font-size:22px;font-weight:800;letter-spacing:.5px}
  .card-value.green{color:var(--green)}
  .card-value.blue{color:var(--blue)}
  .card-value.amber{color:var(--amber)}
  .card-value.purple{color:var(--purple)}
  .bar{height:5px;background:#1a2230;border-radius:3px;overflow:hidden;margin-top:10px}
  .bar>div{height:100%;background:linear-gradient(90deg,#22c55e,#3b82f6);
           width:0;transition:width .6s ease}

  .section{background:var(--panel);border:1px solid var(--border);
           border-radius:12px;padding:18px 20px;margin-bottom:16px}
  .section-title{
    font-size:12px;font-weight:700;text-transform:uppercase;
    letter-spacing:1.5px;color:#9ca3af;margin-bottom:16px;
    display:flex;justify-content:space-between;align-items:center;
  }
  .section-title::before{content:'◆ ';color:var(--green);margin-right:6px}
  .section-title>span:first-child{flex:1}
  .refresh-note{font-size:10px;color:var(--muted);font-weight:400;
                text-transform:none;letter-spacing:0}

  .project{
    padding:16px;border:1px solid var(--border);border-radius:10px;
    margin-bottom:12px;background:#0a0e15;
    transition:border-color .2s;
  }
  .project:hover{border-color:var(--border2)}
  .project-head{display:flex;justify-content:space-between;align-items:center;
                margin-bottom:10px;gap:12px;flex-wrap:wrap}
  .project-name{font-weight:800;font-size:14px;letter-spacing:.3px}
  .status{
    font-size:10px;padding:4px 10px;border-radius:20px;
    font-weight:800;letter-spacing:.5px;white-space:nowrap;
  }
  .status.running{background:rgba(34,197,94,.14);color:var(--green)}
  .status.stopped{background:rgba(107,114,128,.14);color:#9ca3af}
  .status.crashed{background:rgba(239,68,68,.14);color:var(--red)}
  .status.queued{background:rgba(245,158,11,.14);color:var(--amber)}
  .status.expired{background:rgba(167,139,250,.14);color:var(--purple)}
  .project-meta{
    display:flex;flex-wrap:wrap;gap:14px;
    font-size:11px;color:var(--muted);margin-bottom:12px;
  }
  .project-meta>span{display:inline-flex;gap:5px;align-items:center}
  .project-actions{display:flex;flex-wrap:wrap;gap:8px}

  .btn{
    padding:7px 13px;font-size:11px;font-weight:700;letter-spacing:.5px;
    border:1px solid var(--border);background:transparent;color:var(--text);
    border-radius:6px;cursor:pointer;font-family:inherit;
    transition:all .15s;
  }
  .btn:hover{background:#1a2230}
  .btn.start{color:var(--green);border-color:rgba(34,197,94,.45)}
  .btn.start:hover{background:rgba(34,197,94,.14)}
  .btn.stop{color:var(--red);border-color:rgba(239,68,68,.45)}
  .btn.stop:hover{background:rgba(239,68,68,.14)}
  .btn.blue{color:var(--blue);border-color:rgba(59,130,246,.45)}
  .btn.blue:hover{background:rgba(59,130,246,.14)}
  .btn.danger{color:var(--red);border-color:rgba(239,68,68,.45)}
  .btn.danger:hover{background:rgba(239,68,68,.14)}

  .toggle{
    display:flex;justify-content:space-between;align-items:center;
    padding:11px 0;border-bottom:1px solid var(--border);
  }
  .toggle:last-child{border-bottom:none}
  .toggle-name{color:#c9d1d9;font-size:12px}
  .switch{
    position:relative;width:46px;height:24px;background:#1a2230;
    border-radius:12px;cursor:pointer;transition:background .2s;flex-shrink:0;
  }
  .switch.on{background:var(--green);box-shadow:0 0 12px rgba(34,197,94,.4)}
  .switch::after{
    content:'';position:absolute;top:3px;left:3px;width:18px;height:18px;
    background:#fff;border-radius:50%;transition:transform .2s;
  }
  .switch.on::after{transform:translateX(22px)}

  .modal{
    position:fixed;inset:0;background:rgba(0,0,0,.88);
    display:none;align-items:center;justify-content:center;
    padding:20px;z-index:100;backdrop-filter:blur(4px);
  }
  .modal.open{display:flex}
  .modal-box{
    background:var(--panel);border:1px solid var(--border);
    border-radius:12px;width:100%;max-width:900px;max-height:82vh;
    display:flex;flex-direction:column;overflow:hidden;
    box-shadow:0 30px 100px rgba(0,0,0,.9);
  }
  .modal-head{
    padding:14px 20px;border-bottom:1px solid var(--border);
    display:flex;justify-content:space-between;align-items:center;
    font-weight:700;font-size:12px;letter-spacing:1px;
  }
  .modal-body{
    padding:18px 20px;overflow:auto;font-size:12px;line-height:1.65;
    color:#a5b3c4;white-space:pre-wrap;word-break:break-all;
    flex:1;background:#030507;font-family:inherit;
  }
  .empty{text-align:center;padding:44px 20px;color:var(--muted);font-size:12px}
  .blink{animation:blink 1s infinite}
  @keyframes blink{50%{opacity:0}}
  .flash{animation:flash .4s}
  @keyframes flash{0%{background:rgba(34,197,94,.25)}100%{background:transparent}}

  @media (max-width:640px){
    body{padding:10px}
    .card-value{font-size:18px}
    .project-meta{gap:8px;font-size:10px}
    .btn{padding:6px 10px;font-size:10px}
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="brand">⚡ SARKER HOSTING — WEB CONSOLE</div>
  <div class="topbar-right">
    <div class="live"><span class="dot"></span>LIVE · SYNCED WITH TELEGRAM</div>
    <a class="logout" href="/logout">LOGOUT</a>
  </div>
</div>

<div class="grid">
  <div class="card">
    <div class="card-label">CPU</div>
    <div class="card-value" id="v-cpu">—</div>
    <div class="bar"><div id="b-cpu"></div></div>
  </div>
  <div class="card">
    <div class="card-label">RAM</div>
    <div class="card-value" id="v-ram">—</div>
    <div class="bar"><div id="b-ram"></div></div>
  </div>
  <div class="card">
    <div class="card-label">Disk</div>
    <div class="card-value" id="v-disk">—</div>
    <div class="bar"><div id="b-disk"></div></div>
  </div>
  <div class="card">
    <div class="card-label">Bot Uptime</div>
    <div class="card-value green" id="v-up">—</div>
  </div>
  <div class="card">
    <div class="card-label">Total Projects</div>
    <div class="card-value blue" id="v-proj">—</div>
  </div>
  <div class="card">
    <div class="card-label">Running</div>
    <div class="card-value green" id="v-run">—</div>
  </div>
</div>

<div class="section">
  <div class="section-title">
    <span>Projects</span>
    <span class="refresh-note">auto-refresh · <span id="cd">5</span>s</span>
  </div>
  <div id="projects"><div class="empty">loading<span class="blink">▊</span></div></div>
</div>

<div class="section">
  <div class="section-title">
    <span>Control Settings</span>
    <span class="refresh-note">synced with Telegram admin panel</span>
  </div>
  <div id="settings"></div>
</div>

<div class="modal" id="modal" onclick="if(event.target===this)closeLogs()">
  <div class="modal-box">
    <div class="modal-head">
      <span id="modal-title">LOGS</span>
      <button class="btn" onclick="closeLogs()">✕ CLOSE</button>
    </div>
    <div class="modal-body" id="modal-body">loading...</div>
  </div>
</div>

<script>
let cd = 5;

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(p, o){
  const r = await fetch(p, o || {});
  try { return await r.json(); } catch(e){ return {ok:false}; }
}

function fmtUp(s){
  s = Math.max(0, Math.floor(s||0));
  const d = Math.floor(s/86400), h = Math.floor((s%86400)/3600),
        m = Math.floor((s%3600)/60), sec = s%60;
  if (d) return d+'d '+h+'h '+m+'m';
  if (h) return h+'h '+m+'m '+sec+'s';
  return m+'m '+sec+'s';
}

function statusCls(s){
  if (s.startsWith('🟢')) return 'running';
  if (s.includes('CRASHED')) return 'crashed';
  if (s.includes('QUEUED')) return 'queued';
  if (s.includes('EXPIRED')) return 'expired';
  return 'stopped';
}

async function loadStats(){
  const d = await api('/api/stats');
  if (!d.ok) return;
  $('v-cpu').textContent = d.cpu + '%';
  $('v-ram').textContent = d.ram + '%';
  $('v-disk').textContent = d.disk + '%';
  $('v-up').textContent = fmtUp(d.uptime);
  $('v-proj').textContent = d.projects;
  $('v-run').textContent = d.running;
  $('b-cpu').style.width = d.cpu + '%';
  $('b-ram').style.width = d.ram + '%';
  $('b-disk').style.width = d.disk + '%';
}

async function loadProjects(){
  const d = await api('/api/projects');
  if (!d.ok) return;
  const c = $('projects');
  if (!d.projects.length){
    c.innerHTML = '<div class="empty">no projects deployed yet</div>';
    return;
  }
  c.innerHTML = d.projects.map(p => {
    const cls = statusCls(p.status);
    const running = cls === 'running';
    return `
      <div class="project">
        <div class="project-head">
          <div class="project-name">📦 ${esc(p.name)}</div>
          <div class="status ${cls}">${esc(p.status)}</div>
        </div>
        <div class="project-meta">
          <span>👤 ${esc(p.user_name)}</span>
          <span>🆔 ${esc(p.chat_id)}</span>
          <span>🚀 ${esc(p.main_file || '—')}</span>
          <span>🔌 ${esc(p.port || '—')}</span>
          <span>⚡ ${p.cpu}%</span>
          <span>💾 ${p.ram}MB</span>
          <span>⏱ ${fmtUp(p.uptime)}</span>
          <span>♻️ ${p.auto_restart ? 'ON' : 'OFF'}</span>
        </div>
        <div class="project-actions">
          ${ running
            ? `<button class="btn stop" onclick="act('${p.id}','stop')">■ STOP</button>`
            : `<button class="btn start" onclick="act('${p.id}','start')">▶ START</button>` }
          <button class="btn blue" onclick="act('${p.id}','restart')">↻ RESTART</button>
          <button class="btn blue" onclick="openLogs('${p.id}','${esc(p.name)}')">☷ LOGS</button>
          <button class="btn danger" onclick="act('${p.id}','delete')">🗑 DELETE</button>
        </div>
      </div>`;
  }).join('');
}

async function loadSettings(){
  const d = await api('/api/settings');
  if (!d.ok && d.maintenance_mode === undefined) return;
  const rows = [
    ['maintenance_mode',     'Maintenance Mode'],
    ['deploy_enabled',       'Deploy Enabled'],
    ['auto_restart_default', 'Auto Restart Default'],
    ['queue_enabled',        'Start Queue Enabled'],
    ['report_group_enabled', 'Report Group Enabled'],
    ['force_join_enabled',   'Force Join Enabled'],
  ];
  $('settings').innerHTML = rows.map(([k,label]) => `
    <div class="toggle">
      <span class="toggle-name">${label}</span>
      <div class="switch ${d[k] ? 'on' : ''}" onclick="toggleSetting('${k}', ${!d[k]})"></div>
    </div>`).join('');
}

async function toggleSetting(key, val){
  await api('/api/settings', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ [key]: val })
  });
  loadSettings();
}

async function act(id, what){
  if (what === 'delete' && !confirm('Permanently delete this project and all its files?')) return;
  const r = await api('/api/projects/' + id + '/' + what, { method: 'POST' });
  if (r && r.error) alert(r.error);
  if (r && r.message && r.message.startsWith('QUEUED')) alert('Project queued: ' + r.message);
  await loadProjects();
  await loadStats();
}

async function openLogs(id, name){
  $('modal').classList.add('open');
  $('modal-title').textContent = '☷ LOGS — ' + name;
  $('modal-body').textContent = 'loading...';
  const d = await api('/api/projects/' + id + '/logs');
  $('modal-body').textContent = (d && d.logs) || '(empty)';
}

function closeLogs(){ $('modal').classList.remove('open'); }

function tick(){
  cd--;
  if (cd <= 0){ cd = 5; loadStats(); loadProjects(); }
  $('cd').textContent = cd;
}

loadStats(); loadProjects(); loadSettings();
setInterval(tick, 1000);
setInterval(loadSettings, 15000);
</script>
</body>
</html>
"""


# ────────────────────────────────────────────────────────────────
#  PUBLIC STARTER
# ────────────────────────────────────────────────────────────────

def start_web_panel():
    if not FLASK_OK:
        print("[WebPanel] ❌ Flask is not installed.")
        print("[WebPanel]    Run: pip install flask")
        return
    if not WEB_PASSWORD or WEB_PASSWORD == "sarker123":
        print("[WebPanel] ⚠️  Using DEFAULT password 'sarker123'.")
        print("[WebPanel]    Set config.json 'web_panel_password' or env WEB_PANEL_PASSWORD.")

    def _serve():
        try:
            app.run(
                host=WEB_HOST, port=WEB_PORT,
                debug=False, use_reloader=False, threaded=True,
            )
        except OSError as e:
            print(f"[WebPanel] ❌ Port {WEB_PORT} busy: {e}")
        except Exception as e:
            print(f"[WebPanel] ❌ Server error: {e}")

    t = threading.Thread(target=_serve, daemon=True, name="WebPanelThread")
    t.start()

    print("=" * 56)
    print("  🌐 WEB ADMIN PANEL — ONLINE")
    print("=" * 56)
    print(f"  URL      : http://{WEB_HOST}:{WEB_PORT}")
    print(f"  Local    : http://127.0.0.1:{WEB_PORT}")
    print(f"  Password : {WEB_PASSWORD}")
    print("  Sync     : shared with Telegram admin panel")
    print("=" * 56)