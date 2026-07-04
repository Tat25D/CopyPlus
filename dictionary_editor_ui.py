from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from dictionary_editor_styles import EditorStyles
from dictionary_editor_top_ui import EditorTopUI
from dictionary_editor_left_ui import EditorLeftUILogic    # Подключаем левую панель
from dictionary_editor_right_ui import EditorRightUILogic  # Подключаем правую панель

class DictionaryEditorUI(QWidget, EditorTopUI, EditorLeftUILogic, EditorRightUILogic):
    def update_fields_availability(self):
        """
        Заглушка-предохранитель.
        Предотвращает ошибку AttributeError при вызове из оригинального кода dictionary_editor_save.py.
        Безопасно для базы данных, так как оригинальная логика сохранения не меняется.
        """
        pass

    def setup_ui(self):
        self.cases = [
            ("nominative", "Именительный (Кто? Что?)"),
            ("genitive", "Родительный (Кого? Чего?)"),
            ("dative", "Дательный (Кому? Чему?)"),
            ("accusative", "Винительный (Кого? Что?)"),
            ("instrumental", "Творительный (Кем? Чем?)"),
            ("prepositional", "Предложный (О ком? О чём?)")
        ]
        self.setWindowTitle("Редактор словаря")
        self.setMinimumWidth(1200) # Фикс смещения: предотвращаем сжатие при появлении длинных панелей тем
        self.resize(1200, 640)
        self.setStyleSheet(EditorStyles.QSS)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(12)

        # Добавляем верхний слайдер и хоткеи из оригинального EditorTopUI
        root_layout.addLayout(self.create_top_layout())

        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # Получаем готовые скомпонованные левую и правую панели из подключенных модулей
        left_layout = self.create_left_panel_layout()
        right_layout = self.create_right_panel_layout()

        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addLayout(right_layout, stretch=3)
        root_layout.addLayout(main_layout)

        self.setLayout(root_layout)
