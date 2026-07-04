import json
import json
from PyQt6.QtCore import QTimer # ДОБАВИТЬ СЮДА

class DictionaryEditorSettingsLogic:
    def get_hotkey_string(self):
        """Собирает компоненты хоткея из UI в единую строку для библиотеки keyboard"""
        parts = []
        if hasattr(self, 'chk_ctrl') and self.chk_ctrl.isChecked():
            parts.append("ctrl")
        if hasattr(self, 'chk_shift') and self.chk_shift.isChecked():
            parts.append("shift")
        if hasattr(self, 'chk_alt') and self.chk_alt.isChecked():
            parts.append("alt")

        f_key = ""
        if hasattr(self, 'combo_f_keys'):
            f_key = self.combo_f_keys.currentText().lower()

        if f_key and f_key != "нет":
            parts.append(f_key)
        elif hasattr(self, 'inp_char'):
            char = self.inp_char.text().strip().lower()
            if char:
                parts.append(char)

        return "+".join(parts) if parts else "alt+f1"

    def _trigger_delayed_save(self):
        """Отложенное сохранение настроек (защита от зависания при быстром дергании ползунков)"""
        if getattr(self, '_is_initializing', False):
            return
        # Создаем таймер при первом вызове (поскольку класс - миксин без __init__)
        if not hasattr(self, '_settings_save_timer'):
            self._settings_save_timer = QTimer(self)
            self._settings_save_timer.setSingleShot(True)
            self._settings_save_timer.setInterval(150) # Ждем 150мс после остановки ползунка
            self._settings_save_timer.timeout.connect(self.save_global_settings)

        # Если ползунок все еще двигается, сбрасываем таймер
        self._settings_save_timer.stop()
        self._settings_save_timer.start()

    def handle_width_slider_change(self, value):
        self.lbl_width_val.setText(f"{value}px")
        self._trigger_delayed_save() # БЫЛО: self.save_global_settings()

    def handle_opacity_slider_change(self, value):
        self.lbl_opacity_val.setText(f"{value}%")
        self._trigger_delayed_save() # БЫЛО: self.save_global_settings()

    def handle_menu_width_slider_change(self, value):
        self.lbl_menu_width_val.setText(f"{value}px")
        self._trigger_delayed_save() # БЫЛО: self.save_global_settings()

    def handle_font_size_slider_change(self, value):
        self.lbl_font_size_val.setText(f"{value}px")
        self._trigger_delayed_save() # БЫЛО: self.save_global_settings()

    def set_active_color(self, hex_color):
        self.selected_color = hex_color
        # ДОБАВИТЬ: Флаг того, что цвет выбран вручную, а не генерится темой
        self._is_setting_custom_color = True
        self.force_direct_save_to_json()

    def save_global_settings(self):
        if getattr(self, '_is_initializing', False):
            return
        # ЗАГРУЖАЕМ АКТУАЛЬНЫЕ НАСТРОЙКИ
        current_cfg = self.storage.load_default_settings() or {}

        # Сохраняем параметры блока "Кратко"
        if hasattr(self, 'chk_short'):
            current_cfg["is_short"] = self.chk_short.isChecked()
        if hasattr(self, 'inp_from_start'):
            current_cfg["from_start"] = self.inp_from_start.text().strip() or "7"
        if hasattr(self, 'inp_from_end'):
            current_cfg["from_end"] = self.inp_from_end.text().strip() or "4"
        if hasattr(self, 'rad_word') and hasattr(self, 'rad_phrase'):
            current_cfg["is_phrase"] = self.rad_phrase.isChecked()

        if hasattr(self, 'chk_skip_decline_warning'):
            current_cfg["skip_decline_warning"] = self.chk_skip_decline_warning.isChecked()

        # Обновляем слайдеры
        if hasattr(self, 'slider_width'):
            current_cfg["panel_width"] = self.slider_width.value()
        if hasattr(self, 'slider_opacity'):
            current_cfg["opacity"] = self.slider_opacity.value()
        if hasattr(self, 'slider_menu_width'):
            current_cfg["menu_width"] = self.slider_menu_width.value()

        # СОХРАНЕНИЕ РАЗМЕРА ШРИФТА (должно быть ЗДЕСЬ, после current_cfg)
        if hasattr(self, 'slider_font_size'):
            current_cfg["overlay_font_size"] = self.slider_font_size.value()

        current_cfg["is_short"] = self.chk_short.isChecked()
        current_cfg["from_start"] = self.inp_from_start.text().strip() or "7"
        current_cfg["from_end"] = self.inp_from_end.text().strip() or "4"

        if hasattr(self, 'rad_phrase') and self.rad_phrase:
            current_cfg["is_phrase"] = self.rad_phrase.isChecked()

        # Хоткеи
        hk_cfg = {}
        if hasattr(self, 'chk_ctrl'):
            hk_cfg["ctrl"] = self.chk_ctrl.isChecked()
        if hasattr(self, 'chk_shift'):
            hk_cfg["shift"] = self.chk_shift.isChecked()
        if hasattr(self, 'chk_alt'):
            hk_cfg["alt"] = self.chk_alt.isChecked()
        if hasattr(self, 'inp_char'):
            hk_cfg["char"] = self.inp_char.text().strip()
        if hasattr(self, 'combo_f_keys'):
            hk_cfg["f_key"] = self.combo_f_keys.currentText()
        if hk_cfg:
            current_cfg["hotkey_config"] = hk_cfg

        # ДОБАВИТЬ:
        if hasattr(self, 'combo_font_family'):
            current_cfg["overlay_font_family"] = self.combo_font_family.currentText()

        # Сохраняем актуальные настройки
        self.storage.save_default_settings(current_cfg)
        self.settings = current_cfg

        if self.on_save_callback:
            try:
                self.on_save_callback()
            except:
                pass


    def handle_caps_toggle_live(self):
        checked = self.chk_caps.isChecked()
        style = "QLineEdit { text-transform: uppercase; }" if checked else "QLineEdit { text-transform: none; }"
        for key in self.inputs:
            self.inputs[key].setStyleSheet(style)

        target_dict = self.get_current_dict_id()
        target_name = getattr(self, 'current_editing_base_name', "").strip()
        if target_name:
            words = self.storage.load_phrases()
            for w in words:
                if int(w.get("dict_id", 1)) == target_dict and w.get("nominative", "").strip().lower() == target_name.lower():
                    w["is_caps"] = checked
                    break
            self.storage.save_phrases(words)

        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try:
                self.on_save_callback()
            except:
                pass

    def fix_short_block_logic(self):
        """Выставляет дефолты (7, 5, Фраза) при старте и связывает сигналы обновления UI на лету"""
        cfg = self.storage.load_default_settings() or {}
        self.settings = cfg

        # Временно блокируем сигналы, чтобы UI не затёр файл настроек нулями при старте
        if hasattr(self, 'chk_short'): self.chk_short.blockSignals(True)
        if hasattr(self, 'inp_from_start'): self.inp_from_start.blockSignals(True)
        if hasattr(self, 'inp_from_end'): self.inp_from_end.blockSignals(True)
        if hasattr(self, 'rad_word'): self.rad_word.blockSignals(True)
        if hasattr(self, 'rad_phrase'): self.rad_phrase.blockSignals(True)

        # Выставляем состояние чекбокса "Кратко"
        if hasattr(self, 'chk_short'):
            self.chk_short.setChecked(cfg.get("is_short", True))

        # Выставляем "С начала": по умолчанию "7"
        if hasattr(self, 'inp_from_start'):
            val_start = str(cfg.get("from_start", "7")).strip()
            self.inp_from_start.setText(val_start if (val_start and val_start != "0") else "7")

        # Выставляем "С конца": по умолчанию "5"
        if hasattr(self, 'inp_from_end'):
            val_end = str(cfg.get("from_end", "5")).strip()
            self.inp_from_end.setText(val_end if (val_end and val_end != "0") else "4")

        # Настраиваем радиокнопки: по скриншоту rad_word — это визуальная кнопка "Фраза"
        is_phrase_active = cfg.get("is_phrase", True)
        if hasattr(self, 'rad_word'):
            self.rad_word.setChecked(not is_phrase_active) # "Слово" = not True
        if hasattr(self, 'rad_phrase'):
            self.rad_phrase.setChecked(is_phrase_active) # "Фраза" = True
        #
        #
        if hasattr(self, 'rad_phrase'): self.rad_phrase.clicked.connect(self.save_global_settings)
        # if hasattr(self, 'chk_rounded'): self.chk_rounded.clicked.connect(self.save_global_settings) # Добавить эту!

        # Снимаем блокировку сигналов
        if hasattr(self, 'chk_short'): self.chk_short.blockSignals(False)
        if hasattr(self, 'inp_from_start'): self.inp_from_start.blockSignals(False)
        if hasattr(self, 'inp_from_end'): self.inp_from_end.blockSignals(False)
        if hasattr(self, 'rad_word'): self.rad_word.blockSignals(False)
        # ФИКС: Гарантированно загружаем тему Obsidian при старте
        if hasattr(self, 'combo_theme'):
            default_theme = cfg.get("current_theme", "Obsidian")
            idx = self.combo_theme.findText(default_theme)
            if idx >= 0:
                self.combo_theme.blockSignals(True)
                self.combo_theme.setCurrentIndex(idx)
                self.combo_theme.blockSignals(False)
        if hasattr(self, 'inp_from_start'): self.inp_from_start.textChanged.connect(self.save_global_settings)
        if hasattr(self, 'chk_first_capital'): self.chk_first_capital.clicked.connect(self.handle_first_capital_toggle_live)
        if hasattr(self, 'inp_from_end'): self.inp_from_end.textChanged.connect(self.save_global_settings)
        if hasattr(self, 'rad_word'): self.rad_word.clicked.connect(self.save_global_settings)
        # if hasattr(self, 'rad_phrase'): self.rad_phrase.clicked.connect(self.save_global_settings)
