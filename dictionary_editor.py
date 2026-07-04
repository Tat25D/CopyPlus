from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QColor, QPixmap, QIcon
from dictionary_editor_ui import DictionaryEditorUI
from dictionary_part_backend import DictionaryBackendLogic
from dictionary_backend_actions import BackendActionsLogic
from dictionary_editor_settings import DictionaryEditorSettingsLogic
from dictionary_editor_morphology import DictionaryEditorMorphologyLogic
from dictionary_editor_mouse import EditorMouseLogic
from dictionary_editor_events import EditorEventsLogic
from dictionary_editor_io import EditorIOLogic
from dictionary_editor_color_styles import EditorColorStylesLogic
from dictionary_editor_init_loader import EditorInitLoaderLogic
from dictionary_editor_theme_engine import EditorThemeEngineLogic
from dictionary_editor_core_init import EditorCoreInitLogic
from dictionary_editor_saver import EditorSaverLogic
from dictionary_editor_save import DictionaryEditorSaveLogic
from phrase_mode_controller import PhraseModeController
from PyQt6.QtWidgets import QListWidgetItem
from dictionary_editor_rounded_logic import EditorRoundedLogic
from editor_help_logic import EditorHelpLogic


class DictionaryEditorWindow(
    DictionaryEditorUI,
    DictionaryEditorMorphologyLogic,
    DictionaryBackendLogic,
    BackendActionsLogic,
    DictionaryEditorSettingsLogic,
    EditorMouseLogic,
    EditorIOLogic,
    EditorColorStylesLogic,
    EditorInitLoaderLogic,
    EditorThemeEngineLogic,
    EditorSaverLogic,
    DictionaryEditorSaveLogic,
    EditorEventsLogic,
    PhraseModeController,
    EditorRoundedLogic,
    EditorCoreInitLogic,
    EditorHelpLogic
):
    def __init__(self, storage_service, on_save_callback):
        super().__init__()
        self._is_initializing = True
        self.storage = storage_service
        self.on_save_callback = on_save_callback
        self.current_editing_base_name = ""
        self._awaiting_new_word = False
        self.dark_palette = ["#2C3E50"] * 48
        self.selected_color = "#2C3E50"
        self.init_morphology()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.drag_position = QPoint()
        self.setup_ui()
        self.load_initial_ui_state()
        self.initialize_base_editor_state()
        self.bind_phrase_mode_signals()
        self.bind_rounded_signal()
        QTimer.singleShot(0, self.refresh_list)
        QTimer.singleShot(0, self.center_editor_window_on_screen)

    def refresh_list(self):
        """Обновление левого списка слов в соответствии с выбранным словарем"""
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        target_dict = self.get_current_dict_id()
        words = self.storage.load_phrases()
        # Читаем глобальную тему (как в overlay_renderer.py)
        cfg = self.storage.load_default_settings() or {}
        theme_palette = cfg.get("current_theme_palette", None)
        # Считаем общее количество слов для расчета градиента
        total_words_in_dict = sum(1 for w in words if int(w.get("dict_id", 1)) == target_dict and w.get("nominative", "").strip())
        current_index = 0
        for w in words:
            if int(w.get("dict_id", 1)) == target_dict:
                item = QListWidgetItem(w.get("nominative", ""))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.CheckState.Checked if w.get("is_active", True) else Qt.CheckState.Unchecked
                )
                # Вычисляем цвет (Идентичная логика из overlay_renderer.py)
                hex_color = w.get("color", "#2C3E50").lstrip('#')[:6]
                if theme_palette and isinstance(theme_palette, list) and len(theme_palette) > 0:
                    if total_words_in_dict > 1:
                        min_bound = int(len(theme_palette) * 0.2)
                        max_bound = int(len(theme_palette) * 0.8)
                        scaled_index = min_bound + int((current_index / (total_words_in_dict - 1)) * (max_bound - min_bound))
                    else:
                        scaled_index = len(theme_palette) // 2
                    hex_color = str(theme_palette[scaled_index]).lstrip('#')[:6]
                # Рисуем квадратик
                if len(hex_color) == 6:
                    try:
                        r = int(hex_color[0:2], 16)
                        g = int(hex_color[2:4], 16)
                        b = int(hex_color[4:6], 16)
                        pixmap = QPixmap(14, 14)
                        pixmap.fill(QColor(r, g, b))
                        item.setIcon(QIcon(pixmap))
                    except Exception:
                        pass
                self.list_widget.addItem(item)
                current_index += 1
        self.list_widget.blockSignals(False)
        self.update_dict_selector_styles()
