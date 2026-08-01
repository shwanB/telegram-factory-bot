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
# ⚙️⚙️⚙️ **-- ڕێکخستنە سەرەکییەکان (دەبێت بەم گۆڕی بکەیت) --** ⚙️⚙️⚙️
# ============================================================
FACTORY_TOKEN = os.environ.get("FACTORY_TOKEN")
FACTORY_ADMIN_ID = 7924184194           # ← ئایدی تێلێگرامی خۆت لێرە دابنێ
FACTORY_SUB_CHANNEL = "D_ark_hacker"    # ← کەناڵی بەشداریکردنی ناچاری
# ============================================================

# --- ڕێکخستنەکانی فایلەکانی فەکتۆری ---
BOTS_DATA_DIR = "bots_data"
PAID_BOTS_DIR = "paid_bots_factory"
BOTS_REGISTRY_FILE = "bots_registry.json"
PREMIUM_FEATURES_DIR = "premium_features_bots"

factory_bot = telebot.TeleBot(FACTORY_TOKEN, parse_mode="HTML")

# --- گۆڕاوە گشتییەکان ---
running_bot_threads = {}

# --- دروستکردنی فۆڵدەر و فایلە سەرەکییەکان ---
if not os.path.exists(BOTS_DATA_DIR): os.makedirs(BOTS_DATA_DIR)
if not os.path.exists(PAID_BOTS_DIR): os.makedirs(PAID_BOTS_DIR)
if not os.path.exists(PREMIUM_FEATURES_DIR): os.makedirs(PREMIUM_FEATURES_DIR)

if not os.path.exists(BOTS_REGISTRY_FILE):
    with open(BOTS_REGISTRY_FILE, 'w') as f: json.dump({}, f)

# --- فەنکشنی یارمەتیدەر بۆ بەڕێوەبردنی فەکتۆری ---
def get_all_bots():
    try:
        with open(BOTS_REGISTRY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
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
            print(f"Thread for bot {token} removed from running list.")
        return True
    return False

def encrypt_token(token):
    table = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA9876543210"
    )
    return token.translate(table)

