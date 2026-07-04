# БЫЛО:
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy # <--- ДУБЛИКАТ
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QIcon, QPainter
from PyQt6.QtSvg import QSvgRenderer

# ИСПРАВЛЕНО:
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore import Qt
from icons import get_icon, ICON_GEAR # <--- Добавили правильный импорт

class OverlayBottomUILogic:
    def create_bottom_layout(self):
        """Сборка нижней полупрозрачной панели быстрого переключения словарей"""
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(3)
        cfg = self.storage.load_default_settings() or {}
        independent_text_color = cfg.get("default_btn_text_color", "#FFFFFF")
        independent_bg_color = cfg.get("default_btn_bg_color", "#242424")

        # ДОБАВИТЬ:
        is_bold = cfg.get("is_bold", False)
        btn_weight = "bold" if is_bold else "normal"
        o_font_family = cfg.get("overlay_font_family", "Segoe UI")
        o_font_size = cfg.get("overlay_font_size", 13)
        # ══════════════════════════════════

        # ДИНАМИЧЕСКИЙ РАДИУС — читается из настроек
        is_rounded = cfg.get("is_rounded", True)
        btn_radius = "12px" if is_rounded else "0px"
        base_button_qss = f"""
        QPushButton{{
        background-color:{independent_bg_color};
        color:{independent_text_color};
        border: 1px solid #3E3E3E;
        border-radius:{btn_radius};
        font-family: '{o_font_family}', sans-serif;
        font-size: {o_font_size}px;
        }}
        QPushButton:hover{{
        background-color:#2D2D2D;
        color:#FFFFFF;
        }}
        """
        for i in range(1, 9):
            btn = QPushButton(str(i))
            btn.setFixedSize(26, 26)
            btn.setCheckable(True)
            btn.setStyleSheet(base_button_qss)
            self.overlay_dict_group.addButton(btn, i)
            bottom_layout.addWidget(btn)
        bottom_layout.addSpacing(5)

        self.btn_mode = QPushButton(" СЛОВО")
        self.btn_mode.setFixedHeight(26)
        self.btn_mode.setStyleSheet(base_button_qss + " QPushButton{ font-weight: bold; padding: 0px 15px;}")
        bottom_layout.addWidget(self.btn_mode)

        # ИСПРАВЛЕНО:
        gear_icon = get_icon(ICON_GEAR, 16)

        self.settings_btn = QPushButton("")
        self.settings_btn.setIcon(gear_icon)
        self.settings_btn.setFixedSize(26, 26)
        # ИСПРАВЛЕНО: Добавлен шрифт
        self.settings_btn.setStyleSheet(f"QPushButton {{ background: #444444; color: white; border-radius: {btn_radius}; font-family: '{o_font_family}', sans-serif; font-size: {o_font_size}px; }}")
        bottom_layout.addWidget(self.settings_btn)
        #--------------------------------------------------------


        self.btn_mode.clicked.connect(self.handle_mode_cycle)
        self.settings_btn.clicked.connect(self.open_settings)

        return bottom_layout

    def handle_overlay_dict_changed(self, dict_id):
        cfg = self.storage.load_default_settings() or {}
        dict_id_int = int(dict_id)
        cfg["current_dict_id"] = dict_id_int
        self.storage.save_default_settings(cfg)

        if hasattr(self, 'settings_window') and self.settings_window:
            if hasattr(self.settings_window, 'selector_btn_group'):
                r_btn = self.settings_window.selector_btn_group.button(dict_id_int)
                if r_btn:
                    self.settings_window.selector_btn_group.blockSignals(True)
                    r_btn.setChecked(True)
                    self.settings_window.selector_btn_group.blockSignals(False)

            if hasattr(self.settings_window, 'inputs'):
                for inp in self.settings_window.inputs.values():
                    inp.blockSignals(True)
                    inp.clear()
                    inp.blockSignals(False)

            self.settings_window.current_editing_base_name = ""
            self.settings_window._awaiting_new_word = False
            if hasattr(self.settings_window, 'refresh_list'):
                self.settings_window.refresh_list()

        self.refresh_ui()
