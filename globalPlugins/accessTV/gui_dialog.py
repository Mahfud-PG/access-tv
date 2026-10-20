# -*- coding: utf-8 -*-
"""
Access TV - Graphical User Interface (wxPython)
Antarmuka dialog native yang 100% aksesibel untuk NVDA, dirancang khusus dengan urutan tab yang efisien.
"""

try:
    import wx
except ImportError:
    class _DummyWX:
        DEFAULT_DIALOG_STYLE = 0
        RESIZE_BORDER = 0
        VERTICAL = 0
        HORIZONTAL = 0
        ALL = 0
        LEFT = 0
        RIGHT = 0
        BOTTOM = 0
        EXPAND = 0
        ALIGN_CENTER_VERTICAL = 0
        ALIGN_RIGHT = 0
        TE_PROCESS_ENTER = 0
        LB_SINGLE = 0
        SL_HORIZONTAL = 0
        NOT_FOUND = -1
        ID_CANCEL = 0
        WXK_RETURN = 13
        WXK_NUMPAD_ENTER = 13
        WXK_SPACE = 32
        WXK_ESCAPE = 27
        EVT_CLOSE = None
        EVT_CHAR_HOOK = None
        EVT_TEXT = None
        EVT_TEXT_ENTER = None
        EVT_CHOICE = None
        EVT_CHECKBOX = None
        EVT_LISTBOX = None
        EVT_LISTBOX_DCLICK = None
        EVT_KEY_DOWN = None
        EVT_BUTTON = None
        EVT_SLIDER = None
        class Dialog:
            def __init__(self, *args, **kwargs): pass
        class BoxSizer:
            def __init__(self, *args, **kwargs): pass
            def Add(self, *args, **kwargs): pass
        class StaticText:
            def __init__(self, *args, **kwargs): pass
            def SetLabel(self, *args, **kwargs): pass
        class TextCtrl:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def SetToolTip(self, *args, **kwargs): pass
            def SetFocus(self): pass
            def GetValue(self): return ""
        class Choice:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def Clear(self): pass
            def Append(self, *args, **kwargs): pass
            def GetCount(self): return 0
            def SetSelection(self, idx): pass
            def GetSelection(self): return -1
            def GetStringSelection(self): return ""
            def GetClientData(self, idx): return ""
        class CheckBox:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def IsChecked(self): return False
        class ListBox:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def Clear(self): pass
            def Append(self, *args, **kwargs): pass
            def GetSelection(self): return -1
            def SetSelection(self, idx): pass
            def GetCount(self): return 0
        class Button:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def Enable(self, state): pass
            def SetLabel(self, lbl): pass
        class Slider:
            def __init__(self, *args, **kwargs): pass
            def Bind(self, *args, **kwargs): pass
            def GetValue(self): return 80
            def SetValue(self, val): pass
        @staticmethod
        def CallAfter(fn, *args, **kwargs): pass
        @staticmethod
        def GetApp(): return None
    wx = _DummyWX()
from .channel_manager import ChannelManager
from .player_engine import PlayerEngine

try:
    import ui
except ImportError:
    class _UIFallback:
        @staticmethod
        def message(text):
            pass
    ui = _UIFallback()

try:
    import gui
    MAIN_FRAME = gui.mainFrame
except Exception:
    MAIN_FRAME = None