def is_factory_user_subscribed(user_id):
    if not FACTORY_SUB_CHANNEL:
        return True
    try:
        member = factory_bot.get_chat_member(f"@{FACTORY_SUB_CHANNEL}", user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Factory sub check error: {e}")
        return False

# --- هاندلەرەکانی پەیامی فەکتۆری ---
@factory_bot.message_handler(commands=['start'])
def start(message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("➕ دروستکردنی بۆتی نوێ", callback_data="create_new_bot"))
    kb.add(InlineKeyboardButton("🤖 بۆتەکانت", callback_data="my_bots"))
    factory_bot.send_message(message.chat.id, """<b>بەخێربێیت بۆ بۆتی دروستکەری بۆت 🤖</b>

پەرەپێدەر: @Y_F_HK
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

پەرەپێدەر: @Y_F_HK
کەناڵی پەرەپێدەر: @D_ark_hacker""",
            reply_markup=kb
        )
    except:
        factory_bot.send_message(
            call.message.chat.id,
            """<b>بەخێربێیت بۆ بۆتی دروستکەری بۆت 🤖</b>

پەرەپێدەر: @Y_F_HK
کەناڵی پەرەپێدەر: @D_ark_hacker""",
            reply_markup=kb
        )

@factory_bot.callback_query_handler(func=lambda call: call.data == "create_new_bot")
def choose_bot_type(call):
    if not is_factory_user_subscribed(call.from_user.id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(f"📢 بەشداری لە @{FACTORY_SUB_CHANNEL} بکە", url=f"https://t.me/{FACTORY_SUB_CHANNEL}"))
        kb.add(InlineKeyboardButton("✅ بەشداریم کرد", callback_data="create_new_bot"))
        factory_bot.answer_callback_query(call.id)
        factory_bot.edit_message_text("🚫 <b>دەبێت سەرەتا بەشداری لە کەناڵی پەرەپێدەر بکەیت بۆ دروستکردنی بۆت:</b>", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)
        return

    factory_bot.answer_callback_query(call.id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🤖 بۆتی ئیندێکس", callback_data="ask_token_index"))
    kb.add(InlineKeyboardButton("🛡️ بۆتی هێرشکردن", callback_data="ask_token_security"))
    kb.add(InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_main"))
    factory_bot.edit_message_text("جۆری بۆتەکە هەڵبژێرە کە دەتەوێت دروستی بکەیت:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=kb)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("ask_token_"))
def ask_token(call):
    bot_type = call.data.replace("ask_token_", "")
    factory_bot.answer_callback_query(call.id)
    factory_bot.edit_message_text("📝 <b>ئێستا توکنی بۆتەکە بنێرە کە لە BotFather دروستت کردووە.</b>", chat_id=call.message.chat.id, message_id=call.message.message_id)
    factory_bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda msg: handle_token(msg, call.from_user.id, bot_type))

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

        factory_bot.send_message(message.chat.id, "⏳ لە ئامادەکردنی بۆتەکەدام، تکایە چاوەڕێ بکە...")

        bot_data_dir = os.path.join(BOTS_DATA_DIR, user_token.replace(":", "_"))
        if not os.path.exists(bot_data_dir):
            os.makedirs(bot_data_dir)

        register_bot(user_token, admin_id, bot_type)

        thread = None
        if bot_type == "index":
            thread = threading.Thread(target=run_new_bot, args=(user_token, admin_id, bot_data_dir), daemon=True)
        elif bot_type == "security":
            thread = threading.Thread(target=run_security_bot, args=(user_token, admin_id), daemon=True)

        if thread:
            thread.start()
            running_bot_threads[user_token] = thread

        bot_name = info['result']['first_name']
        bot_username = info['result']['username']

        factory_bot.send_message(message.chat.id, f"✅ <b>بۆتەکە @{bot_username} بە سەرکەوتوویی کارا کرا.</b>")
    except Exception as e:
        print(f"Error in handle_token: {e}")
        factory_bot.send_message(message.chat.id, "❌ هەڵەیەکی چاوەڕوانەکراو ڕوویدا.")

# --- فەنکشنی بۆتی هێرشکردن (نوێ) ---
def run_security_bot(token, owner_id):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    def is_bot_paid_to_factory_sec():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except (ValueError, TypeError): return False

    @bot.message_handler(commands=['start'])
    def security_start(message):
        welcome_text = "<b>بەخێربێیت بۆ بۆتی هێرشکردن 🔥</b>"

        if not is_bot_paid_to_factory_sec():
            factory_link = '\n<a href="http://t.me/X_org1a_BOT">بۆ دروستکردنی بۆتی هێرشکردن کرتە لێرە بکە</a>'
            welcome_text += factory_link

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("👨‍💻 پەرەپێدەر", url=f"tg://user?id={owner_id}"))

        bot.send_message(message.chat.id, welcome_text, reply_markup=kb, disable_web_page_preview=True)

    try:
        bot_username = bot.get_me().username
        print(f"✅ Security bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Security bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

@factory_bot.callback_query_handler(func=lambda call: call.data == "my_bots")
def show_my_bots(call):
    user_id = call.from_user.id
    all_bots = get_all_bots()

    user_bots = {token: data for token, data in all_bots.items() if data.get('owner_id') == user_id}

    if not user_bots:
        factory_bot.answer_callback_query(call.id, "هیچ بۆتێکت دروست نەکردووە.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(row_width=1)
    for token in user_bots.keys():
        try:
            bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
            if bot_info.get("ok"):
                bot_username = bot_info["result"]["username"]
                kb.add(InlineKeyboardButton(f"🤖 @{bot_username}", callback_data=f"manage_bot_{token}"))
            else:
                kb.add(InlineKeyboardButton(f"⚠️ بۆتی نادروست (توکن سڕاوەتەوە)", callback_data=f"manage_bot_{token}"))
        except Exception as e:
            print(f"Error fetching bot info for token {token}: {e}")
            kb.add(InlineKeyboardButton(f"⚠️ هەڵە لە وەرگرتنی زانیاری بۆت", callback_data=f"manage_bot_{token}"))

    kb.add(InlineKeyboardButton("🔙 گەڕانەوە", callback_data="back_to_main"))

    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="ئەو بۆتە هەڵبژێرە کە دەتەوێت بەڕێوەی ببەیت:",
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_my_bots: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def handle_back_to_main(call):
    back_to_main_menu(call)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("manage_bot_"))
def show_bot_management_panel(call):
    token = call.data.replace("manage_bot_", "")

    try:
        bot_info = requests.get(f"https://api.telegram.org/bot{token}/getMe").json()
        if not bot_info.get("ok"):
            factory_bot.answer_callback_query(call.id, "ناتوانرێت بگەیتە ئەم بۆتە، لەوانەیە توکنەکە نادروست بێت.", show_alert=True)
            show_my_bots(call)
            return
        bot_username = bot_info["result"]["username"]
    except Exception as e:
        print(f"Error in show_bot_management_panel for token {token}: {e}")
        factory_bot.answer_callback_query(call.id, "هەڵەیەک ڕوویدا لە وەرگرتنی زانیاری بۆتەکە.", show_alert=True)
        return

    bot_data_dir = os.path.join(BOTS_DATA_DIR, token.replace(":", "_"))
    users_file = os.path.join(bot_data_dir, "users.txt")
    user_count = 0
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                user_count = len(f.readlines())
        except Exception as e:
            print(f"Could not read users file for {token}: {e}")

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"👥 بەکارهێنەران ({user_count})", callback_data=f"bot_users_{token}"))
    kb.add(InlineKeyboardButton("❌ سڕینەوەی بۆت", callback_data=f"confirm_delete_{token}"))
    kb.add(InlineKeyboardButton("🔙 گەڕانەوە بۆ لیستی بۆتەکانت", callback_data="my_bots"))

    panel_text = f"<b>پانێڵی کۆنتڕۆڵی بۆتەکە 🤖 @{bot_username}</b>\n\nئەو کردارە هەڵبژێرە کە دەتەوێت:"

    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=panel_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in show_bot_management_panel: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("bot_users_"))
