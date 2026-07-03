from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QButtonGroup, QPushButton, QCheckBox, QListWidget, QSizePolicy
from icons import get_icon, ICON_PLUS, ICON_MINUS, ICON_CLOSE, ICON_SAVE

class EditorLeftUILogic:
    def create_left_panel_layout(self):
        """Сборка левой панели управления словарями и списками фраз"""
        left_layout = QVBoxLayout()

        # === Блок выбора словаря 1-8 + Закрепить ===
        dict_select_layout = QHBoxLayout()
        dict_select_layout.setSpacing(5)
        dict_select_layout.addWidget(QLabel("Словарь:"))
        self.selector_btn_group = QButtonGroup(self)
        self.selector_btn_group.setExclusive(True)

        for i in range(1, 9):
            btn = QPushButton(str(i))
            btn.setFixedSize(26, 30)
            btn.setCheckable(True)
            btn.setStyleSheet("QPushButton{ padding: 0px; font-size: 12px; border-radius: 4px;} QPushButton:checked{ background-color:#7C3AED; color: white;}")
            self.selector_btn_group.addButton(btn, i)
            dict_select_layout.addWidget(btn)

        dict_select_layout.addSpacing(10)
        self.chk_pin_dict = QCheckBox("Закрепить")
        self.chk_pin_dict.setMinimumWidth(90)
        dict_select_layout.addWidget(self.chk_pin_dict)
        dict_select_layout.addStretch()
        left_layout.addLayout(dict_select_layout)

        # === Список фраз ===
        self.list_widget = QListWidget()
        left_layout.addWidget(self.list_widget)

        # === БЛОК 1: Одна строка из 4 кнопок-иконок (+, -, ×, 💾) ===
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        # Кнопка "+" (Добавить)
        self.add_btn = QPushButton()
        self.add_btn.setIcon(get_icon(ICON_PLUS, 18))
        self.add_btn.setFixedHeight(30)
        self.add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.add_btn.setToolTip("Добавить")
        actions_layout.addWidget(self.add_btn)

        # Кнопка "-" (Удалить)
        self.del_btn = QPushButton()
        self.del_btn.setIcon(get_icon(ICON_MINUS, 18))
        self.del_btn.setFixedHeight(30)
        self.del_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.del_btn.setToolTip("Удалить")
        actions_layout.addWidget(self.del_btn)

        # Кнопка "×" (Очистить текущий словарь)
        self.reset_db_btn = QPushButton()
        self.reset_db_btn.setIcon(get_icon(ICON_CLOSE, 18))
        self.reset_db_btn.setFixedHeight(30)
        self.reset_db_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.reset_db_btn.setToolTip("Очистить текущий словарь")
        actions_layout.addWidget(self.reset_db_btn)

        # Кнопка "💾" (Экспорт txt) (Сохранить исходный как словарь)
        self.export_btn = QPushButton()
        self.export_btn.setIcon(get_icon(ICON_SAVE, 18))
        self.export_btn.setFixedHeight(30)
        self.export_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.export_btn.setToolTip("Сохранить исходный как словарь")
        actions_layout.addWidget(self.export_btn)

        left_layout.addLayout(actions_layout)

        # === БЛОК 2: Две кнопки "Сохранить как..." и "Загрузить из..." ===
        bottom_actions_layout = QHBoxLayout()
        bottom_actions_layout.setSpacing(5)

        self.save_as_txt_btn = QPushButton("Сохранить как...")
        self.save_as_txt_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bottom_actions_layout.addWidget(self.save_as_txt_btn)

        self.load_from_btn = QPushButton("Загрузить из...")
        self.load_from_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bottom_actions_layout.addWidget(self.load_from_btn)

        left_layout.addLayout(bottom_actions_layout)

        return left_layout
