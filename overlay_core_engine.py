import time
import win32api
import win32con
import win32clipboard
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QCursor

class OverlayCoreEngine:
    def safe_check_clipboard_qt(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                current_text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            else:
                current_text = ""
            win32clipboard.CloseClipboard()
            if current_text != self._last_clipboard_text:
                self._last_clipboard_text = current_text
                self.refresh_ui()
        except:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass

    def should_block_overlay_hide(self, is_popup_open, is_click_inside_popup):
        if is_popup_open:
            if is_click_inside_popup:
                return True
            if not self.hide_menu_on_click_outside:
                return True
        if not self.hide_on_click_outside:
            return True
        return False

    def handle_mode_cycle(self):
        self.formatter.next_mode()
        self.update_mode_button_view()

    def update_mode_button_view(self):
        cfg = self.storage.load_default_settings()
        mode_text = self.formatter.get_mode_text()
        active = self.formatter.mode != 0
        is_rounded = cfg.get("is_rounded", True)
        btn_radius = "12px" if is_rounded else "0px"

        # Чтение шрифта
        o_font_family = cfg.get("overlay_font_family", "Segoe UI")
        o_font_size = cfg.get("overlay_font_size", 13)

        # ДОБАВИТЬ:
        o_font_weight = "bold" if cfg.get("is_bold", False) else "normal"

        self.btn_mode.setText(f"{mode_text}")
        independent_bg_color = cfg.get("default_btn_bg_color", "#242424")
        independent_text_color = cfg.get("default_btn_text_color", "#FFFFFF")

        def lighten_hex_color(hex_str, percent=20):
            try:
                hex_clean = hex_str.lstrip('#')
                r, g, b = tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))
                r = min(255, int(r + (255 - r) * (percent / 100)))
                g = min(255, int(g + (255 - g) * (percent / 100)))
                b = min(255, int(b + (255 - b) * (percent / 100)))
                return f"#{r:02X}{g:02X}{b:02X}"
            except:
                return "#3D3D3D"

        hover_bg_color = lighten_hex_color(independent_bg_color, percent=20)

        if active:
            self.btn_mode.setStyleSheet(f"""
            QPushButton{{background-color:{independent_bg_color};color:{independent_text_color};border: 2px solid #7C3AED;border-radius:{btn_radius};font-family: '{o_font_family}', sans-serif;font-size: {o_font_size}px;}}
            QPushButton:hover{{background-color:{hover_bg_color};}}
            """)
        else:
            self.btn_mode.setStyleSheet(f"""
            QPushButton{{background-color:{independent_bg_color};color:{independent_text_color};border: 1px solid #3E3E3E;border-radius:{btn_radius};font-family: '{o_font_family}', sans-serif;font-size: {o_font_size}px;}}
            QPushButton:hover{{background-color:{hover_bg_color};color:#FFFFFF;}}
            """)

        self.settings_btn.setStyleSheet(f"""
        QPushButton{{background-color:{independent_bg_color};color:{independent_text_color};border: 1px solid #3E3E3E;border-radius:{btn_radius};font-family: '{o_font_family}', sans-serif;font-size: {o_font_size}px;}}
        QPushButton:hover{{background-color:{hover_bg_color};}}
        """)

        for i in range(1, 9):
            btn = self.overlay_dict_group.button(i)
            if btn:
                btn.setFixedSize(26, 26)
                if btn.isChecked():
                    btn.setStyleSheet(f"""
                    QPushButton{{background-color:#7C3AED;color: white;border: 1px solid #7C3AED;border-radius:{btn_radius};font-family: '{o_font_family}', sans-serif;font-size: {o_font_size}px;}}
                    """)
                else:
                    btn.setStyleSheet(f"""
                    QPushButton{{background-color:{independent_bg_color};color:{independent_text_color};border: 1px solid #3E3E3E;border-radius:{btn_radius};font-family: '{o_font_family}', sans-serif;font-size: {o_font_size}px;}}
                    QPushButton:hover{{background-color:{hover_bg_color};}}
                    """)

    def show_at_cursor(self):
        current_time = time.time()

        # Безопасная проверка: игнорируем только если переменная инициализирована и время меньше 0.5с
        if getattr(self, '_last_hide_time', 0) > 0 and (current_time - self._last_hide_time) < 0.5:
            return

        self.formatter.mode = 0
        self.formatter.reset()
        self.update_mode_button_view()

        cfg = self.storage.load_default_settings() or {}
        if cfg.get("is_dict_pinned", False):
            active_id = int(cfg.get("pinned_dict_id", 1))
            cfg["current_dict_id"] = active_id
            self.storage.save_default_settings(cfg)
        else:
            active_id = int(cfg.get("current_dict_id", 1))

        self.refresh_ui()

        if hasattr(self.storage, '_all_phrases_cache'):
            delattr(self.storage, '_all_phrases_cache')

        btn = self.overlay_dict_group.button(active_id)
        if btn:
            btn.blockSignals(True)
            btn.setChecked(True)
            btn.blockSignals(False)

        panel_width = int(cfg.get("panel_width", 350))
        cursor_pos = QCursor.pos()
        target_x = int(cursor_pos.x() - (panel_width / 2))
        target_y = int(cursor_pos.y() - (self.height() / 2))

        screen = self.screen()
        if screen:
            screen_geo = screen.geometry()
            if target_x < screen_geo.left():
                target_x = screen_geo.left()
            if target_x + panel_width > screen_geo.right():
                target_x = screen_geo.right() - panel_width
            if target_y < screen_geo.top():
                target_y = screen_geo.top()
            if target_y + self.height() > screen_geo.bottom():
                target_y = screen_geo.bottom() - self.height()

        self.move(target_x, target_y)
        self.show()
        self._show_timestamp = time.time()

        # 1. Сначала забираем фокус
        self.activateWindow()
        self.focus_timer.start(30)

        # 2. ИСПРАВЛЕНО: Универсальный сброс ВСЕХ модификаторов (Ctrl, Alt, Shift)
        # Это предотвращает их залипание в Windows для ЛЮБОЙ назначенной комбинации
        for vk_code in [0x11, 0x12, 0x10]: # 0x11=Ctrl, 0x12=Alt, 0x10=Shift
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)

    def hide_overlay(self):
        self._last_hide_time = time.time()
        self.focus_timer.stop()
        self.hide()

    def open_settings(self):
        """Открывает окно редактора словарей"""
        self.hide_overlay()
        cfg = self.storage.load_default_settings()
        active_tab = int(cfg.get("current_dict_id", 1))
        r_btn = self.settings_window.selector_btn_group.button(active_tab)
        if r_btn:
            r_btn.setChecked(True)
        self.settings_window.refresh_list()
        self.settings_window.show()
        self.settings_window.activateWindow()
