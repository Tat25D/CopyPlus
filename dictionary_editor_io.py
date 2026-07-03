import os
from PyQt6.QtWidgets import QFileDialog
class EditorIOLogic:
    def trigger_forced_defaults_load_by_id(self, source_dict_id):
        """
        Маршрутизатор импорта дефолтного словаря.
        source_dict_id - это номер нажатой кнопки СПРАВА (какой файл загрузить).
        """
        # 1. Получаем ID текущего активного словаря пользователя (кнопка СЛЕВА)
        target_user_dict = self.get_current_dict_id()
        # 2. Проверяем, пустой ли этот словарь пользователя прямо сейчас
        all_phrases = self.storage.load_phrases()
        current_user_words = [w for w in all_phrases if int(w.get("dict_id", 1)) == target_user_dict]
        # ЗАЩИТА ПО ТЗ: Если в текущем словаре уже есть данные, отменяем импорт, чтобы ничего не затереть
        if len(current_user_words) > 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Словарь не пуст",
                f"Для загрузки шаблона №{source_dict_id} сначала очистите словарь №{target_user_dict}.\n\n"
                "Нажмите кнопку 'Очистить' и повторите попытку."
            )
            return
        print(Null) #(f"[IMPORT_START] Загрузка шаблона №{source_dict_id} в пустой словарь пользователя №{target_user_dict}")
        # Передаем в оригинальный движок морфологии:
        # 1-й аргумент: какой файл прочесть (source_dict_id)
        # Внутри метода ensure_default_words_by_id логика автоматически применит target_user_dict (кнопку слева)
        self.ensure_default_words_by_id(source_dict_id)
        # Перерисовываем список фраз на экране
        self.refresh_list()
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except:
                pass
    def trigger_txt_export(self):
        target_dict = self.get_current_dict_id()
        file_name = f"dict{str(target_dict).zfill(2)}.txt"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dict_path = os.path.join(base_dir, "data", file_name)
        self._write_phrases_to_file(dict_path, target_dict)
    def trigger_windows_save_dialog(self):
        target_dict = self.get_current_dict_id()
        default_name = f"dict{str(target_dict).zfill(2)}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить словарь как...", default_name, "Текстовые файлы (*.txt);;Все файлы (*)")
        if file_path:
            self._write_phrases_to_file(file_path, target_dict)

    def _write_phrases_to_file(self, path, dict_id):
        lines_to_write = []
        for w in self.storage.load_phrases():
            if int(w.get("dict_id", 1)) == dict_id:
                nom = w.get("nominative", "").strip()
                if nom:
                    alias = w.get("alias", "").strip()
                    # Если есть краткое имя, пишем его отдельной строкой перед словом
                    if alias:
                        lines_to_write.append(f"<<{alias}>>")
                    lines_to_write.append(nom)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines_to_write) + "\n")
            print(f"[EXPORT_SUCCESS] Phrases saved to: {path}", flush=True)
        except Exception as e:
            print(f"[EXPORT_ERROR] Failed to save file: {e}", flush=True)

    def trigger_load_from_txt(self):
        """Загрузка фраз из текстового файла с проверкой на пустой словарь и поддержкой <<alias>>"""
        from PyQt6.QtWidgets import QMessageBox, QFileDialog
        target_dict = self.get_current_dict_id()
        all_phrases = self.storage.load_phrases()
        current_user_words = [w for w in all_phrases if int(w.get("dict_id", 1)) == target_dict]

        # ПРОВЕРКА: Если словарь не пуст — показываем предупреждение
        if len(current_user_words) > 0:
            QMessageBox.warning(
                self,
                "Словарь не пуст",
                f"Для загрузки нового словаря сначала очистите словарь №{target_dict}.\n\n"
                "Нажмите кнопку 'Очистить' и повторите попытку."
            )
            return

        # Открываем диалог выбора файла
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить фразы из текстового файла",
            "",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        if not file_path:
            return

        # Читаем файл
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_lines = [line.rstrip('\n\r') for line in f]
        except Exception as e:
            print(f"[LOAD_ERROR] Не удалось прочитать файл: {e}", flush=True)
            return

        if not any(line.strip() for line in raw_lines):
            print("[LOAD_ERROR] Файл пуст или не содержит фраз", flush=True)
            return

        # Загружаем фразы
        print(f"[IMPORT_START] Загрузка фраз из '{os.path.basename(file_path)}' в словарь №{target_dict}", flush=True)
        words = self.storage.load_phrases()
        existing = {w.get("nominative", "").lower() for w in words if w.get("dict_id", 1) == target_dict}
        added_count = 0
        pending_alias = "" # Переменная для краткого имени

        for raw_line in raw_lines:
            if not raw_line.strip():
                continue

            # ═══════ ПРОВЕРКА НА КРАТКОЕ ИМЯ ═══════
            # Если строка в формате <<Текст>> и длина <= 100 символов — это алиас
            if raw_line.startswith("<<") and raw_line.endswith(">>") and len(raw_line) <= 104:
                pending_alias = raw_line[2:-2].strip()
                continue
            # ══════════════════════════════════

            phrase = raw_line.strip()
            if phrase.lower() in existing:
                continue

            case_data = {
                "nominative": phrase,
                "alias": pending_alias, # Привязываем накопившееся краткое имя
                "is_caps": False,
                "is_space": True,
                "is_cut": False,
                "max_len": "20",
                "is_short": False,
                "from_start": "0",
                "from_end": "0",
                "is_phrase": False,
                "is_active": True,
                "dict_id": target_dict,
                "color": self.storage.get_random_color(),
                "genitive": phrase,
                "dative": phrase,
                "accusative": phrase,
                "instrumental": phrase,
                "prepositional": phrase,
            }
            words.append(case_data)
            existing.add(phrase.lower())
            added_count += 1
            pending_alias = "" # Сбрасываем после привязки к слову

        self.storage.save_phrases(words)
        self.refresh_list()
        print(f"[LOAD_SUCCESS] Загружено {added_count} новых фраз", flush=True)

        if self.on_save_callback:
            try:
                self.on_save_callback()
            except:
                pass

