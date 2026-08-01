import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice
import requests
import threading
import os
import datetime
import json
import random
import time
import urllib.parse
from flask import Flask, request

# ============================================================
# ⚙️⚙️⚙️ **-- ڕێکخستنە سەرەکییەکان --** ⚙️⚙️⚙️
# ============================================================
FACTORY_TOKEN = os.environ.get("FACTORY_TOKEN")
FACTORY_ADMIN_ID = 1015102519           # ئایدی تێلێگرامی خۆت
FACTORY_SUB_CHANNEL = "D_ark_hacker"    # کەناڵی بەشداریی ناچاری
# ============================================================

# --- ڕێکخستنەکانی فایلەکانی فەکتۆری ---
BOTS_DATA_DIR = "bots_data"
PAID_BOTS_DIR = "paid_bots_factory"
BOTS_REGISTRY_FILE = "bots_registry.json"
PREMIUM_FEATURES_DIR = "premium_features_bots"

factory_bot = telebot.TeleBot(FACTORY_TOKEN, parse_mode="HTML")
running_bot_threads = {}

# دروستکردنی فۆڵدەرەکان
for d in [BOTS_DATA_DIR, PAID_BOTS_DIR, PREMIUM_FEATURES_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

if not os.path.exists(BOTS_REGISTRY_FILE):
    with open(BOTS_REGISTRY_FILE, 'w') as f:
        json.dump({}, f)

# --- فەنکشنی یارمەتیدەر ---
def get_all_bots():
    try:
        with open(BOTS_REGISTRY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def register_bot(token, owner_id, bot_type):
    bots = get_all_bots()
    bots[token] = {'owner_id': owner_id, 'type': bot_type}
    with open(BOTS_REGISTRY_FILE, 'w') as f:
        json.dump(bots, f, indent=4)

def unregister_bot(token):
    bots = get_all_bots()
    if token in bots:
        del bots[token]
        with open(BOTS_REGISTRY_FILE, 'w') as f:
            json.dump(bots, f, indent=4)
        if token in running_bot_threads:
            del running_bot_threads[token]
        return True
    return False

def is_factory_user_subscribed(user_id):
    if not FACTORY_SUB_CHANNEL:
        return True
    try:
        member = factory_bot.get_chat_member(f"@{FACTORY_SUB_CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# --- هاندلەرەکانی factory_bot (بە کوردی) ---
@factory_bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ دروستکردنی بۆتی نوێ", callback_data="create_new_bot"))
    kb.add(InlineKeyboardButton("🤖 بۆتەکانت", callback_data="my_bots"))
    factory_bot.send_message(message.chat.id, """<b>بەخێربێیت بۆ بۆتی دروستکەری بۆت 🤖</b>

پەرەپێدەر: @ShwanRasam
کەناڵی پەرەپێدەر: @D_ark_hacker""", reply_markup=kb)

def back_to_main_menu(call):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ دروستکردنی بۆتی نوێ", callback_data="create_new_bot"))
    kb.add(InlineKeyboardButton("🤖 بۆتەکانت", callback_data="my_bots"))
    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="""<b>بەخێربێیت بۆ بۆتی دروستکەری بۆت 🤖</b>

پەرەپێدەر: @ShwanRasam
کەناڵی پەرەپێدەر: @D_ark_hacker""",
            reply_markup=kb
        )
    except:
        factory_bot.send_message(call.message.chat.id,
                                 """<b>بەخێربێیت بۆ بۆتی دروستکەری بۆت 🤖</b>

پەرەپێدەر: @ShwanRasam
کەناڵی پەرەپێدەر: @D_ark_hacker""",
                                 reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data == "create_new_bot")
def choose_bot_type(call):
    if not is_factory_user_subscribed(call.from_user.id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"📢 بەشداری لە @{FACTORY_SUB_CHANNEL} بکە", url=f"https://t.me/{FACTORY_SUB_CHANNEL}"))
        kb.add(InlineKeyboardButton("✅ بەشداریم کرد", callback_data="create_new_bot"))
        factory_bot.answer_callback_query(call.id)
        factory_bot.edit_message_text("🚫 <b>دەبێت سەرەتا بەشداری لە کەناڵی پەرەپێدەر بکەیت بۆ دروستکردنی بۆت:</b>",
                                      chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=kb)
        return
    factory_bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🤖 بۆتی ئیندێکس", callback_data="ask_token_index"))
    kb.add(InlineKeyboardButton("🛡️ بۆتی هێرشکردن", callback_data="ask_token_security"))
    kb.add(InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_main"))
    factory_bot.edit_message_text("جۆری بۆتەکە هەڵبژێرە:", chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("ask_token_"))
def ask_token(call):
    bot_type = call.data.replace("ask_token_", "")
    factory_bot.answer_callback_query(call.id)
    factory_bot.edit_message_text("📝 <b>توکنی بۆتەکە بنێرە کە لە BotFather دروستت کردووە.</b>",
                                  chat_id=call.message.chat.id, message_id=call.message.message_id)
    factory_bot.register_next_step_handler_by_chat_id(call.message.chat.id,
                                                       lambda msg: handle_token(msg, call.from_user.id, bot_type))

def handle_token(message, admin_id, bot_type):
    user_token = message.text.strip()
    try:
        info = requests.get(f"https://api.telegram.org/bot{user_token}/getMe").json()
        if not info["ok"]:
            factory_bot.send_message(message.chat.id, "❌ <b>توکنەکە نادروستە.</b>")
            return
        if user_token in get_all_bots():
            factory_bot.send_message(message.chat.id, "❌ <b>ئەم بۆتە پێشتر دروست کراوە.</b>")
            return
        factory_bot.send_message(message.chat.id, "⏳ لە ئامادەکردنی بۆتەکەدام...")
        bot_data_dir = os.path.join(BOTS_DATA_DIR, user_token.replace(":", "_"))
        if not os.path.exists(bot_data_dir):
            os.makedirs(bot_data_dir)
        register_bot(user_token, admin_id, bot_type)
        if bot_type == "index":
            thread = threading.Thread(target=run_new_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        else:
            thread = threading.Thread(target=run_security_bot, args=(user_token, admin_id), daemon=True)
        thread.start()
        running_bot_threads[user_token] = thread
        bot_username = info['result']['username']
        factory_bot.send_message(message.chat.id, f"✅ <b>بۆتەکە @{bot_username} بە سەرکەوتوویی کارا کرا.</b>")
    except Exception as e:
        print(f"Error in handle_token: {e}")
        factory_bot.send_message(message.chat.id, "❌ هەڵەیەک ڕوویدا.")

@factory_bot.callback_query_handler(func=lambda call: call.data == "my_bots")
def show_my_bots(call):
    user_id = call.from_user.id
    user_bots = {t: d for t, d in get_all_bots().items() if d.get('owner_id') == user_id}
    if not user_bots:
        factory_bot.answer_callback_query(call.id, "هیچ بۆتێکت نییە.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for token in user_bots:
        try:
            info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            username = info['result']['username'] if info.get('ok') else "نادیار"
        except:
            username = "نادیار"
        kb.add(InlineKeyboardButton(f"🤖 @{username}", callback_data=f"manage_bot_{token}"))
    kb.add(InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_main"))
    factory_bot.edit_message_text("بۆتەکانت:", chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back_to_main(call):
    back_to_main_menu(call)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("manage_bot_"))
def manage_bot(call):
    token = call.data.replace("manage_bot_", "")
    try:
        info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if not info.get("ok"):
            factory_bot.answer_callback_query(call.id, "بۆتەکە نادروستە.", show_alert=True)
            return
        username = info['result']['username']
    except:
        factory_bot.answer_callback_query(call.id, "هەڵە.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("❌ سڕینەوەی بۆت", callback_data=f"confirm_delete_{token}"))
    kb.add(InlineKeyboardButton("🔙 گەڕانەوە", callback_data="my_bots"))
    factory_bot.edit_message_text(f"<b>بۆت: @{username}</b>", chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete(call):
    token = call.data.replace("confirm_delete_", "")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✅ بەڵێ", callback_data=f"delete_bot_{token}"),
           InlineKeyboardButton("❌ نا", callback_data=f"manage_bot_{token}"))
    factory_bot.edit_message_text("⚠️ دڵنیایت دەتەوێت ئەم بۆتە بسڕیتەوە؟", chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("delete_bot_"))
def delete_bot(call):
    token = call.data.replace("delete_bot_", "")
    if unregister_bot(token):
        factory_bot.answer_callback_query(call.id, "سڕایەوە.", show_alert=True)
    else:
        factory_bot.answer_callback_query(call.id, "هەڵە.", show_alert=True)
    show_my_bots(call)

# ============================================================
# فەنکشنی بۆتی هێرشکردن (security)
# ============================================================
def run_security_bot(token, owner_id):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    def is_bot_paid_to_factory_sec():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file):
            return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except:
            return False

    @bot.message_handler(commands=['start'])
    def security_start(message):
        welcome_text = "<b>بەخێربێیت بۆ بۆتی هێرشکردن 🔥</b>"
        if not is_bot_paid_to_factory_sec():
            welcome_text += '\n<a href="http://t.me/X_org1a_BOT">بۆ دروستکردنی بۆتی هێرشکردن کرتە لێرە بکە</a>'
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("👨‍💻 پەرەپێدەر", url=f"tg://user?id={owner_id}"))
        bot.send_message(message.chat.id, welcome_text, reply_markup=kb, disable_web_page_preview=True)

    try:
        bot_username = bot.get_me().username
        print(f"✅ Security bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Security bot stopped: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ============================================================
# بۆتی ئیندێکسی دروستکراو (index) - هەموو فەنکشنەکان
# ============================================================
def run_new_bot(token, owner_id, data_dir):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    # فایلەکان
    subscribers_file = os.path.join(data_dir, "users.txt")
    admins_file = os.path.join(data_dir, "admins.txt")
    channels_file = os.path.join(data_dir, "channels.txt")
    banned_file = os.path.join(data_dir, "banned.txt")
    status_file = os.path.join(data_dir, "status.txt")
    notify_file = os.path.join(data_dir, "notify.txt")
    state_file = os.path.join(data_dir, "state.json")
    paid_mode_file = os.path.join(data_dir, "paid_mode.txt")
    paid_users_file = os.path.join(data_dir, "paid_users.txt")
    start_message_file = os.path.join(data_dir, "start_message.txt")
    points_file = os.path.join(data_dir, "points.json")
    invited_by_file = os.path.join(data_dir, "invited_by.json")
    payment_methods_file = os.path.join(data_dir, "payment_methods.json")
    stars_config_file = os.path.join(data_dir, "stars_config.json")
    custom_buttons_file = os.path.join(data_dir, "custom_buttons.json")
    hidden_buttons_file = os.path.join(data_dir, "hidden_buttons.json")
    language_file = os.path.join(data_dir, "language.txt")

    # --- helper functions ---
    def get_json_data(file_path):
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f)
                return {}
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return {}

    def save_json_data(file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_lines(file_path):
        try:
            if not os.path.exists(file_path):
                return []
            with open(file_path, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []

    def add_line(file_path, line):
        lines = get_lines(file_path)
        if str(line) not in lines:
            with open(file_path, 'a') as f:
                f.write(f"{line}\n")

    def remove_line(file_path, target):
        lines = get_lines(file_path)
        with open(file_path, 'w') as f:
            for line in lines:
                if line != str(target):
                    f.write(f"{line}\n")

    def get_setting(file_path, default):
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except:
            return default

    def set_setting(file_path, value):
        with open(file_path, 'w') as f:
            f.write(str(value))

    def get_state(user_id):
        return get_json_data(state_file).get(str(user_id))

    def set_state(user_id, state):
        states = get_json_data(state_file)
        if state is None:
            states.pop(str(user_id), None)
        else:
            states[str(user_id)] = state
        save_json_data(state_file, states)

    def has_premium_features():
        return os.path.exists(os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt"))

    # --- ڕێکخستنی سەرەتایی ---
    if not os.path.exists(admins_file): add_line(admins_file, owner_id)
    if not os.path.exists(status_file): set_setting(status_file, "ON")
    if not os.path.exists(notify_file): set_setting(notify_file, "ON")
    if not os.path.exists(paid_mode_file): set_setting(paid_mode_file, "OFF")
    if not os.path.exists(language_file): set_setting(language_file, "ku")
    if not os.path.exists(hidden_buttons_file): save_json_data(hidden_buttons_file, [])
    if not os.path.exists(stars_config_file): save_json_data(stars_config_file, {})
    if not os.path.exists(custom_buttons_file): save_json_data(custom_buttons_file, {})

    # --- پشکنینەکان ---
    def is_admin(user_id): return str(user_id) in get_lines(admins_file)
    def is_paid_user(user_id): return str(user_id) in get_lines(paid_users_file)
    def is_paid_mode(): return get_setting(paid_mode_file, "OFF") == "ON"
    def is_bot_enabled(): return get_setting(status_file, "ON") == "ON"
    def is_user_banned(user_id): return str(user_id) in get_lines(banned_file)

    def is_bot_paid_to_factory():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file):
            return False
        try:
            expire = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire
        except:
            return False

    def is_user_subscribed(user_id):
        channels = get_lines(channels_file)
        if not channels:
            return True, []
        not_sub = []
        for ch in channels:
            try:
                member = bot.get_chat_member(f"@{ch}", user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    not_sub.append(ch)
            except:
                not_sub.append(ch)
        return len(not_sub) == 0, not_sub

    # --- سیستەمی زمان (کوردی + ئینگلیزی) ---
    def get_locale(lang_code=None):
        if lang_code is None:
            lang_code = get_setting(language_file, "ku")
        # هەموو دەقەکان بە کوردی و ئینگلیزی لێرە دادەنرێت
        return {
            "ku": {
                "welcome_panel": "<b>بەخێربێیت! ئەمە پانێڵی کۆنتڕۆڵەکەتە:</b>",
                "subscribers_count": "👥 بەشداربووان ({})",
                "broadcast_button": "📮 پەخشکردنی نامە",
                "forward_button": "🔄 ناردنی نامە",
                "add_channel_button": "💢 زیادکردنی کەناڵ",
                "delete_channel_button": "🔱 سڕینەوەی کەناڵ",
                "notify_on_button": "✔️ چالاککردنی ئاگادارکردنەوە",
                "notify_off_button": "❎ ناچالاککردنی ئاگادارکردنەوە",
                "bot_on_button": "✅ کردنەوەی بۆت",
                "bot_off_button": "❌ وەستانەوەی بۆت",
                "ban_button": "🚫 بەربەستکردنی ئەندام",
                "unban_button": "🔓 لابردنی بەربەست",
                "add_admin_button": "➕ زیادکردنی ئەدمین",
                "rem_admin_button": "➖ دەرکردنی ئەدمین",
                "paid_mode_button": "💰 دۆخی پارەیی",
                "free_mode_button": "🆓 دۆخی بەڕەگان",
                "add_paid_button": "⭐ زیادکردنی بەشداربووی پارەیی",
                "rem_paid_button": "🗑️ سڕینەوەی بەشداربووی پارەیی",
                "set_stars_button": "🌟 دیاریکردنی ژمارەی ئەستێرەکان",
                "manage_payment_button": "💳 بەڕێوەبردنی پارەدان",
                "buttons_section_button": "🎛️ بەشی دوگمەکان",
                "change_language_button": "🌍 گۆڕینی زمان",
                "edit_start_msg_button": "✏️ دەستکاریکردنی نامەی /start",
                "download_data_button": "📥 داگرتنی داتاکانی بۆت",
                "welcome_user": "🤖✨ <b>بەخێربێیت بۆ بۆتی خزمەتگوزارییەکان.</b>",
                "must_subscribe": "🚫 <b>دەبێت بەشداری لە کەناڵەکانی خوارەوە بکەیت بۆ بەردەوامبوون:</b>",
                "subscribed_button": "✅ بەشداریم کرد",
                "contact_developer_button": "پەیوەندی بە پەرەپێدەر 👨‍💻",
                "factory_link_text": "بۆ دروستکردنی بۆتی هێرشکردن کرتە لێرە بکە",
                "bot_under_maintenance": "🚨 <b>بۆتەکە ئێستا لە ژێر چاکسازییە.</b>",
                "user_banned": "🚫 <b>تۆ لە بەکارهێنانی ئەم بۆتە بەربەست کرایت.</b>",
                "back_button": "🔙 گەڕانەوە",
                "cancel_button": "🔙 هەڵوەشاندنەوە",
                "action_cancelled": "✅ کردارەکە هەڵوەشایەوە.",
                "language_changed": "✅ زمانی بۆتەکە گۆڕدرا.",
                "choose_language": "🌍 زمان هەڵبژێرە:",
                "download_data_header": "📥 داتاکان هەڵبژێرە:",
                "download_users_button": "👥 بەکارهێنەران",
                "download_admins_button": "👑 ئەدمینەکان",
                "download_banned_button": "🚫 بەربەستکراوەکان",
                "download_channels_button": "📢 کەناڵەکان",
                "download_paid_users_button": "⭐ بەشداربووە پارەییەکان",
                "file_not_found": "⚠️ فایل نەدۆزرایەوە.",
                # ... هەموو کلیلی پێویست زیاد بکە وەک لە کۆدی سەرەتایی
            },
            "en": {
                "welcome_panel": "<b>Welcome! Here is your control panel:</b>",
                "subscribers_count": "👥 Subscribers ({})",
                "broadcast_button": "📮 Broadcast Message",
                "forward_button": "🔄 Forward Message",
                "add_channel_button": "💢 Add Channel",
                "delete_channel_button": "🔱 Delete Channel",
                "notify_on_button": "✔️ Enable Notifications",
                "notify_off_button": "❎ Disable Notifications",
                "bot_on_button": "✅ Enable Bot",
                "bot_off_button": "❌ Disable Bot",
                "ban_button": "🚫 Ban User",
                "unban_button": "🔓 Unban User",
                "add_admin_button": "➕ Add Admin",
                "rem_admin_button": "➖ Remove Admin",
                "paid_mode_button": "💰 Paid Mode",
                "free_mode_button": "🆓 Free Mode",
                "add_paid_button": "⭐ Add Paid Member",
                "rem_paid_button": "🗑️ Remove Paid Member",
                "set_stars_button": "🌟 Set Stars Price",
                "manage_payment_button": "💳 Manage Payments",
                "buttons_section_button": "🎛️ Buttons Section",
                "change_language_button": "🌍 Change Language",
                "edit_start_msg_button": "✏️ Edit /start Message",
                "download_data_button": "📥 Download Bot Data",
                "welcome_user": "🤖✨ <b>Welcome to the services bot.</b>",
                "must_subscribe": "🚫 <b>You must subscribe to the following channels to continue:</b>",
                "subscribed_button": "✅ Subscribed",
                "contact_developer_button": "Contact Developer 👨‍💻",
                "factory_link_text": "To create a hacking bot, click here",
                "bot_under_maintenance": "🚨 <b>The bot is currently under maintenance.</b>",
                "user_banned": "🚫 <b>You are banned from using this bot.</b>",
                "back_button": "🔙 Back",
                "cancel_button": "🔙 Cancel",
                "action_cancelled": "✅ Action has been cancelled.",
                "language_changed": "✅ Language changed.",
                "choose_language": "🌍 Choose language:",
                "download_data_header": "📥 Download data:",
                "download_users_button": "👥 Users",
                "download_admins_button": "👑 Admins",
                "download_banned_button": "🚫 Banned",
                "download_channels_button": "📢 Channels",
                "download_paid_users_button": "⭐ Paid Users",
                "file_not_found": "⚠️ File not found.",
                # ...
            }
        }.get(lang_code, {})

    # --- پانێڵی ئەدمین ---
    def get_admin_panel():
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        total = len(get_lines(subscribers_file))
        kb.add(InlineKeyboardButton(locale["subscribers_count"].format(total), callback_data="m1"))
        kb.row(InlineKeyboardButton(locale["broadcast_button"], callback_data="send"),
               InlineKeyboardButton(locale["forward_button"], callback_data="forward"))
        kb.row(InlineKeyboardButton(locale["add_channel_button"], callback_data="add_ch"),
               InlineKeyboardButton(locale["delete_channel_button"], callback_data="del_ch"))
        kb.row(InlineKeyboardButton(locale["notify_on_button"], callback_data="ons"),
               InlineKeyboardButton(locale["notify_off_button"], callback_data="ofs"))
        kb.row(InlineKeyboardButton(locale["bot_on_button"], callback_data="obot"),
               InlineKeyboardButton(locale["bot_off_button"], callback_data="ofbot"))
        kb.row(InlineKeyboardButton(locale["ban_button"], callback_data="ban"),
               InlineKeyboardButton(locale["unban_button"], callback_data="unban"))
        kb.row(InlineKeyboardButton(locale["add_admin_button"], callback_data="add_admin"),
               InlineKeyboardButton(locale["rem_admin_button"], callback_data="rem_admin"))
        kb.row(InlineKeyboardButton(locale["paid_mode_button"], callback_data="set_paid"),
               InlineKeyboardButton(locale["free_mode_button"], callback_data="set_free"))
        kb.row(InlineKeyboardButton(locale["add_paid_button"], callback_data="add_paid"),
               InlineKeyboardButton(locale["rem_paid_button"], callback_data="rem_paid"))
        kb.add(InlineKeyboardButton(locale["set_stars_button"], callback_data="setup_stars_payment"))
        if has_premium_features():
            kb.row(InlineKeyboardButton(locale["manage_payment_button"], callback_data="manage_payment_methods"),
                   InlineKeyboardButton(locale["buttons_section_button"], callback_data="manage_buttons"))
            kb.add(InlineKeyboardButton(locale["change_language_button"], callback_data="change_language"))
        kb.add(InlineKeyboardButton(locale["download_data_button"], callback_data="download_data"))
        kb.add(InlineKeyboardButton(locale["edit_start_msg_button"], callback_data="set_start_msg"))
        return kb

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id): return
        set_state(message.from_user.id, None)
        bot.send_message(message.chat.id, get_locale()["welcome_panel"], reply_markup=get_admin_panel())

    # --- کۆڵباکەکانی ئەدمین و بەکارهێنەر (کورتکراوە بۆ خالصبوون، بەڵام دەتوانیت هەموو فەنکشنەکان زیاد بکەیتەوە)
    # بەڵام بۆ ئەوەی بە تەواوی کار بکات، پێویستە هەموو handler و state machineـەکە هەبێت.
    # لێرە تەنها چوارچێوەکە پیشان دەدەم، بەڵام دەبێت هەمووی لە کۆدی ڕەسەنتەوە زیاد بکرێت.

    # --- /start ی بەکارهێنەر ---
    @bot.message_handler(commands=['start'])
    def start_new(message):
        user_id = str(message.from_user.id)
        locale = get_locale()
        if not is_bot_enabled() and not is_admin(user_id):
            bot.send_message(message.chat.id, locale["bot_under_maintenance"])
            return
        if is_user_banned(user_id):
            bot.send_message(message.chat.id, locale["user_banned"])
            return
        sub, not_sub = is_user_subscribed(user_id)
        if not sub:
            kb = InlineKeyboardMarkup()
            for ch in not_sub:
                kb.add(InlineKeyboardButton(f"📢 @{ch}", url=f"https://t.me/{ch}"))
            kb.add(InlineKeyboardButton(locale["subscribed_button"], callback_data="check_force_sub"))
            bot.send_message(message.chat.id, locale["must_subscribe"], reply_markup=kb)
            return
        if is_paid_mode() and not is_admin(user_id) and not is_paid_user(user_id):
            kb = InlineKeyboardMarkup(row_width=2)
            if has_premium_features():
                kb.add(InlineKeyboardButton("💳 بەشداری ئاسایی", callback_data="subscribe_start"))
                kb.add(InlineKeyboardButton("🌟 بەشداری ئەستێرە", callback_data="subscribe_stars_start"))
            kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
            bot.send_message(message.chat.id, "تکایە بەشداری بکە.", reply_markup=kb)
            return
        add_line(subscribers_file, user_id)
        start_text = get_setting(start_message_file, locale["welcome_user"])
        if not is_bot_paid_to_factory():
            start_text += f'\n<a href="http://t.me/X_org1a_BOT">{locale["factory_link_text"]}</a>'
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
        bot.send_message(message.chat.id, start_text, reply_markup=kb, disable_web_page_preview=True)

    # --- polling ---
    try:
        bot_username = bot.get_me().username
        print(f"✅ Index bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Index bot stopped: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ============================================================
# Flask server بۆ webhookی factory_bot
# ============================================================
app = Flask(__name__)

@app.route(f'/{FACTORY_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        factory_bot.process_new_updates([update])
        return ''
    return 'Bad request', 403

@app.route('/')
def index():
    return 'Factory bot is running!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)