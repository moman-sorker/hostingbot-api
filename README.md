<div align="center">

# ⚡ SARKER HOSTING BOT

**Deploy. Control. Monitor. — All from Telegram.**

A self-hosted Telegram bot that turns your server into a mini hosting platform. Upload a `.zip`, pick an entry file, and the bot runs, monitors, and manages it — with both a Telegram admin panel and a web dashboard.

![Status](https://img.shields.io/badge/status-stable-22c55e?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.9+-3b82f6?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/telegram-bot-229ED9?style=for-the-badge&logo=telegram&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-a78bfa?style=for-the-badge)

</div>

---

## 📖 Table of Contents

- [What Is This?](#-what-is-this)
- [Features](#-features)
- [Use Cases](#-use-cases)
- [Project Files Explained](#-project-files-explained)
- [Requirements](#-requirements)
- [Setup Guide (Beginner)](#-setup-guide-beginner)
  - [Step 1: Install Python](#step-1--install-python)
  - [Step 2: Download the Bot](#step-2--download-the-bot)
  - [Step 3: Install Dependencies](#step-3--install-dependencies)
  - [Step 4: Create a Telegram Bot](#step-4--create-a-telegram-bot)
  - [Step 5: Get Your Owner ID](#step-5--get-your-owner-id)
  - [Step 6: Edit config.json](#step-6--edit-configjson)
  - [Step 7: Run the Bot](#step-7--run-the-bot)
- [Full config.json Reference](#-full-configjson-reference)
- [Web Admin Panel](#-web-admin-panel)
- [Group / Channel Mode](#-group--channel-mode)
- [How Users Deploy Projects](#-how-users-deploy-projects)
- [Running 24/7](#-running-247)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Security Notes](#-security-notes)
- [Architecture](#-architecture)
- [License](#-license)

---

## 🎯 What Is This?

**SARKER Hosting Bot** is a Telegram bot you run on your own server (VPS, Android phone via Termux, Windows PC, Raspberry Pi — anything with Python).

Once running, anyone with access can:

1. Send a `.zip` file to the bot
2. Pick which file to run (e.g. `main.py`)
3. The bot extracts, assigns a free port, and starts the app
4. Users manage it fully from Telegram — start, stop, logs, files, backups

You also get a **web admin panel** in your browser for desktop control.

**In one sentence:** It's like having a mini-Heroku inside your Telegram.

---

## ✨ Features

### 🚀 Deployment
- Upload `.zip` project archives
- Automatic extraction with safety checks
- Auto-detects entry file (`main.py`, `app.py`, `index.js`, etc.)
- Supports Python, Node.js, Bash, and static HTML
- Automatic free-port allocation
- `PORT` environment variable support

### 🎛 Project Control
- Start / Stop / Restart
- Live status with CPU, RAM, uptime
- Restart counter
- Auto-restart on crash
- Crash protection (stops infinite restart loops)
- Queue system for server overload

### 📁 Online File Manager
- Browse all project files
- View / edit source code (up to 512 KB)
- Create files and folders
- Rename, replace, delete
- Download individual files

### 🧰 Runtime Tools
- Live log viewer (last 25 lines)
- Full log download
- `.env` editor (add variables, clear all)
- Missing-module installer (auto-detects from crash logs)
- Full project backup as `.zip`
- Queue position display

### 🛡 Security
- ZIP path traversal protection
- Symlink entry blocking
- Project-root isolation
- Parent-directory access detection
- Restricted process environment (no bot secrets leaked)

### 👑 Admin System
- Owner-only admin panel
- User and project management
- Per-user project limits
- Force Join (channel membership requirement)
- Maintenance mode
- Deploy enable / disable
- Report group integration
- User suspension
- JSON metadata backup

### 🎨 Two Admin UIs (Synced)
- **Telegram Admin Terminal** — coder-themed animated panel
- **Web Admin Console** — Flask dashboard in browser
- Both share the same data — 100% synced

---

## 💡 Use Cases

Real scenarios where SARKER Hosting Bot helps:

### 1. **Host your own Telegram bots**
You write a Telegram bot in Python. Instead of SSH + `nohup` + `screen`, you just zip it and send to this bot. It runs 24/7 and auto-restarts if it crashes.

### 2. **Free API hosting for personal projects**
Deploy a Flask / FastAPI / Express app. The bot gives it a port. You can call it from anywhere.

### 3. **Static site hosting**
Drop an `index.html` in a zip. The bot runs a simple HTTP server on a free port.

### 4. **Learning platform for students**
Give students access. They upload code, see it run, get logs — without needing SSH knowledge.

### 5. **Community tool hosting**
Run small scripts (data fetchers, scrapers, notification bots) for your community. Each user gets their own private workspace.

### 6. **Quick testing environment**
Test a new script without setting up a whole VM. Upload → run → test → delete.

### 7. **Personal dev lab on Android**
Run the bot in Termux. Deploy Python scripts from your phone. No laptop needed.

### 8. **Multi-user mini platform**
Set project limits per user. Run a small hosting service for friends or a paid community.

---

## 📂 Project Files Explained

Here's every file in the project and what it does:

```
SARKER-HOSTING-BOT/
│
├── main.py                ← Core bot (DON'T EDIT — will break everything)
├── config.json            ← ⭐ YOUR SETTINGS GO HERE (edit this)
├── requirements.txt       ← Python packages needed
├── requirements-web.txt   ← Flask (for web panel)
│
├── admin.py               ← Telegram admin panel UI (already set up)
├── welcome.py             ← /start message UI (already set up)
├── web_panel.py           ← Web admin panel (already set up)
├── group_mode.py          ← Group / channel support (already set up)
├── run.py                 ← ⭐ START THE BOT WITH THIS FILE
│
├── projects_meta.json     ← Auto-generated when bot runs (data storage)
└── projects/              ← Auto-generated when bot runs (user projects)
    ├── proj_<chat_id>_<timestamp>/
    │   ├── main.py        ← User's uploaded code
    │   ├── .env           ← User's environment variables
    │   └── output.log     ← Auto-generated log file
    └── ...
```

### ⭐ What YOU need to touch (beginner-friendly)

| File | Action | When |
|------|--------|------|
| `config.json` | **Edit** | Once, before first run |
| `run.py` | **Run** | Every time you start the bot |
| Everything else | **Don't touch** | It's already configured |

### What NOT to edit

- ❌ `main.py` — Core logic. Editing will break features.
- ❌ `admin.py`, `welcome.py`, `web_panel.py`, `group_mode.py` — UI extensions. Pre-configured.
- ❌ `projects_meta.json` — Auto-managed data file.
- ❌ `projects/` — User projects.

---

## 💻 Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| **Python** | 3.9 | 3.11 or newer |
| **RAM** | 512 MB | 1 GB+ |
| **Disk** | 1 GB free | 5 GB+ |
| **OS** | Linux / Termux / Windows | Ubuntu 22.04 / Debian 12 |
| **Node.js** | Optional (only for `.js` projects) | Latest LTS |
| **Internet** | Required (Telegram API) | Stable connection |

---

## 🚀 Setup Guide (Beginner)

Follow these steps **in order**. Don't skip.

### Step 1 — Install Python

Check if you already have Python:

```bash
python --version
```

If it prints `Python 3.9` or higher, skip to Step 2.

**Ubuntu / Debian / VPS:**
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

**Termux (Android):**
```bash
pkg update && pkg upgrade -y
pkg install python nodejs git -y
```

**Windows:**
- Download from https://python.org/downloads
- Install and check **"Add Python to PATH"**
- Verify: open CMD and run `python --version`

---

### Step 2 — Download the Bot

**With Git (recommended):**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

**Without Git:**
- Download the ZIP from GitHub → extract → open terminal in that folder

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-web.txt
```

**Termux users** — if you get a `pip` error:
```bash
pip install --break-system-packages -r requirements.txt
pip install --break-system-packages -r requirements-web.txt
```

You should see packages like `pyTelegramBotAPI`, `requests`, `psutil`, `flask` install successfully.

---

### Step 4 — Create a Telegram Bot

1. Open Telegram and search for **`@BotFather`**
2. Send `/newbot`
3. BotFather asks for a **name** → type anything (e.g. `My Hosting Bot`)
4. BotFather asks for a **username** → must end in `bot` (e.g. `myhosting_bot`)
5. BotFather replies with a token that looks like:
   ```
   8929272862:AAHXRZ9zpyZwSI3hhMkrQLW0KfcHSmvmL-I
   ```
6. **Copy this token** — you'll need it in Step 6.

> ⚠️ **Keep this token secret.** Anyone with this token controls your bot.
>
> If it leaks: `@BotFather` → `/mybots` → your bot → `API Token` → `Revoke`.

---

### Step 5 — Get Your Owner ID

Your **owner ID** is your personal Telegram numeric ID. Only this ID gets admin access.

1. Open Telegram and search for **`@userinfobot`**
2. Send `/start`
3. It replies:
   ```
   Id: 6683255978
   First: Sarker
   Username: @sarker
   ```
4. **Copy the number** (e.g. `6683255978`) — you'll need it in Step 6.

---

### Step 6 — Edit config.json

Open `config.json` in any text editor. Change these **three critical values**:

```json
{
    "bot_token": "PASTE_YOUR_TOKEN_FROM_BOTFATHER",
    "owner_id": 6683255978,
    "web_panel_password": "change-this-to-something-strong"
}
```

Replace:
- `PASTE_YOUR_TOKEN_FROM_BOTFATHER` → the token from Step 4
- `6683255978` → your ID from Step 5
- `change-this-to-something-strong` → your own password for the web panel

Save the file.

**For the rest of the config, you can leave it as-is for now.** Detailed explanation is in [Full config.json Reference](#-full-configjson-reference).

---

### Step 7 — Run the Bot

**Always use `run.py`, NOT `main.py`:**

```bash
python run.py
```

You should see output like this:

```
========================================================
  SARKER HOSTING HUB — ENHANCED + WEB CONSOLE
========================================================
  [Admin] ✅ Enhanced coder-themed admin panel installed.
  [Welcome] ✅ Enhanced /start message installed.
  🌐 WEB ADMIN PANEL — ONLINE
    URL      : http://0.0.0.0:8080
    Password : change-this-to-something-strong
  [Telegram] Connected as @myhosting_bot
  [Telegram] Polling started.
```

**That's it!** Open Telegram, find your bot, send `/start`. 🎉

**To stop:** press `Ctrl + C` in the terminal.

---

## ⚙️ Full config.json Reference

Here's a complete example with all available options:

```json
{
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "owner_id": 6683255978,

    "base_dir": "projects",
    "meta_file": "projects_meta.json",

    "force_join_enabled": false,
    "force_channel": "",
    "force_channels": [],
    "force_join_link": "",

    "default_project_limit": 1,
    "default_online_days": 2,
    "max_online_days": 30,
    "expiry_grace_hours": 24,

    "auto_restart_default": true,
    "max_crash_restarts": 5,
    "crash_window_seconds": 300,
    "process_grace_seconds": 8,

    "monitor_interval_seconds": 8,
    "expiry_cleanup_interval_seconds": 60,

    "deploy_enabled": true,
    "maintenance_mode": false,
    "show_live_status": true,
    "dynamic_animation_enabled": true,
    "animation_style": "wave",
    "animation_speed": 0.12,

    "max_concurrent_projects": 8,
    "queue_enabled": true,
    "queue_interval_seconds": 5,

    "web_panel_port": 8080,
    "web_panel_password": "change-this-password",
    "web_panel_host": "0.0.0.0",

    "allowed_group_ids": [],

    "report_group_enabled": false,
    "report_group_id": 0,

    "max_file_edit_bytes": 524288,

    "suspended_users": {},
    "user_limits": {}
}
```

### What each field means

| Field | Purpose | Default | When to change |
|-------|---------|---------|----------------|
| `bot_token` | Telegram API key | — | **Required** — after creating bot |
| `owner_id` | Your Telegram ID (admin) | — | **Required** — after getting your ID |
| `base_dir` | Where projects are stored | `projects` | If you want a custom path |
| `meta_file` | Data storage file name | `projects_meta.json` | Rarely |
| `force_join_enabled` | Require users to join a channel | `false` | To grow your channel |
| `force_channels` | List of required channels | `[]` | Managed from Admin Panel |
| `default_project_limit` | Max projects per user | `1` | Increase for more lenient limits |
| `default_online_days` | How long a project runs | `2` | Increase for longer runtime |
| `max_online_days` | Max admin can extend to | `30` | Safety limit |
| `expiry_grace_hours` | Grace period after expiry | `24` | Time before files get deleted |
| `auto_restart_default` | Auto-restart on crash | `true` | Default for new projects |
| `max_crash_restarts` | Max restarts in window | `5` | Crash-protection threshold |
| `crash_window_seconds` | Crash-count time window | `300` | 5 minutes |
| `process_grace_seconds` | Wait before force-kill | `8` | For slow shutdown |
| `monitor_interval_seconds` | Crash-check frequency | `8` | Lower = faster detection |
| `expiry_cleanup_interval_seconds` | Expiry-check frequency | `60` | Lower = faster cleanup |
| `deploy_enabled` | Allow new deploys | `true` | Set `false` during maintenance |
| `maintenance_mode` | Lock everyone out | `false` | For updates |
| `show_live_status` | Show live CPU/RAM | `true` | `false` = lighter |
| `dynamic_animation_enabled` | Animations on deploy | `true` | `false` = instant |
| `animation_style` | Animation type | `wave` | `wave`, `pulse`, `dots`, `orbit` |
| `animation_speed` | Animation speed | `0.12` | Higher = slower |
| `max_concurrent_projects` | Max running at once | `8` | Based on your RAM |
| `queue_enabled` | Enable start queue | `true` | `false` = reject extra |
| `queue_interval_seconds` | Queue check frequency | `5` | Lower = faster pickup |
| `web_panel_port` | Web panel port | `8080` | If 8080 is used |
| `web_panel_password` | Web panel password | — | **Always change** |
| `web_panel_host` | Web listen address | `0.0.0.0` | `127.0.0.1` for local-only |
| `allowed_group_ids` | Whitelisted groups | `[]` | See Group Mode section |
| `report_group_enabled` | Send uploads to group | `false` | Set from Admin Panel |
| `report_group_id` | Report group chat ID | `0` | Set from Admin Panel |
| `max_file_edit_bytes` | Max editable file size | `524288` | 512 KB |

### 🧠 RAM to max_concurrent_projects guide

| Server RAM | Recommended value |
|-----------|-------------------|
| 512 MB | `2` |
| 1 GB | `4` |
| 2 GB | `8` |
| 4 GB | `16` |
| 8 GB+ | `32` |

### 💡 Live-editable settings

These can be changed **while the bot is running** from the Admin Panel — no restart needed:

- `maintenance_mode`
- `deploy_enabled`
- `auto_restart_default`
- `queue_enabled`
- `default_project_limit`
- `default_online_days`
- `max_concurrent_projects`
- `expiry_grace_hours`
- `force_join_enabled`, `force_channels`

---

## 🌐 Web Admin Panel

Once the bot is running, open your browser:

| Where you are | URL to open |
|---------------|-------------|
| Same machine (localhost) | `http://127.0.0.1:8080` |
| Same Wi-Fi / LAN | `http://192.168.x.x:8080` |
| VPS / Cloud server | `http://your-server-public-ip:8080` |

**Password:** whatever you set in `config.json` → `web_panel_password`.

### What you can do

- View live CPU / RAM / Disk usage
- See all projects with status badges
- Start / Stop / Restart / Delete any project
- View live logs in a terminal-style modal
- Toggle admin settings (maintenance, deploy, queue, etc.)
- Auto-refresh every 5 seconds

### Finding your server IP

```bash
# Public IP (VPS / cloud)
curl ifconfig.me

# Local IP (same Wi-Fi)
hostname -I
```

### Changing the port

Edit `config.json`:
```json
"web_panel_port": 3000
```

Or use an environment variable:
```bash
WEB_PANEL_PORT=3000 python run.py
```

Or if you want to expose on a specific interface only:
```json
"web_panel_host": "127.0.0.1"
```

### Firewall (VPS)

If you can't access the panel from outside:
```bash
sudo ufw allow 8080/tcp
sudo ufw reload
```

---

## 💬 Group / Channel Mode

**By default, the bot only works in private DMs** — this is safest. Users can't accidentally leak project data to a group.

If you want the bot to **also respond inside your own private group**, you can whitelist it.

### Step 1 — Get the group ID

1. Add **`@userinfobot`** to your group
2. Send any message in the group
3. It shows:
   ```
   Group ID: -1001234567890
   ```
4. Remove `@userinfobot` from the group

### Step 2 — Add to config.json

```json
"allowed_group_ids": [-1001234567890]
```

Multiple groups:
```json
"allowed_group_ids": [-1001234567890, -1009876543210]
```

### Step 3 — Restart the bot

```bash
python run.py
```

### Behavior in whitelisted groups

| Action | Regular user in group | Owner (you) in group |
|--------|----------------------|---------------------|
| `/start` | Bot replies: "Open DM to use bot" | Same reply |
| `/admin` | "⛔ Admin only" | Admin panel sent to your **DM** |
| Any other message | Silent | Silent |

**Why admin panel goes to DM:** cleaner state, no group spam, safer.

**Everything else** (deploy, files, logs, project management) works **only in DM**.

---

## 🚀 How Users Deploy Projects

Share your bot's `@username` with users. Here's what they do:

### Step 1 — Open the bot
Send `/start` in DM. They see the welcome console.

### Step 2 — Tap `🚀 DEPLOY NEW`

### Step 3 — Upload a `.zip` file
The zip should contain the project files at the root level:

```
my_project.zip
├── main.py
├── requirements.txt
├── .env
└── utils/
    └── helpers.py
```

> ⚠️ Don't zip the parent folder. Zip **inside** the folder so `main.py` is at the top level.

### Step 4 — Pick the entry file
The bot lists `.py`, `.js`, `.sh`, `.html` files. Tap one.

### Step 5 — Bot starts the project
- Auto-assigns a free port
- Sets `PORT` env variable
- Runs the process
- Provides a dashboard

### Step 6 — Manage from dashboard

Dashboard buttons:
- ▶ **START / ■ STOP**
- ↻ **RESTART**
- ☷ **LOGS** (view / download)
- 📊 **MONITOR** (CPU / RAM / uptime)
- 📁 **FILES** (browse, edit, create, rename, delete, download)
- ⚙️ **.env** (add variables, clear)
- 📦 **BACKUP** (download zip)
- ♻️ **AUTO RESTART** (toggle)
- 🗑 **TERMINATE** (delete project)

### Supported project types

| Extension | Runtime | Notes |
|-----------|---------|-------|
| `.py` | Python | Run with `python -u` |
| `.js` | Node.js | Requires `node` in PATH |
| `.sh` | Bash | Linux only |
| `.html`, `.htm` | Static HTTP | Python's http.server |

### Using PORT in code

**Python:**
```python
import os
port = int(os.environ.get("PORT", 8080))
app.run(host="0.0.0.0", port=port)
```

**Node.js:**
```javascript
const port = process.env.PORT || 3000;
app.listen(port);
```

---

## ⏰ Running 24/7

### Option A — `screen` (easiest, Linux)

```bash
# Install (Ubuntu)
sudo apt install screen

# Start a session
screen -S sarkerbot

# Inside the session
python run.py

# Detach: press Ctrl+A, then D
```

**Reattach:**
```bash
screen -r sarkerbot
```

**Kill the session:**
```bash
screen -X -S sarkerbot quit
```

### Option B — `systemd` (recommended for VPS)

Create `/etc/systemd/system/sarkerbot.service`:

```ini
[Unit]
Description=SARKER Hosting Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/SARKER-HOSTING-BOT
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable sarkerbot
sudo systemctl start sarkerbot
```

Check status:
```bash
sudo systemctl status sarkerbot
```

View live logs:
```bash
sudo journalctl -u sarkerbot -f
```

Restart after changes:
```bash
sudo systemctl restart sarkerbot
```

### Option C — Termux (Android)

```bash
pkg install termux-services -y

# Prevent Android from killing the process
termux-wake-lock

# Run
python run.py
```

**Keep in background:** use `screen` inside Termux:
```bash
pkg install screen -y
screen -S bot
python run.py
# Ctrl+A, D to detach
```

### Option D — Windows

Use **Task Scheduler** or just run:
```cmd
python run.py
```

To keep running after closing CMD, use `nssm` or run in a Windows Service.

---

## 🔧 Troubleshooting

### Bot doesn't respond to `/start`

**Check the console.** You should see:
```
[Telegram] Connected as @your_bot
[Telegram] Polling started.
```

- If you see **"Unauthorized"** → wrong `bot_token` in `config.json`
- If nothing appears → bot didn't start. Check for Python errors above.

### `/admin` says "Admin only"

Your Telegram ID doesn't match `owner_id`.

**Fix:** Get your correct ID from `@userinfobot` and update `config.json`.

### Web panel not loading

1. **Look at the console.** Find the line:
   ```
   URL      : http://0.0.0.0:8080
   ```
2. Try `http://127.0.0.1:8080` on the same machine first.
3. If local works but external doesn't → **firewall issue**:
   ```bash
   sudo ufw allow 8080
   ```

### "Port already in use"

Change `web_panel_port` in `config.json` to `8081` or `3000`.

Or kill the process using that port:
```bash
sudo lsof -i :8080
sudo kill -9 <PID>
```

### Project crashes with "ModuleNotFoundError"

The bot detects this and shows an **`＋ INSTALL <module>`** button on the dashboard. Tap it.

Or install manually on the server:
```bash
pip install <module>
```

### Project crashes with "command not found: node"

Node.js isn't installed. Install it:

```bash
# Ubuntu/Debian
sudo apt install nodejs npm

# Termux
pkg install nodejs
```

### Bot disconnects randomly

The bot has **auto-reconnect**. If it still fails:
- Check internet connection
- Check if your ISP blocks Telegram (some do)
- Use a VPS in a different region

### ZIP is rejected

Possible reasons:
- Contains symlinks → blocked for safety
- Contains absolute paths (`/etc/passwd`) → blocked
- Contains `..` traversal → blocked

Re-zip without those entries.

### Bot token leaked

1. Immediately go to `@BotFather` → `/mybots` → your bot → `API Token` → `Revoke current token`
2. Update `config.json` with the new token
3. Restart the bot

### `.gitignore` — protect your secrets

Create a `.gitignore` file:

```
config.json
projects_meta.json
projects/
__pycache__/
*.pyc
.env
*.log
```

Then:
```bash
git add .gitignore
git commit -m "add gitignore"
```

---

## ❓ FAQ

**Q: Do users see each other's projects?**
No. Every project is bound to the uploading user's `chat_id`. Users can only see and control their own.

**Q: Do I need a VPS?**
No. Works on any Linux VPS, Android phone (Termux), Windows PC, or Raspberry Pi.

**Q: How many projects can run at once?**
Limited by `max_concurrent_projects` (default 8). Extra ones go to a queue.

**Q: How do I add more admins?**
Currently one owner only (`owner_id`). Multi-admin can be added as a custom feature.

**Q: Where's the admin panel?**
Two places:
- **Telegram:** send `/admin` to your bot
- **Web:** open `http://your-ip:8080`

**Q: Can I customize the welcome message / admin panel?**
Yes, but the extensions (`welcome.py`, `admin.py`) are pre-configured to look professional. Editing them requires Python knowledge.

**Q: Is this safe for public use?**
Reasonably — with the built-in ZIP/path protections. For public use, add OS-level sandboxing (Docker, systemd-nspawn).

**Q: What if my bot_token gets leaked?**
Immediately revoke it at `@BotFather` → `/mybots` → `API Token` → `Revoke`.

**Q: Can I run multiple bots with this?**
Yes — copy the folder, use different `bot_token`, `owner_id`, and `web_panel_port`.

**Q: Does it work behind a proxy?**
Yes. Set `HTTPS_PROXY` / `HTTP_PROXY` environment variables. `telebot` respects them.

**Q: What Python version do I need?**
3.9 minimum. 3.11+ recommended.

**Q: Where is data stored?**
- Metadata: `projects_meta.json`
- Project files: `projects/proj_<chat_id>_<timestamp>/`

**Q: How do I backup everything?**
Download the JSON store from Admin Panel → `📥 JSON STORE`. And copy the `projects/` folder.

---

## 🔐 Security Notes

### ✅ What the bot protects against

- ZIP path traversal (`../../etc/passwd`)
- Symlink entries in uploaded ZIPs
- Projects reading other projects' files
- Parent-directory access attempts (`os.walk("..")`)
- Env variable leakage from bot → project

### ⚠️ What it does NOT protect against

- Malicious code inside a project (crypto miners, port scanners)
- Resource exhaustion (CPU/memory bombs)
- Network attacks launched from hosted projects
- Users with shell access to your server

### 🛡 Recommended hardening for public use

1. **Run the bot as a non-root user**
2. **Use Docker or systemd-nspawn** for isolation
3. **Set CPU/memory limits** via `cgroups`
4. **Firewall** — close unused ports
5. **Change `web_panel_password`** to something strong (not `sarker123`)
6. **Set `web_panel_host: "127.0.0.1"`** if using a reverse proxy
7. **Enable `maintenance_mode`** when you need to lock down
8. **Backup regularly** — projects + `projects_meta.json`

### 🔒 Never commit to Git

Add these to `.gitignore`:
- `config.json` (bot token + web password)
- `projects_meta.json` (user data)
- `projects/` (user code)
- Any `.env` files

---

## 🏗 Architecture

```
                    ┌─────────────────────┐
                    │   TELEGRAM USERS    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐     ┌──────────┐    ┌────────────┐
        │ welcome  │     │  admin   │    │ web_panel  │
        │ (/start) │     │ (panel)  │    │  (Flask)   │
        └────┬─────┘     └────┬─────┘    └─────┬──────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    ┌─────────────────────┐
                    │      main.py        │
                    │    (bot core)       │
                    ├─────────────────────┤
                    │  active_processes{} │ ← shared memory
                    │  CONFIG{}           │
                    │  load_meta()        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ projects_meta.json  │
                    │ projects/           │
                    └─────────────────────┘
```

**Key point:** Everything runs in **one Python process**. That's why Telegram and Web share live data — no sync lag.

---

## 🎓 Learning Path (For Absolute Beginners)

Never used a VPS before? Follow this order:

1. **Create a Telegram bot**
   → `@BotFather` → `/newbot`

2. **Get your Telegram ID**
   → `@userinfobot` → `/start`

3. **Edit `config.json`**
   → Paste your `bot_token` and `owner_id`

4. **Run locally on your PC**
   → `python run.py`

5. **Test in Telegram**
   → Send `/start`, then `/admin`

6. **Open the web panel**
   → `http://127.0.0.1:8080` in your browser

7. **Deploy a test project**
   → Zip any `main.py` → send to bot → pick entry → running!

8. **Move to a VPS (optional)**
   → Rent a $5 VPS → install Python → copy files → use systemd

9. **Set up auto-start**
   → `systemctl enable sarkerbot`

10. **Share with users**
    → Give them your bot's `@username`

---

## 📄 License

MIT License — free to use, modify, and distribute.

Add your own `LICENSE` file before publishing.

---

## 🙏 Credits

Built for fast Telegram-first hosting.

If you find this useful, give the repository a ⭐ — it helps a lot!

---

<div align="center">

**⚡ SARKER HOSTING BOT**

**Deploy. Control. Monitor.**

</div>