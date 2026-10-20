# -*- coding: utf-8 -*-
"""
Access TV - Channel Manager
Mengelola database saluran TV, pencarian instan, dan penyaringan berdasarkan negara / favorit.
"""

import json
import os
from .favorites import FavoritesManager
from .custom_channels import CustomChannelsManager

class ChannelManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.favorites = FavoritesManager()
        self.custom = CustomChannelsManager()
        self.countries = self._load_countries()
        self.channels = self._load_channels()

    def _load_countries(self):
        base_countries = []
        p = os.path.join(self.data_dir, 'countries.json')
        if os.path.exists(p):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    base_countries = json.load(f)
            except Exception:
                pass
        if not base_countries:
            base_countries = [{"code": "ID", "name": "Indonesia"}, {"code": "ALL", "name": "Semua Negara / Internasional"}]

        # Pastikan ada opsi Saluran Kustom Pribadi di pilihan negara
        countries = [{"code": "CUSTOM", "name": "★ Saluran Kustom Pribadi"}]
        for c in base_countries:
            if c.get('code') != 'CUSTOM':
                countries.append(c)
        return countries

    def _load_channels(self):
        channels = []
        if os.path.exists(self.data_dir):
            for fname in sorted(os.listdir(self.data_dir)):
                if fname.startswith('channels_') and fname.endswith('.json'):
                    p = os.path.join(self.data_dir, fname)
                    try:
                        with open(p, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                channels.extend(data)
                    except Exception:
                        pass
        return channels

    def get_countries(self):
        return list(self.countries)

    def get_channels(self, country_code='ID', search_query='', favorites_only=False):
        """
        Menyaring saluran berdasarkan negara, kata kunci pencarian, dan status favorit.
        """
        if favorites_only:
            pool = self.favorites.get_all()
        elif country_code == 'CUSTOM':
            pool = self.custom.get_all()
        elif country_code == 'ALL':
            pool = self.custom.get_all() + self.channels
        else:
            pool = [c for c in self.channels if c.get('country') == country_code]

        query = (search_query or '').strip().lower()
        if not query:
            return pool

        filtered = []
        for ch in pool:
            name = (ch.get('name') or '').lower()
            cat = (ch.get('category') or '').lower()
            if query in name or query in cat:
                filtered.append(ch)

        # Jika sedang mencari di negara tertentu, sertakan juga saluran kustom yang cocok
        if country_code not in ('CUSTOM', 'ALL', 'FAV'):
            custom_matches = [
                c for c in self.custom.get_all()
                if query in (c.get('name') or '').lower() or query in (c.get('category') or '').lower()
            ]
            existing_ids = {c.get('id') for c in filtered}
            for cm in custom_matches:
                if cm.get('id') not in existing_ids:
                    filtered.append(cm)

        return filtered
