import os
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

TOKEN = os.getenv("TOKEN", "8642369502:AAGw-RQbZGIdSJ6WmfBKNGOrF-jcLnGJZqU")
GROUP_ID = -5191459591

# States
CHOOSE_TYPE, CHOOSE_BRANCH, CHOOSE_ACTION, WRITE_MESSAGE = range(4)

# Guruhdagi message_id → user_id map
user_messages = {}

# ─── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🏫 Maktab", callback_data="type_maktab"),
            InlineKeyboardButton("🏡 Bog'cha", callback_data="type_bogcha"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Assalomu alaykum!\n\n"
        "🏫 *MUDARRIR Xalqaro Maktabi*\n"
        "📩 Shikoyat va Taklif Botiga xush kelibsiz!\n\n"
        "Iltimos, murojaat turini tanlang:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )
    return CHOOSE_TYPE


# ─── Maktab / Bog'cha tanlash ─────────────────────────────────────────────────
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # type_maktab | type_bogcha
    context.user_data["type"] = "Maktab" if data == "type_maktab" else "Bog'cha"

    if data == "type_maktab":
        keyboard = [
            [InlineKeyboardButton("🏫 Sergeli Maktab",  callback_data="branch_sergeli_maktab")],
            [InlineKeyboardButton("🏫 Qo'yliq Maktab",  callback_data="branch_qoyliq_maktab")],
            [InlineKeyboardButton("🏫 Qa'ni Maktab",    callback_data="branch_qani_maktab")],
        ]
        text = "Qaysi maktabni tanlaysiz?"
    else:
        keyboard = [
            [InlineKeyboardButton("🏡 Sergeli Bog'cha", callback_data="branch_sergeli_bogcha")],
            [InlineKeyboardButton("🏡 Qo'yliq Bog'cha", callback_data="branch_qoyliq_bogcha")],
            [InlineKeyboardButton("🏡 Qa'ni Bog'cha",   callback_data="branch_qani_bogcha")],
        ]
        text = "Qaysi bog'chani tanlaysiz?"

    await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_BRANCH


# ─── Filial tanlash ───────────────────────────────────────────────────────────
BRANCH_NAMES = {
    "branch_sergeli_maktab":  "Sergeli Maktab",
    "branch_qoyliq_maktab":   "Qo'yliq Maktab",
    "branch_qani_maktab":     "Qa'ni Maktab",
    "branch_sergeli_bogcha":  "Sergeli Bog'cha",
    "branch_qoyliq_bogcha":   "Qo'yliq Bog'cha",
    "branch_qani_bogcha":     "Qa'ni Bog'cha",
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
        text=f"✅ *{context.user_data['branch']}* tanlandi.\n\nMurojaat turini tanlang:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return CHOOSE_ACTION


# ─── Shikoyat / Taklif tanlash ────────────────────────────────────────────────
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = "Shikoyat" if query.data == "action_shikoyat" else "Taklif"
    context.user_data["action"] = action

    emoji = "📢" if action == "Shikoyat" else "💡"
    await query.edit_message_text(
        text=f"{emoji} *{action}* tanlandi.\n\n"
             f"Iltimos, *{context.user_data['branch']}* bo'yicha {action.lower()}ingizni yozing:",
        parse_mode="Markdown",
    )
    return WRITE_MESSAGE


# ─── Xabarni qabul qilish ─────────────────────────────────────────────────────
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    branch = context.user_data.get("branch", "Noma'lum")
    action = context.user_data.get("action", "Noma'lum")
    inst_type = context.user_data.get("type", "Noma'lum")

    username = f"@{user.username}" if user.username else "Yo'q"

    group_message = (
        f"📩 *Yangi {action}*\n\n"
        f"🏫 Tur: {inst_type}\n"
        f"📍 Filial: {branch}\n"
        f"📂 Murojaat turi: {action}\n\n"
        f"👤 Ism: {user.first_name} {user.last_name or ''}\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Username: {username}\n\n"
        f"📝 Matn:\n{text}"
    )

    sent = await context.bot.send_message(
        chat_id=GROUP_ID,
        text=group_message,
        parse_mode="Markdown",
    )
    user_messages[sent.message_id] = user.id

    await update.message.reply_text(
        "✅ *Arizangiz qabul qilindi!*\n\n"
        "⏳ Tez orada ko'rib chiqiladi.\n\n"
        "Yana murojaat qilmoqchi bo'lsangiz /start bosing.",
        parse_mode="Markdown",
    )

    # Reset state
    context.user_data.clear()
    return ConversationHandler.END


# ─── Keyingi xabar (conversation tugagandan keyin) ────────────────────────────
async def handle_extra_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Conversation tugagandan keyin user yana xabar yozsa"""
    await update.message.reply_text(
        "✅ *Murojaatingiz qabul qilindi!*\n\n"
        "Yangi murojaat uchun /start bosing.",
        parse_mode="Markdown",
    )


# ─── Admin guruhda reply ──────────────────────────────────────────────────────
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

    admin = update.message.from_user
    await context.bot.send_message(
        chat_id=user_id,
        text=f"📬 *Admindan javob:*\n\n{reply_text}",
        parse_mode="Markdown",
    )


# ─── Cancel ───────────────────────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi. Qaytadan boshlash uchun /start bosing.")
    return ConversationHandler.END


# ─── App ──────────────────────────────────────────────────────────────────────
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
)

app.add_handler(conv_handler)
app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_extra_message))
app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, handle_group_reply))

app.run_polling()
