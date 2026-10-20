# -*- coding: utf-8 -*-
"""
Access TV - Accessible TV Streaming Addon for NVDA
Modul GlobalPlugin resmi untuk registrasi menu, shortcut global, dan manajemen daur hidup pemutar.
"""

try:
    import globalPluginHandler
except ImportError:
    class _DummyPlugin:
        def __init__(self, *args, **kwargs):
            pass
        def terminate(self):
            pass
    class _DummyHandler:
        GlobalPlugin = _DummyPlugin
    globalPluginHandler = _DummyHandler()

try:
    import gui
except ImportError:
    gui = None

try:
    import ui
except ImportError:
    class _UIFallback:
        @staticmethod
        def message(text):
            pass
    ui = _UIFallback()

try:
    import wx
except ImportError:
    wx = None

from .gui_dialog import AccessTVDialog
from .player_engine import PlayerEngine

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    scriptCategory = "Access TV"

    def __init__(self, *args, **kwargs):
        super(GlobalPlugin, self).__init__(*args, **kwargs)
        self.player = PlayerEngine.get_instance()
        self.menu_item = None
        self._init_menu()

    def _init_menu(self):
        try:
            tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
            self.menu_item = tools_menu.Append(
                wx.ID_ANY,
                "&Access TV (Streaming TV)...",
                "Buka pemutar siaran televisi streaming aksesibel Access TV"
            )
            gui.mainFrame.sysTrayIcon.Bind(
                wx.EVT_MENU,
                self.on_menu_open,
                self.menu_item
            )
        except Exception:
            pass

    def on_menu_open(self, event):
        AccessTVDialog.show_dialog()

    def script_showAccessTV(self, gesture):
        AccessTVDialog.show_dialog()
    script_showAccessTV.__doc__ = "Membuka antarmuka siaran televisi streaming Access TV."

    def script_stopPlayback(self, gesture):
        if self.player.is_playing():
            self.player.stop(status_callback=lambda st, msg: ui.message(msg))
        else:
            ui.message("Access TV: Tidak ada siaran yang sedang diputar.")
    script_stopPlayback.__doc__ = "Menghentikan pemutaran siaran TV seketika."

    def script_announceCurrentChannel(self, gesture):
        if self.player.is_playing():
            title = self.player.get_current_title() or "Siaran TV"
            ui.message(f"Access TV: Sedang memutar {title}, volume {self.player.get_volume()} persen.")
        else:
            ui.message("Access TV: Tidak ada siaran yang sedang diputar.")
    script_announceCurrentChannel.__doc__ = "Menyebutkan informasi siaran TV yang sedang diputar."

    __gestures = {
        "kb:control+windows+a": "showAccessTV",
        "kb:control+windows+shift+s": "stopPlayback",
        "kb:control+windows+shift+a": "announceCurrentChannel",
    }

    def terminate(self):
        try:
            if self.menu_item:
                tools_menu = gui.mainFrame.sysTrayIcon.toolsMenu
                tools_menu.Remove(self.menu_item)
        except Exception:
            pass

        # Hentikan dan bersihkan resource BASS
        try:
            self.player.free()
        except Exception:
            pass

        super(GlobalPlugin, self).terminate()