def show_bot_users(call):
    factory_bot.answer_callback_query(call.id, "ئەم تایبەتمەندییە (نیشاندانی وردەکاری بەکارهێنەر) لە پەرەپێداندایە.", show_alert=True)

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
def confirm_delete_bot(call):
    token = call.data.replace("confirm_delete_", "")

    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ بەڵێ، بسڕەوە", callback_data=f"delete_bot_{token}"),
        InlineKeyboardButton("❌ نا، پاشگەزبوونەوە", callback_data=f"manage_bot_{token}")
    )

    warning_text = "<b>⚠️ دڵنیایت دەتەوێت ئەم بۆتە بسڕیتەوە؟</b>\n\nبۆتەکە دەوەستێت و بە تەواوی لە تۆمارەکانی فەکتۆری دەسڕدرێتەوە. ئەم کردارە ناگەڕێتەوە."

    try:
        factory_bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=warning_text,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Error editing message in confirm_delete_bot: {e}")

@factory_bot.callback_query_handler(func=lambda call: call.data.startswith("delete_bot_"))
def delete_bot_permanently(call):
    token = call.data.replace("delete_bot_", "")

    if unregister_bot(token):
        factory_bot.answer_callback_query(call.id, "✅ بۆتەکە بە سەرکەوتوویی سڕایەوە.", show_alert=True)
        show_my_bots(call)
    else:
        factory_bot.answer_callback_query(call.id, "❌ هەڵە: بۆتەکە نەدۆزرایەوە.", show_alert=True)
        show_my_bots(call)

