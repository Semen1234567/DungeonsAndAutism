import re
import asyncio, os, logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, CallbackQuery
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)


from state.game_state import get_room, langs, rooms, Player
from core.generate import generate_response
from utils.helpers import tr
from utils.safe_send import safe_send, escape_html
from config.prompts import prompt_by
from db import get_db, init_db, get_player

load_dotenv("D:\DungeonsAndAutism\.env")
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEFAULT_MODE = "fantasy"
DEFAULT_LANG = "ru"
MAX_TURNS = 40
ASK_NICK = 1

#-------------- Валидация -------------------
def clean_model_output(text: str) -> str:
    text = re.sub(
        r"(Сценарист|Раунд|Инструкция|Пример|Prompt|Player|Response|Assistant|Игрок|Ответ):?.*",
        "", text, flags=re.IGNORECASE
    )
    text = re.sub(r"\*{1,3}.+?\*{1,3}", "", text)  # markdown bold
    return text.strip()

def is_valid_scene(text: str) -> bool:
    bad_patterns = ["распиши", "пример", "сценарист", "инструкция", "напиши", "как", "describe"]
    if len(text.strip()) < 40:
        return False
    return not any(p in text.lower() for p in bad_patterns)
# ───────────── Команды ─────────────
async def startgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    langs.setdefault(cid, DEFAULT_LANG)
    rooms[cid] = get_room(cid)
    rooms[cid].admin = update.effective_user.id
    await update.message.reply_text(tr(cid, "start"), reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Mode", callback_data="quick_mode"),
         InlineKeyboardButton("🌐 Lang", callback_data="quick_lang")]
    ]))

async def join_start(update: Update, context):
    await update.message.reply_text("🖋 Введите ваш игровой ник:")
    return ASK_NICK

