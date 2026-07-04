from PyQt6.QtCore import Qt


class DictionaryBackendLogic:
    def get_current_dict_id(self):
        """Возвращает ID словаря, открытого в данный момент в редакторе"""
        try:
            cfg = self.storage.load_default_settings() or {}
            return int(cfg.get("current_dict_id", 1))
        except Exception:
            return 1

    def update_dict_selector_styles(self):
        """Подсвечивает закрепленный словарь тёмно-фиолетовым цветом"""
        if not hasattr(self, 'selector_btn_group') or not self.selector_btn_group:
            return
        cfg = self.storage.load_default_settings() or {}
        is_pinned = cfg.get("is_dict_pinned", False)
        pinned_id = int(cfg.get("pinned_dict_id", 1))

        base_style = (
            "QPushButton { padding:0px; font-size:12px; border-radius:4px;"
            " background-color:#242424; color:#E2E8F0; border:1px solid #3E3E3E; }"
            "QPushButton:checked { background-color:#7C3AED; color:white; border:1px solid #7C3AED; }"
            "QPushButton:hover { border:1px solid #7C3AED; }"
        )
        pinned_style = (
            "QPushButton { padding:0px; font-size:12px; border-radius:4px;"
            " background-color:#4C1D95; color:#E2E8F0; border:1px solid #7C3AED; }"
            "QPushButton:checked { background-color:#7C3AED; color:white; border:1px solid #7C3AED; }"
            "QPushButton:hover { background-color:#5B21B6; }"
        )
        for btn in self.selector_btn_group.buttons():
            btn_id = self.selector_btn_group.id(btn)
            btn.setStyleSheet(pinned_style if (is_pinned and btn_id == pinned_id) else base_style)

    def load_selected_word(self, item):
        """Загружает данные выбранной фразы из JSON в поля ввода формы"""
        if not item or getattr(self, '_is_loading_fields', False):
            return
        target_text = item.text().strip()
        target_dict = self.get_current_dict_id()
        words = self.storage.load_phrases()







        widgets_to_block = [self.chk_space, self.chk_caps, self.chk_short,
                            self.inp_from_start, self.inp_from_end, self.rad_word,
                            self.inp_alias] # <--- ДОБАВИЛИ СЮДА







        self._is_loading_fields = True
        try:
            for w in words:
                if (int(w.get("dict_id", 1)) == target_dict
                        and w.get("nominative", "").strip().lower() == target_text.lower()):
                    # Блокируем ВСЕ сигналы
                    for inp in self.inputs.values():
                        inp.blockSignals(True)
                    self.chk_caps.blockSignals(True)
                    self.chk_space.blockSignals(True)
                    for widget in (self.chk_short, self.inp_from_start,
                                   self.inp_from_end, self.rad_word, self.rad_phrase):
                        if hasattr(self, widget.__class__.__name__.lower()) and widget:
                            widget.blockSignals(True)

                    # Загружаем данные
                    is_caps = w.get("is_caps", False)
                    self.chk_caps.setChecked(is_caps)
                    self.inputs["nominative"].setText(w.get("nominative", ""))
                    for key in self.inputs:
                        if key != "nominative":
                            self.inputs[key].setText(w.get(key, ""))

                    caps_style = ("QLineEdit{ text-transform: uppercase;}" if is_caps
                                  else "QLineEdit{ text-transform: none;}")
                    for key in self.inputs:
                        self.inputs[key].setStyleSheet(caps_style)

                    self.chk_space.setChecked(w.get("is_space", True))

                    # ЗАГРУЗКА ALIAS И ШИРИНЫ МЕНЮ
                    if hasattr(self, 'inp_alias'):
                        self.inp_alias.setText(w.get("alias", ""))
                    if hasattr(self, 'inp_menu_width'):
                        self.inp_menu_width.setText(str(w.get("menu_width", "350")))

                    if hasattr(self, 'chk_short'):
                        self.chk_short.setChecked(w.get("is_short", False))
                    if hasattr(self, 'inp_from_start'):
                        self.inp_from_start.setText(str(w.get("from_start", "0")))
                    if hasattr(self, 'inp_from_end'):
                        self.inp_from_end.setText(str(w.get("from_end", "0")))



                    is_phrase = w.get("is_phrase", False)
                    if hasattr(self, 'rad_phrase'):
                        self.rad_phrase.setChecked(is_phrase)
                    if hasattr(self, 'rad_word'):
                        self.rad_word.setChecked(not is_phrase)

                    self.current_editing_base_name = w.get("nominative", "")
                    self.selected_color = w.get("color", "#2C3E50")

                    # ДОБАВИТЬ ЗАГРУЗКУ ALIAS:
                    if hasattr(self, 'inp_alias'):
                        self.inp_alias.setText(w.get("alias", ""))

                    # Разблокируем ВСЕ сигналы
                    for inp in self.inputs.values():
                        inp.blockSignals(False)
                    self.chk_caps.blockSignals(False)
                    self.chk_space.blockSignals(False)
                    for widget in (self.chk_short, self.inp_from_start,
                                   self.inp_from_end, self.rad_word, self.rad_phrase):
                        if hasattr(self, widget.__class__.__name__.lower()) and widget:
                            widget.blockSignals(False)
                    break
        finally:
            self._is_loading_fields = False
            self._awaiting_new_word = False
            if hasattr(self, 'update_fields_availability'):
                self.update_fields_availability()
