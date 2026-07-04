from PyQt6.QtWidgets import QPushButton
class EditorColorStylesLogic:
    def generate_palette_ui_buttons(self, picker_grid):
        """Монолитная генерация палитры с полной очисткой старой сетки от наслоений"""
        # КРИТИЧЕСКИЙ ФИКС: Удаляем старые виджеты из сетки
        while picker_grid.count():
            child = picker_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for idx, hex_color in enumerate(self.dark_palette):
            color_btn = QPushButton()
            color_btn.setFixedSize(36, 36)
            color_btn.setCheckable(True)
            color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid #1A1A1A;
                border-radius: 18px;
            }}
            QPushButton:checked {{
                border: 2px solid #FFFFFF;
            }}
            """)
            self.color_group.addButton(color_btn, idx)

            # ═══════ ДОБАВЛЕНО: Живая привязка к клику при создании ═══════
            color_btn.clicked.connect(lambda checked, c=hex_color: self.set_active_color(c))
            # ═══════════════════════════════════════════════════════════

            picker_grid.addWidget(color_btn, idx // 16, idx % 16)

    def select_active_color_button(self, color_data):
        """Ищет и подсвечивает круглую кнопку, соответствующую сохраненному цвету JSON"""
        self.selected_color = str(color_data).replace("[", "").replace("]", "").replace("'", "").replace('"', '').strip()
        for btn in self.color_group.buttons():
            if self.selected_color.lower() in btn.styleSheet().lower():
                btn.setChecked(True)
                break
