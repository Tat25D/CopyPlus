class CaseFormatter:
    def __init__(self):
        # 0: Без изменений, 1: со строчной, 2: С заглавной, 3: ВСЕ ЗАГЛАВНЫЕ
        self.mode = 0

    def next_mode(self):
        self.mode = (self.mode + 1) % 4

    def reset(self):
        self.mode = 0

    def get_mode_text(self):
        if self.mode == 0: return "Без изменений"
        if self.mode == 1: return "со строчной"
        if self.mode == 2: return "С заглавной"
        if self.mode == 3: return "ВСЕ ЗАГЛАВНЫЕ"
        return "Без изменений"

    def apply(self, text, force_first_capital=False):
        """Применяет выбранный регистр к тексту без повреждения аббревиатур"""
        if not text: return ""

        # 1. Сначала применяем режим кнопки "Без изменений"
        if self.mode == 0:
            res = text
        elif self.mode == 1:
            res = text[0].lower() + text[1:] if len(text) > 1 else text.lower()
        elif self.mode == 2:
            res = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        elif self.mode == 3:
            res = text.upper()
        else:
            res = text

        # 2. ЗАТЕМ: Если стоит галочка "Первая заглавная", принудительно делаем первую букву большой
        # Это перекрывает даже режим "со строчной"
        if force_first_capital and res:
            res = res[0].upper() + res[1:]

        return res
