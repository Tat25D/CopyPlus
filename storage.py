import json
import os
import random



import json
import os
import random
import sys

def get_base_dir():
    """Возвращает правильную папку в зависимости от среды (EXE или скрипт)"""
    if getattr(sys, 'frozen', False):
        # Если запущено как .exe, ищем папку data РЯДОМ с .exe файлом
        return os.path.dirname(sys.executable)
    else:
        # Если запущено как скрипт, ищем в текущей рабочей директории
        return os.path.dirname(os.path.abspath(__file__))
# --------------------

class StorageService:
    def __init__(self, filename="data/phrases.json"):
        self.filename = filename
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self.DEFAULT_LEGAL_WORDS = ["Пункт", "Часть", "Статья", "Заявление", "Копия", "Оригинал"]

    def load_default_settings(self):
        settings_path = "data/settings.json"

        # ДОБАВЛЕНО ПО ТЗ: Параметры блока "Кратко" по умолчанию, если файл не существует или поврежден
        default_dict = {
            "load_defaults": True,
            "panel_width": 350,
            "opacity": 45,
            "current_theme": "Obsidian",
            "is_short": True, # Галочка включена по умолчанию
            "from_start": "7", # 7 символов с начала
            "from_end": "5", # 4 символа с конца
            "is_phrase": True, # Выбрана радиокнопка "Фраза"
            "is_rounded": True # Галочка "Скруглить" включена по умолчанию
        }

        if not os.path.exists(settings_path):
            return default_dict
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Безопасно подмешиваем новые дефолтные параметры, если их еще нет в файле настроек
                for key, val in default_dict.items():
                    if key not in data:
                        data[key] = val
                return data
        except:
            return default_dict

    def save_default_settings(self, settings):
        settings_path = "data/settings.json"
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except:
            pass

    def load_phrases(self, only_active=False):
        # Если кэш всех фраз уже в памяти, отдаем данные моментально без чтения диска
        if hasattr(self, '_all_phrases_cache') and self._all_phrases_cache is not None:
            if only_active:
                return [w for w in self._all_phrases_cache if w.get("is_active", True)]
            return self._all_phrases_cache

        # Холодный старт: если файла нет, инициализируем пустой кэш
        if not os.path.exists(self.filename):
            self._all_phrases_cache = []
            return []

        # Читаем диск один единственный раз при запуске программы
        try:
            with open(self.filename, 'r', encoding='utf-8') as f:
                self._all_phrases_cache = json.load(f)
        except:
            self._all_phrases_cache = []

        if only_active:
            return [w for w in self._all_phrases_cache if w.get("is_active", True)]
        return self._all_phrases_cache

    def save_phrases(self, phrases):
        # На лету обновляем оперативную память, чтобы оверлей сразу видел изменения
        self._all_phrases_cache = phrases
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(phrases, f, ensure_ascii=False, indent=4)
        except:
            pass

    def get_random_color(self):
        return f"#{random.randint(0, 0xFFFFFF):06X}"

    def load_or_generate_random_theme(self):
        path = "data/random_theme.json"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    colors = json.load(f)
                    if isinstance(colors, list) and len(colors) == 48:
                        return colors
            except:
                pass
        new_colors = [f"#{random.randint(30, 220):02X}{random.randint(30, 220):02X}{random.randint(30, 220):02X}" for _ in range(48)]
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_colors, f, indent=4)
        except:
            pass
        return new_colors

    def load_or_generate_random_gray_theme(self):
        path = "data/random_gray_theme.json"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    colors = json.load(f)
                    if isinstance(colors, list) and len(colors) == 48:
                        return colors
            except:
                pass
        new_gray_colors = []
        for _ in range(48):
            val = random.randint(40, 210)
            new_gray_colors.append(f"#{val:02X}{val:02X}{val:02X}")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_gray_colors, f, indent=4)
        except:
            pass
        return new_gray_colors
