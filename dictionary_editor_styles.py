class EditorStyles:
    QSS = """
    /* Базовые стили окна редактора */
    QWidget {
        background-color: #1A1A1A;
        color: #E2E8F0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }

    QLabel {
        background: transparent;
        color: #A3A6A9;
    }

    /* Стили для текстовых полей ввода */
    QLineEdit {
        background-color: #242424;
        border: 1px solid #3E3E3E;
        border-radius: 6px;
        padding: 6px 12px;
        color: #FFFFFF;
        selection-background-color: #7C3AED;
        selection-color: #FFFFFF;
    }
    QLineEdit:focus {
        border: 1px solid #7C3AED;
        background-color: #2D2D2D;
    }

    /* Стили списков (левая колонка) */
    QListWidget {
        background-color: #242424;
        border: 1px solid #3E3E3E;
        border-radius: 8px;
        padding: 5px;
    }
    QListWidget::item {
        padding: 6px 10px;
        border-radius: 4px;
        color: #E2E8F0;
    }
    QListWidget::item:hover {
        background-color: #2D2D2D;
    }
    QListWidget::item:selected {
        background-color: #7C3AED;
        color: #FFFFFF;
    }

    /* Стандартные кнопки интерфейса*/
    QPushButton{
        background-color:#242424;
        color:#E2E8F0;
        border: 1px solid #3E3E3E;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover{
        background-color:#2E2E2E;
        border: 1px solid #7C3AED;
        color:#FFFFFF;
    }
    QPushButton:pressed{
        background-color:#1A1A1A;
    }
    QPushButton:checked{
        background-color:#7C3AED;
        color:#FFFFFF;
        border: 1px solid #7C3AED;
    }
    /* ✅ НОВОЕ: Убираем пунктирную рамку фокуса */
    QPushButton:focus{
        outline: none;
        border: 1px solid #3E3E3E;
    }

    /* Выпадающий список (темы) */
    QComboBox {
        background-color: #242424;
        border: 1px solid #3E3E3E;
        border-radius: 6px;
        padding: 5px 10px;
        color: #FFFFFF;
    }
    QComboBox:hover {
        border: 1px solid #7C3AED;
    }
    QComboBox::drop-down {
        border: none;
        background: transparent;
    }
    QComboBox QAbstractItemView {
        background-color: #242424;
        border: 1px solid #3E3E3E;
        selection-background-color: #7C3AED;
        selection-color: #FFFFFF;
    }

    /* ОРИГИНАЛЬНЫЙ СПЛОШНОЙ СТИЛЬ ДЛЯ ВСЕХ ЧЕКБОКСОВ (Закрепить, Заглавные, Кратко, Пробел) */
    QCheckBox {
        color: #E2E8F0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #4A5568;
        border-radius: 4px;
        background-color: #1A202C;
    }
    QCheckBox::indicator:hover {
        border-color: #7C3AED;
    }
    QCheckBox::indicator:checked {
        border-color: #7C3AED;
        background-color: #7C3AED;
    }

    /* АККУРАТНЫЙ СПЛОШНОЙ КВАДРАТНЫЙ СТИЛЬ ДЛЯ РАДИО-КНОПОК СЛОВО/ФРАЗА, ИДЕНТИЧНЫЙ ЧЕКБОКСАМ */
    QRadioButton {
        color: #E2E8F0;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
        spacing: 8px;
        background: transparent;
    }
    QRadioButton::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #4A5568;
        border-radius: 4px;
        background-color: #1A202C;
    }
    QRadioButton::indicator:hover {
        border-color: #7C3AED;
    }
    QRadioButton::indicator:checked {
        border-color: #7C3AED;
        background-color: #7C3AED;
        border-radius: 4px;
    }

    /* Стили для отключенных элементов */
    QCheckBox:disabled, QRadioButton:disabled {
        color: #4A5568;
    }
    QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {
        border-color: #2D3748;
        background-color: #1A202C;
    }

    /* Стили для отключенных элементов */
    QCheckBox:disabled, QRadioButton:disabled {
        color: #4A5568;
    }
    QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {
        border-color: #2D3748;
        background-color: #1A202C;
    }

    /* <-- ДОБАВИТЬ ЭТО НИЖЕ --> */

    /* Убираем пунктирную рамку фокуса с ползунков Ширина и Прозрачность */


    /* Стили для отключенных элементов */
    QCheckBox:disabled, QRadioButton:disabled {
        color: #4A5568;
    }
    QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {
        border-color: #2D3748;
        background-color: #1A202C;
    }

    /* <-- НАЧАЛО НОВОГО БЛОКА --> */
    /* Полностью переопределяем ползунки */
    QSlider {
        outline: none;
        border: none;
        background: transparent;
    }
    QSlider::groove:horizontal {
        border: 1px solid #3E3E3E;
        height: 8px; /* Фиксированная высота дорожки */
        background: #2D2D2D;
        border-radius: 4px;
    }
    QSlider::handle:horizontal {
        background: #7C3AED;
        border: 1px solid #8B5CF6;
        width: 16px;
        height: 16px;
        margin: -5px 0; /* Центрируем ручку */
        border-radius: 8px;
    }
    QSlider::handle:horizontal:hover {
        background: #9D6AFF;
    }
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5B21B6, stop:1 #7C3AED);
        border-radius: 4px;
    }
    """
