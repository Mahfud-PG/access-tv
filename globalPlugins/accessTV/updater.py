# -*- coding: utf-8 -*-
"""
Access TV - Auto-Updater Module
Memeriksa pembaruan resmi Access TV langsung dari GitHub Releases secara aman dan aksesibel untuk NVDA.
"""

import os
import json
import re
import threading
import tempfile
import urllib.request

try:
    import wx
except ImportError:
    class _DummyWX:
        ID_YES = 5103
        ID_NO = 5104
        ID_CANCEL = 5101
        VERTICAL = 0
        HORIZONTAL = 0
        ALL = 0
        LEFT = 0
        RIGHT = 0
        BOTTOM = 0
        EXPAND = 0
        ALIGN_RIGHT = 0
        TE_MULTILINE = 0
        TE_READONLY = 0
        TE_RICH2 = 0
        DEFAULT_DIALOG_STYLE = 0
        RESIZE_BORDER = 0
        class Dialog:
            def __init__(self, *args, **kwargs): pass
        class Panel:
            def __init__(self, *args, **kwargs): pass
        class BoxSizer:
            def __init__(self, *args, **kwargs): pass
            def Add(self, *args, **kwargs): pass
        class StaticText:
            def __init__(self, *args, **kwargs): pass
        class TextCtrl:
            def __init__(self, *args, **kwargs): pass
        class Button:
            def __init__(self, *args, **kwargs): pass
            def SetDefault(self): pass
            def Bind(self, *args, **kwargs): pass
        @staticmethod
        def CallAfter(fn, *args, **kwargs): pass
        @staticmethod
        def GetApp(): return None
    wx = _DummyWX()

try:
    import ui
except ImportError:
    class _UIFallback:
        @staticmethod
        def message(text):
            print("[UI MESSAGE]:", text)
    ui = _UIFallback()

try:
    import gui
    MAIN_FRAME = gui.mainFrame
except Exception:
    MAIN_FRAME = None


GITHUB_REPO = "Mahfud-PG/access-tv"


def get_current_addon_version():
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), '..', '..', 'manifest.ini')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('version'):
                        parts = line.split('=')
                        if len(parts) >= 2:
                            return parts[1].strip()
    except Exception:
        pass
    return "1.2.0"


class UpdateDialog(wx.Dialog):
    def __init__(self, parent, latest_version, current_version, notes):
        super(UpdateDialog, self).__init__(
            parent,
            title="Pembaruan Access TV Tersedia",
            size=(520, 460),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.CentreOnParent()

        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        msg = f"Versi baru Access TV ({latest_version}) telah tersedia!\nVersi Anda saat ini: {current_version}"
        header = wx.StaticText(panel, label=msg)
        vbox.Add(header, 0, wx.ALL, 12)

        lbl_notes = wx.StaticText(panel, label="Catatan Perubahan:")
        vbox.Add(lbl_notes, 0, wx.LEFT | wx.RIGHT, 12)

        self.txt_notes = wx.TextCtrl(
            panel,
            value=notes,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2
        )
        vbox.Add(self.txt_notes, 1, wx.EXPAND | wx.ALL, 12)

        lbl_question = wx.StaticText(panel, label="Apakah Anda ingin mengunduh dan memasang pembaruan sekarang?")
        vbox.Add(lbl_question, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_yes = wx.Button(panel, wx.ID_YES, label="&Perbarui Sekarang")
        self.btn_no = wx.Button(panel, wx.ID_NO, label="&Nanti")

        btn_sizer.Add(self.btn_yes, 0, wx.RIGHT, 8)
        btn_sizer.Add(self.btn_no, 0)
        vbox.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 12)

        panel.SetSizer(vbox)
        self.btn_yes.SetDefault()

        self.btn_yes.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_YES))
        self.btn_no.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_NO))


class UpdateManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.current_version = get_current_addon_version()
        self._is_checking = False
        self._is_downloading = False

    def check_for_updates(self, silent=True):
        if self._is_checking or self._is_downloading:
            return
        threading.Thread(target=self._worker_check, args=(silent,), daemon=True).start()

    def _worker_check(self, silent):
        self._is_checking = True
        try:
            if not silent:
                ui.message("Memeriksa pembaruan Access TV ke GitHub...")

            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "AccessTV-NVDA-Updater"})
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    tag = data.get("tag_name", "").lstrip("v").strip()
                    
                    if self._compare_versions(tag, self.current_version) > 0:
                        download_url = None
                        for asset in data.get("assets", []):
                            if asset.get("name", "").endswith(".nvda-addon"):
                                download_url = asset.get("browser_download_url")
                                break

                        if download_url:
                            notes = data.get("body", "Pembaruan rilis resmi.")
                            wx.CallAfter(self._show_update_dialog, tag, self.current_version, notes, download_url)
                        elif not silent:
                            ui.message("Pembaruan ditemukan, namun berkas addon belum tersedia di rilis GitHub.")
                    elif not silent:
                        ui.message(f"Access TV Anda sudah versi terbaru ({self.current_version}).")
        except Exception as e:
            if not silent:
                ui.message(f"Gagal memeriksa pembaruan: {str(e)}")
        finally:
            self._is_checking = False

    def _compare_versions(self, v1, v2):
        try:
            p1 = [int(x) for x in re.findall(r'\d+', v1)]
            p2 = [int(x) for x in re.findall(r'\d+', v2)]
            maxlen = max(len(p1), len(p2))
            p1.extend([0] * (maxlen - len(p1)))
            p2.extend([0] * (maxlen - len(p2)))
            return (p1 > p2) - (p1 < p2)
        except Exception:
            return 0 if v1 == v2 else 1

    def _show_update_dialog(self, latest_version, current_version, notes, download_url):
        parent = MAIN_FRAME or wx.GetApp().GetTopWindow() if wx.GetApp() else None
        dlg = UpdateDialog(parent, latest_version, current_version, notes)
        if dlg.ShowModal() == wx.ID_YES:
            threading.Thread(target=self._download_and_install, args=(download_url, latest_version), daemon=True).start()
        dlg.Destroy()

    def _download_and_install(self, download_url, version):
        self._is_downloading = True
        try:
            ui.message(f"Sedang mengunduh pembaruan Access TV v{version}...")
            temp_dir = tempfile.gettempdir()
            addon_path = os.path.join(temp_dir, f"AccessTV_v{version}_Update.nvda-addon")

            req = urllib.request.Request(download_url, headers={"User-Agent": "AccessTV-NVDA-Updater"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(addon_path, 'wb') as f:
                    while True:
                        chunk = resp.read(256 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

            ui.message("Unduhan selesai! Membuka pemasang addon resmi NVDA...")
            # Panggil instalasi resmi via asosiasi Windows file .nvda-addon
            wx.CallAfter(os.startfile, addon_path)
        except Exception as e:
            ui.message(f"Gagal mengunduh pembaruan: {str(e)}")
        finally:
            self._is_downloading = False
