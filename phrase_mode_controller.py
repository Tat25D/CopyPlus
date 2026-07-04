"""
phrase_mode_controller.py
Изолированная логика глобального переключателя "Слово" / "Фраза".
Управляет ТОЛЬКО режимом сокращения имён кнопок парящего окна.
"""


class PhraseModeController:
    """Миксин для DictionaryEditorWindow. Управляет глобальным режимом 'Слово/Фраза'."""

    def get_phrase_mode(self) -> bool:
        """Возвращает текущий режим: True = Фраза, False = Слово."""
        if hasattr(self, 'rad_phrase') and self.rad_phrase:
            return self.rad_phrase.isChecked()
        # Фолбэк: читаем из настроек
        cfg = self.storage.load_default_settings() or {}
        return cfg.get("is_phrase", False)

    def set_phrase_mode(self, is_phrase: bool):
        """Устанавливает режим переключателя в UI и сохраняет в settings.json."""
        if hasattr(self, 'rad_word') and self.rad_word:
            self.rad_word.setChecked(not is_phrase)
        if hasattr(self, 'rad_phrase') and self.rad_phrase:
            self.rad_phrase.setChecked(is_phrase)
        # Сразу сохраняем в настройки
        self._save_phrase_mode_to_settings(is_phrase)

    def _save_phrase_mode_to_settings(self, is_phrase: bool):
        """Записывает состояние переключателя в settings.json."""
        if not hasattr(self, 'storage') or not self.storage:
            return
        cfg = self.storage.load_default_settings() or {}
        cfg["is_phrase"] = bool(is_phrase)
        self.storage.save_default_settings(cfg)
        # Уведомляем оверлей о необходимости перерисовки
        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception:
                pass

    def bind_phrase_mode_signals(self):
        """Привязывает сигналы радиокнопок к сохранению настроек.
        Вызывать ОДИН раз в конце __init__ редактора словарей."""
        if hasattr(self, 'rad_word') and self.rad_word:
            self.rad_word.clicked.connect(self._on_phrase_mode_changed)
        if hasattr(self, 'rad_phrase') and self.rad_phrase:
            self.rad_phrase.clicked.connect(self._on_phrase_mode_changed)

    def _on_phrase_mode_changed(self):
        """Обработчик клика по радиокнопкам 'Слово'/'Фраза'."""
        is_phrase = self.get_phrase_mode()
        self._save_phrase_mode_to_settings(is_phrase)
