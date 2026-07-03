from PyQt6.QtWidgets import QApplication


class EditorCoreInitLogic:
    def initialize_base_editor_state(self):
        """Завершение инициализации: разблокировка сигналов и привязка событий"""
        self._is_initializing = False
        self.bind_events()

    def center_editor_window_on_screen(self):
        """Безопасное выравнивание строго по центру дисплея"""
        self.ensurePolished()
        QApplication.processEvents()
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            center_x = geo.left() + (geo.width() - self.width()) // 2
            center_y = geo.top() + (geo.height() - self.height()) // 2
            self.move(center_x, center_y)
