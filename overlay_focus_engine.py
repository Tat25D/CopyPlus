import time
import win32gui
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QCursor
class OverlayFocusEngineLogic:
    def track_win32_focus_leak(self):
        """Восстановлено и исправлено: Мониторинг фокуса с проверкой положения мыши по ТЗ"""
        # Предохранитель: не закрываем окно в первые 200мс после его появления на экране
        if time.time() - getattr(self, '_show_timestamp', 0.0) < 0.2:
            return
        # ИСПРАВЛЕНО ПО ТЗ: Получаем текущие координаты курсора мыши в Windows
        current_mouse_pos = QCursor.pos()
        # ИСПРАВЛЕНО ПО ТЗ: Если мышка физически находится над основным парящим окном, НЕ прячем его
        if self.geometry().contains(current_mouse_pos):
            return
        # ИСПРАВЛЕНО ПО ТЗ: Если мышка находится над окном редактора словарей (меню падежей), НЕ прячем оверлей
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.isVisible():
            if self.settings_window.geometry().contains(current_mouse_pos):
                return
        # Получаем HWND-дескриптор окна, которое прямо сейчас находится на переднем плане ОС Windows
        active_hwnd = win32gui.GetForegroundWindow()
        popup_hwnd = 0
        # Сканируем дочерние контекстные меню падежей, открытые оверлеем фраз
        for widget in self.findChildren(QMenu):
            if widget.isVisible():
                popup_hwnd = int(widget.winId())
                break
        my_hwnd = int(self.winId())
        is_popup_open = (popup_hwnd != 0)
        is_click_inside_popup = (active_hwnd == popup_hwnd)
        # Если фокус ушел с главного оверлея фраз
        if active_hwnd != my_hwnd:
            # Проверяем, заблокировано ли скрытие глобальным конфигом или открытым меню падежей
            if self.should_block_overlay_hide(is_popup_open, is_click_inside_popup):
                return
            # Если это был клик мимо — безопасно убираем панель фраз с экрана
            self.hide_overlay()
    def check_active_window_hierarchy(self, active_hwnd, my_hwnd, popup_hwnd):
        """Восстановлено: Глубокая win32-проверка родственных связей окон во избежание мерцания панели"""
        if active_hwnd == 0:
            return False
        # Проверяем, не является ли активное окно дочерним по отношению к нашему оверлею
        parent_hwnd = win32gui.GetParent(active_hwnd)
        if parent_hwnd == my_hwnd or parent_hwnd == popup_hwnd:
            return True
        # Проверяем совпадение по имени класса окна Qt6
        try:
            class_name = win32gui.GetClassName(active_hwnd)
            if "Qt6" in class_name and (active_hwnd == my_hwnd or active_hwnd == popup_hwnd):
                return True
        except:
            pass
        return False
    def force_win32_window_focus(self):
        """Восстановлено: Принудительный захват фокуса ввода через Win32 API при вызове хоткеем"""
        hwnd = int(self.winId())
        if hwnd:
            try:
                # Мягко выводим окно на передний план структуры рабочих столов Windows
                win32gui.SetForegroundWindow(hwnd)
                win32gui.BringWindowToTop(hwnd)
            except Exception as e:
                # Если ОС Windows блокирует прямой захват, логируем без падения потока
                print(Null) #(f"[FOCUS_ENGINE_WARNING] Win32 Foreground attachment bypassed: {e}", flush=True)