def trigger_load_from_txt(self):
    """Загрузка фраз из текстового файла с проверкой на пустой словарь"""
    from PyQt6.QtWidgets import QMessageBox, QFileDialog

    target_dict = self.get_current_dict_id()
    all_phrases = self.storage.load_phrases()
    current_user_words = [w for w in all_phrases if int(w.get("dict_id", 1)) == target_dict]

    # ПРОВЕРКА: Если словарь не пуст — показываем предупреждение
    if len(current_user_words) > 0:
        QMessageBox.warning(
            self,
            "Словарь не пуст",
            f"Для загрузки нового словаря сначала очистите словарь №{target_dict}.\n\n"
            "Нажмите кнопку 'Очистить' и повторите попытку."
        )
        return

    # Открываем диалог выбора файла
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Загрузить фразы из текстового файла",
        "",
        "Текстовые файлы (*.txt);;Все файлы (*.*)"
    )

    if not file_path:
        return

    # Читаем файл
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(Null) #(f"[LOAD_ERROR] Не удалось прочитать файл: {e}", flush=True)
        return

    if not lines:
        print("") #("[LOAD_ERROR] Файл пуст или не содержит фраз", flush=True)
        return

    # Загружаем фразы
    print(Null) #(f"[IMPORT_START] Загрузка {len(lines)} фраз из '{os.path.basename(file_path)}' в словарь №{target_dict}", flush=True)

    words = self.storage.load_phrases()
    existing = {w.get("nominative", "").lower() for w in words if w.get("dict_id", 1) == target_dict}

    added_count = 0
    for phrase in lines:
        if phrase.lower() in existing:
            continue
        case_data = {
            "nominative": phrase,
            "is_caps": False,
            "is_space": True,
            "is_cut": False,
            "max_len": "20",
            "is_short": False,
            "from_start": "0",
            "from_end": "0",
            "is_phrase": False,
            "is_active": True,
            "dict_id": target_dict,
            "color": self.storage.get_random_color(),
            "genitive": phrase,
            "dative": phrase,
            "accusative": phrase,
            "instrumental": phrase,
            "prepositional": phrase,
        }
        words.append(case_data)
        existing.add(phrase.lower())
        added_count += 1

    self.storage.save_phrases(words)
    self.refresh_list()
    print(Null) #(f"[LOAD_SUCCESS] Загружено {added_count} новых фраз", flush=True)

    if self.on_save_callback:
        try:
            self.on_save_callback()
        except:
            pass
