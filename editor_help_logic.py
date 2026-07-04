from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QCursor
from help_content import HELP_HTML

class EditorHelpLogic:
    def show_help_window(self):
        # Если окно уже создано — просто показываем
        if hasattr(self, '_help_dialog') and self._help_dialog:
            self._help_dialog.show()
            self._help_dialog.raise_()
            self._help_dialog.activateWindow()
            return

        # Создаем безрамочное окно поверх всех
        self._help_dialog = QWidget()
        self._help_dialog.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._help_dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._help_dialog.setWindowTitle("Справка")
        self._help_dialog.resize(550, 600)
        self._help_dialog.setStyleSheet("""
            QWidget { background-color: #1A1A1A; color: #E2E8F0; }
            QTextBrowser {
                background-color: #242424;
                border: 1px solid #3E3E3E;
                border-radius: 6px;
                padding: 10px;
                color: #E2E8F0;
            }
            QTextBrowser::verticalScrollBar {
                background: #1E1E1E;
                width: 10px;
                border-radius: 5px;
            }
            QTextBrowser::verticalScrollBar::handle:vertical {
                background: #444444;
                min-height: 20px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8B5CF6; }
        """)

        layout = QVBoxLayout(self._help_dialog)
        layout.setContentsMargins(10, 10, 10, 10)

        # Прокручиваемый текст
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(False)
        text_browser.setHtml(HELP_HTML)
        layout.addWidget(text_browser)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._help_dialog.hide)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Логика перетаскивания окна за любую точку
        self._help_dialog._drag_pos = QPoint()
        self._help_dialog.mousePressEvent = self._help_mouse_press
        self._help_dialog.mouseMoveEvent = self._help_mouse_move
        self._help_dialog.mouseReleaseEvent = self._help_mouse_release

        # Центрируем на экране
        self._help_dialog.show()
        screen = self._help_dialog.screen()
        if screen:
            geo = screen.geometry()
            x = geo.left() + (geo.width() - self._help_dialog.width()) // 2
            y = geo.top() + (geo.height() - self._help_dialog.height()) // 2
            self._help_dialog.move(x, y)

    # --- Вспомогательные методы для перетаскивания окна ---
    def _help_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._help_dialog._drag_pos = event.globalPosition().toPoint() - self._help_dialog.frameGeometry().topLeft()

    def _help_mouse_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self._help_dialog.move(event.globalPosition().toPoint() - self._help_dialog._drag_pos)

    def _help_mouse_release(self, event):
        pass
