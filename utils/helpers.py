import re

TEXT = {
    "start": {"en": "📜 New adventure begins! Use /join then /move", "ru": "📜 Новое приключение! /join затем /move"},
    "joined": {"en": "✅ {name} joined.", "ru": "✅ {name} присоединился."},
    "already": {"en": "Already in party", "ru": "Уже в партии"},
    "need_join": {"en": "Use /join first", "ru": "Сначала /join"},
    "format": {"en": "Format: /move action…", "ru": "Формат: /move действие…"},
    "recorded": {"en": "✅ Recorded", "ru": "✅ Записано"},
    "waiting": {"en": "Waiting for: {names}", "ru": "Ожидаем: {names}"},
    "choose_mode": {"en": "Choose setting:", "ru": "Выберите сеттинг:"},
    "only_admin": {"en": "Only game owner can change setting.", "ru": "Только владелец игры может менять сеттинг."},
    "mode_switched": {"en": "Setting → *{mode}*", "ru": "Сеттинг → *{mode}*"},
    "choose_lang": {"en": "Choose language:", "ru": "Выберите язык:"},
    "lang_switched": {"en": "Language switched", "ru": "Язык переключён"},
    "gen_err": {"en": "⚠️ Error: {err}", "ru": "⚠️ Ошибка: {err}"},
    "model_switched": {"en": "✅ Model switched to *{name}*", "ru": "✅ Модель переключена на *{name}*"},
    "unknown_model": {"en": "❗ Unknown model", "ru": "❗ Неизвестная модель"},
}

def tr(cid: int, key: str, **kw) -> str:
    from state.game_state import langs
    lang = langs.get(cid, "ru")
    return TEXT[key][lang].format(**kw)



def is_valid_scene(text: str) -> bool:
    text = text.strip().lower()
    return (
        "промпт" not in text and
        "расскажи" not in text and
        "как описать" not in text and
        "например" not in text and
        len(text) > 40
    )