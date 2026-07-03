from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QButtonGroup, QPushButton
from PyQt6.QtGui import QPainter, QColor, QCursor, QKeyEvent
from dictionary_editor import DictionaryEditorWindow
from case_formatter import CaseFormatter
from overlay_context_menu_manager import OverlayContextMenuManager
from overlay_bottom_ui import OverlayBottomUILogic
from overlay_renderer import OverlayRendererLogic
from overlay_geometry_engine import OverlayGeometryEngineLogic
from overlay_focus_engine import OverlayFocusEngineLogic
from overlay_win32_helper import OverlayWin32Helper
from overlay_core_engine import OverlayCoreEngine
import ui_behavior_config

class ClipboardOverlay(QWidget, OverlayFocusEngineLogic, OverlayGeometryEngineLogic,
                       OverlayBottomUILogic, OverlayWin32Helper, OverlayCoreEngine):

    def __init__(self, storage_service, ui_bg, btn_text, menu_bg, menu_item_bg):
        super().__init__()

        self.storage = storage_service
        self.formatter = CaseFormatter()
        self._is_updating = False
        self._last_hide_time = 0.0
        self._show_timestamp = 0.0
        self._last_clipboard_text = ""
        self.ui_bg = ui_bg
        self.btn_text = btn_text
        self.menu_bg = menu_bg
        self.menu_item_bg = menu_item_bg

        self.overlay_dict_group = QButtonGroup(self)
        self.overlay_dict_group.setExclusive(True)
        self.hide_on_click_outside = ui_behavior_config.HIDE_ON_CLICK_OUTSIDE
        self.hide_menu_on_click_outside = ui_behavior_config.HIDE_MENU_ON_CLICK_OUTSIDE

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.root_layout = QVBoxLayout()
        self.root_layout.setContentsMargins(5, 5, 5, 5)
        self.root_layout.setSpacing(6)

        # ФИКС: Пружина прижимает кнопки фраз к нижней панели (кнопки 1-8)
        self.root_layout.addStretch()

        self.words_container_layout = QVBoxLayout()
        self.words_container_layout.setContentsMargins(0, 0, 0, 0)
        self.words_container_layout.setSpacing(0)

        self.root_layout.addLayout(self.words_container_layout)

        # Оригинальная сборка нижней панели
        self.root_layout.addLayout(self.create_bottom_layout())

        # ФИКС УТЕЧКИ: Подключаем сигнал смены словаря ровно ОДИН раз при старте!
        # Теперь он не будет дублироваться при каждой перерисовке меню.
        self.overlay_dict_group.idClicked.connect(self.handle_overlay_dict_changed)

        self.setLayout(self.root_layout)

        cfg = self.storage.load_default_settings() or {}
        if cfg.get("is_dict_pinned", False):
            active_id = int(cfg.get("pinned_dict_id", 1))
            cfg["current_dict_id"] = active_id
            self.storage.save_default_settings(cfg)
        else:
            active_id = int(cfg.get("current_dict_id", 1))

        self.settings_window = DictionaryEditorWindow(self.storage, self.refresh_ui)

        btn = self.overlay_dict_group.button(active_id)
        if btn:
            btn.setChecked(True)

        self.focus_timer = QTimer(self)
        self.focus_timer.timeout.connect(self.track_win32_focus_leak)
        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(self.safe_check_clipboard_qt)
        self.clipboard_timer.start(100)

        self.refresh_ui()

    def log_and_paste(self, text_val, label, word_data):
        cursor_pos = QCursor.pos()
        print(Null) #(f"[CLICK_MENU_BUTTON] Button: '{label}' | Inserted text: '{text_val}' | X={cursor_pos.x()}, Y={cursor_pos.y()}", flush=True)
        self.paste_text_caps_safe(text_val, word_data)

    def refresh_ui(self):
        """Адаптированный вызов рендеринга с динамической пересборкой нижних кнопок (Оригинал)"""
        OverlayRendererLogic.refresh_ui(self)
        if hasattr(self, 'root_layout'):
            for i in range(self.root_layout.count()):
                item = self.root_layout.itemAt(i)
                if item and isinstance(item, QHBoxLayout) and item != getattr(self, 'words_container_layout', None):
                    while item.count():
                        child = item.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    self.root_layout.removeItem(item)
                    break
        if hasattr(self, 'overlay_dict_group'):
            for btn in self.overlay_dict_group.buttons():
                self.overlay_dict_group.removeButton(btn)
        new_bottom_layout = self.create_bottom_layout()
        self.root_layout.addLayout(new_bottom_layout)

        # Синхронизируем визуальное состояние активной вкладки (1-8) при перерисовке
        cfg = self.storage.load_default_settings() or {}

        # ФИКС: В парящем окне ВСЕГДА подсвечиваем только текущий выбранный словарь.
        # Флаг закрепления здесь игнорируется (он работает только при вызове хоткеем).
        active_tab = int(cfg.get("current_dict_id", 1))

        active_btn = self.overlay_dict_group.button(active_tab)
        if active_btn:
            active_btn.blockSignals(True)
            active_btn.setChecked(True)
            active_btn.blockSignals(False)
        self.update_mode_button_view()

    def paintEvent(self, event):
        # Очищено от тяжелых логов для нормального FPS
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

    def paintEvent(self, event):
        # Очищено от тяжелых логов для нормального FPS
        painter = QPainter(self)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

    # ═══════ НОВЫЙ МЕТОД: Управление с клавиатуры ═══════
    def keyPressEvent(self, event: QKeyEvent):
        """Обработка нажатий 1-8, Пробел и Esc в парящем окне"""
        key = event.key()

        # ЗАЩИТА: Полностью игнорируем модификаторы и F-клавиши,
        # чтобы они не крали фокус у окна в Windows
        if key in (Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Control,
                   Qt.Key.Key_Meta, Qt.Key.Key_CapsLock) or \
           (Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35):
            event.ignore()
            return

        # Переключение словарей цифрами 1-8
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_8:
            dict_id = key - Qt.Key.Key_0  # Получаем цифру (49 - 48 = 1)
            self.handle_overlay_dict_changed(dict_id)
            event.accept()
            return

        # Переключение режима кнопки пробелом
        if key == Qt.Key.Key_Space:
            self.handle_mode_cycle()
            self.refresh_ui() # Перерисовывает кнопки фраз с новым регистром
            event.accept() # Перехватываем, чтобы пробел не нажимал случайную кнопку
            return

        # ═══════ ДОБАВЛЕНО: Закрытие по Esc ═══════
        if key == Qt.Key.Key_Escape:
            self.hide_overlay()
            event.accept()
            return
        # ══════════════════════════════════════════

        # Для всех остальных клавиш передаем событие базовому классу
        super().keyPressEvent(event)
    # ═══════════════════════════════════════════════════
