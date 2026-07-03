import os
if os.name == 'nt':
    import ctypes
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

import ui_behavior_config
from storage import StorageService
from overlay import ClipboardOverlay

class HookHotkeyManager:
    def __init__(self, storage):
        self.storage = storage
        self.callback = None
        self.current_hotkey_str = ""

    def start(self, callback):
        self.callback = callback
        self.update_hotkey()

    def update_hotkey(self):
        import keyboard
        settings = self.storage.load_default_settings() or {}
        hk_cfg = settings.get("hotkey_config", {})

        # ═══ Снимаем ВСЕ старые хоткеи ═══
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        # ═══ Собираем модификаторы ═══
        hotkey_parts = []
        if hk_cfg.get("ctrl"):
            hotkey_parts.append("ctrl")
        if hk_cfg.get("shift"):
            hotkey_parts.append("shift")
        if hk_cfg.get("alt"):
            hotkey_parts.append("alt")

        # Если ни один модификатор не выбран — принудительно добавляем Alt
        if not hotkey_parts:
            hotkey_parts.append("alt")

        # ═══ Определяем основную клавишу ═══
        f_key = hk_cfg.get("f_key", "Нет")
        char = hk_cfg.get("char", "").strip()

        final_key = None
        if f_key and f_key.lower() != "нет":
            # F-клавиши: keyboard понимает "f1", "f2", ..., "f12"
            final_key = f_key.lower()
        elif char and len(char) == 1:
            # ИСПРАВЛЕНО: передаём символ напрямую, а НЕ scan-код
            # keyboard.add_hotkey("alt+a") работает корректно
            final_key = char.lower()

        if not final_key:
            final_key = "f1"

        hotkey_parts.append(final_key)
        primary_hotkey = "+".join(hotkey_parts)
        self.current_hotkey_str = primary_hotkey

        # ═══ Регистрируем ОСНОВНОЙ хоткей ═══
        primary_ok = False
        try:
            keyboard.add_hotkey(primary_hotkey, self.callback, suppress=True)
            primary_ok = True
            print(f"[HOTKEY] Основной: {primary_hotkey}", flush=True)
        except Exception as e:
            print(f"[HOTKEY] Ошибка основного '{primary_hotkey}': {e}", flush=True)

        # ═══ ВСЕГДА регистрируем ЗАПАСНОЙ Alt+F1 ═══
        FALLBACK = "alt+f1"
        if FALLBACK != primary_hotkey:
            # Основной хоткей отличается от фолбэка — регистрируем оба
            try:
                keyboard.add_hotkey(FALLBACK, self.callback, suppress=True)
                print(f"[HOTKEY] Запасной: {FALLBACK}", flush=True)
            except Exception as e:
                print(f"[HOTKEY] Ошибка запасного '{FALLBACK}': {e}", flush=True)
        else:
            # Основной = фолбэк (пользователь выбрал Alt+F1)
            if primary_ok:
                print(f"[HOTKEY] Alt+F1 работает как основной", flush=True)
            else:
                # Основной не зарегистрировался — пробуем фолбэк ещё раз
                try:
                    keyboard.add_hotkey(FALLBACK, self.callback, suppress=True)
                    print(f"[HOTKEY] Alt+F1 зарегистрирован при повторной попытке", flush=True)
                except Exception as e:
                    print(f"[HOTKEY] КРИТИЧЕСКАЯ ОШИБКА: Alt+F1 не работает: {e}", flush=True)

# Защита от двойного срабатывания модификаторов в Windows
_last_hotkey_time = 0.0



def main():
    app = QApplication(sys.argv)

    if getattr(sys, 'frozen', False):
        # Если запущено из .exe, ищем иконку РЯДОМ с .exe файлом
        base_dir = os.path.dirname(sys.executable)
    else:
        # Если запущено как скрипт, ищем в папке проекта
        base_dir = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_dir, "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    app.setStyleSheet(
        "* { outline:none; }"
        "QPushButton:focus { outline:none; border:1px solid #3E3E3E; }"
        "QPushButton:checked:focus { outline:none; border:1px solid #7C3AED; }"
        "QCheckBox:focus, QCheckBox::indicator:focus { outline:none; }"
        "QRadioButton:focus, QRadioButton::indicator:focus { outline:none; }"
        "QLineEdit:focus, QComboBox:focus { outline:none; }"
        "QListWidget:focus { outline:none; border:none; }"
        "QSlider:focus { outline:none; }"
        "QTabBar::tab:focus { outline:none; }"
    )

    from PyQt6.QtCore import QTranslator, QLocale, QLibraryInfo
    translator = QTranslator()
    translator.load(
        QLocale(QLocale.Language.Russian, QLocale.Country.Russia),
        "qtbase", "_",
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    )
    app.installTranslator(translator)
    app.setQuitOnLastWindowClosed(False)

    storage = StorageService()

    current_settings = storage.load_default_settings() or {}
    if "default_btn_text_color" not in current_settings:
        current_settings["default_btn_text_color"] = "#FFFFFF"
        storage.save_default_settings(current_settings)

    def get_config_attr(prefixes):
        for prefix in prefixes:
            for attr in dir(ui_behavior_config):
                attr_lower = attr.lower()
                if all(p in attr_lower for p in prefix):
                    return getattr(ui_behavior_config, attr)
        return "#1E1E1E"

    ui_bg = get_config_attr([["ui", "bg"], ["bg"]])
    btn_text = get_config_attr([["btn", "text"], ["button", "text"]])
    menu_bg = get_config_attr([["menu", "bg"]])
    menu_item_bg = get_config_attr([["menu", "item"]])

    overlay = ClipboardOverlay(storage, ui_bg, btn_text, menu_bg, menu_item_bg)

    hotkey_manager = HookHotkeyManager(storage)

    def safe_show():
        print("[HOTKEY-DEBUG] >>> COLLABACK СРАБОТАЛ! Отправляем команду на показ окна.", flush=True)
        QTimer.singleShot(0, overlay.show_at_cursor)

    try:
        hotkey_manager.start(callback=safe_show)
    except TypeError:
        hotkey_manager.start(safe_show)

    def on_settings_saved():
        overlay.refresh_ui()
        hotkey_manager.update_hotkey()

    if hasattr(overlay, 'settings_window') and overlay.settings_window:
        overlay.settings_window.on_save_callback = on_settings_saved

    overlay.settings_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
