import os
import yaml
import json
import logging
import asyncio
import threading
import uuid
import sys
try:
    import psutil
except ImportError:
    psutil = None
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from core.models import LLMAdapter
from core.tools import ToolManager
from core.server import start_web_server, push_notification

logging.basicConfig(level=logging.ERROR)


class VoidClawAgent:
    def __init__(self, config_path):
        self.config_path = config_path
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.base_dir      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.workspace_dir = os.path.join(self.base_dir, self.config.get('workspace_dir', 'workspace'))
        self.chats_dir     = os.path.join(self.base_dir, 'common', 'chats')
        self.tasks_path    = os.path.join(self.base_dir, 'common', 'tasks.yaml')

        if not os.path.exists(self.chats_dir):
            os.makedirs(self.chats_dir)

        self.model = LLMAdapter(self.config)
        self.tools = ToolManager(self.workspace_dir)
        self.tools.set_agent(self)

        self.system_prompt = self._load_system_prompt()
        self.history       = []
        self.session_id    = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time    = datetime.now()
        self.total_tokens  = 0
        self.tool_usage    = {}
        self.interrupted   = False

        try:
            self.scheduler = AsyncIOScheduler()
        except Exception:
            from datetime import timezone
            self.scheduler = AsyncIOScheduler(timezone=timezone.utc)

        self._load_tasks()

        self.tg_app          = None
        self.last_tg_chat_id = None

        self.LOGO   = "𒆙"
        self.ORANGE = '\033[38;5;214m'
        self.AMBER  = '\033[93m'
        self.SLATE  = '\033[90m'
        self.GREEN  = '\033[92m'
        self.RED    = '\033[91m'
        self.RESET  = '\033[0m'
        self.BOLD   = '\033[1m'
        self.DIM    = '\033[2m'

    # ─────────────────────────────────────────────────────────────────────────
    def reload_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.model         = LLMAdapter(self.config)
        self.system_prompt = self._load_system_prompt()

    def clear_session(self):
        self.history    = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        return "Session reset. Memory cleared."

    def get_dashboard_stats(self):
        uptime      = str(datetime.now() - self.start_time).split('.')[0]
        jobs        = self.scheduler.get_jobs()
        active_tasks = [{"id": j.id, "trigger": str(j.trigger), "instruction": j.args[2]}
                        for j in jobs]

        activity_data = [0] * 7
        try:
            for f in os.listdir(self.chats_dir):
                if f.endswith('.md'):
                    st = os.stat(os.path.join(self.chats_dir, f))
                    activity_data[datetime.fromtimestamp(st.st_mtime).weekday()] += 1
        except Exception:
            pass

        cpu_usage = ram_usage = 0.0
        if psutil:
            try:
                cpu_usage = psutil.cpu_percent()
                ram_usage = psutil.virtual_memory().percent
            except Exception:
                pass

        ws_files = ws_size = 0
        try:
            for root, _, files in os.walk(self.workspace_dir):
                ws_files += len(files)
                ws_size  += sum(os.path.getsize(os.path.join(root, n)) for n in files)
        except Exception:
            pass

        return {
            "uptime":       uptime,
            "total_tokens": self.total_tokens,
            "active_tasks": active_tasks,
            "activity":     activity_data,
            "tool_usage":   self.tool_usage,
            "system":       {"cpu": cpu_usage, "ram": ram_usage},
            "workspace":    {"files": ws_files, "size": round(ws_size / (1024 * 1024), 2)},
            "provider":     self.config['default_provider'],
            "model":        self.config[self.config['default_provider']]['model'],
            "channels":     ["Terminal", "Web UI"] + (["Telegram"] if self.tg_app else []),
        }

    def get_settings(self):
        user_md_path = os.path.join(self.base_dir, 'common', 'user.md')
        prompt = ""
        if os.path.exists(user_md_path):
            with open(user_md_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
        provider = self.config.get('default_provider', 'ollama')
        temp     = self.config.get(provider, {}).get('temperature', 0.7)
        return {"system_prompt": prompt, "temperature": temp}

    def _load_tasks(self):
        if os.path.exists(self.tasks_path):
            with open(self.tasks_path, 'r') as f:
                tasks = yaml.safe_load(f) or []
                for t in tasks:
                    self.add_scheduled_task(t['type'], t['args'], t['instruction'], save=False)

    def _save_tasks(self):
        tasks = [{'type': j.args[0], 'args': j.args[1], 'instruction': j.args[2]}
                 for j in self.scheduler.get_jobs()]
        with open(self.tasks_path, 'w') as f:
            yaml.dump(tasks, f)

    def add_scheduled_task(self, trigger_type, trigger_args, instruction, save=True):
        try:
            if trigger_type == 'cron':
                trigger = CronTrigger.from_crontab(trigger_args)
            elif trigger_type == 'interval':
                if trigger_args.endswith('s'):
                    trigger = IntervalTrigger(seconds=int(trigger_args[:-1]))
                elif trigger_args.endswith('m'):
                    trigger = IntervalTrigger(minutes=int(trigger_args[:-1]))
                else:
                    trigger = IntervalTrigger(minutes=int(trigger_args))
            else:
                return f"Error: Unsupported trigger type {trigger_type}"
            task_id = str(uuid.uuid4())[:8]
            self.scheduler.add_job(
                self.execute_scheduled_task, trigger,
                args=[trigger_type, trigger_args, instruction],
                id=task_id,
            )
            if save:
                self._save_tasks()
            return f"Success: Task {task_id} scheduled ({trigger_type}: {trigger_args})"
        except Exception as e:
            return f"Error scheduling task: {e}"

    def remove_scheduled_task(self, identifier):
        try:
            try:
                self.scheduler.remove_job(identifier)
                self._save_tasks()
                return f"Success: Task {identifier} removed."
            except Exception:
                pass
            jobs = self.scheduler.get_jobs()
            removed = 0
            for j in jobs:
                if identifier.lower() in j.args[2].lower():
                    self.scheduler.remove_job(j.id)
                    removed += 1
            if removed:
                self._save_tasks()
                return f"Success: Removed {removed} task(s) matching '{identifier}'."
            return f"Error: No task found matching '{identifier}'."
        except Exception as e:
            return f"Error: {e}"

    async def execute_scheduled_task(self, t_type, t_args, instruction):
        try:
            self.system_prompt = self._load_system_prompt()
            print(f"\n{self.ORANGE}{self.BOLD}⏰ AUTONOMOUS TASK{self.RESET} {self.DIM}»{self.RESET} {instruction}")
            reply = await self.process_message(f"AUTONOMOUS SCHEDULED TASK: {instruction}", source="AUTO")
            if reply:
                try:
                    push_notification(f"⏰ {reply}")
                except Exception:
                    pass
                if self.tg_app and self.last_tg_chat_id:
                    try:
                        await self.tg_app.bot.send_message(chat_id=self.last_tg_chat_id, text=f"🔔 {reply}")
                    except Exception:
                        pass
        except Exception as e:
            import traceback
            print(f"\n{self.RED}{self.BOLD}[!] SCHEDULED TASK ERROR:{self.RESET} {e}")
            traceback.print_exc()

    # ─────────────────────────────────────────────────────────────────────────
    # SYSTEM PROMPT — Enhanced Android Edition
    # ─────────────────────────────────────────────────────────────────────────
    def _load_system_prompt(self):
        user_md_path = os.path.join(self.base_dir, 'common', 'user.md')
        if not os.path.exists(user_md_path):
            with open(user_md_path, 'w', encoding='utf-8') as f:
                f.write("# User Profile\n- Initialized")

        with open(user_md_path, 'r', encoding='utf-8') as f:
            user_content = f.read()

        current_time = datetime.now().strftime("%A, %B %d, %Y, %H:%M:%S")

        return f"""\
{user_content}

You are VoidClaw, an evolutionary autonomous AI agent.
You were conceptualized and built by Mohd Abuzar.
System Time: {current_time}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE DIRECTIVES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Continuously learn the user's workflow from every interaction and record
  discoveries using update_user_profile.
- Each conversation thread is isolated. Long-term knowledge lives in the
  User Profile above.
- Respond ONLY in JSON when invoking a tool; otherwise respond naturally.
- Tool JSON format:
  {{"thought": "step-by-step reasoning", "tool": "tool_name", "args": {{...}}}}
- You may chain up to 5 tool calls before producing a final answer.
- For ANDROID tasks that touch multiple steps (e.g. open app → tap → screenshot)
  always prefer android_macro over separate calls.
- When a prompt clearly requests app installation, ALWAYS call install_app —
  never just give instructions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── FILE SYSTEM ──────────────────────────────────
list_files
list_files_recursive
get_workspace_tree
read_file: filename              (.txt .md .py .pdf .xlsx supported)
write_file: filename, content
delete_file: filename
create_directory: path
move_file: src, dest
rename_file: old_name, new_name

── WEB & MEDIA ──────────────────────────────────
web_search: query
web_scrape: url
fetch_youtube_transcript: url
fetch_weather: city
download_youtube: url, format_type (video/audio)
convert_media: input_file, output_format

── MEMORY & CONFIG ──────────────────────────────
get_memory
update_memory: fact
update_user_profile: info
update_config: key, value [, subkey]

── INTELLIGENCE ─────────────────────────────────
python_sandbox: code
local_rag_search: query

── SCHEDULING ───────────────────────────────────
schedule_task: trigger_type (cron/interval), schedule_args, instruction
list_tasks
remove_task: keyword
remove_all_tasks
remind_me: message, time_args   (e.g. '5m', '30s', '1h')
stop_reminders: keyword

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANDROID TOOLS  (Shizuku-powered — Android/Termux only)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

── INSTALL APP ──────────────────────────────────
install_app: [app_name] OR [package_name] OR [apk_url] OR [apk_path]

  The single-prompt app installer. Resolves 100+ popular apps by name,
  auto-downloads from F-Droid or vendor URLs, and runs pm install.
  Falls back to opening the Play Store listing automatically.

  Examples (all valid):
    install_app(app_name="telegram")
    install_app(app_name="vlc")
    install_app(app_name="signal")
    install_app(app_name="whatsapp")
    install_app(package_name="org.mozilla.firefox")
    install_app(apk_url="https://example.com/custom.apk")
    install_app(apk_path="myapp.apk")          ← file in workspace

  Supported name examples (not exhaustive):
    whatsapp, telegram, signal, discord, instagram, youtube, netflix,
    spotify, vlc, firefox, brave, chrome, termux, fdroid, aurora,
    bitwarden, protonvpn, nordvpn, gmail, notion, obsidian, todoist,
    tasker, shizuku, canta, gpay, phonepe, paytm, amazon, flipkart,
    minecraft, bgmi, open camera, kodi, jellyfin, rethink dns …

── MANAGE APP ───────────────────────────────────
manage_app: action, [app_name OR package_name], [extra]

  Actions:
    uninstall    — remove app (system apps are hidden instead)
    enable       — re-enable a disabled app
    disable      — hide app without uninstalling
    clear_data   — wipe app data (factory-reset for one app)
    clear_cache  — clear cache only
    force_stop   — kill running app
    info         — version, install date, paths
    permissions  — list all granted permissions
    grant        — grant a permission (extra="android.permission.NAME")
    revoke       — revoke a permission
    update       — open Play Store update page

  Examples:
    manage_app(action="uninstall", app_name="tiktok")
    manage_app(action="disable",   package_name="com.miui.analytics")
    manage_app(action="clear_data", app_name="instagram")
    manage_app(action="grant",     package_name="com.example", extra="android.permission.CAMERA")
    manage_app(action="info",      app_name="telegram")

── LIST PACKAGES ────────────────────────────────
list_packages: filter_type (user/system/all/disabled/enabled), [search]

  Examples:
    list_packages(filter_type="user")
    list_packages(filter_type="system", search="miui")
    list_packages(filter_type="disabled")

── ANDROID CONTROL ──────────────────────────────
android_control: action, [target]

  APP LAUNCH:
    open_app       target=package_name
    open_url       target=URL

  NAVIGATION:
    home | back | recents | menu | lock | power

  MEDIA:
    media_play_pause | media_next | media_prev | media_stop
    volume_up | volume_down | volume_mute
    volume_set        target=0-15

  DISPLAY:
    brightness_set    target=0-255
    brightness_auto | brightness_manual
    dark_mode_on | dark_mode_off
    auto_rotate_on | auto_rotate_off
    font_scale        target=0.85–1.3
    keep_screen_on
    screen_timeout    target=seconds
    wm_size | wm_density
    wm_density_set    target=dpi
    wm_density_reset

  CONNECTIVITY:
    wifi_on | wifi_off
    bluetooth_on | bluetooth_off
    mobile_data_on | mobile_data_off
    airplane_mode_on | airplane_mode_off
    hotspot_on | hotspot_off
    nfc_on | nfc_off

  SYSTEM TOGGLES:
    flashlight_on | flashlight_off
    dnd_on | dnd_off
    battery_saver_on | battery_saver_off

  NOTIFICATION BAR:
    expand_notifications | expand_quick_settings | collapse_notifications

  TOUCH INPUT:
    tap              target="x y"
    long_press       target="x y"
    double_tap       target="x y"
    swipe            target="x1 y1 x2 y2 [duration_ms]"
    swipe_up | swipe_down | swipe_left | swipe_right
    scroll_up | scroll_down
    type_text        target=text_to_type

  SCREEN CAPTURE:
    screenshot                          (saved to workspace)
    record_start     target=seconds     (default 30)
    record_stop

  INFORMATION:
    get_battery | get_current_app | get_wifi_info | get_running_apps
    wm_size | wm_density

  SETTINGS DEEP LINKS:
    open_settings
    open_settings_wifi | open_settings_bt
    open_settings_dev
    open_settings_app  target=package_name
    open_play_store    target=package_name

  COMMUNICATION INTENTS:
    call_number        target=phone_number
    send_sms           target="number|message"
    share_text         target=text
    set_alarm          target="HH:MM"
    set_timer          target=seconds

  RAW SHELL:
    raw_shell          target=shell_command    (full ADB-level shell)

── LAUNCH INTENT ────────────────────────────────
launch_intent: action, [data], [package], [activity], [extras]

  Fire arbitrary Android intents.
  Examples:
    launch_intent(action="VIEW", data="https://google.com")
    launch_intent(action="MAIN", package="com.android.settings")
    launch_intent(activity="com.example.app/.MainActivity")
    launch_intent(action="CALL", data="tel:+911234567890")

── GET SYSTEM INFO ──────────────────────────────
get_system_info   (no args)
  Returns: device model, Android version, SDK, CPU ABI, RAM, storage,
           battery, WiFi SSID, IP address, installed app count.

── ANDROID MACRO ────────────────────────────────
android_macro: steps (JSON list)

  Execute a multi-step sequence atomically. Steps are dicts with:
    {{"action": "...", "target": "..."}}     → android_control
    {{"delay": 1.5}}                         → wait N seconds
    {{"install": "app_name"}}               → install_app
    {{"manage": "action", "pkg": "..."}}    → manage_app

  Example — open Settings, navigate, screenshot:
    android_macro([
      {{"action": "home"}},
      {{"action": "open_app", "target": "com.android.settings"}},
      {{"delay": 1}},
      {{"action": "tap", "target": "540 400"}},
      {{"delay": 0.5}},
      {{"action": "screenshot"}}
    ])

  Example — mass-install apps:
    android_macro([
      {{"install": "telegram"}},
      {{"install": "vlc"}},
      {{"install": "brave"}},
      {{"install": "bitwarden"}}
    ])

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANDROID USAGE EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Install WhatsApp"
  → install_app(app_name="whatsapp")

"Install Telegram and VLC"
  → android_macro([{{"install":"telegram"}},{{"install":"vlc"}}])

"Uninstall TikTok"
  → manage_app(action="uninstall", app_name="tiktok")

"Disable all MIUI bloatware analytics apps"
  → list_packages(filter_type="system", search="miui")
    then manage_app(action="disable", package_name="...") for each

"Turn off WiFi, enable mobile data, set brightness to half"
  → android_macro([
      {{"action":"wifi_off"}},
      {{"action":"mobile_data_on"}},
      {{"action":"brightness_set","target":"128"}}
    ])

"Take a screenshot of what's on screen"
  → android_control(action="screenshot")

"Open YouTube and play"
  → android_macro([
      {{"action":"open_app","target":"com.google.android.youtube"}},
      {{"delay":2}},
      {{"action":"media_play_pause"}}
    ])

"What apps do I have installed?"
  → list_packages(filter_type="user")

"Show me full device info"
  → get_system_info()

"Schedule a task to turn WiFi off at 11 PM every night"
  → schedule_task(trigger_type="cron", schedule_args="0 23 * * *",
                  instruction="Turn off WiFi to save battery")
    (when triggered: android_control(action="wifi_off"))

Respond normally (not JSON) for final answers.
"""

    # ─────────────────────────────────────────────────────────────────────────
    def log_chat(self, role, message):
        log_file  = os.path.join(self.chats_dir, f"session_{self.session_id}.md")
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"### [{timestamp}] {role}\n{message}\n\n")

    def _parse_json(self, response):
        try:
            return json.loads(response)
        except Exception:
            for marker in ["```json", "```"]:
                if marker in response:
                    try:
                        content = response.split(marker)[1].split("```")[0].strip()
                        return json.loads(content)
                    except Exception:
                        pass
        return None

    async def process_message(self, user_input, source="TERM"):
        prefix = "👤 YOU" if source == "TERM" else f"👤 YOU ({source})"
        context_history = []

        if source != "AUTO":
            print(f"\n{self.AMBER}{self.BOLD}{prefix}{self.RESET} {self.DIM}»{self.RESET} {user_input}")
            self.log_chat(f"USER ({source})", user_input)
            self.history.append({"role": "user", "content": user_input})
            self.total_tokens += len(user_input) // 4
            context_history = self.history[-10:]

        context = "\n".join(f"{m['role']}: {m['content']}" for m in context_history)
        if source == "AUTO":
            context = f"SYSTEM: {user_input}"

        for _ in range(5):
            response  = await self.model.generate_response(context, self.system_prompt)
            tool_call = self._parse_json(response)

            if tool_call and isinstance(tool_call, dict) and "tool" in tool_call:
                thought = tool_call.get('thought', 'Processing...')
                print(f"\n{self.ORANGE}{self.BOLD}💭 THOUGHT{self.RESET} {self.DIM}»{self.RESET} {thought}")
                print(f"{self.AMBER}{self.BOLD}🛠  ACTION{self.RESET}  {self.DIM}»{self.RESET} {tool_call['tool']}")

                observation = self.tools.execute_tool(tool_call['tool'], tool_call['args'])
                self.tool_usage[tool_call['tool']] = self.tool_usage.get(tool_call['tool'], 0) + 1

                if tool_call['tool'] == 'update_config' and 'Success' in observation:
                    self.reload_config()

                print(f"{self.GREEN}{self.BOLD}👁  OBSERVE{self.RESET} {self.DIM}»{self.RESET} Task Success")
                self.log_chat("VOIDCLAW_THOUGHT", thought)
                self.log_chat("VOIDCLAW_ACTION",  f"Tool: {tool_call['tool']}")
                self.log_chat("OBSERVATION",       observation)

                context += f"\nAgent Thought: {thought}\nObservation from {tool_call['tool']}: {observation}"
                continue
            else:
                if source == "AUTO":
                    print(f"\n{self.ORANGE}{self.BOLD}📡 PROACTIVE{self.RESET} {self.DIM}»{self.RESET} {response}")
                else:
                    print(f"\n{self.ORANGE}{self.BOLD}{self.LOGO}   VOIDCLAW{self.RESET} {self.DIM}»{self.RESET} {response}")
                self.log_chat("VOIDCLAW_RESPONSE", response)
                if source != "AUTO":
                    self.history.append({"role": "assistant", "content": response})
                return response
        return "Reasoning limit reached."

    async def process_message_stream(self, user_input):
        print(f"\n{self.AMBER}{self.BOLD}👤 YOU (WEB){self.RESET} {self.DIM}»{self.RESET} {user_input}")
        self.log_chat("USER (WEB)", user_input)
        self.history.append({"role": "user", "content": user_input})
        context = "\n".join(f"{m['role']}: {m['content']}" for m in self.history[-10:])

        final_text = ""
        for _ in range(5):
            response  = await self.model.generate_response(context, self.system_prompt)
            tool_call = self._parse_json(response)

            if tool_call and isinstance(tool_call, dict) and "tool" in tool_call:
                thought = tool_call.get('thought', 'Thinking...')
                print(f"\n{self.ORANGE}{self.BOLD}💭 THOUGHT (WEB){self.RESET} {self.DIM}»{self.RESET} {thought}")
                print(f"{self.AMBER}{self.BOLD}🛠  ACTION (WEB){self.RESET}  {self.DIM}»{self.RESET} {tool_call['tool']}")
                yield f"THOUGHT:{thought} | Executing {tool_call['tool']}..."

                observation = self.tools.execute_tool(tool_call['tool'], tool_call['args'])
                print(f"{self.GREEN}{self.BOLD}👁  OBSERVE (WEB){self.RESET} {self.DIM}»{self.RESET} Task Success")
                self.log_chat("VOIDCLAW_THOUGHT", thought)
                self.log_chat("VOIDCLAW_ACTION",  f"Tool: {tool_call['tool']}")
                self.log_chat("OBSERVATION",       observation)

                context += f"\nAgent Thought: {thought}\nObservation: {observation}"
                continue
            else:
                print(f"\n{self.ORANGE}{self.BOLD}{self.LOGO}   VOIDCLAW (WEB){self.RESET} {self.DIM}»{self.RESET} Streaming...")
                yield "START_STREAM"
                async for chunk in self.model.generate_stream(context, self.system_prompt):
                    if self.interrupted:
                        yield "CHUNK:\n\n[TRANSMISSION INTERRUPTED]"
                        self.interrupted = False
                        break
                    final_text += chunk
                    yield f"CHUNK:{chunk}"
                self.log_chat("VOIDCLAW_RESPONSE", final_text)
                self.history.append({"role": "assistant", "content": final_text})
                break


