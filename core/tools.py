# =============================================================================
# tools.py — VoidClaw Agent  |  Android-First Edition
# All 13 audit bugs resolved. Verified for Termux / MIUI 12.5 / Android 11.
# =============================================================================

import os
import json
import time
import shlex
import shutil
import subprocess

from duckduckgo_search import DDGS

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import openpyxl
except ImportError:
    openpyxl = None


# ─────────────────────────────────────────────────────────────────────────────
# ANDROID PACKAGE RESOLUTION MAP  (100 + apps)
# ─────────────────────────────────────────────────────────────────────────────
ANDROID_PACKAGES = {
    # Messaging
    "whatsapp":             "com.whatsapp",
    "whatsapp business":    "com.whatsapp.w4b",
    "telegram":             "org.telegram.messenger",
    "telegram x":           "org.thunderdog.challegram",
    "signal":               "org.thoughtcrime.securesms",
    "messenger":            "com.facebook.orca",
    "discord":              "com.discord",
    "slack":                "com.Slack",
    "viber":                "com.viber.voip",
    "snapchat":             "com.snapchat.android",
    "wechat":               "com.tencent.mm",
    "imo":                  "com.imo.android.imoim",
    "teams":                "com.microsoft.teams",
    "skype":                "com.skype.raider",
    "line":                 "jp.naver.line.android",
    # Social
    "instagram":            "com.instagram.android",
    "facebook":             "com.facebook.katana",
    "twitter":              "com.twitter.android",
    "x":                    "com.twitter.android",
    "tiktok":               "com.zhiliaoapp.musically",
    "pinterest":            "com.pinterest",
    "reddit":               "com.reddit.frontpage",
    "linkedin":             "com.linkedin.android",
    "youtube":              "com.google.android.youtube",
    "youtube music":        "com.google.android.apps.youtube.music",
    "youtube kids":         "com.google.android.apps.youtube.kids",
    "threads":              "com.instagram.barcelona",
    # Browsers
    "chrome":               "com.android.chrome",
    "firefox":              "org.mozilla.firefox",
    "brave":                "com.brave.browser",
    "opera":                "com.opera.browser",
    "opera mini":           "com.opera.mini.native",
    "edge":                 "com.microsoft.emmx",
    "duckduckgo":           "com.duckduckgo.mobile.android",
    "via":                  "mark.via.gp",
    "kiwi":                 "com.kiwibrowser.browser",
    "bromite":              "org.bromite.bromite",
    # Streaming & Media
    "netflix":              "com.netflix.mediaclient",
    "spotify":              "com.spotify.music",
    "vlc":                  "org.videolan.vlc",
    "twitch":               "tv.twitch.android.app",
    "prime video":          "com.amazon.avod.thirdpartyclient",
    "amazon prime":         "com.amazon.avod.thirdpartyclient",
    "mx player":            "com.mxtech.videoplayer.ad",
    "mx player pro":        "com.mxtech.videoplayer.pro",
    "kodi":                 "org.xbmc.kodi",
    "hotstar":              "in.startv.hotstar",
    "jio cinema":           "com.jio.media.stb.ui",
    "zee5":                 "com.graymatrix.did",
    "plex":                 "com.plexapp.android",
    "jellyfin":             "org.jellyfin.mobile",
    # Productivity
    "word":                 "com.microsoft.office.word",
    "excel":                "com.microsoft.office.excel",
    "powerpoint":           "com.microsoft.office.powerpoint",
    "microsoft word":       "com.microsoft.office.word",
    "microsoft excel":      "com.microsoft.office.excel",
    "microsoft powerpoint": "com.microsoft.office.powerpoint",
    "google docs":          "com.google.android.apps.docs.editors.docs",
    "google sheets":        "com.google.android.apps.docs.editors.sheets",
    "google slides":        "com.google.android.apps.docs.editors.slides",
    "notion":               "notion.id",
    "obsidian":             "md.obsidian",
    "todoist":              "com.todoist.android.Todoist",
    "evernote":             "com.evernote",
    "onenote":              "com.microsoft.office.onenote",
    "adobe acrobat":        "com.adobe.reader",
    "adobe reader":         "com.adobe.reader",
    "pdf viewer":           "com.github.axet.pdfviewer",
    # Developer Tools
    "termux":               "com.termux",
    "f-droid":              "org.fdroid.fdroid",
    "fdroid":               "org.fdroid.fdroid",
    "aurora store":         "com.aurora.store",
    "aurora":               "com.aurora.store",
    "tasker":               "net.dinglisch.android.taskerm",
    "acode":                "com.foxdebug.acodefree",
    "spck editor":          "io.spck",
    "androidide":           "com.itsaky.androidide",
    "userland":             "tech.ula",
    "shizuku":              "moe.shizuku.privileged.api",
    "canta":                "io.github.markusressel.canta",
    "juicessh":             "com.sonelli.juicessh",
    "ssh client":           "com.sonelli.juicessh",
    # File Management
    "files by google":      "com.google.android.apps.nbu.files",
    "es file explorer":     "com.estrongs.android.pop",
    "total commander":      "com.ghisler.android.TotalCommander",
    "cx file explorer":     "com.cxinventor.file.explorer",
    "mixplorer":            "com.mixplorer",
    "solid explorer":       "pl.solidexplorer2",
    "mt manager":           "bin.mt.plus",
    # System
    "calculator":           "com.google.android.calculator",
    "maps":                 "com.google.android.apps.maps",
    "google maps":          "com.google.android.apps.maps",
    "clock":                "com.google.android.deskclock",
    "contacts":             "com.android.contacts",
    "settings":             "com.android.settings",
    "play store":           "com.android.vending",
    "google play":          "com.android.vending",
    "keep":                 "com.google.android.keep",
    "keep notes":           "com.google.android.keep",
    "photos":               "com.google.android.apps.photos",
    "gallery":              "com.miui.gallery",
    "miui gallery":         "com.miui.gallery",
    "mi gallery":           "com.miui.gallery",
    "miui security":        "com.miui.securitycenter",
    "security":             "com.miui.securitycenter",
    "mi remote":            "com.duokan.phone.remotecontroller",
    # Security & Privacy
    "bitwarden":            "com.x8bit.bitwarden",
    "1password":            "com.agilebits.onepassword",
    "lastpass":             "com.lastpass.lpandroid",
    "nordvpn":              "com.nordvpn.android",
    "expressvpn":           "com.expressvpn.vpn",
    "protonvpn":            "ch.protonvpn.android",
    "mullvad":              "net.mullvad.mullvadvpn",
    "rethink dns":          "com.celzero.bravedns",
    "netguard":             "eu.faircode.netguard",
    "adaway":               "org.adaway",
    "blokada":              "org.blokada.alarm",
    # Finance
    "gpay":                 "com.google.android.apps.nbu.paisa.user",
    "google pay":           "com.google.android.apps.nbu.paisa.user",
    "phonepe":              "com.phonepe.app",
    "paytm":                "net.one97.paytm",
    "amazon":               "in.amazon.mShop.android.shopping",
    "flipkart":             "com.flipkart.android",
    "cred":                 "com.dreamplug.androidapp",
    # Email
    "gmail":                "com.google.android.gm",
    "outlook":              "com.microsoft.office.outlook",
    "protonmail":           "ch.protonmail.android",
    "proton mail":          "ch.protonmail.android",
    "k-9 mail":             "com.fsck.k9",
    "k9 mail":              "com.fsck.k9",
    "yahoo mail":           "com.yahoo.mobile.client.android.mail",
    # Games
    "minecraft":            "com.mojang.minecraftpe",
    "bgmi":                 "com.pubg.imobile",
    "pubg mobile":          "com.tencent.ig",
    "free fire":            "com.dts.freefireth",
    "clash of clans":       "com.supercell.clashofclans",
    "clash royale":         "com.supercell.clashroyale",
    "candy crush":          "com.king.candycrushsaga",
    "roblox":               "com.roblox.client",
    # Camera
    "open camera":          "net.sourceforge.opencamera",
    "google camera":        "com.google.android.GoogleCamera",
    "gcam":                 "com.google.android.GoogleCamera",
}

