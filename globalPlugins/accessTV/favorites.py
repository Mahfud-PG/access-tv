# -*- coding: utf-8 -*-
"""
Access TV - Favorites Manager
Menyimpan dan mengelola daftar saluran TV favorit pengguna secara permanen.
"""

import json
import os
import threading

class FavoritesManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._favorites_file = self._get_storage_path()
        self._favorites = self._load()

    def _get_storage_path(self):
        try:
            import globalVars
            if hasattr(globalVars, 'appArgs') and hasattr(globalVars.appArgs, 'configPath') and globalVars.appArgs.configPath:
                return os.path.join(globalVars.appArgs.configPath, 'accessTV_favorites.json')
        except Exception:
            pass

        appdata = os.environ.get('APPDATA', '')
        if appdata:
            nvda_dir = os.path.join(appdata, 'nvda')
            if os.path.exists(nvda_dir):
                return os.path.join(nvda_dir, 'accessTV_favorites.json')

        # Fallback lokal
        return os.path.join(os.path.dirname(__file__), 'data', 'user_favorites.json')

    def _load(self):
        with self._lock:
            if os.path.exists(self._favorites_file):
                try:
                    with open(self._favorites_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            return data
                except Exception:
                    pass
            return []

    def save(self):
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self._favorites_file), exist_ok=True)
                with open(self._favorites_file, 'w', encoding='utf-8') as f:
                    json.dump(self._favorites, f, ensure_ascii=False, indent=2)
                return True
            except Exception:
                return False

    def is_favorite(self, channel_id):
        with self._lock:
            return any(c.get('id') == channel_id for c in self._favorites)

    def add_favorite(self, channel):
        with self._lock:
            cid = channel.get('id')
            if not any(c.get('id') == cid for c in self._favorites):
                self._favorites.append(channel)
        return self.save()

    def remove_favorite(self, channel_id):
        with self._lock:
            self._favorites = [c for c in self._favorites if c.get('id') != channel_id]
        return self.save()

    def toggle_favorite(self, channel):
        cid = channel.get('id')
        if self.is_favorite(cid):
            self.remove_favorite(cid)
            return False  # Sekarang bukan favorit
        else:
            self.add_favorite(channel)
            return True   # Sekarang favorit

    def get_all(self):
        with self._lock:
            return list(self._favorites)
