from PyQt6.QtWidgets import QMenu, QApplication
from PyQt6.QtGui import QAction, QCursor, QFontMetrics
from PyQt6.QtCore import Qt, QPoint, QObject, QEvent


class _MenuSpaceFilter(QObject):
    """Скрытый фильтр: перехватывает Пробел внутри меню падежей для смены режима"""
    def __init__(self, overlay_ref, menu_ref, actions_list, word_data, formatter_ref):
        super().__init__()
        self.overlay = overlay_ref
        self.menu = menu_ref
        self.actions = actions_list
        self.word_data = word_data
        self.formatter = formatter_ref

    def eventFilter(self, obj, event):
        # Закрытие меню по Esc
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.menu.close()
            return True

        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
            # 1. Переключаем режим (это обновит кнопку внизу)
            self.overlay.handle_mode_cycle()

            # ═══════ ДОБАВЛЕНО: Перерисовываем кнопки фраз в фоне ═══════
            # Это устраняет рассинхронизацию между меню и фоном
            self.overlay.refresh_ui()
            # ══════════════════════════════════════════════════════════

            # 2. Обновляем текст внутри уже открытого меню
            cases_keys = [
                ("nominative", "И"), ("genitive", "Р"), ("dative", "Д"),
                ("accusative", "В"), ("instrumental", "Т"), ("prepositional", "П")
            ]

            cfg = self.overlay.storage.load_default_settings() or {}
            item_max_width = int(cfg.get("menu_width", 350))
            font_metrics = QFontMetrics(self.menu.font())
            css_padding = 30

            for i, (key, label) in enumerate(cases_keys):
                if i < len(self.actions):
                    raw_text = self.word_data.get(key, self.word_data.get("nominative", "")).strip()

                    # Применяем НОВЫЙ режим регистратора
                    if self.formatter.mode == 0:
                        if self.word_data.get("is_caps", False):
                            full_text_to_paste = raw_text.upper()
                        elif self.word_data.get("is_first_capital", False) and raw_text:
                            full_text_to_paste = raw_text[0].upper() + raw_text[1:]
                        else:
                            full_text_to_paste = raw_text
                    else:
                        full_text_to_paste = self.formatter.apply(raw_text)

                    # Формируем визуальный текст (с троеточием, если не влезает)
                    prefix = f"{label}: "
                    prefix_width = font_metrics.boundingRect(prefix).width()
                    available_text_width = item_max_width - prefix_width - css_padding

                    visual_text = full_text_to_paste
                    if font_metrics.boundingRect(visual_text).width() > available_text_width:
                        visual_text = font_metrics.elidedText(visual_text, Qt.TextElideMode.ElideRight, available_text_width)

                    self.actions[i].setText(f"{prefix}{visual_text}")

                    # 3. ПЕРЕПОДКЛЮЧАЕМ клик по пункту меню, чтобы при вставке был верный регистр
                    try:
                        self.actions[i].triggered.disconnect()
                    except Exception:
                        pass

                    w_data = self.word_data
                    l = label
                    t = full_text_to_paste
                    self.actions[i].triggered.connect(
                        lambda checked, txt=t, lb=l, wd=w_data: self.overlay.log_and_paste(txt, lb, wd)
                    )

            return True # Блокируем закрытие меню
        return False