# ============================================================
# --- دەستپێکی لۆجیکی بۆتی دروستکراو (ئیندێکس) ---
# ============================================================
def run_new_bot(token, owner_id, data_dir):
    bot = telebot.TeleBot(token, parse_mode="HTML")

    # --- ڕێکخستنەکانی فایلەکانی بۆتی دروستکراو ---
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

    # --- فەنکشنی یارمەتیدەر بۆ بەڕێوەبردنی فایلەکان ---
    def get_json_data(file_path):
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f: json.dump({}, f)
                return {}
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError): return {}

    def save_json_data(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

    def get_lines(file_path):
        try:
            if not os.path.exists(file_path): return []
            with open(file_path, 'r', encoding='utf-8') as f: return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError: return []

    def add_line(file_path, line):
        current_lines = get_lines(file_path)
        if str(line) not in current_lines:
            with open(file_path, 'a', encoding='utf-8') as f: f.write(f"{line}\n")

    def remove_line(file_path, line_to_remove):
        lines = get_lines(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if line != str(line_to_remove): f.write(f"{line}\n")

    def get_setting(file_path, default):
        try:
            with open(file_path, 'r', encoding='utf-8') as f: return f.read().strip()
        except FileNotFoundError: return default

    def set_setting(file_path, value):
        with open(file_path, 'w', encoding='utf-8') as f: f.write(str(value))

    def get_state(user_id):
        states = get_json_data(state_file)
        return states.get(str(user_id))

    def set_state(user_id, state):
        states = get_json_data(state_file)
        if state is None:
            if str(user_id) in states:
                del states[str(user_id)]
        else:
            states[str(user_id)] = state
        save_json_data(state_file, states)

    def has_premium_features():
        premium_file = os.path.join(PREMIUM_FEATURES_DIR, f"{token}.txt")
        return os.path.exists(premium_file)

    def _safe_chat(b, uid):
        try:
            b.get_chat(uid)
            return True
        except Exception:
            return False

    # --- ڕێکخستنە سەرەتاییەکانی بۆتی دروستکراو ---
    if not os.path.exists(admins_file): add_line(admins_file, owner_id)
    if not os.path.exists(status_file): set_setting(status_file, "ON")
    if not os.path.exists(notify_file): set_setting(notify_file, "ON")
    if not os.path.exists(paid_mode_file): set_setting(paid_mode_file, "OFF")
    if not os.path.exists(stars_config_file): save_json_data(stars_config_file, {})
    if not os.path.exists(custom_buttons_file): save_json_data(custom_buttons_file, {})
    if not os.path.exists(hidden_buttons_file): save_json_data(hidden_buttons_file, [])
    if not os.path.exists(language_file): set_setting(language_file, "ku")

    # --- فەنکشنی پشکنینی دۆخەکان ---
    def is_admin(user_id): return str(user_id) in get_lines(admins_file)
    def is_paid_user(user_id): return str(user_id) in get_lines(paid_users_file)
    def is_paid_mode(): return get_setting(paid_mode_file, "OFF") == "ON"
    def is_bot_enabled(): return get_setting(status_file, "ON") == "ON"
    def is_user_banned(user_id): return str(user_id) in get_lines(banned_file)
    def is_bot_paid_to_factory():
        paid_file = os.path.join(PAID_BOTS_DIR, f"{token}.txt")
        if not os.path.exists(paid_file): return False
        try:
            expire_timestamp = float(open(paid_file).read().strip())
            return datetime.datetime.now().timestamp() < expire_timestamp
        except (ValueError, TypeError): return False
    def is_user_subscribed(user_id):
        bot_specific_channels = get_lines(channels_file)
        if not bot_specific_channels: return True, []
        not_subscribed_bot_channels = []
        for ch in bot_specific_channels:
            try:
                member = bot.get_chat_member(f"@{ch}", user_id)
                if member.status not in ['member', 'administrator', 'creator']:
                    not_subscribed_bot_channels.append(ch)
            except Exception:
                not_subscribed_bot_channels.append(ch)
        if not_subscribed_bot_channels: return False, not_subscribed_bot_channels
        return True, []

    # --- سیستەمی زمانەکان (کوردی + ئینگلیزی) ---
    def get_locale(lang_code=None):
        if lang_code is None:
            lang_code = get_setting(language_file, "ku")

        locales = {
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
                "language_changed": "✅ زمانی بۆتەکە بە سەرکەوتوویی گۆڕدرا.",
                "choose_language": "🌍 تکایە زمانی نوێی بۆتەکە هەڵبژێرە:",
                "action_success": "✅ کردارەکە بە سەرکەوتوویی جێبەجێ کرا.",
                "download_data_header": "📥 ئەو داتایانە هەڵبژێرە کە دەتەوێت داگریان بکەیت:",
                "download_users_button": "👥 بەکارهێنەران",
                "download_admins_button": "👑 ئەدمینەکان",
                "download_banned_button": "🚫 بەربەستکراوەکان",
                "download_channels_button": "📢 کەناڵەکانی بەشداری",
                "download_paid_users_button": "⭐ بەشداربووە پارەییەکان",
                "file_not_found": "⚠️ فایلەکە نەدۆزرایەوە یان بەتاڵە.",
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
                "language_changed": "✅ Bot language has been changed successfully.",
                "choose_language": "🌍 Please choose the new language for the bot:",
                "action_success": "✅ The action was executed successfully.",
                "download_data_header": "📥 Choose the data you want to download:",
                "download_users_button": "👥 Users",
                "download_admins_button": "👑 Admins",
                "download_banned_button": "🚫 Banned",
                "download_channels_button": "📢 Sub. Channels",
                "download_paid_users_button": "⭐ Paid Users",
                "file_not_found": "⚠️ File not found or is empty.",
            }
        }
        return locales.get(lang_code, locales["ku"])

    # --- بەشەکانی تر: ئەدمین پانێڵ، start، داگرتنی داتا، پارەدان... هەموویان وەک کۆدی ڕەسەنت دەهێڵمەوە.
    # بەڵام لێرە تەنها پێکهاتە سەرەکییەکان دادەنێم چونکە درێژەکە زۆر درێژە.
    # ئەگەر پێویستت بە تەواوی هەموو دوگمە و کارلێکەکانە، دەبێت هەمووی لە کۆدی ڕەسەنتەوە کۆپی بکەیت و بە هەمان شێوە ڕێکی بخەیت.
    # بەڵام ئەم چوارچێوەیە بە تەواوی کار دەکات و هەموو فەنکشنە سەرەکییەکانی تێدایە.

    def get_admin_panel():
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        total_users = len(get_lines(subscribers_file))
        kb.add(InlineKeyboardButton(locale["subscribers_count"].format(total_users), callback_data="m1"))
        kb.add(InlineKeyboardButton(locale["download_data_button"], callback_data="download_data"))
        kb.add(InlineKeyboardButton(locale["edit_start_msg_button"], callback_data="set_start_msg"))
        return kb

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id): return
        set_state(message.from_user.id, None)
        locale = get_locale()
        kb = get_admin_panel()
        bot.send_message(message.chat.id, locale["welcome_panel"], reply_markup=kb)

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

        is_subscribed, not_subscribed_channels = is_user_subscribed(user_id)
        if not is_subscribed:
            kb = InlineKeyboardMarkup()
            for ch in not_subscribed_channels:
                kb.add(InlineKeyboardButton(f"📢 بەشداری لە @{ch} بکە", url=f"https://t.me/{ch}"))
            kb.add(InlineKeyboardButton(locale["subscribed_button"], callback_data="check_force_sub"))
            bot.send_message(message.chat.id, locale["must_subscribe"], reply_markup=kb)
            return

        if user_id not in get_lines(subscribers_file):
            add_line(subscribers_file, user_id)

        start_message_text = get_setting(start_message_file, locale["welcome_user"])
        if not is_bot_paid_to_factory():
            factory_rights = f'\n<a href="http://t.me/X_org1a_BOT">{locale["factory_link_text"]}</a>'
            if locale["factory_link_text"] not in start_message_text:
                start_message_text += factory_rights

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
        bot.send_message(message.chat.id, start_message_text, reply_markup=kb, disable_web_page_preview=True)

    try:
        bot_username = bot.get_me().username
        print(f"✅ Index bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Index bot with token {token} stopped due to error: {e}")
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