import os
import ast
import zipfile
import sys
import logging
import re
import tokenize
import io
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


# ============================================================================
# Настройка логирования — вывод ошибок в консоль
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# Технические папки, которые строго игнорируются при сканировании
IGNORE_DIRS = {'.venv', 'venv', 'env', '.git', '.idea', '.vscode', '__pycache__'}

# Приоритетные имена файлов для точки входа
ENTRY_FILE_NAMES = {'main.py', 'app.py', 'run.py', '__main__.py', 'start.py', 'entry.py'}

# ============================================================================
# Стиль Obsidian (тёмная тема)
# ============================================================================
OBSIDIAN_STYLE = """
QMainWindow, QWidget {
    background-color: #202020;
    color: #dcddde;
    font-family: "Segoe UI", "Inter", "SF Pro Text", sans-serif;
    font-size: 13px;
}

QLabel {
    color: #dcddde;
    background-color: transparent;
}

QGroupBox {
    background-color: #262626;
    border: 1px solid #383838;
    border-radius: 6px;
    margin-top: 10px;
    padding: 12px 6px 6px 6px;
    font-weight: 600;
    color: #b0b0b0;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #8a7cf7;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

QListWidget {
    background-color: #1e1e1e;
    color: #dcddde;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 4px;
    outline: none;
    selection-background-color: #3a3a52;
    selection-color: #ffffff;
    alternate-background-color: #232323;
}

QListWidget::item {
    padding: 4px 6px;
    border-radius: 3px;
}

QListWidget::item:hover {
    background-color: #2d2d2d;
}

QListWidget::item:selected {
    background-color: #3a3a52;
    color: #ffffff;
}

QScrollBar:vertical {
    background: #1e1e1e;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #444444;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QPushButton {
    background-color: #2d2d2d;
    color: #dcddde;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
    min-height: 18px;
}

QPushButton:hover {
    background-color: #363636;
    border-color: #4a4a4a;
}

QPushButton:pressed {
    background-color: #252525;
}

QPushButton:disabled {
    background-color: #252525;
    color: #555555;
    border-color: #333333;
}

QPushButton#autoBtn {
    background-color: #7c3aed;
    color: #ffffff;
    border: 1px solid #8a7cf7;
    font-weight: 600;
}

QPushButton#autoBtn:hover {
    background-color: #8b5cf6;
    border-color: #a78bfa;
}

QPushButton#autoBtn:pressed {
    background-color: #6d28d9;
}

QPushButton#deleteBtn {
    background-color: #7f1d1d;
    color: #fecaca;
    border: 1px solid #991b1b;
    font-weight: 600;
}

QPushButton#deleteBtn:hover {
    background-color: #991b1b;
    color: #ffffff;
}

QPushButton#deleteBtn:pressed {
    background-color: #6b1717;
}

QPushButton#deleteBtn:disabled {
    background-color: #2a1a1a;
    color: #5a3a3a;
    border-color: #3a2020;
}

QPushButton#selectBtn {
    background-color: #3a3a52;
    color: #e0e0e0;
    border: 1px solid #4a4a62;
}

QPushButton#selectBtn:hover {
    background-color: #45455f;
    border-color: #5a5a72;
}

QSplitter::handle {
    background-color: #2d2d2d;
    width: 2px;
    margin: 0px 4px;
}

QSplitter::handle:hover {
    background-color: #8a7cf7;
}
"""


def find_module_chain(name_parts, base_dir):
    """
    Возвращает список файлов проекта, которые будут загружены при импорте модуля.
    Учитывает промежуточные __init__.py пакетов.
    """
    result = []
    if not name_parts:
        return result

    for i in range(1, len(name_parts)):
        pkg_init = os.path.join(base_dir, *name_parts[:i], '__init__.py')
        if os.path.isfile(pkg_init):
            result.append(os.path.normpath(pkg_init))

    file_path = os.path.join(base_dir, *name_parts) + '.py'
    if os.path.isfile(file_path):
        result.append(os.path.normpath(file_path))
        return result

    pkg_init = os.path.join(base_dir, *name_parts, '__init__.py')
    if os.path.isfile(pkg_init):
        result.append(os.path.normpath(pkg_init))
        return result

    return result