# Known vendor-hosted direct APK download URLs
DIRECT_APK_URLS = {
    "com.whatsapp": "https://www.whatsapp.com/android/current/WhatsApp.apk",
}

# F-Droid available packages (used to prioritise F-Droid over Play Store)
FDROID_PACKAGES = {
    "org.telegram.messenger",
    "org.thoughtcrime.securesms",
    "org.videolan.vlc",
    "org.mozilla.firefox",
    "org.fdroid.fdroid",
    "net.mullvad.mullvadvpn",
    "ch.protonvpn.android",
    "com.duckduckgo.mobile.android",
    "org.xbmc.kodi",
    "com.x8bit.bitwarden",
    "ch.protonmail.android",
    "com.fsck.k9",
    "net.sourceforge.opencamera",
    "eu.faircode.netguard",
    "org.adaway",
    "com.celzero.bravedns",
    "tech.ula",
    "org.jellyfin.mobile",
    "com.github.axet.pdfviewer",
    "org.blokada.alarm",
}

# BUG-1 FIX: /sdcard/Download is writable by Termux after termux-setup-storage
# AND readable by shell (rish). /data/local/tmp is NOT writable by Termux UID.
_SDCARD_DL = "/sdcard/Download"
_RISH_TMP  = "/data/local/tmp"      # writable only by shell (via rish)


