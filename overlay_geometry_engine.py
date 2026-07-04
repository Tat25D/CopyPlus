from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QCursor
class OverlayGeometryEngineLogic:
    def reposition_overlay_safely(self):
        """
        ИСПРАВЛЕНО ПО ТЗ: Устранен IndentationError.
        При вызове хоткеем - центр UI строго под мышкой с учетом актуальной высоты.
        При кликах 1-8 - нижняя панель намертво застывает на экране.
        """
        cfg = self.storage.load_default_settings() or {}
        panel_width = int(cfg.get("panel_width", 350))
        # Получаем реальную, только что вычисленную рендерером высоту резинового контента
        new_height = self.height()
        # Получаем параметры текущего активного экрана (монитора), где находится мышь
        screen = self.screen()
        screen_geo = screen.geometry() if screen else None
        # 1. СТРОГО ПО ТЗ: Окно открывается с нуля из скрытого состояния (вызов хоткеем)
        if not getattr(self, '_is_already_visible', False):
            cursor_pos = QCursor.pos()
            # Математический расчет центра окна точно под кончиком курсора мыши
            target_x = int(cursor_pos.x() - (panel_width / 2))
            target_y = int(cursor_pos.y() - (new_height / 2))
            # Умный предохранитель границ экрана (чтобы центрированное окно не обрезалось монитором)
            if screen_geo:
                if target_x + panel_width > screen_geo.right():
                    target_x = screen_geo.right() - panel_width
                if target_x < screen_geo.left():
                    target_x = screen_geo.left()
                if target_y + new_height > screen_geo.bottom():
                    target_y = screen_geo.bottom() - new_height
                if target_y < screen_geo.top():
                    target_y = screen_geo.top()
            # Мгновенно перемещаем окно в рассчитанную центральную позицию
            self.move(target_x, target_y)
            return
        # 2. СТРОГО ПО ТЗ: Клик мышкой по кнопкам 1-8 или «СЛОВО» (окно уже на экране)
        # Считываем сохраненную ДО перерисовки координату нижнего края окна на экране
        saved_bottom_y = getattr(self, '_original_bottom_y', self.geometry().y() + self.geometry().height())
        # Горизонталь X не меняется, а верх Y подгоняется так, чтобы линия низа застыла
        target_x = self.geometry().x()
        target_y = saved_bottom_y - new_height
        # Защищаем зафиксированный низ и верх от вылета за рамки монитора при переключениях
        if screen_geo:
            if target_y < screen_geo.top():
                target_y = screen_geo.top()
            if target_y + new_height > screen_geo.bottom():
                target_y = screen_geo.bottom() - new_height
        # Перемещаем окно, удерживая нижнюю плашку на экране неподвижно
        self.move(target_x, target_y)