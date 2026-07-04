import win32gui
import win32clipboard
import win32api
import win32con
import time

class OverlayWin32Helper:
    def track_win32_focus_leak(self):
        if not hasattr(self, 'isVisible') or not self.isVisible(): return
        fg_hwnd = win32gui.GetForegroundWindow()
        if fg_hwnd == int(self.winId()): return
        if self.settings_window and self.settings_window.isVisible() and fg_hwnd == int(self.settings_window.winId()): return
        win_title = win32gui.GetWindowText(fg_hwnd) or "System/Desktop Area"
        self.hide_overlay()

    # def paste_text_caps_safe(self, text, word_data):
    #     self.hide_overlay()

    #     # Кнопка "Без изменений" - абсолютный хозяин. Галочки на неё не влияют.
    #     final_text = self.formatter.apply(text)

    #     # НАСТРОЙКА ПРОБЕЛА: Если флаг is_space активен, подставляем пробел в начало строки
    #     if word_data.get("is_space", True):
    #         final_text = " " + final_text

    #     # Аппаратно отпускаем физические клавиши Alt (0x12) и F1 (0x70) в Windows.
    #     win32api.keybd_event(0x12, 0, win32con.KEYEVENTF_KEYUP, 0)
    #     win32api.keybd_event(0x70, 0, win32con.KEYEVENTF_KEYUP, 0)

    #     for _ in range(5):
    #         try:
    #             win32clipboard.OpenClipboard()
    #             win32clipboard.EmptyClipboard()
    #             win32clipboard.SetClipboardText(final_text, win32clipboard.CF_UNICODETEXT)
    #             win32clipboard.CloseClipboard()
    #             break
    #         except:
    #             time.sleep(0.01)

    #     # Увеличенная пауза для возврата фокуса
    #     time.sleep(0.15)

    #     # Симуляция нажатия Ctrl+V
    #     win32api.keybd_event(0x11, 0, 0, 0)
    #     win32api.keybd_event(0x56, 0, 0, 0)
    #     win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)
    #     win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)


    def paste_text_caps_safe(self, text, word_data):
        self.hide_overlay()
        final_text = self.formatter.apply(text)
        if word_data.get("is_space", True):
            final_text = " " + final_text

        # ═══ ИСПРАВЛЕНО: Отпускаем ВСЕ модификаторы, а не только Alt+F1 ═══
        modifier_scan_codes = [
            0x10,  # Shift
            0x11,  # Ctrl
            0x12,  # Alt
        ]
        for vk in modifier_scan_codes:
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)

        for _ in range(5):
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(final_text, win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                break
            except:
                time.sleep(0.01)

        time.sleep(0.15)
        win32api.keybd_event(0x11, 0, 0, 0)            # Ctrl down
        win32api.keybd_event(0x56, 0, 0, 0)            # V down
        win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)  # V up
        win32api.keybd_event(0x11, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl up