# ─────────────────────────────────────────────────────────────────────────────
def print_dashboard(config):
    ORANGE, GREEN, AMBER, RESET, BOLD = '\033[38;5;214m', '\033[92m', '\033[93m', '\033[0m', '\033[1m'
    logo = r"""
      ██╗   ██╗ ██████╗ ██╗██████╗  ██████╗██╗      █████╗ ██╗    ██╗
      ██║   ██║██╔═══██╗██║██╔══██╗██╔════╝██║     ██╔══██╗██║    ██║
      ██║   ██║██║   ██║██║██║  ██║██║     ██║     ███████║██║ █╗ ██║
      ╚██╗ ██╔╝██║   ██║██║██║  ██║██║     ██║     ██╔══██║██║███╗██║
       ╚████╔╝ ╚██████╔╝██║██████╔╝╚██████╗███████╗██║  ██║╚███╔███╔╝
        ╚═══╝   ╚═════╝ ╚═╝╚═════╝  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝

           A U T O N O M O U S   C O M M A N D   C E N T E R   [ A N D R O I D   E D I T I O N ]
    """
    print(f"{ORANGE}━" * 64)
    print(f"{ORANGE}{logo}{RESET}")
    print(f"{AMBER}           AI Agent for Windows, Mac, Android & Linux{RESET}")
    print(f"{ORANGE}━" * 64 + RESET)
    print(f"{ORANGE}{BOLD}𒆙   VoidClaw Hybrid Interface v2.0.0  [Android-Supercharged]{RESET}")
    print(f"{AMBER}PROVIDER: {RESET}{config['default_provider'].upper()} | "
          f"{AMBER}MODEL: {RESET}{config[config['default_provider']]['model']}")
    print(f"{AMBER}CHANNELS: {GREEN}TERMINAL{RESET} & {GREEN}TELEGRAM{RESET} & {GREEN}WEB UI{RESET}")
    print(f"{AMBER}ANDROID:  {GREEN}Shizuku ✓{RESET}  |  {GREEN}install_app ✓{RESET}  |  "
          f"{GREEN}50+ actions ✓{RESET}  |  {GREEN}android_macro ✓{RESET}")
    print(f"{ORANGE}{'━'*64}{RESET}\n")