def extract_string_from_node(node):
    """Извлекает строковое значение из AST узла (только ast.Constant для Python 3.8+)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def check_syntax(file_path):
    """
    Проверяет синтаксис файла через ast.parse.
    Возвращает (True, None) если всё OK, или (False, error_message) при ошибке.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"строка {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def get_dynamic_imports(file_path, root):
    """Ищет динамические импорты: __import__(), importlib.import_module()"""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == '__import__':
                if node.args:
                    module_name = extract_string_from_node(node.args[0])
                    if module_name:
                        parts = module_name.split('.')
                        chain = find_module_chain(parts, root)
                        imports.extend(chain)

            elif isinstance(node.func, ast.Attribute) and node.func.attr == 'import_module':
                if node.args:
                    module_name = extract_string_from_node(node.args[0])
                    if module_name:
                        parts = module_name.split('.')
                        chain = find_module_chain(parts, root)
                        imports.extend(chain)

    return imports


def get_file_references(file_path, root):
    """Ищет ссылки на .py файлы в open(), exec(), eval(), subprocess, os.system"""
    references = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except Exception:
        return []

    file_dir = os.path.dirname(file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                if node.args:
                    path_str = extract_string_from_node(node.args[0])
                    if path_str and path_str.endswith('.py'):
                        abs_path = os.path.normpath(os.path.join(file_dir, path_str))
                        if os.path.isfile(abs_path):
                            references.append(abs_path)
                        abs_path_root = os.path.normpath(os.path.join(root, path_str))
                        if os.path.isfile(abs_path_root):
                            references.append(abs_path_root)

            elif isinstance(node.func, ast.Name) and node.func.id in ('exec', 'eval'):
                if node.args:
                    code_str = extract_string_from_node(node.args[0])
                    if code_str:
                        import_matches = re.findall(r'import\s+([\w.]+)', code_str)
                        for module_name in import_matches:
                            parts = module_name.split('.')
                            chain = find_module_chain(parts, root)
                            references.extend(chain)

            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ('run', 'call', 'Popen', 'check_output', 'check_call'):
                    if node.args:
                        arg = node.args[0]
                        if isinstance(arg, ast.List):
                            for elt in arg.elts:
                                path_str = extract_string_from_node(elt)
                                if path_str and path_str.endswith('.py'):
                                    abs_path = os.path.normpath(os.path.join(file_dir, path_str))
                                    if os.path.isfile(abs_path):
                                        references.append(abs_path)
                                    abs_path_root = os.path.normpath(os.path.join(root, path_str))
                                    if os.path.isfile(abs_path_root):
                                        references.append(abs_path_root)

                elif node.func.attr == 'system':
                    if node.args:
                        cmd_str = extract_string_from_node(node.args[0])
                        if cmd_str:
                            py_matches = re.findall(r'[\w./\\]+\.py', cmd_str)
                            for py_file in py_matches:
                                abs_path = os.path.normpath(os.path.join(file_dir, py_file))
                                if os.path.isfile(abs_path):
                                    references.append(abs_path)
                                abs_path_root = os.path.normpath(os.path.join(root, py_file))
                                if os.path.isfile(abs_path_root):
                                    references.append(abs_path_root)

    return references


def get_imports(file_path, root):
    """Комплексный анализ всех способов использования .py файлов."""
    imports = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except Exception as e:
        logger.warning(f"Не удалось распарсить файл {file_path}: {e}")
        return []

    if os.path.basename(file_path) == '__init__.py':
        pkg_dir = os.path.dirname(file_path)
    else:
        pkg_dir = os.path.dirname(file_path)

    norm_root = os.path.normpath(root)

    # 1. Стандартные импорты
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split('.')
                chain = find_module_chain(parts, root)
                imports.extend(chain)

        elif isinstance(node, ast.ImportFrom):
            level = node.level or 0
            module = node.module or ''
            names = [alias.name for alias in node.names]

            if level > 0:
                base_dir = pkg_dir
                for _ in range(level - 1):
                    base_dir = os.path.dirname(base_dir)

                norm_base = os.path.normpath(base_dir)
                if not (norm_base == norm_root or norm_base.startswith(norm_root + os.sep)):
                    continue

                if module:
                    parts = module.split('.')
                    chain = find_module_chain(parts, base_dir)
                    imports.extend(chain)
                    if chain and os.path.basename(chain[-1]) == '__init__.py':
                        sub_dir = os.path.dirname(chain[-1])
                        for name in names:
                            imports.extend(find_module_chain([name], sub_dir))
                else:
                    for name in names:
                        imports.extend(find_module_chain([name], base_dir))
            else:
                if module:
                    parts = module.split('.')
                    chain = find_module_chain(parts, root)
                    imports.extend(chain)
                    if chain and os.path.basename(chain[-1]) == '__init__.py':
                        sub_dir = os.path.dirname(chain[-1])
                        for name in names:
                            imports.extend(find_module_chain([name], sub_dir))

    # 2. Динамические импорты
    imports.extend(get_dynamic_imports(file_path, root))

    # 3. Ссылки на файлы
    imports.extend(get_file_references(file_path, root))

    return list(set(imports))


def find_all_py_files(root):
    """Рекурсивно находит все .py файлы, пропуская технические директории."""
    result = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            if filename.endswith('.py'):
                result.append(os.path.normpath(os.path.join(dirpath, filename)))
    return result


def has_main_guard(file_path):
    """Проверяет, содержит ли файл конструкцию if __name__ == '__main__':"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                test = node.test
                if isinstance(test, ast.Compare):
                    if isinstance(test.left, ast.Name) and test.left.id == '__name__':
                        if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                            if len(test.comparators) == 1:
                                comp = test.comparators[0]
                                if isinstance(comp, ast.Constant) and comp.value == '__main__':
                                    return True
        return False
    except Exception as e:
        logger.debug(f"Ошибка проверки main guard в {file_path}: {e}")
        return False


def auto_detect_entry_point(script_dir):
    """Автоматически определяет точку входа в проекте."""
    logger.info(f"Автопоиск точки входа в: {script_dir}")
    all_files = find_all_py_files(script_dir)

    candidates_root = []
    candidates_sub = []
    priority_candidates = []

    for file_path in all_files:
        rel_path = os.path.relpath(file_path, script_dir)
        dir_part = os.path.dirname(rel_path)
        file_name = os.path.basename(file_path)

        if has_main_guard(file_path):
            if dir_part == '':
                candidates_root.append(file_path)
                if file_name.lower() in ENTRY_FILE_NAMES:
                    priority_candidates.append(file_path)
            else:
                candidates_sub.append(file_path)
        else:
            if dir_part == '' and file_name.lower() in ENTRY_FILE_NAMES:
                priority_candidates.append(file_path)

    if priority_candidates:
        logger.info(f"Найдена точка входа (приоритетная): {priority_candidates[0]}")
        return priority_candidates[0]
    if candidates_root:
        logger.info(f"Найдена точка входа (корневая): {candidates_root[0]}")
        return candidates_root[0]
    if candidates_sub:
        logger.info(f"Найдена точка входа (в подпапке): {candidates_sub[0]}")
        return candidates_sub[0]

    logger.warning("Точка входа не найдена")
    return None


def analyze_project(entry_file):
    """
    Строит граф зависимостей от точки входа.
    Возвращает четыре списка:
    - used: задействованные файлы (безопасно оставлять)
    - unused: незадействованные файлы (можно удалить)
    - problematic: файлы с ошибками синтаксиса (НЕ удалять!)
    - root: корень проекта
    """
    logger.info(f"Анализ проекта от точки входа: {entry_file}")
    root = os.path.dirname(os.path.normpath(entry_file))
    entry_file = os.path.normpath(entry_file)

    all_files = find_all_py_files(root)

    # ===== Этап 1: проверка синтаксиса всех файлов =====
    problematic = {}  # {file_path: error_message}
    clean_files = []

    for file_path in all_files:
        ok, error = check_syntax(file_path)
        if ok:
            clean_files.append(file_path)
        else:
            problematic[file_path] = error
            logger.warning(
                f"Файл с ошибками синтаксиса (будет сохранён): "
                f"{os.path.relpath(file_path, root)} — {error}"
            )

    clean_files_set = set(clean_files)

    # ===== Этап 2: BFS только по "чистым" файлам =====
    used = set()
    queue = []

    # Точка входа должна быть в чистых файлах
    if entry_file in clean_files_set:
        queue.append(entry_file)
    else:
        logger.error(
            f"Точка входа {entry_file} имеет синтаксические ошибки! "
            f"Анализ невозможен."
        )
        return set(), [], problematic, root

    while queue:
        current = queue.pop(0)
        if current in used:
            continue
        if current not in clean_files_set:
            continue
        used.add(current)
        for imp in get_imports(current, root):
            if imp in clean_files_set and imp not in used:
                queue.append(imp)

    unused = [f for f in clean_files if f not in used]

    logger.info(
        f"Результат анализа: {len(used)} задействованных, "
        f"{len(unused)} незадействованных, "
        f"{len(problematic)} с ошибками (сохранить)"
    )
    return used, unused, problematic, root


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dead Code Finder — Obsidian")
        self.resize(1200, 650)
        self.setMinimumSize(900, 500)

        self.entry_file = None
        self.project_root = None
        self.used_files = []
        self.unused_files = []
        self.problematic_files = {}  # {file_path: error_message}

        self._build_ui()

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # ===== Верхняя панель =====
        top_layout = QHBoxLayout()
        self.path_label = QLabel("Файл точки входа: Не выбран")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #999999; font-size: 12px;")

        self.auto_btn = QPushButton("⚡ Автопоиск")
        self.auto_btn.setObjectName("autoBtn")
        self.auto_btn.clicked.connect(self._auto_detect)

        self.select_btn = QPushButton("Выбрать файл (*.py)")
        self.select_btn.setObjectName("selectBtn")
        self.select_btn.clicked.connect(self._select_entry)

        top_layout.addWidget(self.path_label, 1)
        top_layout.addWidget(self.auto_btn)
        top_layout.addWidget(self.select_btn)
        main_layout.addLayout(top_layout)

        # ===== Центральная панель с ТРЕМЯ колонками =====
        splitter = QSplitter(Qt.Horizontal)

        # Колонка 1: задействованные
        left_group = QGroupBox("Задействованные файлы (Остаются):")
        left_layout = QVBoxLayout(left_group)
        left_layout.setContentsMargins(8, 20, 8, 8)
        self.used_list = QListWidget()
        self.used_list.setAlternatingRowColors(True)
        left_layout.addWidget(self.used_list)
        splitter.addWidget(left_group)

        # Колонка 2: незадействованные (красным)
        middle_group = QGroupBox("Незадействованные файлы (Будут удалены):")
        middle_layout = QVBoxLayout(middle_group)
        middle_layout.setContentsMargins(8, 20, 8, 8)
        self.unused_list = QListWidget()
        self.unused_list.setAlternatingRowColors(True)
        middle_layout.addWidget(self.unused_list)
        splitter.addWidget(middle_group)

        # Колонка 3: проблемные (оранжевым)
        right_group = QGroupBox("⚠ Файлы с ошибками (НЕ удалять!):")
        right_layout = QVBoxLayout(right_group)
        right_layout.setContentsMargins(8, 20, 8, 8)
        self.problematic_list = QListWidget()
        self.problematic_list.setAlternatingRowColors(True)
        self.problematic_list.setWordWrap(True)
        right_layout.addWidget(self.problematic_list)
        splitter.addWidget(right_group)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 1)
        main_layout.addWidget(splitter, 1)

        # ===== Нижняя панель =====
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        self.export_btn = QPushButton("📄 Экспорт отчета в TXT")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_report)
        bottom_layout.addWidget(self.export_btn)

        self.delete_btn = QPushButton("🗑 Заархивировать и удалить")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._archive_and_delete)
        bottom_layout.addWidget(self.delete_btn)

        main_layout.addLayout(bottom_layout)

        # ===== Строка статуса =====
        self.status_label = QLabel("Готово к работе")
        self.status_label.setStyleSheet(
            "color: #888; font-size: 12px; padding: 6px 4px; "
            "background-color: #1e1e1e; border-radius: 4px;"
        )
        main_layout.addWidget(self.status_label)

    def _update_status(self, message, color="#888"):
        """Обновляет строку статуса внизу окна."""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(
            f"color: {color}; font-size: 12px; padding: 6px 4px; "
            f"background-color: #1e1e1e; border-radius: 4px;"
        )

    def _auto_detect(self):
        """Автоматически находит точку входа в проекте."""
        if getattr(sys, 'frozen', False):
            script_dir = os.path.dirname(sys.executable)
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        self._update_status("⏳ Поиск точки входа...", "#8a7cf7")
        QApplication.processEvents()

        try:
            entry_file = auto_detect_entry_point(script_dir)

            if entry_file:
                self.entry_file = entry_file
                self.path_label.setText(f"Файл точки входа: {self.entry_file}")
                self.path_label.setStyleSheet("color: #dcddde; font-size: 12px;")
                self._update_status(
                    f"✓ Найдена точка входа: {os.path.basename(entry_file)}",
                    "#70c070"
                )
                self._run_analysis()
            else:
                self._update_status(
                    "✗ Не удалось определить точку входа. Выберите файл вручную.",
                    "#e06c75"
                )
        except Exception as e:
            logger.error(f"Ошибка автопоиска: {e}", exc_info=True)
            self._update_status(f"✗ Ошибка автопоиска: {e}", "#e06c75")

    def _select_entry(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл точки входа",
            "",
            "Python files (*.py);;All files (*.*)"
        )
        if not path:
            return
        self.entry_file = os.path.normpath(path)
        self.path_label.setText(f"Файл точки входа: {self.entry_file}")
        self.path_label.setStyleSheet("color: #dcddde; font-size: 12px;")
        self._run_analysis()

    def _run_analysis(self):
        try:
            used, unused, problematic, root = analyze_project(self.entry_file)
            self.project_root = root
            self.used_files = sorted(used)
            self.unused_files = sorted(unused)
            self.problematic_files = problematic
            self._update_lists()
            self.export_btn.setEnabled(True)

            if self.unused_files:
                self.delete_btn.setEnabled(True)
            else:
                self.delete_btn.setEnabled(False)

            # Формируем статусное сообщение
            parts = [
                f"✓ Задействовано: {len(self.used_files)}",
                f"Незадействовано: {len(self.unused_files)}"
            ]
            if self.problematic_files:
                parts.append(f"⚠ С ошибками: {len(self.problematic_files)}")
                status_color = "#e5c07b"
            else:
                status_color = "#70c070"

            if not self.unused_files and not self.problematic_files:
                self._update_status(
                    "✓ Все файлы проекта задействованы. Удалять нечего.",
                    "#8a7cf7"
                )
            else:
                self._update_status("  •  ".join(parts), status_color)

        except Exception as e:
            logger.error(f"Ошибка анализа проекта: {e}", exc_info=True)
            self._update_status(f"✗ Ошибка анализа: {e}", "#e06c75")

    def _update_lists(self):
        # Задействованные
        self.used_list.clear()
        for f in self.used_files:
            rel_path = os.path.relpath(f, self.project_root)
            self.used_list.addItem(rel_path)

        # Незадействованные (красным)
        self.unused_list.clear()
        unused_color = QColor("#e06c75")
        for f in self.unused_files:
            rel_path = os.path.relpath(f, self.project_root)
            item = QListWidgetItem(rel_path)
            item.setForeground(unused_color)
            self.unused_list.addItem(item)

        # Проблемные (оранжевым, с описанием ошибки)
        self.problematic_list.clear()
        problem_color = QColor("#e5c07b")
        for f, error_msg in sorted(self.problematic_files.items()):
            rel_path = os.path.relpath(f, self.project_root)
            item = QListWidgetItem(f"{rel_path}\n↳ {error_msg}")
            item.setForeground(problem_color)
            self.problematic_list.addItem(item)

    def _export_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт",
            "",
            "Text files (*.txt);;All files (*.*)"
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(f"Отчёт по проекту: {self.project_root}\n")
                f.write(f"Точка входа: {self.entry_file}\n\n")

                f.write(f"=== Задействованные файлы ({len(self.used_files)}) ===\n")
                for file in self.used_files:
                    f.write(os.path.relpath(file, self.project_root) + '\n')

                f.write(f"\n=== Незадействованные файлы ({len(self.unused_files)}) ===\n")
                for file in self.unused_files:
                    f.write(os.path.relpath(file, self.project_root) + '\n')

                if self.problematic_files:
                    f.write(
                        f"\n=== Файлы с ошибками синтаксиса "
                        f"({len(self.problematic_files)}) — НЕ УДАЛЯТЬ ===\n"
                    )
                    f.write(
                        "Эти файлы не удалось проанализировать из-за ошибок синтаксиса. "
                        "Они могут использоваться в проекте, поэтому их следует "
                        "проверить вручную и исправить.\n\n"
                    )
                    for file, error_msg in sorted(self.problematic_files.items()):
                        f.write(f"{os.path.relpath(file, self.project_root)}\n")
                        f.write(f"  Ошибка: {error_msg}\n\n")

            logger.info(f"Отчёт сохранён: {path}")
            self._update_status(f"✓ Отчёт сохранён: {path}", "#70c070")
        except Exception as e:
            logger.error(f"Ошибка сохранения отчёта: {e}", exc_info=True)
            self._update_status(f"✗ Ошибка сохранения отчёта: {e}", "#e06c75")

    def _archive_and_delete(self):
        if not self.unused_files:
            return

        archive_path = os.path.join(self.project_root, 'unused_files_archive.zip')

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in self.unused_files:
                    arcname = os.path.relpath(file, self.project_root)
                    zf.write(file, arcname)
            logger.info(f"Архив создан: {archive_path}")
        except Exception as e:
            logger.error(f"Ошибка архивации: {e}", exc_info=True)
            self._update_status(f"✗ Ошибка архивации: {e}", "#e06c75")
            return

        errors = []
        for file in self.unused_files:
            try:
                os.remove(file)
            except Exception as e:
                rel_path = os.path.relpath(file, self.project_root)
                logger.error(f"Не удалось удалить {rel_path}: {e}")
                errors.append(f"{rel_path}: {e}")

        if errors:
            logger.warning(f"Не удалось удалить {len(errors)} файл(ов)")
            self._update_status(
                f"⚠ Архив создан, но {len(errors)} файл(ов) не удалось удалить",
                "#e5c07b"
            )
        else:
            logger.info(f"Удалено {len(self.unused_files)} файлов")
            self._update_status(
                f"✓ Архив создан, удалено {len(self.unused_files)} файлов",
                "#70c070"
            )

        self._run_analysis()


if __name__ == '__main__':
    logger.info("Запуск Dead Code Finder")
    app = QApplication(sys.argv)
    app.setStyleSheet(OBSIDIAN_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
