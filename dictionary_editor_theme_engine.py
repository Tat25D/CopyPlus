import os
import json
import random
import colorsys
from PyQt6.QtWidgets import QColorDialog, QApplication
from PyQt6.QtGui import QColor
class EditorThemeEngineLogic:

    def generate_random_obsidian_palette(self, count=48):
        """Генерирует случайные глубокие цвета в стиле Obsidian"""
        import random
        palette = []
        for _ in range(count):
            # Ограничиваем светлость (25%-45%) и насыщенность (40%-80%)
            h = random.randint(0, 359)
            s = random.randint(40, 80)
            l = random.randint(25, 45)
            r, g, b = colorsys.hls_to_rgb(h/360.0, l/100.0, s/100.0)
            palette.append(f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}")
        random.shuffle(palette)
        return palette

    def generate_safe_random_palette(self, count=48):
        """Генерирует случайные цвета с ограничением по яркости"""
        import random
        settings = self.storage.load_default_settings() or {}

        # Читаем границы из пикеров (по умолчанию средне-серые)
        dark_hex = settings.get("random_dark_bound", "#3C3C3C")
        light_hex = settings.get("random_light_bound", "#DCDCDC")

        def hex_to_luminance(h):
            h = h.lstrip('#')
            r, g, b = int(h[0:2], 16)/255.0, int(h[2:4], 16)/255.0, int(h[4:6], 16)/255.0
            return 0.299 * r + 0.587 * g + 0.114 * b # Формула восприятия яркости глазом

        min_l = hex_to_luminance(dark_hex)
        max_l = hex_to_luminance(light_hex)
        if min_l > max_l: min_l, max_l = max_l, min_l

        palette = []
        for _ in range(count):
            h = random.random() # Случайный оттенок
            s = random.uniform(0.3, 0.85) # Сохраняем насыщенность
            l = random.uniform(min_l, max_l) # Яркость строго в заданных границах
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            palette.append(f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}")
        return palette

    def trigger_gradient_picker(self, picker_index):
        """Вызывает нативный диалог Windows для окраски выбранного прямоугольного пикера"""
        key_name = f"gradient_c{picker_index}"
        current_hex = self.settings.get(key_name, "#7C3AED")
        color = QColorDialog.getColor(QColor(current_hex), self, f"Выберите цвет пикера №{picker_index}")
        if color.isValid():
            hex_color = color.name().upper()
            self.settings[key_name] = hex_color
            self.storage.save_default_settings(self.settings)
            # Проверка наличия пикеров в UI для защиты от AttributeError
            target_btn_attr = f"grad_pick{picker_index}"
            if hasattr(self, target_btn_attr):
                target_btn = getattr(self, target_btn_attr)
                target_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #FFFFFF; border-radius: 4px;")

    def calculate_double_gradient(self):
        """Математический расчет составного двухколенного градиента (C1 -> C2 -> C3)"""
        c1 = QColor(self.settings.get("gradient_c1", "#1A365D"))
        c2 = QColor(self.settings.get("gradient_c2", "#7C3AED"))
        c3 = QColor(self.settings.get("gradient_c3", "#78281F"))
        palette_48 = []
        for i in range(24):
            ratio = i / 23.0 if i > 0 else 0.0
            r = int(c1.red() + (c2.red() - c1.red()) * ratio)
            g = int(c1.green() + (c2.green() - c1.green()) * ratio)
            b = int(c1.blue() + (c2.blue() - c1.blue()) * ratio)
            palette_48.append(f"#{r:02X}{g:02X}{b:02X}")
        for i in range(24):
            ratio = i / 23.0 if i > 0 else 0.0
            r = int(c2.red() + (c3.red() - c2.red()) * ratio)
            g = int(c2.green() + (c3.green() - c2.green()) * ratio)
            b = int(c2.blue() + (c3.blue() - c2.blue()) * ratio)
            palette_48.append(f"#{r:02X}{g:02X}{b:02X}")

        # Проверка чекбокса случайного порядка
        if hasattr(self, 'chk_gradient_random') and self.chk_gradient_random.isChecked():
            random.shuffle(palette_48)
            self.settings["gradient_mode"] = "Случайно"
        else:
            self.settings["gradient_mode"] = "Градиент"

        # РАСЧЕТ ГРАДИЕНТА ДЛЯ 8 КНОПОК СЛОВАРЯ (C1 -> C3)
        dict_gradient_8 = []
        for i in range(8):
            ratio = i / 7.0 if i > 0 else 0.0
            r = int(c1.red() + (c3.red() - c1.red()) * ratio)
            g = int(c1.green() + (c3.green() - c1.green()) * ratio)
            b = int(c1.blue() + (c3.blue() - c1.blue()) * ratio)
            dict_gradient_8.append(f"#{r:02X}{g:02X}{b:02X}")

        self.settings["dict_btn_gradient"] = dict_gradient_8
        self.storage.save_default_settings(self.settings)
        return palette_48

    def trigger_apply_gradient_click(self):
        if hasattr(self, 'combo_theme') and self.combo_theme.currentText() == "Оттенки":
            self.dark_palette = self.calculate_double_gradient()
            if hasattr(self, 'generate_palette_ui_buttons') and hasattr(self, 'picker_grid'):
                self.generate_palette_ui_buttons(self.picker_grid)
            if hasattr(self, 'force_direct_save_to_json'):
                self.force_direct_save_to_json()

            # Обновляем цвета на самих кнопках C1, C2, C3
            for i in range(1, 4):
                target_btn_attr = f"grad_pick{i}"
                if hasattr(self, target_btn_attr):
                    color = self.settings.get(f"gradient_c{i}", "#7C3AED")
                    getattr(self, target_btn_attr).setStyleSheet(f"background-color: {color}; border: 1px solid #FFFFFF; border-radius: 4px;")

    def rebuild_palette_by_theme_name(self, theme_name, is_refresh_action=False, clear_custom_colors=True):
        """Интеллектуальный расчет тем"""
        # ═══════ ДОБАВЛЕНО: Сброс ручных цветов при смене/обновлении темы ═══════
        if clear_custom_colors:
            words = self.storage.load_phrases()
            needs_save = False
            for w in words:
                if w.get("is_custom_color", False):
                    w["is_custom_color"] = False
                    needs_save = True
            if needs_save:
                self.storage.save_phrases(words)
        # ═══════════════════════════════════════════════════════════════════
        obsidian_base = [
            "#2C3E50", "#1A365D", "#1A472A", "#4A3728", "#3B2244", "#2D3748", "#4A1525", "#2C2C2C",
            "#34495E", "#2C3E6B", "#27AE60", "#D35400", "#8E44AD", "#7F8C8D", "#C0392B", "#16A085",
            "#212F3D", "#1B2631", "#1E4620", "#512E5F", "#4A235A", "#0E6251", "#78281F", "#626567",
            "#3B82F6", "#6366F1", "#10B981", "#F59E0B", "#EC4899", "#84CC16", "#14B8A6", "#6B7280",
            "#1E1B4B", "#311042", "#064E3B", "#451A03", "#701A75", "#0F172A", "#581C87", "#032B30",
            "#4338CA", "#6D28D9", "#047857", "#B45309", "#BE185D", "#4B5563", "#9333EA", "#374151"
        ]

        if theme_name == "Случайная":
            self.dark_palette = self.generate_safe_random_palette()
        elif theme_name == "Json":
            user_path = "data/buttonColors.json"
            if os.path.exists(user_path):
                try:
                    with open(user_path, 'r', encoding='utf-8') as f:
                        colors = json.load(f)
                        if isinstance(colors, list) and len(colors) == 48:
                            self.dark_palette = colors
                        else:
                            self.dark_palette = obsidian_base
                except:
                    self.dark_palette = obsidian_base
            else:
                self.dark_palette = obsidian_base
        elif theme_name == "Оттенки":
            self.dark_palette = self.calculate_double_gradient()
        else:
            # ЛОГИКА OBSIDIAN:
            # Если это клик по кнопке "Обновить" - генерируем новые
            # Если это просто переключение/запуск - берем классический obsidian_base
            if is_refresh_action:
                self.dark_palette = self.generate_random_obsidian_palette()
            else:
                self.dark_palette = obsidian_base

        # ФИКС ДЛЯ ПАРЯЩЕГО ОКНА: Сохраняем цвета для парящего окна
        # Сначала подтягиваем из файла самые свежие настройки (например, новые цвета пикеров),
        # чтобы наш старый кэш self.settings их не затер!
        # Сохраняем цвета для парящего окна
        self.settings = self.storage.load_default_settings() or {}
        self.settings["current_theme_palette"] = self.dark_palette
        self.storage.save_default_settings(self.settings)

        # ТОЛЬКО перерисовываем кнопки, не трогая геометрию окна!
        if hasattr(self, 'generate_palette_ui_buttons') and hasattr(self, 'picker_grid'):
            self.generate_palette_ui_buttons(self.picker_grid)

        # ДОБАВИТЬ: Перерисовываем цветные квадратики в списке слева
        if hasattr(self, 'refresh_list'):
            self.refresh_list()

        self.update()
