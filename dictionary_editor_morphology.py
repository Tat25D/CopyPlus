import os
import pymorphy3

class DictionaryEditorMorphologyLogic:
    def init_morphology(self):
        self.morph = pymorphy3.MorphAnalyzer()

    def restore_case(self, original_word, declined_word):
        """Вспомогательный метод: возвращает просклонированному слову исходный регистр букв"""
        if not original_word or not declined_word:
            return declined_word
        res_chars = []
        for i, char in enumerate(declined_word):
            if i < len(original_word):
                if original_word[i].isupper():
                    res_chars.append(char.upper())
                else:
                    res_chars.append(char.lower())
            else:
                if original_word[-1].isupper():
                    res_chars.append(char.upper())
                else:
                    res_chars.append(char.lower())
        return "".join(res_chars)

    def ensure_default_words_by_id(self, dict_id):
        """Парсинг готовых словарей с поддержкой строк <<alias>>"""
        default_array = []
        file_name = f"dict{str(dict_id).zfill(2)}.txt"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dict_path = os.path.join(os.path.dirname(base_dir), "data", file_name)

        if not os.path.exists(dict_path):
            dict_path = os.path.join(base_dir, "data", file_name)

        if not os.path.exists(dict_path):
            alt_path = dict_path + ".txt"
            if os.path.exists(alt_path):
                dict_path = alt_path

        if os.path.exists(dict_path):
            try:
                with open(dict_path, 'r', encoding='utf-8') as f:
                    raw_lines = [line.rstrip('\n\r') for line in f]

                pending_alias = ""
                target_active_dict = self.get_current_dict_id()
                words = self.storage.load_phrases()
                existing = {w.get("nominative", "").lower() for w in words if w.get("dict_id", 1) == target_active_dict}
                updated = False

                for raw_line in raw_lines:
                    if not raw_line.strip():
                        continue

                    # Проверка на краткое имя (в формате <<Имя>>)
                    if raw_line.startswith("<<") and raw_line.endswith(">>") and len(raw_line) <= 104:
                        pending_alias = raw_line[2:-2].strip()
                        continue

                    # Это реальная фраза
                    base_word = raw_line.strip()
                    if base_word.lower() not in existing:
                        case_data = {
                            "nominative": base_word,
                            "alias": pending_alias,
                            "is_caps": False, "is_space": True, "is_cut": False, "max_len": "20",
                            "dict_id": target_active_dict
                        }

                        for key, tag in [("genitive", "gent"), ("dative", "datv"), ("accusative", "accs"), ("instrumental", "ablt"), ("prepositional", "loct")]:
                            parts = base_word.split(" ")
                            declined_parts = []
                            for part in parts:
                                parsed = self.morph.parse(part)
                                best_match = parsed[0] if parsed else None
                                inflected = best_match.inflect({tag}) if best_match else None
                                raw_declined = inflected.word if inflected else part
                                declined_parts.append(self.restore_case(part, raw_declined))
                            case_data[key] = " ".join(declined_parts)

                        case_data["color"] = self.storage.get_random_color()
                        case_data["is_active"] = True
                        words.append(case_data)
                        updated = True
                        pending_alias = "" # Сбрасываем после привязки

                if updated:
                    self.storage.save_phrases(words)
                    if hasattr(self.storage, '_all_phrases_cache'):
                        delattr(self.storage, '_all_phrases_cache')

            except Exception as e:
                print(f"[MORPH_ERROR] Failed to read {file_name}: {e}", flush=True)

    def trigger_manual_decline(self):
        """Кнопка «Склонять»: изменяет окончания слов"""
        text = self.inputs["nominative"].text().strip()
        if not text:
            return

        # Диалог подтверждения (если галочка выключена)
        if not (hasattr(self, 'chk_skip_decline_warning') and self.chk_skip_decline_warning.isChecked()):
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, "Подтверждение склонения",
                "Этот алгоритм не точный. Он перезапишет содержимое полей падежей. Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Блокируем сигналы, чтобы поля не триггерили сохранение на каждый символ
        for inp in self.inputs.values():
            inp.blockSignals(True)

        for key, tag in [("genitive", "gent"), ("dative", "datv"), ("accusative", "accs"),
                         ("instrumental", "ablt"), ("prepositional", "loct")]:
            parts = text.split(" ")
            declined_parts = []
            for part in parts:
                if not part.strip():
                    continue
                parsed = self.morph.parse(part)
                best_match = parsed[0] if parsed else None
                inflected = best_match.inflect({tag}) if best_match else None
                raw_declined = inflected.word if inflected else part

                if self.chk_caps.isChecked():
                    res = raw_declined.upper()
                else:
                    res = self.restore_case(part, raw_declined)
                declined_parts.append(res)

            final_text = " ".join(declined_parts)
            self.inputs[key].setText(final_text)

        # Разблокируем сигналы
        for inp in self.inputs.values():
            inp.blockSignals(False)

        # ЕДИНОРОВНОЕ сохранение всех падежей в JSON
        self.force_direct_save_to_json()

        # ПРЯМОЕ СОХРАНЕНИЕ ПАДЕЖЕЙ В СЛОВАРЬ (гарантированная запись)
        current_dict_id = self.get_current_dict_id()
        words = self.storage.load_phrases()
        target_word = None
        for w in words:
            if (int(w.get("dict_id", 1)) == current_dict_id and
                w.get("nominative", "").strip().lower() == text.lower()):
                target_word = w
                break

        if target_word:
            target_word["genitive"] = self.inputs["genitive"].text().strip()
            target_word["dative"] = self.inputs["dative"].text().strip()
            target_word["accusative"] = self.inputs["accusative"].text().strip()
            target_word["instrumental"] = self.inputs["instrumental"].text().strip()
            target_word["prepositional"] = self.inputs["prepositional"].text().strip()
            target_word["is_caps"] = self.chk_caps.isChecked() if hasattr(self, 'chk_caps') else False
            target_word["is_space"] = self.chk_space.isChecked() if hasattr(self, 'chk_space') else False

            self.storage.save_phrases(words)
            if hasattr(self, 'refresh_list'):
                self.refresh_list()
