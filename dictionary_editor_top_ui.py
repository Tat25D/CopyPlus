from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QLineEdit, QComboBox, QSlider, QPushButton
from PyQt6.QtCore import Qt
class EditorTopUI:
    def create_top_layout(self):
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # === Хоткеи ===
        top_layout.addWidget(QLabel("Хоткей:"))
        self.chk_ctrl = QCheckBox("Ctrl")
        self.chk_ctrl.setMinimumWidth(75)
        self.chk_shift = QCheckBox("Shift")
        self.chk_shift.setMinimumWidth(75)
        self.chk_alt = QCheckBox("Alt")
        self.chk_alt.setMinimumWidth(65)
        top_layout.addWidget(self.chk_ctrl)
        top_layout.addWidget(self.chk_shift)
        top_layout.addWidget(self.chk_alt)
        top_layout.addWidget(QLabel("Символ:"))
        self.inp_char = QLineEdit()
        self.inp_char.setFixedWidth(35)
        self.inp_char.setMaxLength(1)
        self.inp_char.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.inp_char)
        top_layout.addWidget(QLabel("или"))
        self.combo_f_keys = QComboBox()
        self.combo_f_keys.addItems(["Нет"] + [f"F{i}" for i in range(1, 13)])
        top_layout.addWidget(self.combo_f_keys)

        # ═══════ ДОБАВИТЬ: Выбор шрифта ═══════
        # top_layout.addWidget(QLabel(" | Шрифт:"))
        # self.combo_font_family = QComboBox()
        # self.combo_font_family.addItems([
        #     "Segoe UI", "Arial", "Verdana", "Tahoma",
        #     "Roboto", "Open Sans", "Times New Roman", "Consolas"
        # ])
        # self.combo_font_family.setFixedWidth(130)
        # top_layout.addWidget(self.combo_font_family)
        # ══════════════════════════════════

        # === Ширина ===
        top_layout.addWidget(QLabel(" | Ширина:"))
        self.slider_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_width.setRange(350, 1600)
        top_layout.addWidget(self.slider_width, stretch=1)
        self.lbl_width_val = QLabel("350px")
        self.lbl_width_val.setMinimumWidth(55)
        top_layout.addWidget(self.lbl_width_val)

        # === Шир. меню ===
        top_layout.addWidget(QLabel("Шир. меню:"))
        self.slider_menu_width = QSlider(Qt.Orientation.Horizontal)
        self.slider_menu_width.setRange(150, 800)
        self.slider_menu_width.setFixedWidth(200)
        top_layout.addWidget(self.slider_menu_width)
        self.lbl_menu_width_val = QLabel("350px")
        # ... (код ползунков и комбобоксов) ...

        self.lbl_menu_width_val.setMinimumWidth(50)
        top_layout.addWidget(self.lbl_menu_width_val)

        # ═══════ ДОБАВЛЕНО: Кнопка "?" (Справка) ═══════
        top_layout.addStretch()

        # ... конец create_top_layout ...
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(28, 28)
        self.help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_btn.setToolTip("Помощь (?)")
        self.help_btn.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: #FFFFFF;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9D6AFF; }
        """)
        top_layout.addWidget(self.help_btn)

        return top_layout