class AddChannelDialog(wx.Dialog):
    def __init__(self, parent=None):
        super(AddChannelDialog, self).__init__(
            parent,
            title="Tambah Saluran TV Kustom",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        self.channel_data = None
        self._init_ui()
        self.SetSize((460, 320))
        self.CentreOnParent()

    def _init_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Nama Saluran
        lbl_name = wx.StaticText(self, label="Nama Saluran TV:")
        sizer.Add(lbl_name, 0, wx.ALL, 6)
        self.txt_name = wx.TextCtrl(self)
        sizer.Add(self.txt_name, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # URL Streaming
        lbl_url = wx.StaticText(self, label="URL Streaming (.m3u8):")
        sizer.Add(lbl_url, 0, wx.LEFT | wx.RIGHT, 6)
        self.txt_url = wx.TextCtrl(self)
        sizer.Add(self.txt_url, 0, wx.EXPAND | wx.ALL, 6)

        # Kategori
        lbl_cat = wx.StaticText(self, label="Kategori Saluran (Misal: Berita, Religi, Musik):")
        sizer.Add(lbl_cat, 0, wx.LEFT | wx.RIGHT, 6)
        self.txt_cat = wx.TextCtrl(self, value="Kustom")
        sizer.Add(self.txt_cat, 0, wx.EXPAND | wx.ALL, 6)

        # Tombol Simpan & Batal
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_save = wx.Button(self, wx.ID_OK, label="Simpan Saluran")
        self.btn_save.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.Add(self.btn_save, 1, wx.RIGHT, 6)

        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Batal")
        btn_sizer.Add(self.btn_cancel, 1, wx.LEFT, 6)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)

        self.SetSizer(sizer)
        self.txt_name.SetFocus()

    def on_save(self, event):
        name = self.txt_name.GetValue().strip()
        url = self.txt_url.GetValue().strip()
        cat = self.txt_cat.GetValue().strip() or "Kustom"

        if not name:
            ui.message("Nama saluran tidak boleh kosong.")
            self.txt_name.SetFocus()
            return
        if not url:
            ui.message("URL streaming tidak boleh kosong.")
            self.txt_url.SetFocus()
            return
        if not (url.lower().startswith("http://") or url.lower().startswith("https://")):
            ui.message("URL streaming harus diawali http:// atau https://")
            self.txt_url.SetFocus()
            return

        self.channel_data = (name, url, cat)
        self.EndModal(wx.ID_OK)


class AccessTVDialog(wx.Dialog):
    _instance = None

    @classmethod
    def show_dialog(cls):
        if cls._instance:
            try:
                cls._instance.Raise()
                cls._instance.SetFocus()
                return
            except Exception:
                cls._instance = None

        parent = MAIN_FRAME or wx.GetApp().GetTopWindow() if wx.GetApp() else None
        dlg = cls(parent)
        cls._instance = dlg
        dlg.Show()
        dlg.Raise()
        dlg.SetFocus()

    def __init__(self, parent=None):
        super(AccessTVDialog, self).__init__(
            parent,
            title="Access TV - Siaran Televisi Streaming",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        self.channel_mgr = ChannelManager()
        self.player = PlayerEngine.get_instance()
        self._current_channels = []

        self._init_ui()
        self._populate_countries()
        self._update_channel_list()
        self._update_button_states()

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)

        # Ukuran awal dialog yang proporsional
        self.SetSize((520, 640))
        self.CentreOnScreen()

        # Fokus awal mutlak: Kotak Pencarian
        self.txt_search.SetFocus()

    def _init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 1. Kotak Pencarian Cepat
        lbl_search = wx.StaticText(self, label="Cari Saluran TV:")
        main_sizer.Add(lbl_search, 0, wx.ALL, 6)

        self.txt_search = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.txt_search.SetToolTip("Ketik kata kunci nama stasiun untuk menyaring saluran secara instan")
        self.txt_search.Bind(wx.EVT_TEXT, self.on_search_text)
        self.txt_search.Bind(wx.EVT_TEXT_ENTER, self.on_search_enter)
        main_sizer.Add(self.txt_search, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 2. Pilihan Negara
        lbl_country = wx.StaticText(self, label="Pilih Negara:")
        main_sizer.Add(lbl_country, 0, wx.LEFT | wx.RIGHT, 6)

        self.combo_country = wx.Choice(self)
        self.combo_country.Bind(wx.EVT_CHOICE, self.on_country_changed)
        main_sizer.Add(self.combo_country, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 3. Filter Favorit Saja
        self.chk_favorites = wx.CheckBox(self, label="Tampilkan Saluran Favorit Saja")
        self.chk_favorites.Bind(wx.EVT_CHECKBOX, self.on_filter_changed)
        main_sizer.Add(self.chk_favorites, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 4. Daftar Saluran TV (ListBox)
        lbl_list = wx.StaticText(self, label="Daftar Saluran TV (Tekan Enter untuk Putar):")
        main_sizer.Add(lbl_list, 0, wx.LEFT | wx.RIGHT, 6)

        self.list_channels = wx.ListBox(self, style=wx.LB_SINGLE)
        self.list_channels.Bind(wx.EVT_LISTBOX, self.on_channel_selection_changed)
        self.list_channels.Bind(wx.EVT_LISTBOX_DCLICK, self.on_channel_activate)
        self.list_channels.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        main_sizer.Add(self.list_channels, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 5. Bilah Tombol Aksi (Putar/Stop & Tambah/Hapus Favorit)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_play_stop = wx.Button(self, label="Putar")
        self.btn_play_stop.Bind(wx.EVT_BUTTON, self.on_btn_play_stop)
        btn_sizer.Add(self.btn_play_stop, 1, wx.RIGHT, 4)

        self.btn_fav = wx.Button(self, label="Tambah ke Favorit")
        self.btn_fav.Bind(wx.EVT_BUTTON, self.on_btn_fav)
        btn_sizer.Add(self.btn_fav, 1, wx.LEFT, 4)

        main_sizer.Add(btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 6. Bilah Tombol Saluran Kustom Pribadi
        custom_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btn_add_custom = wx.Button(self, label="Tambah Saluran Kustom...")
        self.btn_add_custom.Bind(wx.EVT_BUTTON, self.on_add_custom)
        custom_btn_sizer.Add(self.btn_add_custom, 1, wx.RIGHT, 4)

        self.btn_del_custom = wx.Button(self, label="Hapus Saluran Kustom")
        self.btn_del_custom.Bind(wx.EVT_BUTTON, self.on_del_custom)
        custom_btn_sizer.Add(self.btn_del_custom, 1, wx.LEFT, 4)

        main_sizer.Add(custom_btn_sizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        # 7. Slider Volume Native
        vol_box = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_volume = wx.StaticText(self, label=f"Volume: {self.player.get_volume()}%")
        vol_box.Add(self.lbl_volume, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        self.slider_volume = wx.Slider(
            self,
            value=self.player.get_volume(),
            minValue=0,
            maxValue=100,
            style=wx.SL_HORIZONTAL
        )
        self.slider_volume.Bind(wx.EVT_SLIDER, self.on_slider_volume)
        vol_box.Add(self.slider_volume, 1, wx.EXPAND)

        main_sizer.Add(vol_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # 8. Tombol Tutup Dialog
        self.btn_close = wx.Button(self, wx.ID_CANCEL, label="Tutup")
        self.btn_close.Bind(wx.EVT_BUTTON, self.on_close)
        main_sizer.Add(self.btn_close, 0, wx.ALIGN_RIGHT | wx.ALL, 6)

        self.SetSizer(main_sizer)

    def _populate_countries(self):
        countries = self.channel_mgr.get_countries()
        self.combo_country.Clear()
        for idx, c in enumerate(countries):
            self.combo_country.Append(c.get('name', ''), c.get('code', ''))
        if self.combo_country.GetCount() > 0:
            self.combo_country.SetSelection(0)

    def _get_selected_country_code(self):
        sel = self.combo_country.GetSelection()
        if sel != wx.NOT_FOUND:
            return self.combo_country.GetClientData(sel)
        return 'ID'

    def _update_channel_list(self):
        country_code = self._get_selected_country_code()
        search = self.txt_search.GetValue()
        fav_only = self.chk_favorites.IsChecked()

        self._current_channels = self.channel_mgr.get_channels(
            country_code=country_code,
            search_query=search,
            favorites_only=fav_only
        )

        self.list_channels.Clear()
        for ch in self._current_channels:
            fav_marker = "★ " if self.channel_mgr.favorites.is_favorite(ch.get('id')) else ""
            custom_marker = "[Kustom] " if ch.get('is_custom') else ""
            cat = f" [{ch.get('category')}]" if ch.get('category') else ""
            self.list_channels.Append(f"{fav_marker}{custom_marker}{ch.get('name', '')}{cat}")

        if self._current_channels:
            self.list_channels.SetSelection(0)

        self._update_button_states()

    def _get_selected_channel(self):
        sel = self.list_channels.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self._current_channels):
            return self._current_channels[sel]
        return None

    def _update_button_states(self):
        ch = self._get_selected_channel()
        if not ch:
            self.btn_play_stop.Enable(False)
            self.btn_fav.Enable(False)
            self.btn_del_custom.Enable(False)
            return

        self.btn_play_stop.Enable(True)
        self.btn_fav.Enable(True)

        # Status tombol hapus saluran kustom
        if ch.get('is_custom') or self.channel_mgr.custom.is_custom(ch.get('id')):
            self.btn_del_custom.Enable(True)
        else:
            self.btn_del_custom.Enable(False)

        # Status tombol favorit
        if self.channel_mgr.favorites.is_favorite(ch.get('id')):
            self.btn_fav.SetLabel("Hapus dari Favorit")
        else:
            self.btn_fav.SetLabel("Tambah ke Favorit")

        # Status tombol putar / stop
        if self.player.is_playing() and self.player.get_current_title() == ch.get('name'):
            self.btn_play_stop.SetLabel("Stop")
        else:
            self.btn_play_stop.SetLabel("Putar")

    def _play_channel(self, channel):
        if not channel:
            return

        name = channel.get('name', 'Siaran TV')
        url = channel.get('url', '')

        def _on_status(status, msg):
            wx.CallAfter(self._on_player_status, status, msg)

        self.player.play(url, name, status_callback=_on_status)

    def _on_player_status(self, status, msg):
        ui.message(msg)
        try:
            self._update_button_states()
        except Exception:
            pass

    def on_search_text(self, event):
        self._update_channel_list()

    def on_search_enter(self, event):
        # Tekan Enter di kotak pencarian: jika ada hasil, langsung putar saluran pertama
        ch = self._get_selected_channel()
        if ch:
            self._play_channel(ch)
        else:
            ui.message("Saluran tidak ditemukan.")

    def on_country_changed(self, event):
        self._update_channel_list()
        country_name = self.combo_country.GetStringSelection()
        ui.message(f"Negara: {country_name}")

    def on_filter_changed(self, event):
        self._update_channel_list()
        if self.chk_favorites.IsChecked():
            ui.message("Menampilkan daftar favorit")
        else:
            ui.message("Menampilkan semua saluran")

    def on_channel_selection_changed(self, event):
        self._update_button_states()

    def on_channel_activate(self, event):
        ch = self._get_selected_channel()
        if ch:
            self._play_channel(ch)

    def on_list_key_down(self, event):
        key = event.GetKeyCode()
        if key in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE):
            ch = self._get_selected_channel()
            if ch:
                self._play_channel(ch)
                return
        event.Skip()

    def on_btn_play_stop(self, event):
        ch = self._get_selected_channel()
        if not ch:
            return

        if self.player.is_playing() and self.player.get_current_title() == ch.get('name'):
            self.player.stop(status_callback=lambda st, msg: wx.CallAfter(self._on_player_status, st, msg))
        else:
            self._play_channel(ch)

    def on_btn_fav(self, event):
        ch = self._get_selected_channel()
        if not ch:
            return

        is_now_fav = self.channel_mgr.favorites.toggle_favorite(ch)
        name = ch.get('name', '')
        if is_now_fav:
            ui.message(f"{name} ditambahkan ke favorit.")
        else:
            ui.message(f"{name} dihapus dari favorit.")

        # Perbarui tampilan list
        sel_idx = self.list_channels.GetSelection()
        self._update_channel_list()
        if sel_idx != wx.NOT_FOUND and sel_idx < self.list_channels.GetCount():
            self.list_channels.SetSelection(sel_idx)
        self._update_button_states()

    def on_add_custom(self, event):
        dlg = AddChannelDialog(self)
        if dlg.ShowModal() == wx.ID_OK and dlg.channel_data:
            name, url, cat = dlg.channel_data
            ch, err = self.channel_mgr.custom.add_channel(name, url, cat)
            if err:
                ui.message(err)
            else:
                ui.message(f"Saluran {name} berhasil ditambahkan.")
                # Pilih kategori custom jika ada
                for idx in range(self.combo_country.GetCount()):
                    if self.combo_country.GetClientData(idx) == 'CUSTOM':
                        self.combo_country.SetSelection(idx)
                        break
                self._update_channel_list()
                # Pilih saluran yang baru ditambahkan
                for idx, c in enumerate(self._current_channels):
                    if c.get('id') == ch.get('id'):
                        self.list_channels.SetSelection(idx)
                        self._update_button_states()
                        break
        dlg.Destroy()

    def on_del_custom(self, event):
        ch = self._get_selected_channel()
        if not ch or not (ch.get('is_custom') or self.channel_mgr.custom.is_custom(ch.get('id'))):
            return

        name = ch.get('name', 'Saluran')
        self.channel_mgr.custom.remove_channel(ch.get('id'))
        ui.message(f"Saluran kustom {name} berhasil dihapus.")
        self._update_channel_list()

    def on_slider_volume(self, event):
        val = self.slider_volume.GetValue()
        self.player.set_volume(val)
        self.lbl_volume.SetLabel(f"Volume: {val}%")
        # Announce ke NVDA
        ui.message(f"Volume {val} persen")

    def on_char_hook(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.Close()
            return
        event.Skip()

    def on_close(self, event):
        AccessTVDialog._instance = None
        self.Destroy()
