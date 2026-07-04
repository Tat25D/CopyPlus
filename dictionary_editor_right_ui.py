# ИСПРАВЛЕНО:
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, QLineEdit,
QSlider, QRadioButton, QButtonGroup, QPushButton, QSizePolicy,
QGridLayout, QWidget, QComboBox, QMenu)
from PyQt6.QtCore import Qt, QByteArray, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QIntValidator
from PyQt6.QtSvg import QSvgRenderer
from icons import get_icon, ICON_OPEN, ICON_SAVE, ICON_HIDE, ICON_CLOSE

from PyQt6.QtCore import Qt, QByteArray, QPoint, QTimer # Добавили QTimer

class UpComboBox(QComboBox):
    """Чистый PyQt список на базе QMenu. НЕ вызывает прыжков окна от Windows!"""
    def showPopup(self):
        if self.count() == 0: return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #242424; color: #E2E8F0; border: 1px solid #3E3E3E; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 15px; border-radius: 4px; }
            QMenu::item:selected { background-color: #7C3AED; color: white; }
        """)

        for i in range(self.count()):
            action = menu.addAction(self.itemText(i))
            action.triggered.connect(lambda checked, idx=i: self._select_item(idx))

        # Открываем строго ВЫШЕ кнопки
        point = self.mapToGlobal(self.rect().topLeft())
        menu.exec(point)

    def _select_item(self, index):
        # Блокируем сигналы, чтобы не было циклического вызова toggle_gradient_ui
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)
        # Имитируем ручной выбор пункта
        self.currentTextChanged.emit(self.itemText(index))

class EditorRightUILogic:
    def create_right_panel_layout(self):
        """Изолированная сборка правой текстовой и цветовой панели редактора словаря"""
        right_layout = QVBoxLayout()
        initial_cfg = self.storage.load_default_settings() or {}
        saved_text_color = initial_cfg.get("default_btn_text_color", "#FFFFFF")
        saved_bg_color = initial_cfg.get("default_btn_bg_color", "#242424")

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 1: Склонять, Не спрашивать | Пружина | Прозрачность, Размер шрифта
        # ═══════════════════════════════════════════════════════════════
        action_row_layout = QHBoxLayout()
        action_row_layout.setSpacing(10)

        # --- ЛЕВАЯ ЧАСТЬ: Кнопка и галочка ---
        decline_container = QWidget()
        decline_container.setStyleSheet("background: transparent;")
        decline_layout = QHBoxLayout(decline_container)
        decline_layout.setContentsMargins(0, 0, 0, 0)
        decline_layout.setSpacing(6)

        self.decline_btn = QPushButton("Склонять")
        self.decline_btn.setStyleSheet("""
        QPushButton {
            background-color: #242424;
            color: #E2E8F0;
            border: 1px solid #3E3E3E;
            border-radius: 6px;
            font-weight: bold;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #2D2D2D;
            border: 1px solid #7C3AED;
            color: #FFFFFF;
        }
        """)
        decline_layout.addWidget(self.decline_btn)

        self.chk_skip_decline_warning = QCheckBox("Не спрашивать")
        self.chk_skip_decline_warning.setToolTip("Не показывать предупреждение при склонении")
        self.chk_skip_decline_warning.setStyleSheet("""
        QCheckBox {
            color: #A3A6A9;
            spacing: 6px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #4A5568;
            border-radius: 3px;
            background-color: #1A202C;
        }
        QCheckBox::indicator:hover {
            border-color: #7C3AED;
        }
        QCheckBox::indicator:checked {
            border-color: #7C3AED;
            background-color: #7C3AED;
        }
        """)
        decline_layout.addWidget(self.chk_skip_decline_warning)

        # Добавляем левую часть БЕЗ stretch, чтобы она не жрала место у ползунков
        action_row_layout.addWidget(decline_container)

        # --- ПРУЖИНА: Прижимает ползунки к правому краю и защищает от сжатия ---
        action_row_layout.addStretch(1)

        # --- ПРАВАЯ ЧАСТЬ: Ползунки (находятся вне контейнера, поэтому не ломаются) ---
        opacity_lbl = QLabel("Прозрачность:")
        opacity_lbl.setStyleSheet("color: #A3A6A9;")
        action_row_layout.addWidget(opacity_lbl)

        self.slider_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setFixedWidth(120)
        action_row_layout.addWidget(self.slider_opacity)

        self.lbl_opacity_val = QLabel("45%")
        self.lbl_opacity_val.setFixedWidth(40) # 40px достаточно для "100%" в редакторе
        self.lbl_opacity_val.setStyleSheet("color: #A3A6A9;")
        action_row_layout.addWidget(self.lbl_opacity_val)

        action_row_layout.addSpacing(15) # Отступ между прозрачностью и шрифтом

        font_size_lbl = QLabel("Размер шрифта:")
        font_size_lbl.setStyleSheet("color: #A3A6A9;")
        action_row_layout.addWidget(font_size_lbl)

        self.slider_font_size = QSlider(Qt.Orientation.Horizontal)
        self.slider_font_size.setRange(10, 24)
        self.slider_font_size.setFixedWidth(100)
        action_row_layout.addWidget(self.slider_font_size)

        self.lbl_font_size_val = QLabel("13px")
        self.lbl_font_size_val.setFixedWidth(35)
        self.lbl_font_size_val.setStyleSheet("color: #A3A6A9;")
        action_row_layout.addWidget(self.lbl_font_size_val)
        # ----------------------------------------

        right_layout.addLayout(action_row_layout)

        # ═══════════════════════════════════════════════════════════════
        # НОВЫЙ БЛОК: Краткое имя + Пружина + Шрифт + Кнопка B
        # ═══════════════════════════════════════════════════════════════
        alias_layout = QHBoxLayout()
        alias_layout.setSpacing(10)

        lbl_alias = QLabel("<< Краткое имя >>:")
        lbl_alias.setStyleSheet("color:#A3A6A9;")
        lbl_alias.setFixedWidth(140)
        alias_layout.addWidget(lbl_alias)

        self.inp_alias = QLineEdit()
        self.inp_alias.setPlaceholderText("Оставьте пустым для обычной работы")
        # Растягиваем поле на всё доступное место слева
        alias_layout.addWidget(self.inp_alias, stretch=1)

        # Пружина, которая отталкивает правую часть к самому краю
        alias_layout.addStretch()

        # --- Блок Шрифт ---
        alias_layout.addWidget(QLabel("Шрифт:"))
        self.combo_font_family = UpComboBox() # Используем безопасный список без прыжков окна
        self.combo_font_family.addItems([
            "Segoe UI", "Arial", "Verdana", "Tahoma",
            "Roboto", "Open Sans", "Times New Roman", "Consolas"
        ])
        self.combo_font_family.setFixedWidth(130)
        alias_layout.addWidget(self.combo_font_family)

        # --- Кнопка Жирности (B) ---
        self.btn_toggle_bold = QPushButton("B")
        self.btn_toggle_bold.setFixedSize(30, 30)
        self.btn_toggle_bold.setCheckable(True)
        self.btn_toggle_bold.setToolTip("Жирный шрифт в парящем окне")
        self.btn_toggle_bold.setStyleSheet("""
        QPushButton {
            background-color: #242424;
            color: #E2E8F0;
            border: 1px solid #3E3E3E;
            border-radius: 6px;
            font-weight: bold;
            font-size: 14px;
        }
        QPushButton:hover {
            border: 1px solid #7C3AED;
        }
        QPushButton:checked {
            background-color: #7C3AED;
            color: white;
            border: 1px solid #8B5CF6;
        }
        """)
        alias_layout.addWidget(self.btn_toggle_bold)

        right_layout.addLayout(alias_layout)

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 2: Поля падежей (Именительный... Предложный)
        # ═══════════════════════════════════════════════════════════════
        grid = QGridLayout()
        grid.setSpacing(8)
        self.inputs = {}
        for i, (key, label) in enumerate(self.cases):
            grid.addWidget(QLabel(label), i, 0)
            self.inputs[key] = QLineEdit()
            grid.addWidget(self.inputs[key], i, 1)

        right_layout.addLayout(grid)

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 3: Первая заглавная, ВСЕ ЗАГЛАВНЫЕ, ПРОБЕЛ, Текст, Фон
        # ═══════════════════════════════════════════════════════════════
        checkboxes_row = QHBoxLayout()
        self.chk_first_capital = QCheckBox("Первая заглавная")
        self.chk_first_capital.setFixedWidth(160)
        self.chk_caps = QCheckBox("ВСЕ ЗАГЛАВНЫЕ")
        self.chk_caps.setFixedWidth(140)
        self.chk_space = QCheckBox("ПРОБЕЛ В НАЧАЛЕ")
        self.chk_space.setFixedWidth(180)
        checkboxes_row.addWidget(self.chk_first_capital)
        checkboxes_row.addWidget(self.chk_caps)
        checkboxes_row.addWidget(self.chk_space)
        checkboxes_row.addStretch()
        self.lbl_text_color_title = QLabel("Текст:")
        self.lbl_text_color_title.setStyleSheet("margin-left: 10px;")
        checkboxes_row.addWidget(self.lbl_text_color_title)
        self.btn_text_color_picker = QPushButton()
        self.btn_text_color_picker.setFixedSize(50, 24)
        self.btn_text_color_picker.setStyleSheet(
            f"background-color:{saved_text_color}; border: 1px solid #555555; border-radius: 4px;"
        )
        checkboxes_row.addWidget(self.btn_text_color_picker)
        self.lbl_bg_color_title = QLabel("Фон:")
        self.lbl_bg_color_title.setStyleSheet("margin-left: 10px;")
        checkboxes_row.addWidget(self.lbl_bg_color_title)
        self.btn_bg_color_picker = QPushButton()
        self.btn_bg_color_picker.setFixedSize(50, 24)
        self.btn_bg_color_picker.setStyleSheet(
            f"background-color:{saved_bg_color}; border: 1px solid #555555; border-radius: 4px;"
        )
        checkboxes_row.addWidget(self.btn_bg_color_picker)
        right_layout.addLayout(checkboxes_row)

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 4: Кратко / С начала / С конца / Слово-Фраза / Скруглить
        # ═══════════════════════════════════════════════════════════════
        new_params_row = QHBoxLayout()
        new_params_row.setSpacing(12)
        self.chk_short = QCheckBox("Кратко")
        self.chk_short.setFixedWidth(90)
        new_params_row.addWidget(self.chk_short)
        int_validator = QIntValidator(0, 99, self)
        lbl_start = QLabel("С начала:")
        lbl_start.setStyleSheet("color:#A3A6A9;")
        new_params_row.addWidget(lbl_start)
        self.inp_from_start = QLineEdit()
        self.inp_from_start.setFixedSize(42, 26)
        self.inp_from_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inp_from_start.setValidator(int_validator)
        self.inp_from_start.setText("7")
        self.inp_from_start.setStyleSheet(
            "QLineEdit{ border: 1px solid #4A5568; background-color:#1A202C; "
            "border-radius: 4px; color:#FFFFFF; padding: 0px 4px;}"
        )
        new_params_row.addWidget(self.inp_from_start)
        lbl_end = QLabel("С конца:")
        lbl_end.setStyleSheet("color:#A3A6A9;")
        new_params_row.addWidget(lbl_end)
        self.inp_from_end = QLineEdit()
        self.inp_from_end.setFixedSize(42, 26)
        self.inp_from_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inp_from_end.setValidator(int_validator)
        self.inp_from_end.setText("4")
        self.inp_from_end.setStyleSheet(
            "QLineEdit{ border: 1px solid #4A5568; background-color:#1A202C; "
            "border-radius: 4px; color:#FFFFFF; padding: 0px 4px;}"
        )
        new_params_row.addWidget(self.inp_from_end)
        new_params_row.addSpacing(15)
        self.rad_word = QRadioButton("Слово")
        self.rad_phrase = QRadioButton("Фраза")
        self.rad_word.setChecked(True)
        self.type_mode_group = QButtonGroup(self)
        self.type_mode_group.addButton(self.rad_word, 0)
        self.type_mode_group.addButton(self.rad_phrase, 1)
        new_params_row.addWidget(self.rad_word)
        new_params_row.addWidget(self.rad_phrase)
        # Разделитель и галочка "Скруглить"
        new_params_row.addWidget(QLabel(" | "))
        self.chk_rounded = QCheckBox("Скруглить")
        self.chk_rounded.setChecked(True)
        new_params_row.addWidget(self.chk_rounded)
        new_params_row.addStretch()
        # Блок добавляется над палитрой (см. ниже)

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 5: Палитра цветов
        # ═══════════════════════════════════════════════════════════════
        self.picker_container = QWidget()
        self.picker_container.setStyleSheet("background: transparent; border: none;")
        self.picker_grid = QGridLayout(self.picker_container)
        self.picker_grid.setContentsMargins(0, 0, 0, 0)
        self.picker_grid.setSpacing(6)
        self.color_group = QButtonGroup(self)

        # Сначала блок "Кратко...Скруглить", потом палитра
        right_layout.addLayout(new_params_row)
        right_layout.addWidget(self.picker_container)

        # ══════════════════════════════════════════════════════════════
        # БЛОК 6: Кнопка "Выбрать сплошной цвет"
        # ═══════════════════════════════════════════════════════════════
        self.solid_container_widget = QWidget()
        self.solid_container_widget.setStyleSheet("background: transparent; border: none;")
        solid_box_layout = QHBoxLayout(self.solid_container_widget)
        solid_box_layout.setContentsMargins(0, 0, 0, 0)
        self.solid_color_pick_btn = QPushButton("Выбрать сплошной цвет")
        self.solid_color_pick_btn.setFixedWidth(240)
        self.solid_color_pick_btn.setMinimumHeight(32)
        solid_box_layout.addStretch(1)
        solid_box_layout.addWidget(self.solid_color_pick_btn)
        solid_box_layout.addStretch(1)
        self.solid_container_widget.hide()
        right_layout.addWidget(self.solid_container_widget)

        # ═══════════════════════════════════════════════════════════════
        # БЛОК 7: Тема, Обновить, Сохранить, Открыть, Скрыть, Закрыть
        # ═══════════════════════════════════════════════════════════════
        editor_exit_layout = QHBoxLayout()
        editor_exit_layout.setSpacing(8)
        editor_exit_layout.addWidget(QLabel("Тема:"))
        self.combo_theme = UpComboBox()
        self.combo_theme.addItems(["Obsidian", "Оттенки", "Случайная", "Json"])
        self.combo_theme.setFixedWidth(105)
        editor_exit_layout.addWidget(self.combo_theme)
        self.combo_theme.currentTextChanged.connect(self.toggle_gradient_ui)

        # Кнопка Обновить (Стрелочка)
        svg_icon_xml = """
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#E2E8F0" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 4 23 10 17 10"></polyline>
        <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
        </svg>"""
        renderer = QSvgRenderer(QByteArray(svg_icon_xml.encode('utf-8')))
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(icon_pixmap)
        renderer.render(painter)
        painter.end()
        self.btn_refresh_random = QPushButton()
        self.btn_refresh_random.setIcon(QIcon(icon_pixmap))
        self.btn_refresh_random.setIconSize(icon_pixmap.size())
        self.btn_refresh_random.setFixedSize(26, 26)
        self.btn_refresh_random.clicked.connect(self.trigger_theme_update)
        editor_exit_layout.addWidget(self.btn_refresh_random)

        # УНИВЕРСАЛЬНЫЕ кнопки Сохранить и Открыть
        self.btn_save = QPushButton()
        self.btn_save.setIcon(get_icon(ICON_SAVE, 18))
        self.btn_save.setFixedSize(26, 26)
        self.btn_save.clicked.connect(self.unified_save_action)
        editor_exit_layout.addWidget(self.btn_save)
        self.btn_open = QPushButton()
        self.btn_open.setIcon(get_icon(ICON_OPEN, 18))
        self.btn_open.setFixedSize(26, 26)
        self.btn_open.clicked.connect(self.unified_open_action)
        editor_exit_layout.addWidget(self.btn_open)

        # Контейнер для динамических настроек темы (Скрыт по умолчанию)
        self.theme_settings_container = QWidget()
        self.theme_settings_container.setStyleSheet("background: transparent;")
        self.theme_settings_layout = QHBoxLayout(self.theme_settings_container)
        self.theme_settings_layout.setContentsMargins(0, 0, 0, 0)
        self.theme_settings_layout.setSpacing(5)
        self.theme_settings_container.hide()

        # Вложенная панель для Оттенков
        self.gradient_widget = QWidget()
        self.gradient_widget.setStyleSheet("background: transparent;")
        grad_lay = QHBoxLayout(self.gradient_widget)
        grad_lay.setContentsMargins(0, 0, 0, 0)
        grad_lay.setSpacing(5)
        self.grad_pick1 = QPushButton()
        self.grad_pick1.setFixedSize(24, 24)
        self.grad_pick1.clicked.connect(lambda: self.trigger_gradient_picker(1))
        grad_lay.addWidget(QLabel("C1:"))
        grad_lay.addWidget(self.grad_pick1)
        self.grad_pick2 = QPushButton()
        self.grad_pick2.setFixedSize(24, 24)
        self.grad_pick2.clicked.connect(lambda: self.trigger_gradient_picker(2))
        grad_lay.addWidget(QLabel("C2:"))
        grad_lay.addWidget(self.grad_pick2)
        self.grad_pick3 = QPushButton()
        self.grad_pick3.setFixedSize(24, 24)
        self.grad_pick3.clicked.connect(lambda: self.trigger_gradient_picker(3))
        grad_lay.addWidget(QLabel("C3:"))
        grad_lay.addWidget(self.grad_pick3)
        grad_lay.addSpacing(10)
        self.chk_gradient_random = QCheckBox("Случайно")
        self.chk_gradient_random.setStyleSheet("color: #E2E8F0;")
        self.chk_gradient_random.clicked.connect(self.trigger_gradient_random_toggle)
        grad_lay.addWidget(self.chk_gradient_random)
        self.theme_settings_layout.addWidget(self.gradient_widget)

        # Вложенная панель для Случайной
        self.random_widget = QWidget()
        self.random_widget.setStyleSheet("background: transparent;")
        rand_lay = QHBoxLayout(self.random_widget)
        rand_lay.setContentsMargins(0, 0, 0, 0)
        rand_lay.setSpacing(5)
        init_cfg = self.storage.load_default_settings() or {}
        dark_c = init_cfg.get("random_dark_bound", "#3C3C3C")
        light_c = init_cfg.get("random_light_bound", "#DCDCDC")
        rand_lay.addWidget(QLabel("Тёмный:"))
        self.btn_random_dark = QPushButton()
        self.btn_random_dark.setFixedSize(24, 24)
        self.btn_random_dark.setStyleSheet(
            f"background-color:{dark_c}; border: 1px solid #FFF; border-radius: 4px;"
        )
        self.btn_random_dark.clicked.connect(lambda: self.pick_grayscale("dark"))
        rand_lay.addWidget(self.btn_random_dark)
        rand_lay.addWidget(QLabel("Светлый:"))
        self.btn_random_light = QPushButton()
        self.btn_random_light.setFixedSize(24, 24)
        self.btn_random_light.setStyleSheet(
            f"background-color:{light_c}; border: 1px solid #FFF; border-radius: 4px;"
        )
        self.btn_random_light.clicked.connect(lambda: self.pick_grayscale("light"))
        rand_lay.addWidget(self.btn_random_light)
        self.theme_settings_layout.addWidget(self.random_widget)
        editor_exit_layout.addWidget(self.theme_settings_container)
        editor_exit_layout.addStretch()

        # Кнопки Скрыть и Закрыть с иконками
        self.hide_editor_btn = QPushButton()
        self.hide_editor_btn.setIcon(get_icon(ICON_HIDE, 20))
        self.hide_editor_btn.setFixedSize(100, 30)
        editor_exit_layout.addWidget(self.hide_editor_btn)
        self.exit_app_btn = QPushButton()
        self.exit_app_btn.setIcon(get_icon(ICON_CLOSE, 20))
        self.exit_app_btn.setFixedSize(100, 30)
        editor_exit_layout.addWidget(self.exit_app_btn)
        right_layout.addLayout(editor_exit_layout)

        # ═══════════════════════════════════════════════════════════════
        # Привязка сигналов чекбоксов заглавных
        # ═══════════════════════════════════════════════════════════════
        self.chk_first_capital.clicked.connect(self._manage_first_capital)
        self.chk_caps.clicked.connect(self._manage_all_caps)

        return right_layout

# --------------------------------------------------------------------------------------

    def _manage_first_capital(self):
        if self.chk_first_capital.isChecked():
            self.chk_caps.blockSignals(True)
            self.chk_caps.setChecked(False)
            self.chk_caps.blockSignals(False)
            if hasattr(self, 'handle_caps_toggle_live'):
                self.handle_caps_toggle_live()
        self._apply_first_capital_toggle()

    def _manage_all_caps(self):
        if self.chk_caps.isChecked():
            self.chk_first_capital.blockSignals(True)
            self.chk_first_capital.setChecked(False)
            self.chk_first_capital.blockSignals(False)
        if hasattr(self, 'handle_caps_toggle_live'):
            self.handle_caps_toggle_live()

    def _apply_first_capital_toggle(self):
        if getattr(self, '_is_loading_fields', False): return
        checked = self.chk_first_capital.isChecked()
        for inp in self.inputs.values(): inp.blockSignals(True)
        for key, inp in self.inputs.items():
            text = inp.text().strip()
            if not text: continue
            new_text = text[0].upper() + text[1:] if checked else text[0].lower() + text[1:]
            inp.setText(new_text)
        for inp in self.inputs.values(): inp.blockSignals(False)
        if hasattr(self, 'force_direct_save_to_json'): self.force_direct_save_to_json()

    def trigger_theme_update(self):
        theme = self.combo_theme.currentText()
        if hasattr(self, 'rebuild_palette_by_theme_name'):
            self.rebuild_palette_by_theme_name(theme, is_refresh_action=True)
        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try: self.on_save_callback()
            except: pass

    def trigger_gradient_random_toggle(self):
        if self.combo_theme.currentText() == "Оттенки":
            if hasattr(self, 'rebuild_palette_by_theme_name'):
                self.rebuild_palette_by_theme_name("Оттенки")
            if hasattr(self, 'on_save_callback') and self.on_save_callback:
                try: self.on_save_callback()
                except: pass

    def unified_save_action(self):
        from PyQt6.QtWidgets import QFileDialog
        import json
        if not hasattr(self, 'dark_palette') or not self.dark_palette: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить палитру", "", "JSON Files (*.json)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.dark_palette, f, indent=4)

    def unified_open_action(self):
        from PyQt6.QtWidgets import QFileDialog
        import json
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть палитру", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    colors = json.load(f)
                if isinstance(colors, list):
                    while len(colors) < 48: colors.append(colors[-1] if colors else "#2C3E50")
                    self.dark_palette = colors[:48]
                    self.settings["current_theme_palette"] = self.dark_palette
                    self.storage.save_default_settings(self.settings)
                    if hasattr(self, 'generate_palette_ui_buttons'): self.generate_palette_ui_buttons(self.picker_grid)
                    if hasattr(self, 'on_save_callback') and self.on_save_callback:
                        try: self.on_save_callback()
                        except: pass
            except Exception as e: print(Null) #(f"[JSON ERROR] {e}")

    def toggle_gradient_ui(self, theme_name):
        # Просто показываем нужную вложенную панель, не трогая геометрию окна!
        self.gradient_widget.hide()
        self.random_widget.hide()
        self.theme_settings_container.hide()

        if theme_name == "Оттенки":
            self.gradient_widget.show()
            self.theme_settings_container.show()
            if hasattr(self, 'trigger_apply_gradient_click'): self.trigger_apply_gradient_click()
        elif theme_name == "Случайная":
            self.random_widget.show()
            self.theme_settings_container.show()

        if hasattr(self, 'settings'): self.settings["current_theme"] = theme_name
        if hasattr(self, 'storage'): self.storage.save_default_settings(self.settings)

        if hasattr(self, 'rebuild_palette_by_theme_name'):
            self.rebuild_palette_by_theme_name(theme_name, is_refresh_action=False)
        self.update()

        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try: self.on_save_callback()
            except: pass

    def trigger_theme_update(self):
        theme = self.combo_theme.currentText()
        if hasattr(self, 'rebuild_palette_by_theme_name'):
            self.rebuild_palette_by_theme_name(theme, is_refresh_action=True)
        if hasattr(self, 'on_save_callback') and self.on_save_callback:
            try: self.on_save_callback()
            except: pass

    def trigger_gradient_random_toggle(self):
        if self.combo_theme.currentText() == "Оттенки":
            if hasattr(self, 'rebuild_palette_by_theme_name'):
                self.rebuild_palette_by_theme_name("Оттенки")
            if hasattr(self, 'on_save_callback') and self.on_save_callback:
                try: self.on_save_callback()
                except: pass

    def pick_grayscale(self, target):
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor
        settings = self.storage.load_default_settings() or {}
        initial = settings.get(f"random_{target}_bound", "#808080")
        color = QColorDialog.getColor(QColor(initial), self)
        if color.isValid():
            gray = (color.red() + color.green() + color.blue()) // 3
            hex_c = f"#{gray:02X}{gray:02X}{gray:02X}"
            settings[f"random_{target}_bound"] = hex_c
            self.storage.save_default_settings(settings)
            btn = self.btn_random_dark if target == "dark" else self.btn_random_light
            btn.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #FFF; border-radius: 4px;")

    def pick_grayscale(self, target):
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtGui import QColor
        settings = self.storage.load_default_settings() or {}
        initial = settings.get(f"random_{target}_bound", "#808080")
        color = QColorDialog.getColor(QColor(initial), self)
        if color.isValid():
            gray = (color.red() + color.green() + color.blue()) // 3
            hex_c = f"#{gray:02X}{gray:02X}{gray:02X}"
            settings[f"random_{target}_bound"] = hex_c
            self.storage.save_default_settings(settings)
            btn = self.btn_random_dark if target == "dark" else self.btn_random_light
            btn.setStyleSheet(f"background-color: {hex_c}; border: 1px solid #FFF; border-radius: 4px;")