async def terminal_loop(agent):
    loop = asyncio.get_running_loop()
    while True:
        try:
            print(f"\033[38;5;214m\033[1m❯\033[0m ", end="", flush=True)
            user_input = await loop.run_in_executor(None, sys.stdin.readline)
            if not user_input:
                break
            user_input = user_input.strip()
            if user_input.lower() in ['exit', 'quit']:
                print("\033[91mShutting down VoidClaw...\033[0m")
                os._exit(0)
            if user_input.lower() == 'new chat':
                print(f"\033[92m{agent.clear_session()}\033[0m")
                continue
            if not user_input:
                continue
            await agent.process_message(user_input, source="TERM")
        except Exception as e:
            print(f"Terminal Error: {e}")
            break


async def main():
    base_dir    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, 'common', 'config.yaml')

    if not os.path.exists(config_path):
        print("\033[91m[!] Configuration file not found at common/config.yaml\033[0m")
        print("\033[93m[*] Please run the installation script first.\033[0m")
        return

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    agent = VoidClawAgent(config_path)

    # Auto-provision Shizuku on Android
    if os.path.exists('/data/data/com.termux'):
        agent.tools._provision_shizuku()

    os.system('cls' if os.name == 'nt' else 'clear')
    print_dashboard(config)

    web_thread = threading.Thread(target=start_web_server, args=(agent,), daemon=True)
    web_thread.start()

    print(f"\033[38;5;214m[SYSTEM]\033[0m Starting Autonomous Scheduler...")
    agent.scheduler.start()

    token = config.get('telegram_token', '').strip()
    if token and token != "YOUR_TELEGRAM_BOT_TOKEN":
        print(f"\033[38;5;214m[SYSTEM]\033[0m Establishing Telegram Secure Link...")

        async def handle_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not update.message or not update.message.text:
                return
            agent.last_tg_chat_id = update.effective_chat.id
            print(f"\n\033[38;5;214m[TELEGRAM]\033[0m Incoming from {update.effective_user.first_name}...")
            reply = await agent.process_message(update.message.text, source="TG")
            await update.message.reply_text(reply)

        for attempt in range(3):
            try:
                from telegram.request import HTTPXRequest
                request     = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
                application = ApplicationBuilder().token(token).request(request).build()
                agent.tg_app = application
                application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_tg))
                await application.initialize()
                await application.start()
                await application.updater.start_polling(drop_pending_updates=True)
                print(f"\033[92m[+] Telegram Bot active.\033[0m")
                await terminal_loop(agent)
                return
            except Exception as e:
                try:
                    if 'application' in locals():
                        await application.shutdown()
                except Exception:
                    pass
                if attempt < 2:
                    wait = (attempt + 1) * 5
                    print(f"\033[93m[!] Telegram retry {attempt+1}/3 in {wait}s... ({e})\033[0m")
                    await asyncio.sleep(wait)
                else:
                    print(f"\n\033[91m[!] Telegram Setup Failed: {e}\033[0m")
                    print("\033[93m[*] Continuing in Terminal + Web mode.\033[0m")
                    await terminal_loop(agent)
    else:
        print("\033[93m[!] Telegram token not set. Running in Terminal + Web mode.\033[0m")
        await terminal_loop(agent)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