# =============================================================================
class ToolManager:
    def __init__(self, workspace_dir):
        self.workspace_dir = os.path.abspath(workspace_dir)
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
        self.agent     = None
        self._rish_bin = None   # cached after first successful probe

    def set_agent(self, agent):
        self.agent = agent

    # ── is this running inside Termux (raw, not proot)? ──────────────────────
    @staticmethod
    def _is_termux():
        return os.path.exists('/data/data/com.termux')

    def execute_tool(self, tool_name, args):
        tools = {
            # File System
            "list_files":               self.list_files,
            "list_files_recursive":     self.list_files_recursive,
            "get_workspace_tree":       self.get_workspace_tree,
            "read_file":                self.read_file,
            "write_file":               self.write_file,
            "delete_file":              self.delete_file,
            "create_directory":         self.create_directory,
            "move_file":                self.move_file,
            "rename_file":              self.rename_file,
            "read_pdf":                 self.read_pdf,
            "read_excel":               self.read_excel,
            # Web
            "web_search":               self.web_search,
            "web_scrape":               self.web_scrape,
            "fetch_youtube_transcript": self.fetch_youtube_transcript,
            "fetch_weather":            self.fetch_weather,
            # Media
            "download_youtube":         self.download_youtube,
            "convert_media":            self.convert_media,
            # Memory & Config
            "get_memory":               self.get_memory,
            "update_memory":            self.update_memory,
            "update_config":            self.update_config,
            "update_user_profile":      self.update_user_profile,
            # Intelligence
            "python_sandbox":           self.python_sandbox,
            "local_rag_search":         self.local_rag_search,
            # Scheduling
            "schedule_task":            self.schedule_task,
            "list_tasks":               self.list_tasks,
            "remove_task":              self.remove_task,
            "remove_all_tasks":         self.remove_all_tasks,
            "remind_me":                self.remind_me,
            "stop_reminders":           self.stop_reminders,
            # Android (all enhanced)
            "android_control":          self.android_control,
            "install_app":              self.install_app,
            "manage_app":               self.manage_app,
            "list_packages":            self.list_packages,
            "launch_intent":            self.launch_intent,
            "get_system_info":          self.get_system_info,
            "android_macro":            self.android_macro,
        }
        if tool_name in tools:
            return tools[tool_name](**args)
        return f"Error: Tool '{tool_name}' not found."

    # =========================================================================
    # SHIZUKU CORE
    # =========================================================================

    def _provision_shizuku(self):
        """
        Locate rish. Tries PATH → known paths → auto-imports from
        /sdcard/Shizuku/ if user exported files there. Result is cached.
        """
        if self._rish_bin and os.path.exists(self._rish_bin):
            return self._rish_bin
        if not self._is_termux():
            return None

        # 1. In PATH already
        rish = shutil.which('rish')
        if rish:
            self._rish_bin = rish
            return rish

        # 2. Known locations
        for p in [
            '/data/data/com.termux/files/usr/bin/rish',
            '/data/data/com.termux/files/home/.local/bin/rish',
            '/data/data/com.termux/files/usr/local/bin/rish',
        ]:
            if os.path.exists(p):
                self._rish_bin = p
                return p

        # 3. Auto-provision from /sdcard/Shizuku/ (user exported from Shizuku app)
        src      = '/sdcard/Shizuku'
        dest_bin = '/data/data/com.termux/files/usr/bin'
        rish_src = os.path.join(src, 'rish')
        dex_src  = os.path.join(src, 'rish_shizuku.dex')
        if os.path.exists(rish_src) and os.path.exists(dex_src):
            try:
                dest_rish = os.path.join(dest_bin, 'rish')
                dest_dex  = os.path.join(dest_bin, 'rish_shizuku.dex')
                os.system(f'cp "{rish_src}" "{dest_rish}"')
                os.system(f'cp "{dex_src}"  "{dest_dex}"')
                os.system(f'chmod +x  "{dest_rish}"')
                os.system(f'chmod 444 "{dest_dex}"')
                if os.path.exists(dest_rish):
                    self._rish_bin = dest_rish
                    print("\033[92m[SYSTEM]\033[0m Shizuku provisioned successfully.")
                    return dest_rish
            except Exception as e:
                print(f"\033[91m[!] Shizuku auto-import failed:\033[0m {e}")
        return None

    def _rish_exec(self, cmd, timeout=20):
        """
        Run a shell command via rish (Shizuku ADB-level shell).
        Returns (stdout, stderr, returncode).
        """
        rish = self._provision_shizuku()
        if not rish:
            return "", "Shizuku not available.", 1
        env = os.environ.copy()
        env["RISH_APPLICATION_ID"] = "com.termux"
        try:
            r = subprocess.run(
                ["sh", rish, "-c", cmd],
                capture_output=True, text=True,
                timeout=timeout, env=env,
            )
            return r.stdout, r.stderr, r.returncode
        except subprocess.TimeoutExpired:
            return "", f"Timed out after {timeout}s — is Shizuku service running?", 1
        except Exception as e:
            return "", str(e), 1

    def _rish_result(self, cmd, timeout=20, success_msg=None):
        """Convenience wrapper: runs cmd via rish, returns a readable string."""
        stdout, stderr, code = self._rish_exec(cmd, timeout)
        if code == 0:
            out = stdout.strip()
            return success_msg or (out if out else "Done.")
        err = stderr.strip() or stdout.strip() or "Unknown error"
        return f"Error: {err}"

    # =========================================================================
    # ANDROID CONTROL — 50 + actions
    # =========================================================================

    def android_control(self, action, target=""):
        """
        Unified Android system control via Shizuku (ADB-level shell).
        All shell commands are safe-quoted where needed.

        Quick reference:
          open_app target=package_name
          tap / long_press / double_tap  target="x y"
          swipe  target="x1 y1 x2 y2 [ms]"
          type_text  target=text
          brightness_set  target=0-255
          volume_set  target=0-15
          screen_timeout  target=seconds
          open_url  target=URL
          call_number  target=phone_number
          send_sms  target="number|message"
          set_alarm  target="HH:MM"
          raw_shell  target=shell_command
        """
        if not self._is_termux():
            return "Error: android_control only works in Termux on Android."

        if not self._provision_shizuku():
            return (
                "Shizuku not set up. Steps:\n"
                "  1. Install Shizuku from F-Droid or Play Store.\n"
                "  2. Enable Wireless Debugging → start Shizuku service.\n"
                "  3. Shizuku app → 'Use Shizuku in terminal apps' → 'Export files'\n"
                "     → save to /sdcard/Shizuku/\n"
                "  4. In Termux: termux-setup-storage\n"
                "  5. Retry."
            )

        t = str(target).strip()

        # BUG-4 FIX: type_text — use shlex.quote so single-quotes in text don't
        # break the shell command.
        t_quoted = shlex.quote(t)

        # BUG-5 FIX: screen_timeout — guard against empty target
        timeout_ms = f"{int(t) * 1000}" if t.isdigit() else ("60000" if not t else t)

        cmd_map = {
            # ── App launch ───────────────────────────────────────────────────
            "open_app":              (
                f"am start -a android.intent.action.MAIN "
                f"-c android.intent.category.LAUNCHER --package {t} 2>/dev/null "
                f"|| monkey -p {t} -c android.intent.category.LAUNCHER 1"
            ),
            # ── Navigation ───────────────────────────────────────────────────
            "home":                  "input keyevent 3",
            "back":                  "input keyevent 4",
            "recents":               "input keyevent 187",
            "menu":                  "input keyevent 82",
            "power":                 "input keyevent 26",
            "lock":                  "input keyevent 26",
            # ── Media keys ───────────────────────────────────────────────────
            "media_play_pause":      "input keyevent 85",
            "media_next":            "input keyevent 87",
            "media_prev":            "input keyevent 88",
            "media_stop":            "input keyevent 86",
            "volume_up":             "input keyevent 24",
            "volume_down":           "input keyevent 25",
            "volume_mute":           "input keyevent 164",
            "volume_set":            f"media volume --stream 3 --set {t}",
            # ── Display ──────────────────────────────────────────────────────
            "screen_off":            "input keyevent 26",
            "brightness_set":        f"settings put system screen_brightness {t}",
            "brightness_auto":       "settings put system screen_brightness_mode 1",
            "brightness_manual":     "settings put system screen_brightness_mode 0",
            "dark_mode_on":          "cmd uimode night yes",
            "dark_mode_off":         "cmd uimode night no",
            "auto_rotate_on":        "settings put system accelerometer_rotation 1",
            "auto_rotate_off":       "settings put system accelerometer_rotation 0",
            "font_scale":            f"settings put system font_scale {t or '1.0'}",
            "keep_screen_on":        "svc power stayon true",
            # BUG-5 FIX: empty-target guard via timeout_ms computed above
            "screen_timeout":        f"settings put system screen_off_timeout {timeout_ms}",
            "wm_size":               "wm size",
            "wm_density":            "wm density",
            "wm_density_set":        f"wm density {t}",
            "wm_density_reset":      "wm density reset",
            # ── Connectivity ─────────────────────────────────────────────────
            "wifi_on":               "svc wifi enable",
            "wifi_off":              "svc wifi disable",
            "bluetooth_on":          "svc bluetooth enable",
            "bluetooth_off":         "svc bluetooth disable",
            "mobile_data_on":        "svc data enable",
            "mobile_data_off":       "svc data disable",
            "airplane_mode_on": (
                "settings put global airplane_mode_on 1 && "
                "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true"
            ),
            "airplane_mode_off": (
                "settings put global airplane_mode_on 0 && "
                "am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false"
            ),
            "hotspot_on":            "svc wifi hotspot enable",
            "hotspot_off":           "svc wifi hotspot disable",
            "nfc_on":                "svc nfc enable",
            "nfc_off":               "svc nfc disable",
            # ── Toggles ──────────────────────────────────────────────────────
            "flashlight_on":         "cmd notification set_flashlight 1",
            "flashlight_off":        "cmd notification set_flashlight 0",
            "dnd_on":                "cmd notification set_dnd on",
            "dnd_off":               "cmd notification set_dnd off",
            "battery_saver_on":      "settings put global low_power 1",
            "battery_saver_off":     "settings put global low_power 0",
            # ── Notification bar ─────────────────────────────────────────────
            "expand_notifications":  "cmd statusbar expand-notifications",
            "expand_quick_settings": "cmd statusbar expand-settings",
            "collapse_notifications":"cmd statusbar collapse",
            # ── Touch input ──────────────────────────────────────────────────
            "tap":                   f"input tap {t}",
            # long_press: swipe from coords to same coords for 1000 ms
            "long_press":            f"input swipe {t} {t} 1000",
            # BUG-12 FIX: sub-second sleep — try toybox sleep 0.1,
            # fall back to 1s sleep if shell doesn't support decimals
            "double_tap": (
                f"input tap {t}"
                f" && {{ sleep 0.1 2>/dev/null || sleep 1; }}"
                f" && input tap {t}"
            ),
            "swipe":                 f"input swipe {t}",
            "swipe_up":              "input swipe 540 1200 540 400 300",
            "swipe_down":            "input swipe 540 400 540 1200 300",
            "swipe_left":            "input swipe 900 700 200 700 300",
            "swipe_right":           "input swipe 200 700 900 700 300",
            "scroll_up":             "input roll 0 -3",
            "scroll_down":           "input roll 0 3",
            # BUG-3 FIX: shlex.quote handles single-quotes and special chars
            "type_text":             f"input text {t_quoted}",
            # ── Screen capture ───────────────────────────────────────────────
            "screenshot":            "__SCREENSHOT__",   # handled specially below
            # NOTE-1 FIX: screenrecord not on all MIUI builds — check first
            "record_start": (
                f"which screenrecord >/dev/null 2>&1 "
                f"&& screenrecord --time-limit {t or '30'} /sdcard/Download/vc_record.mp4 "
                f"|| echo 'Error: screenrecord not available on this device'"
            ),
            "record_stop":           "pkill screenrecord 2>/dev/null || true",
            # ── Information ──────────────────────────────────────────────────
            "get_battery": (
                "dumpsys battery | grep -E '(level|status|health|voltage|temperature)'"
            ),
            "get_current_app": (
                "dumpsys window | grep -E '(mCurrentFocus|mFocusedApp)' | head -3"
            ),
            "get_wifi_info": (
                "dumpsys wifi | grep -E '(mWifiInfo|SSID=|Frequency|LinkSpeed|RSSI|ipAddress)'"
                " | head -10"
            ),
            "get_running_apps": (
                "dumpsys activity recents | grep 'Recent #' | head -10"
            ),
            # ── Intents & deep links ─────────────────────────────────────────
            "open_url":              f"am start -a android.intent.action.VIEW -d '{t}'",
            "open_settings":         "am start -n com.android.settings/.Settings",
            "open_settings_wifi":    "am start -a android.settings.WIFI_SETTINGS",
            "open_settings_bt":      "am start -a android.settings.BLUETOOTH_SETTINGS",
            "open_settings_dev":     "am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
            "open_settings_app":     f"am start -a android.settings.APPLICATION_DETAILS_SETTINGS -d 'package:{t}'",
            "open_play_store":       f"am start -a android.intent.action.VIEW -d 'market://details?id={t}'",
            "share_text":            f"am start -a android.intent.action.SEND -t text/plain --es android.intent.extra.TEXT {t_quoted}",
            "call_number":           f"am start -a android.intent.action.CALL -d tel:{t}",
            "send_sms": (
                "am start -a android.intent.action.SENDTO "
                f"-d smsto:{t.split('|')[0]} "
                "--es sms_body "
                + (shlex.quote(t.split('|')[1]) if '|' in t else "''")
            ),
            "set_alarm": (
                f"am start -a android.intent.action.SET_ALARM "
                f"--ei android.intent.extra.alarm.HOUR {t.split(':')[0] if ':' in t else '8'} "
                f"--ei android.intent.extra.alarm.MINUTES {t.split(':')[1] if ':' in t else '0'}"
            ),
            "set_timer": (
                f"am start -a android.intent.action.SET_TIMER "
                f"--ei android.intent.extra.alarm.LENGTH {t}"
            ),
            # ── Raw shell ────────────────────────────────────────────────────
            "raw_shell":             t,
        }

        if action not in cmd_map:
            return (
                f"Error: Unknown action '{action}'.\n"
                f"Available ({len(cmd_map)}): {', '.join(sorted(cmd_map.keys()))}"
            )

        # Screenshot: binary output — pipe directly to file ──────────────────
        if action == "screenshot":
            try:
                rish = self._provision_shizuku()
                env  = os.environ.copy()
                env["RISH_APPLICATION_ID"] = "com.termux"
                fname = f"screenshot_{os.urandom(2).hex()}.png"
                dest  = os.path.join(self.workspace_dir, fname)
                with open(dest, "wb") as f:
                    subprocess.run(
                        ["sh", rish, "-c", "screencap -p"],
                        stdout=f, env=env, timeout=20,
                    )
                sz = os.path.getsize(dest)
                if sz < 1024:
                    os.remove(dest)
                    return "Error: Screenshot failed — is Shizuku service running?"
                return f"✓ Screenshot saved → {fname} ({sz // 1024} KB)"
            except Exception as e:
                return f"Error taking screenshot: {e}"

        return self._rish_result(cmd_map[action],
                                 success_msg=f"✓ Action '{action}' executed.")

    # =========================================================================
    # INSTALL APP — natural-language pipeline
    # =========================================================================

    def install_app(self, app_name="", package_name="", apk_url="", apk_path=""):
        """
        Install any Android app from a single prompt.

        Priority:
          1. apk_path   → pm install directly
          2. apk_url    → download → pm install
          3. package_name → already-installed check → vendor URL → F-Droid → Play Store
          4. app_name   → resolve → same as #3

        Examples:
          install_app(app_name='telegram')
          install_app(package_name='org.videolan.vlc')
          install_app(apk_url='https://example.com/app.apk')
          install_app(apk_path='myapp.apk')
        """
        if not self._is_termux():
            return "Error: install_app is only available in Termux on Android."
        if not self._provision_shizuku():
            return "Error: Shizuku required. Set it up first."

        # 1. Direct APK file ──────────────────────────────────────────────────
        if apk_path:
            if not apk_path.startswith('/'):
                apk_path = os.path.join(self.workspace_dir, apk_path)
            if not os.path.exists(apk_path):
                return f"Error: APK not found at '{apk_path}'"
            return self._pm_install(apk_path)

        # 2. Direct URL ───────────────────────────────────────────────────────
        if apk_url:
            print("\033[93m[INSTALL]\033[0m Downloading APK from URL...")
            dest = self._download_apk(apk_url, "vc_url.apk")
            if dest.startswith("Error"):
                return dest
            result = self._pm_install(dest)
            self._cleanup_apk(dest)
            return result

        # 3. Resolve app_name → package_name ─────────────────────────────────
        if app_name and not package_name:
            package_name = self._resolve_package(app_name)
            if not package_name:
                return (
                    f"Could not identify package for '{app_name}'.\n"
                    f"Try: install_app(package_name='com.example.app') or apk_url=...\n"
                    f"Or open Play Store: android_control(action='open_play_store', target='com.example')"
                )

        if not package_name:
            return "Error: Provide app_name, package_name, apk_url, or apk_path."

        # 4. Already installed? ───────────────────────────────────────────────
        out, _, _ = self._rish_exec(f"pm list packages | grep -w '{package_name}'")
        if package_name in out:
            return (
                f"'{package_name}' is already installed.\n"
                f"To update: manage_app(action='update', package_name='{package_name}')\n"
                f"To reinstall: manage_app(action='uninstall', ...) then retry."
            )

        print(f"\033[93m[INSTALL]\033[0m Resolving '{package_name}'...")

        # 5a. Known vendor URL ────────────────────────────────────────────────
        if package_name in DIRECT_APK_URLS:
            print("\033[93m[INSTALL]\033[0m Trying vendor URL...")
            dest = self._download_apk(DIRECT_APK_URLS[package_name], f"{package_name}.apk")
            if not dest.startswith("Error"):
                result = self._pm_install(dest)
                self._cleanup_apk(dest)
                if "installed successfully" in result:
                    return result

        # 5b. F-Droid ─────────────────────────────────────────────────────────
        fdroid = self._try_fdroid(package_name)
        if fdroid and not fdroid.startswith("Error"):
            return fdroid

        # 5c. Play Store fallback ─────────────────────────────────────────────
        ps = self._rish_result(
            f"am start -a android.intent.action.VIEW -d 'market://details?id={package_name}'",
            success_msg=f"Opened Play Store for '{package_name}'. Tap Install.",
        )
        return f"Auto-download unavailable for '{package_name}'.\n→ {ps}"

    # ── helpers ───────────────────────────────────────────────────────────────

    def _resolve_package(self, app_name):
        """Fuzzy-match human app name → Android package identifier."""
        key = app_name.lower().strip()
        if key in ANDROID_PACKAGES:
            return ANDROID_PACKAGES[key]
        for name, pkg in ANDROID_PACKAGES.items():
            if key in name or name in key:
                return pkg
        tokens = set(key.split())
        for name, pkg in ANDROID_PACKAGES.items():
            if tokens & set(name.split()):
                return pkg
        return None

    def _download_apk(self, url, filename="install.apk"):
        """
        Download an APK.

        BUG-1 FIX: Primary target is /sdcard/Download/ which is writable by
        Termux after termux-setup-storage AND readable by rish (shell user).
        /data/local/tmp is NOT writable by the Termux app UID.

        Fallback: rish downloads via wget/curl (shell user CAN write to
        /data/local/tmp) if /sdcard is not mounted.
        """
        safe_name = filename.replace('/', '_').replace(' ', '_')

        # Primary: /sdcard/Download/ ──────────────────────────────────────────
        sdcard_dest = f"{_SDCARD_DL}/{safe_name}"
        sdcard_ok   = os.path.isdir(_SDCARD_DL) and os.access(_SDCARD_DL, os.W_OK)

        if not sdcard_ok:
            try:
                os.makedirs(_SDCARD_DL, exist_ok=True)
                sdcard_ok = os.access(_SDCARD_DL, os.W_OK)
            except Exception:
                pass

        if sdcard_ok:
            try:
                import requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 11; M2006C3LG) AppleWebKit/537.36",
                    "Accept":     "application/vnd.android.package-archive,*/*",
                }
                r = requests.get(url, stream=True, timeout=120,
                                 headers=headers, allow_redirects=True)
                if r.status_code != 200:
                    return f"Error: HTTP {r.status_code}"
                ct = r.headers.get("content-type", "")
                if "text/html" in ct and "android.package" not in ct:
                    return "Error: URL returned an HTML page, not an APK."
                size = 0
                with open(sdcard_dest, "wb") as f:
                    for chunk in r.iter_content(65536):
                        if chunk:
                            f.write(chunk)
                            size += len(chunk)
                if size < 102400:
                    try: os.remove(sdcard_dest)
                    except Exception: pass
                    return "Error: Download too small — not a valid APK."
                print(f"\033[92m[INSTALL]\033[0m Downloaded {size // 1024} KB → {sdcard_dest}")
                return sdcard_dest
            except Exception:
                pass   # fall through to rish fallback

        # Fallback: download via rish (shell writes to /data/local/tmp) ───────
        print("\033[93m[INSTALL]\033[0m /sdcard unavailable — trying rish wget fallback...")
        tmp_dest = f"{_RISH_TMP}/{safe_name}"
        self._rish_exec(
            f"wget -q -O '{tmp_dest}' '{url}' 2>/dev/null "
            f"|| curl -L -f -s -o '{tmp_dest}' '{url}'",
            timeout=180,
        )
        # Verify size via rish (Python can't read /data/local/tmp)
        out, _, _ = self._rish_exec(f"wc -c < '{tmp_dest}' 2>/dev/null")
        try:
            if int(out.strip()) > 102400:
                return tmp_dest
        except Exception:
            pass
        return (
            "Error: Download failed.\n"
            "Make sure termux-setup-storage has been run and internet is available."
        )

    def _pm_install(self, apk_path):
        """
        Run pm install via rish.
        BUG-9 FIX: success is determined purely by 'Success' in stdout —
        pm always prints 'Success' to stdout on success, regardless of stderr.
        """
        print(f"\033[93m[INSTALL]\033[0m pm install {os.path.basename(apk_path)}...")
        stdout, stderr, code = self._rish_exec(
            f"pm install -r -d -g '{apk_path}'",
            timeout=180,
        )
        # pm always prints "Success" to stdout on success
        if "Success" in stdout:
            return f"✓ App installed successfully — '{os.path.basename(apk_path)}'"
        out = (stdout + stderr).strip()
        for token, msg in [
            ("ALREADY_EXISTS",         "App already installed."),
            ("VERSION_DOWNGRADE",      "Downgrade blocked — uninstall current version first."),
            ("PARSE_FAILED",           "Invalid APK — file may be corrupted."),
            ("VERIFICATION_FAILURE",   "Blocked by Play Protect / MIUI Security — "
                                       "disable 'Scan apps' in Play Store settings and retry."),
            ("USER_RESTRICTED",        "Blocked by MIUI — enable 'Install via USB' in Developer Options."),
            ("permission denied",      "Permission denied — is Shizuku service running?"),
        ]:
            if token.lower() in out.lower():
                return f"Install failed: {msg}"
        return f"Install may have failed: {out}"

    def _try_fdroid(self, package_name):
        """Download from the official F-Droid API and install."""
        try:
            import requests
            r = requests.get(
                f"https://f-droid.org/api/v1/packages/{package_name}",
                timeout=15,
            )
            if r.status_code != 200:
                return None
            pkgs = r.json().get("packages", [])
            if not pkgs:
                return None
            latest   = pkgs[0]
            apk_name = latest.get("apkName")
            version  = latest.get("versionName", "?")
            if not apk_name:
                return None
            print(f"\033[93m[INSTALL]\033[0m F-Droid: v{version} → {apk_name}")
            dest = self._download_apk(f"https://f-droid.org/repo/{apk_name}", apk_name)
            if dest.startswith("Error"):
                return dest
            result = self._pm_install(dest)
            self._cleanup_apk(dest)
            return f"{result} [F-Droid v{version}]" if "installed" in result else result
        except Exception as e:
            return f"Error (F-Droid): {e}"

    def _cleanup_apk(self, apk_path=""):
        """
        BUG-10 FIX: Remove APK after install from wherever it was downloaded.
        Handles both /sdcard/Download/ and /data/local/tmp/ paths.
        """
        if apk_path:
            if apk_path.startswith(_SDCARD_DL):
                try: os.remove(apk_path)
                except Exception: pass
            else:
                # Came from rish tmp — remove via rish
                self._rish_exec(f"rm -f '{apk_path}' 2>/dev/null")
        # Also sweep any stale vc_*.apk files we may have left
        try:
            for f in os.listdir(_SDCARD_DL):
                if f.startswith("vc_") and f.endswith(".apk"):
                    try: os.remove(f"{_SDCARD_DL}/{f}")
                    except Exception: pass
        except Exception:
            pass
        self._rish_exec("rm -f /data/local/tmp/vc_*.apk 2>/dev/null")

    # =========================================================================
    # MANAGE APP
    # =========================================================================

    def manage_app(self, action, app_name="", package_name="", extra=""):
        """
        Manage installed apps via Shizuku.
        action: uninstall | enable | disable | clear_data | clear_cache |
                force_stop | info | permissions | grant | revoke | update
        app_name OR package_name must be supplied.
        extra: permission name for grant/revoke.
        """
        if not self._is_termux():
            return "Error: Only available in Termux on Android."
        if not self._provision_shizuku():
            return "Error: Shizuku not set up."

        if app_name and not package_name:
            package_name = self._resolve_package(app_name)
            if not package_name:
                return f"Error: Cannot resolve '{app_name}'. Use package_name directly."
        if not package_name:
            return "Error: Provide app_name or package_name."

        if action == "uninstall":
            out, _, code = self._rish_exec(f"pm uninstall {package_name}")
            if code == 0 or "Success" in out:
                return f"✓ '{package_name}' uninstalled."
            # System app — disable for current user instead
            out2, _, _ = self._rish_exec(f"pm disable-user --user 0 {package_name}")
            return f"System app hidden: {out2.strip() or 'disabled for current user.'}"

        elif action == "enable":
            return self._rish_result(
                f"pm enable --user 0 {package_name}",
                success_msg=f"✓ '{package_name}' enabled.",
            )

        elif action == "disable":
            return self._rish_result(
                f"pm disable-user --user 0 {package_name}",
                success_msg=f"✓ '{package_name}' disabled.",
            )

        elif action == "clear_data":
            return self._rish_result(
                f"pm clear {package_name}",
                success_msg=f"✓ Data cleared for '{package_name}'.",
            )

        elif action == "clear_cache":
            # BUG-6 FIX: per-app cache clear (Android 8+); fall back to
            # global trim-caches if the per-app command isn't supported.
            stdout, _, code = self._rish_exec(
                f"cmd package clear-cache {package_name} 2>/dev/null"
                f" || pm clear --cache-only {package_name} 2>/dev/null"
            )
            if code == 0:
                return f"✓ Cache cleared for '{package_name}'."
            return self._rish_result(
                "pm trim-caches 999999999",
                success_msg=(
                    f"✓ Caches trimmed (per-app cache clear not supported "
                    f"on this Android version; all-apps trim ran instead)."
                ),
            )

        elif action == "force_stop":
            return self._rish_result(
                f"am force-stop {package_name}",
                success_msg=f"✓ '{package_name}' force-stopped.",
            )

        elif action == "info":
            out, _, _ = self._rish_exec(
                f"pm dump {package_name} | grep -E "
                f"'(versionName|versionCode|firstInstallTime|lastUpdateTime|codePath|dataDir)'"
                f" | head -8"
            )
            return out.strip() or f"No info found for '{package_name}'."

        elif action == "permissions":
            # BUG-2 FIX: grep -oP not supported by Android toybox grep.
            # Use grep -o + sed (both supported everywhere).
            out, _, _ = self._rish_exec(
                f"pm dump {package_name}"
                f" | grep 'granted=true'"
                f" | grep -o 'name=[^ ]*'"
                f" | sed 's/name=//'"
            )
            return out.strip() or "No granted permissions found."

        elif action == "grant":
            if not extra:
                return "Error: extra='android.permission.PERMISSION_NAME' required."
            return self._rish_result(
                f"pm grant {package_name} {extra}",
                success_msg=f"✓ Permission '{extra}' granted to '{package_name}'.",
            )

        elif action == "revoke":
            if not extra:
                return "Error: extra='android.permission.PERMISSION_NAME' required."
            return self._rish_result(
                f"pm revoke {package_name} {extra}",
                success_msg=f"✓ Permission '{extra}' revoked from '{package_name}'.",
            )

        elif action == "update":
            return self._rish_result(
                f"am start -a android.intent.action.VIEW -d 'market://details?id={package_name}'",
                success_msg=f"Opened Play Store for '{package_name}'.",
            )

        else:
            return (
                f"Unknown action '{action}'. Valid: uninstall, enable, disable, "
                "clear_data, clear_cache, force_stop, info, permissions, "
                "grant, revoke, update"
            )

    # =========================================================================
    # LIST PACKAGES
    # =========================================================================

    def list_packages(self, filter_type="user", search=""):
        """
        List installed packages.
        filter_type: user | system | all | disabled | enabled
        search: optional substring filter (case-insensitive)
        """
        if not self._is_termux():
            return "Error: Only available in Termux on Android."
        if not self._provision_shizuku():
            return "Error: Shizuku not set up."

        flags = {"user": "-3", "third": "-3", "system": "-s",
                 "all":  "",   "disabled": "-d", "enabled": "-e"}
        flag = flags.get(filter_type, "-3")
        cmd  = f"pm list packages {flag}"
        if search:
            cmd += f" | grep -i '{search}'"

        out, _, _ = self._rish_exec(cmd)
        if not out.strip():
            return f"No packages (filter={filter_type}, search='{search}')."

        pkgs = sorted(
            line.replace("package:", "").strip()
            for line in out.strip().splitlines()
            if line.startswith("package:")
        )
        return f"Installed ({filter_type}) — {len(pkgs)} found:\n" + "\n".join(pkgs)

    # =========================================================================
    # LAUNCH INTENT
    # =========================================================================

    def launch_intent(self, action="VIEW", data="", package="",
                      activity="", extras=""):
        """
        Fire any Android intent via am start.

        Examples:
          launch_intent(action='VIEW', data='https://example.com')
          launch_intent(action='MAIN', package='com.android.settings')
          launch_intent(activity='com.example.app/.MainActivity')
          launch_intent(action='CALL', data='tel:+911234567890')
        """
        if not self._is_termux():
            return "Error: Only available in Termux on Android."
        if not self._provision_shizuku():
            return "Error: Shizuku not set up."

        parts = ["am start"]
        if activity: parts.append(f"-n {activity}")
        if action:   parts.append(f"-a android.intent.action.{action}")
        if data:     parts.append(f"-d '{data}'")
        if package:  parts.append(f"--package {package}")
        if extras:   parts.append(extras)

        return self._rish_result(
            " ".join(parts),
            success_msg=f"✓ Intent '{action}' launched.",
        )

    # =========================================================================
    # GET SYSTEM INFO
    # =========================================================================

    def get_system_info(self):
        """Return a full Android device profile via Shizuku."""
        if not self._is_termux():
            return "Error: Only available in Termux on Android."
        if not self._provision_shizuku():
            return "Error: Shizuku not set up."

        queries = [
            ("Device Model",    "getprop ro.product.model"),
            ("Manufacturer",    "getprop ro.product.manufacturer"),
            ("Android Version", "getprop ro.build.version.release"),
            ("SDK Level",       "getprop ro.build.version.sdk"),
            ("Security Patch",  "getprop ro.build.version.security_patch"),
            ("Build ID",        "getprop ro.build.id"),
            ("CPU ABI",         "getprop ro.product.cpu.abi"),
            ("CPU ABI List",    "getprop ro.product.cpu.abilist"),
            ("Kernel",          "uname -r"),
            ("Screen Size",     "wm size"),
            ("Screen Density",  "wm density"),
            ("Total RAM",       "grep MemTotal /proc/meminfo"),
            ("Available RAM",   "grep MemAvailable /proc/meminfo"),
            ("Storage /data",   "df /data | tail -1"),
            ("Storage /sdcard", "df /sdcard 2>/dev/null | tail -1"),
            ("Battery",         "dumpsys battery | grep -E '(level|status|health|voltage|temperature)'"),
            ("WiFi SSID",       "dumpsys wifi | grep 'SSID:' | head -1"),
            # BUG-2 FIX: grep -oP → awk (toybox grep has no -P flag)
            ("IP Address",
             "ip route get 1.1.1.1 2>/dev/null | awk '/src/{for(i=1;i<=NF;i++){if($i==\"src\"){print $(i+1);exit}}}'"),
            ("User Packages",   "pm list packages -3 | wc -l"),
        ]
        lines = ["╔══ ANDROID DEVICE PROFILE ══╗"]
        for label, cmd in queries:
            out, _, _ = self._rish_exec(cmd, timeout=5)
            val = out.strip().replace("\n", " ") if out.strip() else "N/A"
            lines.append(f"  {label:<22} {val}")
        lines.append("╚═════════════════════════════╝")
        return "\n".join(lines)

    # =========================================================================
    # ANDROID MACRO
    # =========================================================================

    def android_macro(self, steps):
        """
        Execute a multi-step Android action sequence.

        steps — JSON list (or Python list) of dicts:
          {"action": "home"}
          {"action": "open_app", "target": "com.android.settings"}
          {"delay": 1.5}
          {"action": "tap", "target": "540 400"}
          {"install": "telegram"}
          {"manage": "force_stop", "pkg": "com.example.app"}

        BUG-11 FIX: a single dict is wrapped in a list automatically.
        BUG-7/8 FIX: json and time are now module-level imports.
        """
        # Normalise input
        if isinstance(steps, str):
            try:
                steps = json.loads(steps)
            except Exception:
                return "Error: steps must be a JSON list of action dicts."
        if isinstance(steps, dict):       # LLM passed one step instead of list
            steps = [steps]
        if not isinstance(steps, list):
            return "Error: steps must be a list."

        results = []
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                results.append(f"[{i}] skipped (invalid step)")
                continue

            # Delay
            if "delay" in step:
                sec = float(step["delay"])
                time.sleep(sec)
                results.append(f"[{i}] delay({sec}s) ✓")
                continue

            # Install
            if "install" in step:
                r = self.install_app(app_name=str(step["install"]))
                results.append(f"[{i}] install({step['install']}): {r}")
                continue

            # Manage
            if "manage" in step:
                r = self.manage_app(
                    action=step["manage"],
                    package_name=step.get("pkg", ""),
                    app_name=step.get("app", ""),
                )
                results.append(f"[{i}] manage({step['manage']}): {r}")
                continue

            # android_control
            act = step.get("action", "")
            tgt = str(step.get("target", ""))
            if not act:
                results.append(f"[{i}] skipped (no action key)")
                continue
            r = self.android_control(action=act, target=tgt)
            results.append(f"[{i}] {act}: {r}")
            # Brief pause to let Android UI settle between actions
            time.sleep(0.4)

        return "\n".join(results)

    # =========================================================================
    # FILE SYSTEM
    # =========================================================================

    def _safe_path(self, filename):
        path = os.path.abspath(os.path.join(self.workspace_dir, filename))
        if not path.startswith(self.workspace_dir):
            raise ValueError("Access outside workspace is restricted.")
        return path

    def update_config(self, key, value, subkey=None):
        try:
            import yaml
            config_path = os.path.join(
                os.path.dirname(self.workspace_dir), 'common', 'config.yaml'
            )
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            if subkey:
                if key not in config:
                    config[key] = {}
                config[key][subkey] = value
            else:
                config[key] = value
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            return f"Config updated: {key}{'/' + subkey if subkey else ''} = {value}"
        except Exception as e:
            return f"Error updating config: {e}"

    def update_user_profile(self, info):
        try:
            path = os.path.join(
                os.path.dirname(self.workspace_dir), 'common', 'user.md'
            )
            with open(path, 'a', encoding='utf-8') as f:
                f.write(f"\n- {info}")
            return "User profile updated."
        except Exception as e:
            return str(e)

    def list_files(self):
        try:
            return "\n".join(os.listdir(self.workspace_dir)) or "Workspace is empty."
        except Exception as e:
            return str(e)

    def list_files_recursive(self):
        try:
            files = []
            for root, _, filenames in os.walk(self.workspace_dir):
                for fn in filenames:
                    files.append(
                        os.path.relpath(os.path.join(root, fn), self.workspace_dir)
                    )
            return "\n".join(files) or "Workspace is empty."
        except Exception as e:
            return str(e)

    def get_workspace_tree(self):
        try:
            tree = []
            for root, dirs, files in os.walk(self.workspace_dir):
                lvl    = root.replace(self.workspace_dir, '').count(os.sep)
                indent = '  ' * lvl
                tree.append(f"{indent}{os.path.basename(root)}/")
                for fn in files:
                    tree.append(f"{'  ' * (lvl + 1)}{fn}")
            return "\n".join(tree)
        except Exception as e:
            return str(e)

    def read_file(self, filename):
        try:
            path = self._safe_path(filename)
            ext  = os.path.splitext(filename)[1].lower()
            if ext == '.pdf':
                return self.read_pdf(filename)
            if ext in ('.xlsx', '.xls'):
                return self.read_excel(filename)
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return str(e)

    def read_pdf(self, filename):
        if not PdfReader:
            return "Error: pypdf not installed."
        try:
            reader = PdfReader(self._safe_path(filename))
            return "".join(p.extract_text() + "\n" for p in reader.pages)[:10000]
        except Exception as e:
            return f"Error reading PDF: {e}"

    def read_excel(self, filename):
        if not openpyxl:
            return "Error: openpyxl not installed."
        try:
            wb  = openpyxl.load_workbook(self._safe_path(filename), data_only=True)
            out = ""
            for sheet in wb.worksheets:
                out += f"--- Sheet: {sheet.title} ---\n"
                for row in sheet.iter_rows(values_only=True):
                    out += "\t".join(
                        str(c) if c is not None else "" for c in row
                    ) + "\n"
            return out[:10000]
        except Exception as e:
            return f"Error reading Excel: {e}"

    def write_file(self, filename, content):
        try:
            path = self._safe_path(filename)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File '{filename}' written."
        except Exception as e:
            return str(e)

    def delete_file(self, filename):
        try:
            path = self._safe_path(filename)
            if os.path.isdir(path):
                shutil.rmtree(path)
                return f"Directory '{filename}' deleted."
            os.remove(path)
            return f"File '{filename}' deleted."
        except Exception as e:
            return str(e)

    def create_directory(self, path):
        try:
            os.makedirs(self._safe_path(path), exist_ok=True)
            return f"Directory '{path}' created."
        except Exception as e:
            return str(e)

    def move_file(self, src, dest):
        try:
            sp = self._safe_path(src)
            dp = self._safe_path(dest)
            os.makedirs(os.path.dirname(dp), exist_ok=True)
            shutil.move(sp, dp)
            return f"Moved '{src}' → '{dest}'."
        except Exception as e:
            return str(e)

    def rename_file(self, old_name, new_name):
        return self.move_file(old_name, new_name)

    # =========================================================================
    # WEB
    # =========================================================================

    def web_search(self, query):
        if not self._is_termux():
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    if results:
                        return "\n\n".join(
                            f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}"
                            for r in results
                        )
            except Exception:
                pass
        try:
            import requests
            from bs4 import BeautifulSoup
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(
                f"https://html.duckduckgo.com/html/?q={query}",
                headers=headers, timeout=10,
            )
            if resp.status_code == 200:
                soup    = BeautifulSoup(resp.content, "html.parser")
                results = []
                for r in soup.find_all("div", class_="result")[:5]:
                    ta = r.find("a", class_="result__a")
                    sa = r.find("a", class_="result__snippet")
                    if ta:
                        results.append(
                            f"Title: {ta.get_text().strip()}\n"
                            f"Link: {ta.get('href')}\n"
                            f"Snippet: {sa.get_text().strip() if sa else 'N/A'}"
                        )
                if results:
                    return "\n\n".join(results)
        except Exception as e:
            return f"Search error: {e}"
        return "No results found."

    def web_scrape(self, url):
        try:
            import requests
            from bs4 import BeautifulSoup
            r    = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            for s in soup(["script", "style"]):
                s.extract()
            text = '\n'.join(
                c for c in (
                    p.strip()
                    for ln in soup.get_text().splitlines()
                    for p in ln.split("  ")
                ) if c
            )
            return text[:4000]
        except Exception as e:
            return f"Error scraping: {e}"

    def fetch_youtube_transcript(self, url):
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(url)
            vid_id = None
            if parsed.hostname in ('www.youtube.com', 'youtube.com'):
                if parsed.path == '/watch':
                    vid_id = parse_qs(parsed.query).get('v', [None])[0]
                else:
                    vid_id = parsed.path.split('/')[-1]
            elif parsed.hostname == 'youtu.be':
                vid_id = parsed.path.split('/')[1]
            if not vid_id:
                vid_id = parsed.path.split('/')[-1]
            api  = YouTubeTranscriptApi()
            data = api.fetch(vid_id).to_raw_data()
            return " ".join(t['text'] for t in data)[:4000]
        except Exception as e:
            return f"Error fetching transcript: {e}"

    def fetch_weather(self, city):
        try:
            import requests
            return requests.get(
                f"https://wttr.in/{city}?format=3", timeout=5
            ).text.strip()
        except Exception as e:
            return f"Error: {e}"

    # =========================================================================
    # MEDIA
    # =========================================================================

    def download_youtube(self, url, format_type="video"):
        try:
            import yt_dlp
            opts = {
                'outtmpl':          os.path.join(self.workspace_dir, '%(title)s.%(ext)s'),
                'restrictfilenames': True,
                'noplaylist':        True,
            }
            if format_type == "audio":
                opts['format'] = 'bestaudio/best'
                opts['postprocessors'] = [{
                    'key':             'FFmpegExtractAudio',
                    'preferredcodec':  'mp3',
                    'preferredquality': '192',
                }]
            else:
                opts['format']              = 'bestvideo+bestaudio/best'
                opts['merge_output_format'] = 'mp4'
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                fn   = ydl.prepare_filename(info)
                if format_type == "audio":
                    fn = fn.rsplit('.', 1)[0] + '.mp3'
            return f"Downloaded: {os.path.basename(fn)}"
        except Exception as e:
            return f"Error: {e}"

    def convert_media(self, input_file, output_format):
        try:
            ip = self._safe_path(input_file)
            op = self._safe_path(
                f"{os.path.splitext(input_file)[0]}.{output_format}"
            )
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            r = subprocess.run(
                ['ffmpeg', '-i', ip, op, '-y'],
                capture_output=True, text=True,
            )
            return (
                f"Converted to {output_format}."
                if r.returncode == 0 else f"FFmpeg error: {r.stderr}"
            )
        except FileNotFoundError:
            return "Error: FFmpeg not installed."
        except Exception as e:
            return f"Error: {e}"

    # =========================================================================
    # MEMORY
    # =========================================================================

    def get_memory(self):
        try:
            path = os.path.join(
                os.path.dirname(self.workspace_dir), 'common', 'memory.md'
            )
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return str(e)

    def update_memory(self, fact):
        try:
            path = os.path.join(
                os.path.dirname(self.workspace_dir), 'common', 'memory.md'
            )
            with open(path, 'a', encoding='utf-8') as f:
                f.write(f"\n- {fact}")
            return "Memory updated."
        except Exception as e:
            return str(e)

    # =========================================================================
    # INTELLIGENCE
    # =========================================================================

    def python_sandbox(self, code):
        """
        BUG-4 FIX: use 'python3' — Termux only ships python3, not python.
        """
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True, text=True, timeout=10,
            )
            out = result.stdout + (f"\nError: {result.stderr}" if result.stderr else "")
            return out[-4000:] or "No output."
        except subprocess.TimeoutExpired:
            return "Execution timed out."
        except FileNotFoundError:
            # Final fallback: try bare 'python'
            try:
                result = subprocess.run(
                    ["python", "-c", code],
                    capture_output=True, text=True, timeout=10,
                )
                return result.stdout[-4000:] or "No output."
            except Exception as e2:
                return f"Sandbox error: {e2}"
        except Exception as e:
            return f"Sandbox error: {e}"

    def local_rag_search(self, query):
        try:
            import glob
            from sklearn.feature_extraction.text import TfidfVectorizer
            docs, mapping = [], []
            for pat in ['*.txt', '*.md', '*.py', '*.json', '*.csv', '*.html']:
                for fp in glob.glob(
                    os.path.join(self.workspace_dir, '**', pat), recursive=True
                ):
                    try:
                        with open(fp, 'r', encoding='utf-8') as f:
                            content = f.read()
                        for i in range(0, len(content), 1000):
                            chunk = content[i:i + 1000]
                            if chunk.strip():
                                docs.append(chunk)
                                mapping.append(
                                    os.path.relpath(fp, self.workspace_dir)
                                )
                    except Exception:
                        pass
            if not docs:
                return "No readable documents in workspace."
            vec   = TfidfVectorizer(stop_words='english')
            tfidf = vec.fit_transform(docs)
            qv    = vec.transform([query])
            sims  = (tfidf * qv.T).toarray().flatten()
            top   = sims.argsort()[-3:][::-1]
            res   = [
                f"--- {mapping[i]} ---\n{docs[i]}..."
                for i in top if sims[i] > 0.05
            ]
            return "\n\n".join(res) if res else "No relevant results."
        except ImportError:
            return "Error: scikit-learn not installed."
        except Exception as e:
            return f"RAG error: {e}"

    # =========================================================================
    # SCHEDULING
    # =========================================================================

    def remind_me(self, message, time_args):
        if not self.agent:
            return "Agent not connected."
        return self.agent.add_scheduled_task('interval', time_args, f"REMINDER: {message}")

    def stop_reminders(self, keyword):
        if not self.agent:
            return "Agent not connected."
        return self.agent.remove_scheduled_task(keyword)

    def schedule_task(self, trigger_type, schedule_args, instruction):
        if not self.agent:
            return "Agent not connected."
        return self.agent.add_scheduled_task(trigger_type, schedule_args, instruction)

    def list_tasks(self):
        if not self.agent:
            return "Agent not connected."
        jobs = self.agent.scheduler.get_jobs()
        if not jobs:
            return "No active scheduled tasks."
        return "\n".join(
            f"ID: {j.id} | {j.trigger} | {j.args[2]}" for j in jobs
        )

    def remove_task(self, keyword):
        if not self.agent:
            return "Agent not connected."
        return self.agent.remove_scheduled_task(keyword)

    def remove_all_tasks(self):
        if not self.agent:
            return "Agent not connected."
        for j in self.agent.scheduler.get_jobs():
            self.agent.scheduler.remove_job(j.id)
        self.agent._save_tasks()
        return "All scheduled tasks removed."
