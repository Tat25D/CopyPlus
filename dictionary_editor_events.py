from PyQt6.QtWidgets import QApplication, QColorDialog, QMessageBox
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QEvent


class EditorEventsLogic:
    def bind_events(self):
        """Изолированная привязка всех сигналов интерфейса редактора"""
        # Список слов
        self.list_widget.itemClicked.connect(self.load_selected_word)
        self.list_widget.itemChanged.connect(self.handle_word_check_changed)

        # Кнопки действий
        self.add_btn.clicked.connect(self.clear_form_for_new)
        self.del_btn.clicked.connect(self.delete_word)
        self.decline_btn.clicked.connect(self.handle_decline_click)
        self.export_btn.clicked.connect(self.trigger_txt_export)
        self.save_as_txt_btn.clicked.connect(self.trigger_windows_save_dialog)
        self.load_from_btn.clicked.connect(self.trigger_load_from_txt)

        # Кнопки словарей 1-8 (справа) и селектор слева
        # self.dict_btn_group.idClicked.connect(self.trigger_forced_defaults_load_by_id)
        self.selector_btn_group.idClicked.connect(self.handle_dict_tab_changed)

        # Галочка "Закрепить"
        self.chk_pin_dict.toggled.connect(self.handle_pin_checkbox_toggled)

        # Кнопка "Очистить" и выход
        self.reset_db_btn.clicked.connect(self.reset_entire_database)
        # ... (другие сигналы) ...
        self.hide_editor_btn.clicked.connect(lambda: self.hide())
        self.exit_app_btn.clicked.connect(lambda: QApplication.instance().quit())

        # ДОБАВИТЬ: Кнопка справки
        self.help_btn.clicked.connect(self.show_help_window)

        # Пикеры цветов
        self.btn_text_color_picker.clicked.connect(self.trigger_text_color_picker_dialog)
        self.btn_bg_color_picker.clicked.connect(self.trigger_bg_color_picker_dialog)

        # Сигналы параметров текста
        self.chk_caps.toggled.connect(self.handle_caps_toggle_live)

        # ДОБАВИТЬ:
        self.chk_skip_decline_warning.toggled.connect(self.save_global_settings)

        self.chk_space.toggled.connect(self.force_direct_save_to_json)
        self.chk_short.toggled.connect(self.save_global_settings)
        self.inp_from_start.textEdited.connect(self.save_global_settings)
        self.inp_from_end.textEdited.connect(self.save_global_settings)
        # self.rad_word.toggled.connect(self.save_global_settings)
        # self.rad_phrase.toggled.connect(self.save_global_settings)
        self.inputs["nominative"].editingFinished.connect(self.force_direct_save_to_json)

        # ДОБАВИТЬ:
        self.inp_alias.editingFinished.connect(self.force_direct_save_to_json)

        # ДОБАВИТЬ:
        self.slider_font_size.valueChanged.connect(self.handle_font_size_slider_change)

        # ДОБАВИТЬ:
        self.btn_toggle_bold.toggled.connect(self.handle_bold_toggle)

        # Слайдеры ширины и прозрачности
        self.slider_width.valueChanged.connect(self.handle_width_slider_change)
        self.slider_opacity.valueChanged.connect(self.handle_opacity_slider_change)

        # ДОБАВИТЬ:
        self.slider_menu_width.valueChanged.connect(self.handle_menu_width_slider_change)

        # Хоткей
        self.chk_ctrl.checkStateChanged.connect(self.save_global_settings)
        self.chk_shift.checkStateChanged.connect(self.save_global_settings)
        self.chk_alt.checkStateChanged.connect(self.save_global_settings)
        self.inp_char.textChanged.connect(self.save_global_settings)
        self.combo_f_keys.currentTextChanged.connect(self.save_global_settings)

        # ДОБАВИТЬ:
        self.combo_font_family.currentTextChanged.connect(self.save_global_settings)

        # Палитра цветов
        # palette_len = len(self.dark_palette)
        # for idx, btn in enumerate(self.color_group.buttons()):
        #     if palette_len > 0:
        #         color_from_palette = self.dark_palette[idx % palette_len]
        #         btn.clicked.connect(lambda checked, c=color_from_palette: self.set_active_color(c))

        # Event filter на все поля падежей — ОДИН РАЗ
        for key, input_field in self.inputs.items():
            input_field.installEventFilter(self)

    def handle_decline_click(self):
        """Обработчик клика по кнопке 'Склонять'"""
        if hasattr(self, 'chk_skip_decline_warning') and self.chk_skip_decline_warning.isChecked():
            self.trigger_manual_decline()
            return
        reply = QMessageBox.question(
            self, "Подтверждение склонения",
            "Этот алгоритм не точный. Он перезапишет содержимое полей падежей. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.trigger_manual_decline()

    def handle_pin_checkbox_toggled(self, checked):
        """Закрепление текущего просматриваемого словаря"""
        if not hasattr(self, 'storage') or not self.storage:
            return
        current_cfg = self.storage.load_default_settings() or {}
        current_cfg["is_dict_pinned"] = checked
        current_view_id = int(current_cfg.get("current_dict_id", 1))
        if checked:
            current_cfg["pinned_dict_id"] = current_view_id
            current_cfg["current_dict_id"] = current_view_id
        else:
            current_cfg["pinned_dict_id"] = 1
        self.storage.save_default_settings(current_cfg)
        if hasattr(self, 'update_dict_selector_styles'):
            self.update_dict_selector_styles()
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception:
                pass

    def trigger_text_color_picker_dialog(self):
        current_cfg = self.storage.load_default_settings() or {}
        current_hex = current_cfg.get("default_btn_text_color", "#FFFFFF")
        color = QColorDialog.getColor(QColor(current_hex), self, "Выберите цвет текста кнопок")
        if color.isValid():
            hex_color = color.name().upper()
            current_cfg["default_btn_text_color"] = hex_color
            self.storage.save_default_settings(current_cfg)
            self.btn_text_color_picker.setStyleSheet(
                f"background-color:{hex_color}; border:1px solid #FFFFFF; border-radius:4px;"
            )
            if self.on_save_callback:
                try:
                    self.on_save_callback()
                except Exception:
                    pass

    def trigger_bg_color_picker_dialog(self):
        current_cfg = self.storage.load_default_settings() or {}
        current_hex = current_cfg.get("default_btn_bg_color", "#242424")
        color = QColorDialog.getColor(QColor(current_hex), self, "Выберите цвет фона кнопок")
        if color.isValid():
            hex_color = color.name().upper()
            current_cfg["default_btn_bg_color"] = hex_color
            self.storage.save_default_settings(current_cfg)
            self.btn_bg_color_picker.setStyleSheet(
                f"background-color:{hex_color}; border:1px solid #FFFFFF; border-radius:4px;"
            )
            if self.on_save_callback:
                try:
                    self.on_save_callback()
                except Exception:
                    pass

    # ── Event Filter для полей падежей ──

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            for key, input_field in self.inputs.items():
                if obj == input_field:
                    self.force_direct_save_to_json()
                    break
        return super().eventFilter(obj, event) if hasattr(super(), 'eventFilter') else False

    # ── Чекбокс в списке слов ──

    def handle_word_check_changed(self, item):
        if not item or getattr(self, '_is_loading_fields', False):
            return
        target_text = item.text().strip()
        target_dict = self.get_current_dict_id()
        is_checked = item.checkState() == Qt.CheckState.Checked
        words = self.storage.load_phrases()
        for w in words:
            if (int(w.get("dict_id", 1)) == target_dict
                    and w.get("nominative", "").strip().lower() == target_text.lower()):
                w["is_active"] = is_checked
                self.storage.save_phrases(words)
                break
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception:
                pass

    # ── Переключение вкладок словарей 1-8 ──

    def handle_dict_tab_changed(self, dict_id):
        cfg = self.storage.load_default_settings() or {}
        cfg["current_dict_id"] = int(dict_id)
        self.storage.save_default_settings(cfg)

        for inp in self.inputs.values():
            inp.blockSignals(True)
            inp.clear()
            inp.blockSignals(False)
        self.current_editing_base_name = ""
        self._awaiting_new_word = False

        if hasattr(self, 'chk_pin_dict'):
            is_pinned = cfg.get("is_dict_pinned", False)
            pinned_id = int(cfg.get("pinned_dict_id", 1))
            self.chk_pin_dict.blockSignals(True)
            self.chk_pin_dict.setChecked(is_pinned and int(dict_id) == pinned_id)
            self.chk_pin_dict.blockSignals(False)

        self.refresh_list()
        if hasattr(self, 'update_fields_availability'):
            self.update_fields_availability()
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception:
                pass

    # ДОБАВИТЬ В КОНЕЦ КЛАССА:
    def handle_bold_toggle(self, checked):
        current_cfg = self.storage.load_default_settings() or {}
        current_cfg["is_bold"] = checked
        self.storage.save_default_settings(current_cfg)
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except:
                pass
