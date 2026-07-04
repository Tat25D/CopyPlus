import json

class DictionaryEditorSaveLogic:
    def local_save_word(self):
        """
        Сохранение слова/фразы со всеми падежами и параметрами в JSON-базу.
        Используется при ручном сохранении или фиксации изменений.
        """
        nom_text = self.inputs["nominative"].text().strip()
        if not nom_text:
            return

        target_dict = self.get_current_dict_id()
        words = self.storage.load_phrases()

        # Ищем существующее слово по имени и текущему ID словаря
        target_name = getattr(self, 'current_editing_base_name', "").strip()
        idx = -1
        if target_name:
            idx = next((i for i, w in enumerate(words) if int(w.get("dict_id", 1)) == target_dict and w.get("nominative", "").strip().lower() == target_name.lower()), -1)

        word_data = {}
        if idx != -1:
            word_data = words[idx]
        else:
            word_data = {"dict_id": target_dict, "is_active": True}

        # Заполняем текстовые поля падежей
        for key in self.inputs:
            word_data[key] = self.inputs[key].text().strip()

        # Сохраняем основные параметры и цвета
        # ИСПРАВЛЕНО:
        word_data["nominative"] = nom_text
        if getattr(self, '_is_setting_custom_color', False):
            word_data["color"] = self.selected_color
            word_data["is_custom_color"] = True

        word_data["color"] = getattr(self, 'selected_color', '#2C3E50')
        word_data["is_caps"] = self.chk_caps.isChecked()

        # ИСПРАВЛЕНО:
        word_data["is_first_capital"] = self.chk_first_capital.isChecked() if hasattr(self, 'chk_first_capital') else False

        # НОВЫЕ ПАРАМЕТРЫ ИЗ UI
        word_data["is_space"] = self.chk_space.isChecked()
        word_data["is_short"] = self.chk_short.isChecked()
        word_data["from_start"] = self.inp_from_start.text().strip() or "0"
        word_data["from_end"] = self.inp_from_end.text().strip() or "0"
        word_data["is_phrase"] = self.rad_phrase.isChecked()

        # НОВЫЕ ПАРАМЕТРЫ ALIAS И ШИРИНЫ МЕНЮ
        word_data["alias"] = self.inp_alias.text().strip()

        if idx != -1:
            words[idx] = word_data
        else:
            words.append(word_data)

        self.storage.save_phrases(words)
        self.current_editing_base_name = nom_text
        self._awaiting_new_word = False

        # Обновляем визуальный список в UI
        self.list_widget.blockSignals(True)
        self.refresh_list()
        for r in range(self.list_widget.count()):
            if self.list_widget.item(r).text().strip().lower() == nom_text.lower():
                self.list_widget.setCurrentRow(r)
                break
        self.list_widget.blockSignals(False)
        self.update_fields_availability()

        # Уведомляем оверлей о необходимости живого обновления
        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception as e:
                print(Null) #(f"[SAVE_CALLBACK_ERROR] {e}")
