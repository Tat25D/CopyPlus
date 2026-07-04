class EditorInitLoaderLogic:
    def load_initial_ui_state(self):
        """Загрузка параметров слайдеров, хоткеев и сохраненной темы из JSON"""
        self.settings = self.storage.load_default_settings()

        # Ширина и прозрачность
        self.slider_width.setValue(self.settings.get("panel_width", 350))
        self.lbl_width_val.setText(f"{self.slider_width.value()}px")
        self.slider_opacity.setValue(self.settings.get("opacity", 45))
        self.lbl_opacity_val.setText(f"{self.settings.get('opacity', 45)}%")

        # ДОБАВИТЬ:
        self.slider_menu_width.setValue(self.settings.get("menu_width", 350))
        self.lbl_menu_width_val.setText(f"{self.settings.get('menu_width', 350)}px")

        # ДОБАВИТЬ:
        if hasattr(self, 'slider_font_size'):
            self.slider_font_size.setValue(self.settings.get("overlay_font_size", 13))
            self.lbl_font_size_val.setText(f"{self.settings.get('overlay_font_size', 13)}px")

        # Хоткеи
        hk_cfg = self.settings.get("hotkey_config", {"ctrl": False, "shift": False, "alt": True, "char": "", "f_key": "F1"})
        self.chk_ctrl.setChecked(hk_cfg.get("ctrl", False))
        self.chk_shift.setChecked(hk_cfg.get("shift", False))
        self.chk_alt.setChecked(hk_cfg.get("alt", True))
        self.inp_char.setText(hk_cfg.get("char", ""))
        self.combo_f_keys.setCurrentText(hk_cfg.get("f_key", "F1"))

        if hasattr(self, 'combo_font_family'):
            self.combo_font_family.setCurrentText(self.settings.get("overlay_font_family", "Segoe UI"))

        # ДОБАВИТЬ:
        if hasattr(self, 'btn_toggle_bold'):
            self.btn_toggle_bold.setChecked(self.settings.get("is_bold", False))

        # Активный словарь
        active_tab = int(self.settings.get("current_dict_id", 1))
        btn = self.selector_btn_group.button(active_tab)
        if btn:
            btn.setChecked(True)

        # Закрепление
        pinned_id = int(self.settings.get("pinned_dict_id", 1))
        self.chk_pin_dict.setChecked(active_tab == pinned_id)

        # Пробел
        self.chk_space.setChecked(True)

        # Блок "Кратко"
        if hasattr(self, 'chk_short'):
            self.chk_short.setChecked(self.settings.get("is_short", False))
            if hasattr(self, 'inp_from_start'):
                self.inp_from_start.setText(str(self.settings.get("from_start", "7")))
            if hasattr(self, 'inp_from_end'):
                self.inp_from_end.setText(str(self.settings.get("from_end", "5")))
        if hasattr(self, 'rad_word') and hasattr(self, 'rad_phrase'):
            is_phrase = self.settings.get("is_phrase", False)
            self.rad_word.setChecked(not is_phrase)
            self.rad_phrase.setChecked(is_phrase)

        # Галочка "Скруглить"
        if hasattr(self, 'chk_rounded'):
            self.chk_rounded.setChecked(self.settings.get("is_rounded", True))

        # Галочка "Не спрашивать при склонении"
        if hasattr(self, 'chk_skip_decline_warning'):
            self.chk_skip_decline_warning.setChecked(self.settings.get("skip_decline_warning", False))

        # Тема оформления
        saved_theme = self.settings.get("current_theme", "Obsidian")
        if hasattr(self, 'combo_theme'):
            self.combo_theme.setCurrentText(saved_theme)
        if hasattr(self, 'rebuild_palette_by_theme_name'):
            self.rebuild_palette_by_theme_name(saved_theme, clear_custom_colors=False)
