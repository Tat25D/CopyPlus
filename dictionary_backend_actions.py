from PyQt6.QtCore import Qt


class BackendActionsLogic:
    def clear_form_for_new(self):
        """Кнопка 'Добавить' очищает поля падежей и активирует их для ввода"""
        self.force_direct_save_to_json()
        self.list_widget.blockSignals(True)
        self.list_widget.clearSelection()
        self.list_widget.setCurrentRow(-1)
        self.list_widget.blockSignals(False)
        self._awaiting_new_word = True

        for inp in self.inputs.values():
            inp.clear()

        widgets_to_block = [self.chk_space, self.chk_caps, self.chk_short,
                            self.inp_from_start, self.inp_from_end, self.rad_word]
        for widget in widgets_to_block:
            widget.blockSignals(True)

        self.chk_space.setChecked(True)
        self.chk_caps.setChecked(False)
        self.chk_short.setChecked(False)
        self.inp_from_start.setText("0")
        self.inp_from_end.setText("0")
        self.rad_word.setChecked(True)

        for widget in widgets_to_block:
            widget.blockSignals(False)

        self.current_editing_base_name = ""
        self.update_fields_availability()
        self.inputs["nominative"].setFocus()

    def delete_word(self):
        current_row = self.list_widget.currentRow()
        item = self.list_widget.currentItem()
        if not item:
            return
        target_dict = self.get_current_dict_id()
        words = [
            w for w in self.storage.load_phrases()
            if not (int(w.get("dict_id", 1)) == target_dict and w.get("nominative", "") == item.text())
        ]
        self.storage.save_phrases(words)
        self._awaiting_new_word = False
        self.refresh_list()
        total_items = self.list_widget.count()
        if total_items > 0:
            target_row = total_items - 1 if current_row >= total_items else current_row
            self.list_widget.setCurrentRow(target_row)
            new_item = self.list_widget.item(target_row)
            if new_item:
                self.load_selected_word(new_item)
        else:
            for inp in self.inputs.values():
                inp.clear()
            self.current_editing_base_name = ""
        self.save_global_settings()

    def reset_entire_database(self):
        target_dict = self.get_current_dict_id()
        words = [w for w in self.storage.load_phrases() if int(w.get("dict_id", 1)) != target_dict]
        self.storage.save_phrases(words)
        self._awaiting_new_word = False
        self.refresh_list()
        for inp in self.inputs.values():
            inp.clear()
        self.current_editing_base_name = ""
        self.save_global_settings()