async def join_nick(update: Update, context):
    cid, uid = update.effective_chat.id, update.effective_user.id
    room = get_room(cid)
    if uid in room.players:
        await update.message.reply_text(tr(cid, "already"))
        return ConversationHandler.END
    nick = update.message.text.strip()[:32]
    room.players[uid] = Player(uid, update.effective_user.first_name, nick)
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO players (user_id, chat_id, nick)
            VALUES (?, ?, ?)
        """, (uid, cid, nick))
    await update.message.reply_text(tr(cid, "joined", name=nick))
    return ConversationHandler.END

async def move(update: Update, context):
    cid, uid = update.effective_chat.id, update.effective_user.id
    room = get_room(cid)
    if uid not in room.players:
        await update.message.reply_text(tr(cid, "need_join"))
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(tr(cid, "format"))
        return
    room.actions[uid] = parts[1].strip()
    await update.message.reply_text(tr(cid, "recorded"))

    pending = [p.nick for p in room.players.values() if p.id not in room.actions]
    if pending:
        await context.bot.send_message(cid, tr(cid, "waiting", names=", ".join(pending)))
    else:
        await narrate(cid, context)

async def stats(update: Update, context):
    from db import get_player
    uid, cid = update.effective_user.id, update.effective_chat.id
    row = get_player(uid, cid)
    if not row:
        await update.message.reply_text("Вы ещё не присоединились.")
        return
    nick, hp, str_, int_, agi_, alive = row
    text = (
        f"🧝 {nick}\n"
        f"❤️ HP: {hp}\n"
        f"💪 Сила: {str_}\n"
        f"🧠 Интеллект: {int_}\n"
        f"🏃 Ловкость: {agi_}\n"
        f"⚰️ Жив: {'да' if alive else 'нет'}"
    )
    await update.message.reply_text(text)



async def narrate(cid, context):
    room = get_room(cid)

    # 1. Формируем блок действий игроков
    lines = []
    for uid, text in room.actions.items():
        player_data = get_player(uid, cid)
        if player_data:
            nick, hp, str_, int_, agi_, alive = player_data
            if alive:
                lines.append(f"{nick} (HP: {hp}, STR: {str_}, INT: {int_}, AGI: {agi_}): {text}")
            else:
                lines.append(f"{nick} (мертв): не участвует в раунде.")
        else:
            # fallback на случай, если игрок не найден в БД
            lines.append(f"Игрок {uid}: {text}")

    user_block = "\n".join(lines).strip()
    room.chat.append({"role": "user", "content": user_block})

    # 2. Вычисляем лимит токенов
    max_tokens = 250 + len(room.players) * 50

    # 3. Обновляем system_prompt

    room.system_prompt = prompt_by(room.mode, room.lang, tokens=max_tokens)

    # 4. Генерация ответа
    try:
        raw_answer = generate_response(room.chat, room.system_prompt, max_tokens=max_tokens)
    except Exception as e:
        await safe_send(context.bot.send_message, cid, tr(cid, "gen_err", err=str(e)))
        room.actions.clear()
        return

    # 5. Очистка и добавление
    cleaned = clean_model_output(raw_answer)
    if is_valid_scene(cleaned) and cleaned != user_block:
        room.chat.append({"role": "assistant", "content": cleaned})

    html = escape_html(cleaned)
    await safe_send(context.bot.send_message, cid, f"<b>Раунд {room.round}</b>\n{html}", parse_mode="HTML")

    # 6. Сброс и обрезка истории
    room.round += 1
    room.actions.clear()
    if len(room.chat) // 2 > MAX_TURNS:
        room.chat = room.chat[:1] + room.chat[-MAX_TURNS * 2:]


# ───────────── Кнопки ─────────────
async def button_cb(update: Update, context):
    q: CallbackQuery = update.callback_query
    await q.answer()
    cid, data = q.message.chat.id, q.data
    room = get_room(cid)
    user_is_admin = q.from_user.id == room.admin

    if data == "quick_mode":
        await context.bot.send_message(cid, tr(cid, "choose_mode"), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🧙 Fantasy", callback_data="set_fantasy"),
             InlineKeyboardButton("🚀 Sci-Fi", callback_data="set_sci-fi"),
             InlineKeyboardButton("💾 Cyberpunk", callback_data="set_cyberpunk")]
        ]))
        return

    if data == "quick_lang":
        await context.bot.send_message(cid, tr(cid, "choose_lang"), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("English", callback_data="lang_en"),
             InlineKeyboardButton("Русский", callback_data="lang_ru")]
        ]))
        return

    if data.startswith("set_"):
        if not user_is_admin:
            await q.edit_message_text(tr(cid, "only_admin"))
            return
        room.mode = data.split("_", 1)[1]
        from config.prompts import prompt_by
        room.chat = [{"role": "system", "content": prompt_by(room.mode, room.lang)}]
        room.actions.clear()
        room.round = 1
        await q.edit_message_text(tr(cid, "mode_switched", mode=room.mode), parse_mode="Markdown")
        return

    if data.startswith("lang_"):
        lang_code = data.split("_", 1)[1]
        langs[cid] = lang_code
        room.lang = lang_code
        from config.prompts import prompt_by
        room.chat = [{"role": "system", "content": prompt_by(room.mode, lang_code)}]
        await q.edit_message_text(tr(cid, "lang_switched"))

# ───────────── Telegram setup ─────────────
async def set_commands(app):
    from utils.helpers import TEXT
    await app.bot.set_my_commands([
        BotCommand("startgame", TEXT["start"]["ru"]),
        BotCommand("join", TEXT["joined"]["ru"]),
        BotCommand("move", TEXT["recorded"]["ru"]),
    ])

def main():
    logging.basicConfig(level=logging.INFO)
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("startgame", startgame))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("join", join_start)],
        states={ASK_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_nick)]},
        fallbacks=[]
    ))
    app.add_handler(CommandHandler("move", move))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(button_cb))

    asyncio.get_event_loop().run_until_complete(set_commands(app))
    app.run_polling()

if __name__ == "__main__":
    main()
