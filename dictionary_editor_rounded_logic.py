class EditorRoundedLogic:
    """
    Изолированная логика галочки "Скруглить".
    Вынесена в отдельный файл, чтобы не перезаписать при генерациях кода.
    """
    def bind_rounded_signal(self):
        """Привязка сигнала галочки 'Скруглить' для мгновенного применения к оверлею."""
        if hasattr(self, 'chk_rounded') and self.chk_rounded:
            self.chk_rounded.clicked.connect(self._on_rounded_toggled)

    def _on_rounded_toggled(self):
        """Обработчик клика по галочке — сохраняет и сразу перерисовывает парящее окно."""
        if getattr(self, '_is_initializing', False):
            return

        # 1. Сохраняем в JSON
        current_cfg = self.storage.load_default_settings() or {}
        current_cfg["is_rounded"] = self.chk_rounded.isChecked()
        self.storage.save_default_settings(current_cfg)
        self.settings = current_cfg

        # 2. Мгновенно перерисовываем оверлей (без закрытия окна настроек)
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception:
                pass
