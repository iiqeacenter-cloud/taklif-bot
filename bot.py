import os
import html
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN", "8642369502:AAGw-RQbZGIdSJ6WmfBKNGOrF-jcLnGJZqU")
GROUP_ID = -1003982155612

CHOOSE_TYPE, CHOOSE_BRANCH, CHOOSE_ACTION, WRITE_MESSAGE = range(4)
user_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🏫 Maktab", callback_data="type_maktab"),
            InlineKeyboardButton("🏡 Bogcha", callback_data="type_bogcha"),
        ]
    ]
    await update.message.reply_text(
        "Assalomu alaykum!\n\n"
        "MUDARRIR Xalqaro Maktabi\n"
        "Shikoyat va Taklif Botiga xush kelibsiz!\n\n"
        "Murojaat turini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_TYPE

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data["type"] = "Maktab" if data == "type_maktab" else "Bogcha"

    if data == "type_maktab":
        keyboard = [
            [InlineKeyboardButton("🏫 Sergeli Maktab",  callback_data="branch_sergeli_maktab")],
            [InlineKeyboardButton("🏫 Qoyliq Maktab",   callback_data="branch_qoyliq_maktab")],
            [InlineKeyboardButton("🏫 Qani Maktab",     callback_data="branch_qani_maktab")],
        ]
        text = "Qaysi maktabni tanlaysiz?"
    else:
        keyboard = [
            [InlineKeyboardButton("🏡 Sergeli Bogcha",  callback_data="branch_sergeli_bogcha")],
            [InlineKeyboardButton("🏡 Qoyliq Bogcha",   callback_data="branch_qoyliq_bogcha")],
            [InlineKeyboardButton("🏡 Qani Bogcha",     callback_data="branch_qani_bogcha")],
        ]
        text = "Qaysi bogchani tanlaysiz?"

    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BRANCH

BRANCH_NAMES = {
    "branch_sergeli_maktab": "Sergeli Maktab",
    "branch_qoyliq_maktab":  "Qoyliq Maktab",
    "branch_qani_maktab":    "Qani Maktab",
    "branch_sergeli_bogcha": "Sergeli Bogcha",
    "branch_qoyliq_bogcha":  "Qoyliq Bogcha",
    "branch_qani_bogcha":    "Qani Bogcha",
}

async def choose_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["branch"] = BRANCH_NAMES.get(query.data, query.data)

    keyboard = [
        [
            InlineKeyboardButton("📢 Shikoyat", callback_data="action_shikoyat"),
            InlineKeyboardButton("💡 Taklif",   callback_data="action_taklif"),
        ]
    ]
    await query.edit_message_text(
        text=f"{context.user_data['branch']} tanlandi.\n\nMurojaat turini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_ACTION

async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = "Shikoyat" if query.data == "action_shikoyat" else "Taklif"
    context.user_data["action"] = action

    emoji = "📢" if action == "Shikoyat" else "💡"
    await query.edit_message_text(
        text=f"{emoji} {action} tanlandi.\n\n"
             f"{context.user_data['branch']} boyicha {action.lower()}ingizni yozing:",
    )
    return WRITE_MESSAGE

async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    # html.escape — maxsus belgilardan himoya
    text     = html.escape(update.message.text or "")
    branch   = html.escape(context.user_data.get("branch", "Noma'lum"))
    action   = html.escape(context.user_data.get("action", "Noma'lum"))
    inst_type = html.escape(context.user_data.get("type",  "Noma'lum"))
    username = html.escape(f"@{user.username}" if user.username else "Yoq")
    fullname = html.escape(f"{user.first_name or ''} {user.last_name or ''}".strip())

    group_message = (
        f"📩 Yangi {action}\n\n"
        f"Tur: {inst_type}\n"
        f"Filial: {branch}\n"
        f"Murojaat: {action}\n\n"
        f"Ism: {fullname}\n"
        f"ID: {user.id}\n"
        f"Username: {username}\n\n"
        f"Matn:\n{text}"
    )

    logger.info(f"Guruhga yuborish: GROUP_ID={GROUP_ID}")

    try:
        sent = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=group_message,
            parse_mode="HTML",
        )
        user_messages[sent.message_id] = user.id
        logger.info(f"Guruhga yuborildi! message_id={sent.message_id}")

        await update.message.reply_text(
            "✅ Arizangiz qabul qilindi!\n\n"
            "Tez orada korib chiqiladi.\n\n"
            "Yana murojaat uchun /start bosing."
        )

    except Exception as e:
        logger.error(f"XATO guruhga yuborishda: {e}")
        await update.message.reply_text(
            f"Xatolik yuz berdi: {e}\n\nAdmin bilan boglanin."
        )

    context.user_data.clear()
    return ConversationHandler.END

async def handle_extra_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yangi murojaat uchun /start bosing.")

async def handle_group_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.id != GROUP_ID:
        return
    if not update.message or not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id
    if replied_msg_id not in user_messages:
        return

    user_id = user_messages[replied_msg_id]
    reply_text = update.message.text or ""
    if not reply_text.strip():
        return

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Admindan javob:\n\n{reply_text}",
        )
        logger.info(f"User {user_id} ga javob yuborildi.")
    except Exception as e:
        logger.error(f"Userga javob yuborishda xato: {e}")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Bu chatning ID si: {update.effective_chat.id}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi. /start bosing.")
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_TYPE:   [CallbackQueryHandler(choose_type,   pattern="^type_")],
        CHOOSE_BRANCH: [CallbackQueryHandler(choose_branch, pattern="^branch_")],
        CHOOSE_ACTION: [CallbackQueryHandler(choose_action, pattern="^action_")],
        WRITE_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("getid", getid))
app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_extra_message))
app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, handle_group_reply))

logger.info(f"Bot ishga tushdi. GROUP_ID={GROUP_ID}")
app.run_polling(drop_pending_updates=True)