class OverlayContextMenuManager:
    """Компонент отрисовки и позиционирования выпадающего меню падежей Windows"""
    @staticmethod
    def show_menu(parent_widget, word_data, storage_service, formatter_service, log_paste_callback):
        active_dict_id = int(storage_service.load_default_settings().get("current_dict_id", 1))
        target_nominative = word_data.get("nominative", "").strip()
        live_word = word_data
        for w in storage_service.load_phrases():
            if int(w.get("dict_id", 1)) == active_dict_id and w.get("nominative", "").strip().lower() == target_nominative.lower():
                live_word = w
                break

        menu = QMenu(parent_widget)
        menu.setWindowFlags(menu.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        def custom_close_event(event):
            if event.spontaneous() and not getattr(parent_widget, 'hide_menu_on_click_outside', True):
                event.ignore()
            else:
                event.accept()
        menu.closeEvent = custom_close_event

        cfg = storage_service.load_default_settings() or {}
        item_max_width = cfg.get("menu_width", "350")

        is_bold = cfg.get("is_bold", False)
        menu_font_weight = "bold" if is_bold else "normal"
        menu_font_family = cfg.get("overlay_font_family", "Segoe UI")
        menu_font_size = cfg.get("overlay_font_size", 13)

        independent_bg_color = cfg.get("default_btn_bg_color", "#242424")
        independent_text_color = cfg.get("default_btn_text_color", "#E0E0E0")

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
        menu_radius = "12px" if storage_service.load_default_settings().get("is_rounded", True) else "0px"

        menu.setStyleSheet(f"""
        QMenu {{ background-color: transparent; border: none; padding: 0px; }}
        QMenu::item {{
            background-color: {independent_bg_color}; color: {independent_text_color};
            padding: 6px 12px;
            border-radius: {menu_radius}; margin: 2px 0px;
            font-family: '{menu_font_family}', sans-serif;
            font-size: {menu_font_size}px; border: none;
            font-weight: {menu_font_weight}; border: none;
            max-width: {item_max_width}px;
        }}
        QMenu::item:selected {{ background-color: {hover_bg_color}; color: #FFFFFF; }}
        """)

        menu_font = menu.font()
        font_metrics = QFontMetrics(menu_font)
        css_padding = 30

        cases_keys = [
            ("nominative", "И"), ("genitive", "Р"), ("dative", "Д"),
            ("accusative", "В"), ("instrumental", "Т"), ("prepositional", "П")
        ]

        # СЮДА БУДЕМ СОБИРАТЬ ЭКЗЕМПЛЯРЫ QAction
        menu_actions = []

        for key, label in cases_keys:
            raw_text = live_word.get(key, live_word.get("nominative", "")).strip()

            if formatter_service.mode == 0:
                if live_word.get("is_caps", False):
                    full_text_to_paste = raw_text.upper()
                elif live_word.get("is_first_capital", False) and raw_text:
                    full_text_to_paste = raw_text[0].upper() + raw_text[1:]
                else:
                    full_text_to_paste = raw_text
            else:
                full_text_to_paste = formatter_service.apply(raw_text)

            prefix = f"{label}: "
            prefix_width = font_metrics.boundingRect(prefix).width()
            available_text_width = int(item_max_width) - prefix_width - css_padding

            visual_text = full_text_to_paste
            if font_metrics.boundingRect(visual_text).width() > available_text_width:
                visual_text = font_metrics.elidedText(visual_text, Qt.TextElideMode.ElideRight, available_text_width)

            action = QAction(f"{prefix}{visual_text}", menu)
            action.triggered.connect(lambda checked, t=full_text_to_paste, l=label, w_data=live_word: log_paste_callback(t, l, w_data))
            menu.addAction(action)

            menu_actions.append(action) # СОХРАНЯЕМ ССЫЛКУ НА ACTION

        # ═══════ ДОБАВЛЕНО: Вешаем фильтр пробела на меню ═══════
        space_filter = _MenuSpaceFilter(
            parent_widget, menu, menu_actions, live_word, formatter_service
        )
        menu.installEventFilter(space_filter)
        menu._space_filter = space_filter # Защита от удаления сборщиком мусора Python
        # ════════════════════════════════════════════════════════

        import ui_behavior_config
        mode = getattr(ui_behavior_config, 'MENU_POSITION_MODE', 1)
        cursor_pos = QCursor.pos()
        menu.adjustSize()
        menu_w, menu_h = menu.sizeHint().width(), menu.sizeHint().height()
        screen = QApplication.screenAt(cursor_pos)
        screen_geo = screen.geometry() if screen else parent_widget.geometry()
        overlay_geo = parent_widget.geometry()
        overlay_center_y = overlay_geo.top() + (overlay_geo.height() // 2)

        target_pos = cursor_pos
        if mode == 2:
            target_pos = QPoint(cursor_pos.x() + 15, overlay_center_y - (menu_h // 2))
        elif mode == 3:
            pos_y = cursor_pos.y() + 5 if cursor_pos.y() < overlay_center_y else cursor_pos.y() - menu_h - 5
            target_pos = QPoint(cursor_pos.x() + 10, pos_y)

        final_x, final_y = target_pos.x(), target_pos.y()
        if final_x + menu_w > screen_geo.right() - 10: final_x = screen_geo.right() - menu_w - 10
        if final_x < screen_geo.left() + 10: final_x = screen_geo.left() + 10
        if final_y + menu_h > screen_geo.bottom() - 55: final_y = screen_geo.bottom() - menu_h - 55
        if final_y < screen_geo.top() + 15: final_y = screen_geo.top() + 15

        menu.exec(QPoint(final_x, final_y))
