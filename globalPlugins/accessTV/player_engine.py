# -*- coding: utf-8 -*-
"""
Access TV - Audio Player Engine (BASS Library Integration)
Memutar aliran audio HLS (.m3u8) siaran TV secara ringan di latar belakang tanpa membebani sistem.
"""

import ctypes
import os
import threading
import time

# BASS Constants
_BASS_ATTRIB_VOL = 2
_BASS_CONFIG_BUFFER = 0
_BASS_CONFIG_NET_TIMEOUT = 11
_BASS_CONFIG_NET_BUFFER = 12
_BASS_CONFIG_NET_PREBUF = 15
_BASS_CONFIG_NET_AGENT = 16
_BASS_CONFIG_NET_READTIMEOUT = 37
_BASS_CONFIG_NET_HTTPS_FLAG = 71
_BASS_CONFIG_NET_SSL = 73
_BASS_CONFIG_NET_SSL_VERIFY = 74
_BASS_ERROR_ALREADY = 8
_BASS_STREAM_BLOCK = 0x100000

_BASS_ACTIVE_STOPPED = 0
_BASS_ACTIVE_PLAYING = 1
_BASS_ACTIVE_STALLED = 2
_BASS_ACTIVE_PAUSED = 3

class PlayerEngine:
    _instance = None
    _singleton_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self):
        self._lock = threading.Lock()
        self._dll = None
        self._current_stream = 0
        self._current_title = ""
        self._current_url = ""
        self._volume = 80  # Default 80%
        self._is_initialized = False
        self._worker_thread = None

        # Auto-Reconnect State
        self._is_user_stopped = True
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3
        self._stalled_count = 0
        self._status_callback = None
        self._monitor_running = True
        self._monitor_thread = None

        self._init_bass()
        self._start_monitor_thread()

    def _init_bass(self):
        base_dir = os.path.dirname(__file__)
        is_64bit = ctypes.sizeof(ctypes.c_void_p) == 8

        if is_64bit:
            bass_dir = os.path.join(base_dir, 'bass', 'x64')
        else:
            bass_dir = os.path.join(base_dir, 'bass')

        bass_dll_path = os.path.join(bass_dir, 'bass.dll')
        if not os.path.exists(bass_dll_path):
            return

        try:
            self._dll = ctypes.WinDLL(bass_dll_path)
        except Exception:
            return

        # Inisialisasi BASS audio device (-1 = default Windows soundcard)
        if not self._dll.BASS_Init(-1, 44100, 0, None, None):
            err = self._dll.BASS_ErrorGetCode()
            if err != _BASS_ERROR_ALREADY:
                return

        # Konfigurasi timeout & SSL untuk streaming HLS
        try:
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_HTTPS_FLAG, 1)
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL, 1)
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_SSL_VERIFY, 0) # Bypass expired certs
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_TIMEOUT, 10000) # 10s timeout
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_READTIMEOUT, 10000)
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_BUFFER, 15000)  # Buffer 15s (aman untuk chunk HLS 10s & hemat RAM ~1MB)
            self._dll.BASS_SetConfig(_BASS_CONFIG_NET_PREBUF, 0)

            # User Agent browser modern agar stream tidak diblokir
            ua = b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            if hasattr(self._dll, 'BASS_SetConfigPtr'):
                self._dll.BASS_SetConfigPtr(_BASS_CONFIG_NET_AGENT, ua)
        except Exception:
            pass

        # Muat plugin pendukung (HLS, AAC, SSL, FLAC, OPUS)
        plugins = ['basshls.dll', 'bass_aac.dll', 'bass_ssl.dll', 'bassopus.dll', 'bassflac.dll']
        for p in plugins:
            plugin_path = os.path.join(bass_dir, p)
            if os.path.exists(plugin_path):
                try:
                    self._dll.BASS_PluginLoad(plugin_path.encode('mbcs'), 0)
                except Exception:
                    pass

        self._is_initialized = True

    def _start_monitor_thread(self):
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def _monitor_loop(self):
        while self._monitor_running:
            time.sleep(1.5)
            if not self._is_initialized or not self._dll:
                continue

            with self._lock:
                if self._is_user_stopped or not self._current_stream or not self._current_url:
                    continue
                stream = self._current_stream
                url = self._current_url
                title = self._current_title
                callback = self._status_callback
                stalled_count = self._stalled_count

            try:
                state = self._dll.BASS_ChannelIsActive(stream)
            except Exception:
                continue

            if state == _BASS_ACTIVE_PLAYING:
                with self._lock:
                    self._stalled_count = 0
            elif state == _BASS_ACTIVE_STALLED:
                with self._lock:
                    self._stalled_count = stalled_count + 1
                    current_stalled = self._stalled_count
                # Jika tersendat lebih dari 6 detik (4 x 1.5s), coba sambung ulang
                if current_stalled >= 4:
                    self._trigger_reconnect(url, title, callback)
            elif state == _BASS_ACTIVE_STOPPED:
                # Aliran terputus dari sisi server tanpa diminta pengguna
                self._trigger_reconnect(url, title, callback)

    def _trigger_reconnect(self, url, title, callback):
        with self._lock:
            if self._is_user_stopped or self._current_url != url:
                return

            if self._reconnect_attempts >= self._max_reconnect_attempts:
                self._stop_current_stream_locked()
                self._is_user_stopped = True
                self._reconnect_attempts = 0
                if callback:
                    callback("error", f"Koneksi {title} terputus setelah {self._max_reconnect_attempts} kali mencoba.")
                return

            self._reconnect_attempts += 1
            attempt = self._reconnect_attempts
            self._stop_current_stream_locked()
            self._current_url = url
            self._current_title = title
            self._stalled_count = 0

        if callback:
            callback("buffering", f"Koneksi tersendat. Menyambung ulang {title} ({attempt}/{self._max_reconnect_attempts})...")

        time.sleep(1.0)

        def _reconnect_worker():
            try:
                stream = self._dll.BASS_StreamCreateURL(
                    url.encode('utf-8'),
                    0,
                    _BASS_STREAM_BLOCK,
                    None,
                    None
                )
                if not stream:
                    stream = self._dll.BASS_StreamCreateURL(
                        url.encode('utf-8'),
                        0,
                        0,
                        None,
                        None
                    )
                with self._lock:
                    if self._is_user_stopped or self._current_url != url:
                        if stream:
                            self._dll.BASS_StreamFree(stream)
                        return

                    if stream:
                        self._current_stream = stream
                        vol_float = ctypes.c_float(float(self._volume) / 100.0)
                        self._dll.BASS_ChannelSetAttribute(stream, _BASS_ATTRIB_VOL, vol_float)
                        self._dll.BASS_ChannelPlay(stream, 0)
                        self._stalled_count = 0
                        self._reconnect_attempts = 0

                if stream:
                    if callback:
                        callback("playing", f"Tersambung kembali: {title}")
            except Exception:
                pass

        threading.Thread(target=_reconnect_worker, daemon=True).start()

    def play(self, url, title="Siaran TV", status_callback=None):
        """
        Memulai pemutaran siaran TV di background thread agar NVDA tidak macet saat koneksi.
        """
        if not self._is_initialized or not self._dll:
            if status_callback:
                status_callback("error", "Mesin pemutar audio BASS tidak tersedia.")
            return

        with self._lock:
            # Hentikan stream sebelumnya jika ada
            self._stop_current_stream_locked()
            self._current_title = title
            self._current_url = url
            self._is_user_stopped = False
            self._reconnect_attempts = 0
            self._stalled_count = 0
            self._status_callback = status_callback

        if status_callback:
            status_callback("buffering", f"Menghubungkan {title}...")

        def _worker():
            try:
                # Buka URL siaran via BASS (coba BLOCK dahulu, fallback non-block)
                stream = self._dll.BASS_StreamCreateURL(
                    url.encode('utf-8'),
                    0,
                    _BASS_STREAM_BLOCK,
                    None,
                    None
                )
                if not stream:
                    stream = self._dll.BASS_StreamCreateURL(
                        url.encode('utf-8'),
                        0,
                        0,
                        None,
                        None
                    )
                err = self._dll.BASS_ErrorGetCode()

                with self._lock:
                    if self._current_url != url:
                        # Pengguna sudah memilih saluran lain saat proses koneksi berlangsung
                        if stream:
                            self._dll.BASS_StreamFree(stream)
                        return

                    if stream:
                        self._current_stream = stream
                        # Terapkan volume tersimpan
                        vol_float = ctypes.c_float(float(self._volume) / 100.0)
                        self._dll.BASS_ChannelSetAttribute(stream, _BASS_ATTRIB_VOL, vol_float)
                        self._dll.BASS_ChannelPlay(stream, 0)

                if stream:
                    if status_callback:
                        status_callback("playing", f"Memutar {title}")
                else:
                    if status_callback:
                        msg = f"Gagal memutar {title}"
                        if err == 41:
                            msg += " (Format atau enkripsi siaran tidak didukung)"
                        elif err in (2, 40):
                            msg += " (Server siaran offline atau menolak koneksi)"
                        elif err == 32:
                            msg += " (Koneksi timeout)"
                        else:
                            msg += f" (Kode: {err})"
                        status_callback("error", msg)
            except Exception as e:
                if status_callback:
                    status_callback("error", f"Kesalahan memutar {title}: {str(e)}")

        self._worker_thread = threading.Thread(target=_worker, daemon=True)
        self._worker_thread.start()

    def _stop_current_stream_locked(self):
        if self._current_stream:
            try:
                self._dll.BASS_ChannelStop(self._current_stream)
                self._dll.BASS_StreamFree(self._current_stream)
            except Exception:
                pass
            self._current_stream = 0
            # Bersihkan memori buffer seketika
            try:
                import gc
                gc.collect()
            except Exception:
                pass

    def stop(self, status_callback=None):
        with self._lock:
            self._is_user_stopped = True
            self._reconnect_attempts = 0
            self._stalled_count = 0
            self._stop_current_stream_locked()
            title = self._current_title
            self._current_title = ""
            self._current_url = ""

        if status_callback:
            status_callback("stopped", "Siaran dihentikan")

    def toggle_play_pause(self, status_callback=None):
        with self._lock:
            if not self._current_stream or not self._dll:
                return

            state = self._dll.BASS_ChannelIsActive(self._current_stream)
            if state == _BASS_ACTIVE_PLAYING:
                self._dll.BASS_ChannelPause(self._current_stream)
                self._is_user_stopped = True
                if status_callback:
                    status_callback("paused", f"Jeda {self._current_title}")
            elif state == _BASS_ACTIVE_PAUSED:
                self._dll.BASS_ChannelPlay(self._current_stream, 0)
                self._is_user_stopped = False
                if status_callback:
                    status_callback("playing", f"Melanjutkan {self._current_title}")

    def set_volume(self, vol_percent):
        with self._lock:
            vol = max(0, min(100, int(vol_percent)))
            self._volume = vol
            if self._current_stream and self._dll:
                vol_float = ctypes.c_float(float(vol) / 100.0)
                self._dll.BASS_ChannelSetAttribute(self._current_stream, _BASS_ATTRIB_VOL, vol_float)

    def get_volume(self):
        with self._lock:
            return self._volume

    def is_playing(self):
        with self._lock:
            if self._current_stream and self._dll:
                return self._dll.BASS_ChannelIsActive(self._current_stream) == _BASS_ACTIVE_PLAYING
            return False

    def get_current_title(self):
        with self._lock:
            return self._current_title

    def free(self):
        self._monitor_running = False
        with self._lock:
            self._is_user_stopped = True
            self._stop_current_stream_locked()
            if self._dll:
                try:
                    self._dll.BASS_Free()
                except Exception:
                    pass
                self._dll = None
            self._is_initialized = False
