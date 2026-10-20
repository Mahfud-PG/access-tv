# -*- coding: utf-8 -*-
"""
Access TV - Custom Channels Manager
Menyimpan dan mengelola daftar saluran TV kustom yang ditambahkan sendiri oleh pengguna secara permanen.
"""

import json
import os
import re
import threading
import time

class CustomChannelsManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._custom_file = self._get_storage_path()
        self._channels = self._load()

    def _get_storage_path(self):
        try:
            import globalVars
            if hasattr(globalVars, 'appArgs') and hasattr(globalVars.appArgs, 'configPath') and globalVars.appArgs.configPath:
                return os.path.join(globalVars.appArgs.configPath, 'accessTV_custom.json')
        except Exception:
            pass

        appdata = os.environ.get('APPDATA', '')
        if appdata:
            nvda_dir = os.path.join(appdata, 'nvda')
            if os.path.exists(nvda_dir):
                return os.path.join(nvda_dir, 'accessTV_custom.json')

        # Fallback lokal
        return os.path.join(os.path.dirname(__file__), 'data', 'user_custom.json')

    def _load(self):
        with self._lock:
            if os.path.exists(self._custom_file):
                try:
                    with open(self._custom_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data
                except Exception:
                    pass
            return []

    def save(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._custom_file), exist_ok=True)
                with open(self._custom_file, 'w', encoding='utf-8') as f:
                    json.dump(self._channels, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    def get_all(self):
        with self._lock:
            return list(self._channels)

    def is_custom(self, channel_id):
        with self._lock:
            return any(c.get('id') == channel_id for c in self._channels)

    def add_channel(self, name, url, category="Kustom"):
        name = (name or '').strip()
        url = (url or '').strip()
        category = (category or 'Kustom').strip()

        if not name:
            return None, "Nama saluran tidak boleh kosong."
        if not url:
            return None, "URL streaming tidak boleh kosong."

        if not (url.lower().startswith('http://') or url.lower().startswith('https://')):
            return None, "URL streaming harus diawali dengan http:// atau https://"

        with self._lock:
            for c in self._channels:
                if c.get('url', '').strip().lower() == url.lower():
                    return None, f"URL ini sudah ada di daftar saluran kustom ({c.get('name')})."

            slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
            cid = f"custom-{slug}-{int(time.time())}"

            channel = {
                'id': cid,
                'name': name,
                'category': category,
                'country': 'CUSTOM',
                'url': url,
                'is_custom': True
            }
            self._channels.append(channel)

        if self.save():
            return channel, None
        return None, "Gagal menyimpan saluran kustom ke penyimpanan."

    def remove_channel(self, channel_id):
        with self._lock:
            self._channels = [c for c in self._channels if c.get('id') != channel_id]
        return self.save()
