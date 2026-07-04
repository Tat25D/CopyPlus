from PyQt6.QtGui import QPixmap, QColor, QIcon
class EditorSaverLogic:
    def force_direct_save_to_json(self):
        """
        Дублирующий метод автоматического сохранения для миксинов редактора.
        Вызывается при уходе фокуса с полей ввода или кликах по чекбоксам/радиокнопкам.
        """
        if getattr(self, '_is_initializing', False) or getattr(self, '_is_saving', False):
            return

        nom_text = self.inputs["nominative"].text().strip()
        if not nom_text:
            return

        target_name = getattr(self, 'current_editing_base_name', "").strip()
        target_dict = self.get_current_dict_id()
        words = self.storage.load_phrases()
        self._is_saving = True

        try:
            # Обработка добавления абсолютно нового слова
            if getattr(self, '_awaiting_new_word', False) and not target_name:
                if any(w.get("nominative", "").strip().lower() == nom_text.lower() and int(w.get("dict_id", 1)) == target_dict for w in words):
                    return

                new_word_data = {
                    "nominative": nom_text,
                    "is_caps": self.chk_caps.isChecked(),
                    "is_first_capital": self.chk_first_capital.isChecked() if hasattr(self, 'chk_first_capital') else False,
                    "is_space": self.chk_space.isChecked(),
                    "is_short": self.chk_short.isChecked(),
                    "from_start": self.inp_from_start.text().strip() or "0",
                    "from_end": self.inp_from_end.text().strip() or "0",
                    "is_phrase": self.rad_phrase.isChecked(),
                    "is_custom_color": getattr(self, '_is_setting_custom_color', False),
                    "is_active": True,
                    "dict_id": target_dict,
                    # НОВЫЕ ПАРАМЕТРЫ ALIAS И ШИРИНЫ МЕНЮ
                    "alias": self.inp_alias.text().strip(),
                }
                for key in self.inputs:
                    if key != "nominative":
                        new_word_data[key] = self.inputs[key].text().strip()
                words.append(new_word_data)
                self.storage.save_phrases(words)
                self.current_editing_base_name = nom_text


                self._awaiting_new_word = False

                self.list_widget.blockSignals(True)
                self.refresh_list()
                for r in range(self.list_widget.count()):
                    if self.list_widget.item(r).text().strip().lower() == nom_text.lower():
                        self.list_widget.setCurrentRow(r)
                        break
                self.list_widget.blockSignals(False)
                self.update_fields_availability()
                return

            if not target_name:
                return

            idx = next((i for i, w in enumerate(words) if int(w.get("dict_id", 1)) == target_dict and w.get("nominative", "").strip().lower() == target_name.lower()), -1)
            if idx == -1:
                return

            # Обновление параметров существующего слова
            word_data = words[idx]
            for key in self.inputs:
                word_data[key] = self.inputs[key].text().strip()

            word_data["nominative"] = nom_text

            # ИСПРАВЛЕНО: Меняем цвет ТОЛЬКО если пользователь кликнул по палитре
            if getattr(self, '_is_setting_custom_color', False):
                word_data["color"] = self.selected_color
                word_data["is_custom_color"] = True

            word_data["is_caps"] = self.chk_caps.isChecked()

            # НОВЫЕ ПАРАМЕТРЫ ИЗ UI
            word_data["is_space"] = self.chk_space.isChecked()
            word_data["is_short"] = self.chk_short.isChecked()
            word_data["from_start"] = self.inp_from_start.text().strip() or "0"
            word_data["from_end"] = self.inp_from_end.text().strip() or "0"
            word_data["is_phrase"] = self.rad_phrase.isChecked()

            # ДОБАВИТЬ:
            word_data["alias"] = self.inp_alias.text().strip()

            words[idx] = word_data
            self.storage.save_phrases(words)
            self.current_editing_base_name = nom_text

            # ═══════ НАДЕЖНОЕ ОБНОВЛЕНИЕ КВАДРАТИКА БЕЗ ПЕРЕЗАГРУЗКИ СПИСКА ═══════
            for r in range(self.list_widget.count()):
                list_item = self.list_widget.item(r)
                if list_item and list_item.text().strip().lower() == nom_text.lower():
                    c_hex = self.selected_color.lstrip('#')[:6]
                    if len(c_hex) == 6:
                        try:
                            r_c = int(c_hex[0:2], 16)
                            g_c = int(c_hex[2:4], 16)
                            b_c = int(c_hex[4:6], 16)
                            pixmap = QPixmap(14, 14)
                            pixmap.fill(QColor(r_c, g_c, b_c))
                            list_item.setIcon(QIcon(pixmap))
                        except Exception:
                            pass
                    break # Нашли нужную строку - выходим из цикла
            # ═════════════════════════════════════════════════════════════════════

        finally:
            self._is_saving = False

        # ДОБАВИТЬ: Сбрасываем флаг ручного цвета
        self._is_setting_custom_color = False

        if hasattr(self, 'on_save_callback') and self.on_save_callback:
                try:
                    self.on_save_callback()
                except:
                    pass
