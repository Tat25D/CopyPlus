class StringTrimmer:
    """Движок сокращений. Работает ТОЛЬКО если включена галочка 'Кратко'."""

    @staticmethod
    def apply_shortning(text: str, from_start: str, from_end: str, is_phrase: bool = True) -> str:
        if not text or not isinstance(text, str):
            return text

        # Парсим значения один раз
        s_start = str(from_start).strip()
        s_end = str(from_end).strip()
        val_start = int(s_start) if s_start.isdigit() else 7
        val_end = int(s_end) if s_end.isdigit() else 4

        # ══════════════════════════════════════════
        # Режим "ФРАЗА" (is_phrase=True)
        # Берём ВЕСЬ текст кнопки целиком, НЕ разделяя
        # ══════════════════════════════════════════
        if is_phrase:
            # Защита от слишком коротких строк (срезы не должны перекрываться)
            if len(text) <= val_start + val_end:
                return text

            start_part = text[:val_start] if val_start > 0 else ""
            end_part = text[-val_end:] if val_end > 0 else ""
            return f"{start_part}-{end_part}"

        # ══════════════════════════════════════════
        # Режим "СЛОВО" (is_phrase=False)
        # Разбиваем по пробелам, каждое длинное слово сокращаем
        # ══════════════════════════════════════════
        else:
            limit = val_start + val_end + 1
            words = text.split(" ")
            processed = []

            for word in words:
                # Пустые элементы (от двойных пробелов) — не трогаем
                if not word:
                    processed.append(word)
                    continue

                # Короткое слово — оставляем целиком
                if len(word) <= limit:
                    processed.append(word)
                else:
                    # Длинное слово — сокращаем
                    start_part = word[:val_start] if val_start > 0 else ""
                    end_part = word[-val_end:] if val_end > 0 else ""
                    processed.append(f"{start_part}-{end_part}")

            # ✅ ИСПРАВЛЕНО: объединяем через пробел (было "".join — без пробелов)
            return " ".join(processed)
