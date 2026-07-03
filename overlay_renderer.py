from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QHBoxLayout
from PyQt6.QtCore import Qt
from flow_layout import FlowLayout
from string_trimmer import StringTrimmer
from overlay_context_menu_manager import OverlayContextMenuManager

class OverlayRendererLogic:
    def refresh_ui(self):
        if getattr(self, '_is_updating', False):
            return
        self._is_updating = True
        try:
            # 1. Фиксация начальной геометрии
            geom = self.geometry()
            self._original_bottom_y = geom.y() + geom.height()
            self._is_already_visible = self.isVisible() and geom.height() > 30

            # 2. ФИКС RUNTIME ERROR: Создаем или находим постоянный контейнер фраз
            if not hasattr(self, 'phrases_scroll_widget') or self.phrases_scroll_widget is None:
                self.phrases_scroll_widget = QWidget(self)
                self.phrases_scroll_layout = QHBoxLayout(self.phrases_scroll_widget)
                self.phrases_scroll_layout.setContentsMargins(0, 0, 0, 0)
                self.phrases_scroll_layout.setSpacing(0)
                self.words_container_layout.insertWidget(0, self.phrases_scroll_widget)

            # ИСПРАВЛЕНО: Безопасно вычищаем ТОЛЬКО верхние старые кнопки фраз
            while self.phrases_scroll_layout.count():
                child = self.phrases_scroll_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()

            # 3. Чтение параметров интерфейса из оперативной памяти
            cfg = self.storage.load_default_settings() or {}

            # ══════════════════════════════════════════════════
            # [DEBUG] Диагностика состояния галочек и кнопок
            # ══════════════════════════════════════════════════
            dbg_is_short = cfg.get("is_short", False)
            dbg_is_phrase = cfg.get("is_phrase", False)
            dbg_is_rounded = cfg.get("is_rounded", True)
            dbg_from_start = cfg.get("from_start", "7")
            dbg_from_end = cfg.get("from_end", "4")
            print("") # (f"[DEBUG-RENDER] ═══════ refresh_ui() ═══════")
            print("") #(f"[DEBUG-RENDER] is_short={dbg_is_short} | is_phrase={dbg_is_phrase} | is_rounded={dbg_is_rounded}")
            print("") #(f"[DEBUG-RENDER] from_start={dbg_from_start} | from_end={dbg_from_end}")
            print("") #(f"[DEBUG-RENDER] btn_radius={'12px' if dbg_is_rounded else '0px'}")
            # ══════════════════════════════════════════════════

            opacity_val = cfg.get("opacity", 45)
            alpha_float = round(opacity_val / 100.0, 2)
            alpha_hex = hex(int(opacity_val * 2.55))[2:].upper().zfill(2)
            active_dict_id = int(cfg.get("current_dict_id", 1))
            panel_width = cfg.get("panel_width", 350)
            independent_text_color = cfg.get("default_btn_text_color", "#FFFFFF")
            is_short_active = cfg.get("is_short", False)
            from_start_val = cfg.get("from_start", "7")
            from_end_val = cfg.get("from_end", "5")

            # ДОБАВИТЬ:
            font_size_val = cfg.get("overlay_font_size", 13)

            # ДОБАВИТЬ:
            font_family_val = cfg.get("overlay_font_family", "Segoe UI")
            font_size_val = cfg.get("overlay_font_size", 13)

            # ДОБАВИТЬ:
            is_bold = cfg.get("is_bold", False)
            font_weight = "bold" if is_bold else "normal"
            font_family_val = cfg.get("overlay_font_family", "Segoe UI")
            font_size_val = cfg.get("overlay_font_size", 13)

            # 4. Создание чистого, стандартного контейнера фраз
            words_widget = QWidget()
            words_widget.setFixedWidth(panel_width)
            words_widget.setStyleSheet("background: transparent; border: none;")
            words_layout = FlowLayout(words_widget, spacing=5)

            # 5. Генерация кнопок СТРОГО под текущий активный словарь 1-8
            has_buttons = False
            active_phrase_index = 0
            all_phrases = self.storage.load_phrases(only_active=True) or []

            # Сначала считаем точное количество кнопок для идеального 3-точечного градиента
            total_buttons = sum(1 for w in all_phrases if int(w.get("dict_id", 1)) == active_dict_id and w.get("nominative", "").strip())

            for w in all_phrases:
                if int(w.get("dict_id", 1)) != active_dict_id:
                    continue
                nom_text = w.get("nominative", "").strip()
                if not nom_text:
                    continue
                has_buttons = True

                # Кнопка "Без изменений" - абсолютный хозяин. Галочки на неё не влияют.
                # button_display_text = self.formatter.apply(nom_text)

                # Читаем состояние галочки "Слово" (False) или "Фраза" (True)
                # is_phrase_mode = cfg.get("is_phrase", True)

                # ЖЕЛЕЗНОЕ ПРАВИЛО: Алгоритм сокращения работает ТОЛЬКО если включена "Кратко"
                # if is_short_active:
                #     button_display_text = StringTrimmer.apply_shortning(
                #         text=button_display_text,
                #         from_start=str(from_start_val),
                #         from_end=str(from_end_val),
                #         is_phrase=is_phrase_mode
                #     )

                # ПРОВЕРКА НА ALIAS
                raw_alias = w.get("alias", "").strip()
                if raw_alias:
                    # Алиас показываем как есть (пользователь сам указал регистр)
                    button_display_text = f"<<{raw_alias}>>"
                else:
                    # ═══════ НОВАЯ ЛОГИКА РЕГИСТРОВ ═══════
                    if self.formatter.mode == 0:  # Режим "Без изменений"
                        if w.get("is_caps", False):
                            button_display_text = nom_text.upper()
                        elif w.get("is_first_capital", False) and nom_text:
                            button_display_text = nom_text[0].upper() + nom_text[1:]
                        else:
                            button_display_text = nom_text
                    else:
                        # Режимы (со строчной / С заглавной / ВСЕ ЗАГЛАВНЫЕ) - игнорируем галочки слова
                        button_display_text = self.formatter.apply(nom_text)
                    # ═══════════════════════════════════

                    # Логика сокращений (Кратко)
                    is_phrase_mode = cfg.get("is_phrase", True)
                    if is_short_active:
                        button_display_text = StringTrimmer.apply_shortning(
                            text=button_display_text,
                            from_start=str(from_start_val),
                            from_end=str(from_end_val),
                            is_phrase=is_phrase_mode
                        )


                # ═══════ ЛОГИКА ЦВЕТА КНОПКИ ═══════
                theme_palette = cfg.get("current_theme_palette", None)

                # ПРИОРИТЕТ 1: Если пользователь вручную задал цвет этой фразе
                if w.get("is_custom_color", False):
                    hex_color = w.get("color", "#2196F3").lstrip('#')[:6]

                # ПРИОРИТЕТ 2: Иначе рисуем градиент активной темы
                elif theme_palette and isinstance(theme_palette, list) and len(theme_palette) > 0:
                    if total_buttons > 1:
                        min_bound = int(len(theme_palette) * 0.2)
                        max_bound = int(len(theme_palette) * 0.8)
                        scaled_index = min_bound + int((active_phrase_index / (total_buttons - 1)) * (max_bound - min_bound))
                    else:
                        scaled_index = len(theme_palette) // 2
                    hex_color = str(theme_palette[scaled_index]).lstrip('#')[:6]
                    active_phrase_index += 1

                # ПРИОРИТЕТ 3: Фолбэк (если тема не выбрана)
                else:
                    color_data = w.get("color", "#2196F3")
                    hex_color = str(color_data).replace("[", "").replace("]", "").replace("'", "").replace('"', '').strip().lstrip('#')[:6]
                # ═══════════════════════════════════
                if not hex_color or len(hex_color) < 6: hex_color = "2196F3"

                r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                rgba_style = f"background-color: rgba({r}, {g}, {b}, {alpha_float});"

                btn = QPushButton(button_display_text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
                # Динамический радиус углов в зависимости от галочки "Скруглить"
                btn_radius = "12px" if cfg.get("is_rounded", True) else "0px"

                btn.setStyleSheet(f"""
                QPushButton {{
                {rgba_style}
                color: {independent_text_color};
                border: none;
                border-radius: {btn_radius};
                padding: 6px 12px;
                font-family: '{font_family_val}', sans-serif;
                font-size: {font_size_val}px;
                font-weight: {font_weight};
                }}
                QPushButton:hover {{ background-color: rgba({r}, {g}, {b}, 1.0); }}
                """)
                btn.clicked.connect(lambda checked=False, word_data=w: OverlayContextMenuManager.show_menu(
                    parent_widget=self,
                    word_data=word_data,
                    storage_service=self.storage,
                    formatter_service=self.formatter,
                    log_paste_callback=self.log_and_paste
                ))
                words_layout.addWidget(btn)

            words_widget.setLayout(words_layout)

            # Расчет точной многострочной высоты плитки фраз
            real_content_height = 10
            if has_buttons:
                words_layout.activate()
                real_content_height = words_layout.heightForWidth(panel_width)
                if real_content_height <= 15:
                    real_content_height = words_layout.minimumSize().height()
                if real_content_height <= 15:
                    real_content_height = 40
            words_widget.setFixedHeight(real_content_height)

            self.phrases_scroll_layout.addWidget(words_widget)
            self.resize(panel_width, real_content_height + 26 + 16)

            if hasattr(self, 'settings_btn') and self.settings_btn:
                self.settings_btn.setStyleSheet(f"QPushButton {{ background: #444444{alpha_hex}; color: white; border-radius: 6px; }}")
            self.update_mode_button_view()

            if not getattr(self, '_block_reposition', False):
                if hasattr(self, 'reposition_overlay_safely'):
                    self.reposition_overlay_safely()
                elif hasattr(self, 'show_at_cursor'):
                    self.show_at_cursor()

            self.words_container_layout.invalidate()
            self.update()
        finally:
            self._is_updating = False
