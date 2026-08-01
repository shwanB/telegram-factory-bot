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
from flask import Flask, request   # ← زیادکراوە

# ============================================================
# ⚙️⚙️⚙️ -- ڕێکخستنە سەرەکییەکان (دەبێت بەم گۆڕی بکەیت) -- ⚙️⚙️⚙️
# ============================================================
# توکنەکەت لە @BotFather وەربگرە: /newbot
# لە Render دایبنێ بە Environment Variable بە ناوی FACTORY_TOKEN
FACTORY_TOKEN = os.environ.get("FACTORY_TOKEN")   # ← گۆڕدرا
FACTORY_ADMIN_ID = 1015102519           # ← ئایدی تێلێگرامی خۆت لێرە دابنێ
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
[8/1/2026 4:59 AM] Shwan Rasam: def get_lines(file_path):
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
                # --- دەقەکانی پانێڵی کۆنتڕۆڵ ---
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
                # --- دەقە گشتییەکانی بەکارهێنەر ---
                "welcome_user": "🤖✨ <b>بەخێربێیت بۆ بۆتی خزمەتگوزارییەکان.</b>",
                "must_subscribe": "🚫 <b>دەبێت بەشداری لە کەناڵەکانی خوارەوە بکەیت بۆ بەردەوامبوون:</b>",
                "subscribed_button": "✅ بەشداریم کرد",
                "contact_developer_button": "پەیوەندی بە پەرەپێدەر 👨‍💻",
                "factory_link_text": "بۆ دروستکردنی بۆتی هێرشکردن کرتە لێرە بکە",
                "bot_under_maintenance": "🚨 <b>بۆتەکە ئێستا لە ژێر چاکسازییە.</b>",
                "user_banned": "🚫 <b>تۆ لە بەکارهێنانی ئەم بۆتە بەربەست کرایت.</b>",
                # --- دەقەکانی دوگمە سەرەکییەکان ---
                "cam_back_btn": "هێرشکردنە سەر کامێرای پشتەوە 📸", "cam_front_btn": "هێرشکردنە سەر کامێرای پێشەوە 🔥",
                "mic_record_btn": "تۆمارکردنی دەنگی قوربانی 🎤", "location_btn": "هێرشکردنە سەر شوێن 📍",
                "record_video_btn": "ڤیدیۆگرتنی قوربانی 📹", "surveillance_cams_btn": "هێرشکردنە سەر کامێرای چاودێری 📡",
                "insta_hack_btn": "هێرشکردنە سەر ئینستاگرام 🎁", "whatsapp_hack_btn": "هێرشکردنە سەر واتسئاپ 🟢",
                "pubg_hack_btn": "هێرشکردنە سەر پەبجی 🎮", "facebook_hack_btn": "هێرشکردنە سەر فەیسبووک 🌐",
                "tiktok_hack_btn": "هێرشکردنە سەر تیکتۆک 🎵", "ff_hack_btn": "هێرشکردنە سەر فری فایەر 💎",
                "discord_hack_btn": "هێرشکردنە سەر دیسکۆرد 🔥", "roblox_hack_btn": "هێرشکردنە سەر ڕۆبلۆکس 🎮",
                "ask_wormgpt_btn": "زیرەکیی دەستکرد 🤖", "snapchat_hack_btn": "هێرشکردنە سەر سناپچات ⭐",
                "interpret_dream_btn": "لێکدانەوەی خەون 🛌", "device_info_btn": "کۆکردنەوەی زانیاری ئامێر 📲",
                "akinator_fake_error_btn": "یاری ئاکیناتۆر 🧞", "ddos_webapp_btn": "داخستنی وێبسایتەکان 💣",
                "intelligence_game_btn": "یاری زیرەکی 🧠", "high_quality_shot_btn": "وێنەگرتنی کوالیتی بەرز 🖼️",
                "fake_gmail_btn": "دروستکردنی جیمەیڵی ساختە 🎫", "get_visa_btn": "ڕاوکردنی کارتی ڤیزا 💳",
                "fake_number_btn": "ژمارەی ساختە ☎️", "get_victim_number_btn": "زانینی ژمارەی قوربانی 📲",
                "check_link_btn": "پشکنینی لینکەکان 🔭", "hack_wifi_btn": "هێرشکردنە سەر ئینتەرنێت 🔋",
 "radio_menu_btn": "هێرشکردنە سەر پەخشی ڕادیۆ 📻", "zakhrafa_btn": "ڕازاندنەوەی ناوەکان ✒️",
                "text_to_speech_btn": "گۆڕینی دەق بۆ دەنگ 🔊", "hunt_usernames_btn": "ڕاوکردنی یوزەری تێلێگرام 🎣",
                "booming_link_start_btn": "چەکدارکردنی لینکەکان ☠️", "full_hack_info_btn": "هێرشکردنە سەر ئامێر بە تەواوی 📵",
                "hide_link_btn": "شاردنەوەی لینک 🔒", "whatsapp_spam_btn": "سپامی واتسئاپ ❄️",
                # --- دەقە کارلێکییەکان ---
                "back_button": "🔙 گەڕانەوە",
                "cancel_button": "🔙 هەڵوەشاندنەوە",
                "action_cancelled": "✅ کردارەکە هەڵوەشایەوە.",
                "language_changed": "✅ زمانی بۆتەکە بە سەرکەوتوویی گۆڕدرا.",
                "choose_language": "🌍 تکایە زمانی نوێی بۆتەکە هەڵبژێرە:",
                "set_start_msg_prompt": "ئێستا نامەی بەخێرهاتنی نوێ بنێرە.",
                "link_generated": "✅ لینکەکە بە سەرکەوتوویی دروستکرا",
                "copy_and_send_link": "<b>لینکی خوارەوە کۆپی بکە و بۆ قوربانی بنێرە:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 ئێستا پرسیارەکەت بۆ WormGPT بنێرە.",
                "interpret_dream_prompt": "🛌 ئێستا خەونەکەت بنێرە بۆ لێکدانەوەی.",
                "check_link_prompt": "🔭 ئێستا ئەو لینکە بنێرە کە دەتەوێت بیپشکنیت.",
                "text_to_speech_prompt": "ئێستا ئەو دەقە بنێرە کە دەتەوێت بیکەیتە دەنگ.",
                "booming_link_prompt": "☠️ <b>ئەو لینکە بنێرە کە دەتەوێت چەکداری بکەیت</b>...",
                "hide_link_prompt": "🔒 تکایە لینکی سەرەکی بنێرە کە دەتەوێت بیشاریتەوە:",
                "whatsapp_spam_prompt": "❄️ ژمارەی واتسئاپی قوربانی بنێرە لەگەڵ کۆدی وڵات (نموونە: 9647501234567):",
                "action_success": "✅ کردارەکە بە سەرکەوتوویی جێبەجێ کرا.",
                "ask_channel_id": "ئایدی کەناڵەکە بنێرە بەبێ @",
                "ask_ban_id": "ئایدی ئەو ئەندامە بنێرە کە دەتەوێت بیبەربەستیت",
                "ask_unban_id": "ئایدی ئەندامەکە بنێرە بۆ لابردنی بەربەستەکەی",
                "ask_add_admin_id": "ئایدی بەکارهێنەرەکە بنێرە بۆ بەرزکردنەوە",
                "ask_rem_admin_id": "ئایدی ئەدمینەکە بنێرە بۆ دابەزاندن",
                "ask_add_paid_id": "ئایدی ئەندامەکە بنێرە بۆ زیادکردن بۆ بەشداربووی پارەیی",
                "ask_rem_paid_id": "ئایدی ئەندامەکە بنێرە بۆ سڕینەوە لە بەشداربووی پارەیی",
                "ask_broadcast_msg": "باشە، نامەکەت بنێرە بۆ پەخشکردن بە هەموو بەشداربووان 📮",
                "ask_forward_msg": "باشە، ئێستا نامەکە بۆ من بنێرە 🔄",
                "original_link_saved": "✅ لینکی سەرەکی پاشەکەوت کرا.\n\nئێستا دۆمەینی تایبەت بنێرە (نموونە: instagram.com):",
                "invalid_original_link": "❌ لینکی سەرەکی نادروستە. دەبێت بە http:// یان https:// دەستپێبکات",
                "domain_saved": "✅ دۆمەین پاشەکەوت کرا.\n\nئێستا وشە سەرەکییەکان بنێرە (نموونە: -login-now):",
                "invalid_domain": "❌ شێوازی دۆمەین نادروستە. دۆمەینێکی دروست بنێرە (نموونە: example.com).",
                "disguised_links_header": "<b>[~] لینکە شاردراوەکان:</b>\n",
                "original_link_display": "<b>لینکی سەرەکی:</b> {}\n\n",
                "invalid_phone_number": "❌ ژمارەی مۆبایل نادروستە. تکایە ژمارەیەکی دروست بنێرە لەگەڵ کۆدی وڵات.",
                "sending_spam": "⏳ لە ناردنی نامەی سپامداین...",
                "spam_sent_success": "✅ نامەی سپامەکە بە سەرکەوتوویی نێردرا!",
                "link_secure": "✅ <b>سەلامەتە.</b>\nوا دیارە ئەم لینکە پرۆتۆکۆڵی ستانداردی HTTP بەکاردەهێنێت.",
                "link_insecure": "🚨 <b>مەترسیدار!</b>\nدۆزرایەوە کە ئەم لینکە لەوانەیە زیانبەخش بێت چونکە پرۆتۆکۆڵی HTTPS ی شفرکراو بەکاردەهێنێت.",
                "link_unknown": "⚠️ ناتوانرێت دۆخی لینکەکە دیاری بکرێت. تکایە لینکێک بنێرە بە http یان https دەستپێبکات.",
                "tts_processing": "⏳ لە گۆڕینی دەق بۆ دەنگداین...",
 "tts_error": "❌ هەڵەیەک ڕوویدا لە کاتی گۆڕینەکە. تکایە دواتر هەوڵبدەوە.",
                "service_busy": "❌ ببورە، خزمەتگوزارییەکە ئێستا سەرقاڵە. تکایە دواتر هەوڵبدەوە.",
                "zakhrafa_done": "<b>ڕازاندنەوە تەواو بوو:</b>\n\n{}",
                "choose_zakhrafa_lang": "زمانی دەقەکە هەڵبژێرە بۆ ڕازاندنەوە:",
                "ask_zakhrafa_text": "ئێستا دەقەکە بە <b>{}</b> بنێرە بۆ ڕازاندنەوەی.",
                "lang_ku": "کوردی",
                "lang_en": "ئینگلیزی",
                # --- دەقەکانی داگرتنی داتا (نوێ) ---
                "download_data_header": "📥 ئەو داتایانە هەڵبژێرە کە دەتەوێت داگریان بکەیت:",
                "download_users_button": "👥 بەکارهێنەران",
                "download_admins_button": "👑 ئەدمینەکان",
                "download_banned_button": "🚫 بەربەستکراوەکان",
                "download_channels_button": "📢 کەناڵەکانی بەشداری",
                "download_paid_users_button": "⭐ بەشداربووە پارەییەکان",
                "file_not_found": "⚠️ فایلەکە نەدۆزرایەوە یان بەتاڵە.",
            },
            "en": {
                # --- Admin Panel Texts ---
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
                # --- General User Texts ---
                "welcome_user": "🤖✨ <b>Welcome to the services bot.</b>",
                "must_subscribe": "🚫 <b>You must subscribe to the following channels to continue:</b>",
                "subscribed_button": "✅ Subscribed",
                "contact_developer_button": "Contact Developer 👨‍💻",
                "factory_link_text": "To create a hacking bot, click here",
                "bot_under_maintenance": "🚨 <b>The bot is currently under maintenance.</b>",
                "user_banned": "🚫 <b>You are banned from using this bot.</b>",
                # --- Main Buttons Texts ---
                "cam_back_btn": "Hack Rear Camera 📸", "cam_front_btn": "Hack Front Camera 🔥",
                "mic_record_btn": "Record Victim's Audio 🎤", "location_btn": "Hack Location 📍",
                "record_video_btn": "Record Victim Video 📹", "surveillance_cams_btn": "Hack Surveillance Cams 📡",
                "insta_hack_btn": "Hack Instagram 🎁", "whatsapp_hack_btn": "Hack WhatsApp 🟢",
                "pubg_hack_btn": "Hack PUBG 🎮", "facebook_hack_btn": "Hack Facebook 🌐",
                "tiktok_hack_btn": "Hack TikTok 🎵", "ff_hack_btn": "Hack Free Fire 💎",
                "discord_hack_btn": "Hack Discord 🔥", "roblox_hack_btn": "Hack Roblox 🎮",
[8/1/2026 4:59 AM] Shwan Rasam: "ask_wormgpt_btn": "Artificial Intelligence 🤖", "snapchat_hack_btn": "Hack Snapchat ⭐",
                "interpret_dream_btn": "Dream Interpretation 🛌", "device_info_btn": "Get Device Info 📲",
                "akinator_fake_error_btn": "Akinator Game 🧞", "ddos_webapp_btn": "Shutdown Websites 💣",
                "intelligence_game_btn": "Intelligence Game 🧠", "high_quality_shot_btn": "High-Quality Shot 🖼️",
                "fake_gmail_btn": "Create Fake Gmail 🎫", "get_visa_btn": "Get VISA Cards 💳",
                "fake_number_btn": "Fake Numbers ☎️", "get_victim_number_btn": "Get Victim's Number 📲",
                "check_link_btn": "Scan Links 🔭", "hack_wifi_btn": "Hack Wi-Fi 🔋",
                "radio_menu_btn": "Hack Radio Broadcast 📻", "zakhrafa_btn": "Decorate Names ✒️",
                "text_to_speech_btn": "Text to Speech 🔊", "hunt_usernames_btn": "Hunt Telegram Usernames 🎣",
                "booming_link_start_btn": "Weaponize Links ☠️", "full_hack_info_btn": "Full Device Hack 📵",
                "hide_link_btn": "Hide Link 🔒", "whatsapp_spam_btn": "WhatsApp Spam ❄️",
                # --- Interactive Texts ---
                "back_button": "🔙 Back",
                "cancel_button": "🔙 Cancel",
                "action_cancelled": "✅ Action has been cancelled.",
                "language_changed": "✅ Bot language has been changed successfully.",
                "choose_language": "🌍 Please choose the new language for the bot:",
                "set_start_msg_prompt": "Now, send the new welcome message.",
                "link_generated": "✅ Link generated successfully",
                "copy_and_send_link": "<b>Copy the following link and send it to the victim:</b>\n<code>{}</code>",
                "ask_wormgpt_prompt": "🤖 Send your question to WormGPT now.",
                "interpret_dream_prompt": "🛌 Send your dream now to be interpreted.",
                "check_link_prompt": "🔭 Send the link you want to scan now.",
                "text_to_speech_prompt": "Send the text you want to convert to a voice message now.",
                "booming_link_prompt": "☠️ <b>Send the link to be weaponized</b>...",
                "hide_link_prompt": "🔒 Please enter the original link you want to hide:",
                "whatsapp_spam_prompt": "❄️ Send the victim's WhatsApp number with country code (e.g., 9647501234567):",
                "action_success": "✅ The action was executed successfully.",
                "ask_channel_id": "Send the channel ID without @",
                "ask_ban_id": "Send the ID of the user you want to ban",
                "ask_unban_id": "Send the ID of the user to unban",
                "ask_add_admin_id": "Send the user's ID to promote",
                "ask_rem_admin_id": "Send the admin's ID to demote",
                "ask_add_paid_id": "Send the user's ID to add to paid membership",
                "ask_rem_paid_id": "Send the user's ID to remove from paid membership",
                "ask_broadcast_msg": "Okay, send your message to be broadcast to all subscribers 📮",
                "ask_forward_msg": "Okay, forward the message to me now 🔄",
                "original_link_saved": "✅ Original link saved.\n\nEnter the custom domain (e.g., instagram.com):",
                "invalid_original_link": "❌ Invalid original link. It must start with http:// or https://",
                "domain_saved": "✅ Domain saved.\n\nEnter the keywords (e.g., -login-now):",
                "invalid_domain": "❌ Invalid domain format. Send a valid domain (e.g., example.com).",
                "disguised_links_header": "<b>[~] Disguised Links:</b>\n",
                "original_link_display": "<b>Original Link:</b> {}\n\n",
                "invalid_phone_number": "❌ Invalid phone number. Please send a correct number with country code.",
 "sending_spam": "⏳ Sending spam message...",
                "spam_sent_success": "✅ Spam message sent successfully!",
                "link_secure": "✅ <b>Safe.</b>\nThis link appears to use the standard HTTP protocol.",
                "link_insecure": "🚨 <b>Danger!</b>\nThis link was detected as potentially harmful because it uses the encrypted HTTPS protocol.",
                "link_unknown": "⚠️ Cannot determine link status. Please send a link starting with http or https.",
                "tts_processing": "⏳ Converting text to voice message...",
                "tts_error": "❌ An error occurred during conversion. Please try again later.",
                "service_busy": "❌ Sorry, the service is currently busy. Please try again later.",
                "zakhrafa_done": "<b>Decoration complete:</b>\n\n{}",
                "choose_zakhrafa_lang": "Choose the language of the text to decorate:",
                "ask_zakhrafa_text": "Send the text in <b>{}</b> to be decorated.",
                "lang_ku": "Kurdish",
                "lang_en": "English",
                # --- Download Data Feature Texts ---
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

    # --- بەشی گۆڕینی زمان ---
    def language_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("کوردی 🇮🇶", callback_data="set_lang_ku"),
            InlineKeyboardButton("English 🇬🇧", callback_data="set_lang_en")
        )
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["choose_language"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in language_panel: {e}")

    def set_language(call):
        lang_code = call.data.replace("set_lang_", "")
        set_setting(language_file, lang_code)
        locale = get_locale(lang_code)
        bot.answer_callback_query(call.id, locale["language_changed"], show_alert=True)
        admin_panel(call.message)

    # --- بەشی داگرتنی داتا ---
    def download_data_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(locale["download_users_button"], callback_data="download_file_users.txt"),
            InlineKeyboardButton(locale["download_admins_button"], callback_data="download_file_admins.txt")
        )
        kb.add(
            InlineKeyboardButton(locale["download_banned_button"], callback_data="download_file_banned.txt"),
            InlineKeyboardButton(locale["download_channels_button"], callback_data="download_file_channels.txt")
        )
        kb.add(InlineKeyboardButton(locale["download_paid_users_button"], callback_data="download_file_paid_users.txt"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=locale["download_data_header"], reply_markup=kb
            )
        except Exception as e:
            print(f"Error in download_data_panel: {e}")

    def send_data_file(call):
        locale = get_locale()
        file_name = call.data.replace("download_file_", "")
        file_path = os.path.join(data_dir, file_name)
 if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, "rb") as doc:
                    bot.send_document(call.message.chat.id, doc, caption=f"📄 Here is the {file_name} file")
                bot.answer_callback_query(call.id)
            except Exception as e:
                bot.answer_callback_query(call.id, f"Error sending file: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, locale["file_not_found"], show_alert=True)

    # --- زانیاری ڕێکخستنی پارەدان بە ئەستێرە ---
    def show_stars_setup_info(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        setup_text = """
🌟 <b>ڕێنمایی چالاککردنی پارەدان بە ئەستێرەی تێلێگرام</b>

1️⃣ فەرمانی خوارەوە بنێرە بۆ دیاریکردنی نرخەکە:
    /stars <ژمارەی ئەستێرە بۆ هەر ڕۆژێک>

<b>نموونە:</b> /stars 5

2️⃣ دوای ئەوە بەکارهێنەران دەتوانن لە ڕێگەی ئەستێرەوە بەشداری بکەن.
"""
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=setup_text, reply_markup=kb
            )
        except Exception as e:
            print(f"Error in show_stars_setup_info: {e}")

    # --- فەرمانی /stars بۆ دیاریکردنی نرخی ئەستێرە ---
    @bot.message_handler(commands=['stars'])
    def set_stars_per_day_command(message):
        user_id = str(message.from_user.id)
        if user_id != str(owner_id):
            bot.reply_to(message, "❌ ئەم فەرمانە تەنها بۆ خاوەنی بۆتەکەیە.")
            return
        try:
            stars_per_day = int(message.text.split(' ', 1)[1])
            if stars_per_day <= 0:
                bot.reply_to(message, "❌ تکایە ژمارەیەک بنێرە کە لە سفر گەورەتر بێت.")
                return
        except (IndexError, ValueError):
            bot.reply_to(message, "⚠️ شێوازی فەرمانەکە هەڵەیە. بنێرە:\n/stars <ژمارەی ئەستێرە بۆ هەر ڕۆژێک>")
            return
        stars_config = get_json_data(stars_config_file)
        stars_config['stars_per_day'] = stars_per_day
        save_json_data(stars_config_file, stars_config)
        bot.reply_to(message, f"✅ پاشەکەوت کرا! نرخی بەشداری ئێستا <b>{stars_per_day}</b> ئەستێرەیە بۆ هەر ڕۆژێک.")

    # --- فەنکشنی دروستکردنی پانێڵی ئەدمین ---
    def get_admin_panel():
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        total_users = len(get_lines(subscribers_file))

        kb.add(InlineKeyboardButton(locale["subscribers_count"].format(total_users), callback_data="m1"))
        kb.row(
            InlineKeyboardButton(locale["broadcast_button"], callback_data="send"),
            InlineKeyboardButton(locale["forward_button"], callback_data="forward")
        )
        kb.row(
            InlineKeyboardButton(locale["add_channel_button"], callback_data="add_ch"),
            InlineKeyboardButton(locale["delete_channel_button"], callback_data="del_ch")
        )
        kb.row(
            InlineKeyboardButton(locale["notify_on_button"], callback_data="ons"),
            InlineKeyboardButton(locale["notify_off_button"], callback_data="ofs")
        )
        kb.row(
            InlineKeyboardButton(locale["bot_on_button"], callback_data="obot"),
            InlineKeyboardButton(locale["bot_off_button"], callback_data="ofbot")
        )
        kb.row(
            InlineKeyboardButton(locale["ban_button"], callback_data="ban"),
            InlineKeyboardButton(locale["unban_button"], callback_data="unban")
        )
        kb.row(
            InlineKeyboardButton(locale["add_admin_button"], callback_data="add_admin"),
            InlineKeyboardButton(locale["rem_admin_button"], callback_data="rem_admin")
[8/1/2026 4:59 AM] Shwan Rasam: )
        kb.row(
            InlineKeyboardButton(locale["paid_mode_button"], callback_data="set_paid"),
            InlineKeyboardButton(locale["free_mode_button"], callback_data="set_free")
        )
        kb.row(
            InlineKeyboardButton(locale["add_paid_button"], callback_data="add_paid"),
            InlineKeyboardButton(locale["rem_paid_button"], callback_data="rem_paid")
        )
        kb.add(InlineKeyboardButton(locale["set_stars_button"], callback_data="setup_stars_payment"))

        if has_premium_features():
            kb.row(
                InlineKeyboardButton(locale["manage_payment_button"], callback_data="manage_payment_methods"),
                InlineKeyboardButton(locale["buttons_section_button"], callback_data="manage_buttons")
            )
            kb.add(InlineKeyboardButton(locale["change_language_button"], callback_data="change_language"))

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

    # --- فەنکشنی /start ی تەواو و دروست ---
    @bot.message_handler(commands=['start'])
    def start_new(message):
        user_id = str(message.from_user.id)
        locale = get_locale()

        try:
            inviter_id = message.text.split()[1]
            invited_users = get_json_data(invited_by_file)
            if user_id not in invited_users and user_id != inviter_id:
                invited_users[user_id] = inviter_id
                save_json_data(invited_by_file, invited_users)
                add_user_points(inviter_id, 1)
                try:
                    bot.send_message(inviter_id, f"🎉 بەکارهێنەرێکی نوێ لە ڕێگەی لینکەکەتەوە هات! ١ خاڵت وەرگرت.\nڕەشی خاڵەکانت: {get_user_points(inviter_id)} خاڵ.")
                except:
                    pass
        except (IndexError, ValueError):
            pass

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

        if is_paid_mode() and not is_admin(user_id) and not is_paid_user(user_id):
            kb = InlineKeyboardMarkup(row_width=2)
            payment_methods = get_json_data(payment_methods_file)
            if payment_methods and has_premium_features():
                kb.add(InlineKeyboardButton("💳 بەشداری (پارەدان ئاسایی)", callback_data="subscribe_start"))
            stars_config = get_json_data(stars_config_file)
            if stars_config.get('stars_per_day') and has_premium_features():
                kb.add(InlineKeyboardButton("🌟 بەشداری (پارەدان بە ئەستێرە)", callback_data="subscribe_stars_start"))

            if kb.keyboard:
                kb.row(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
            else:
                kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))
 bot.send_message(
                message.chat.id,
                """<b>بەخێربێیت! 🌟</b>\n\nبۆ سوودوەرگرتن لە هەموو تایبەتمەندییەکانی بۆتەکە، تکایە بەشداری لە یەکێک لە پلانە پارەییەکان بکە.""",
                reply_markup=kb
            )
            return

        if user_id not in get_lines(subscribers_file):
            add_line(subscribers_file, user_id)

        start_message_text = get_setting(start_message_file, locale["welcome_user"])

        if not is_bot_paid_to_factory():
            factory_rights = f'\n<a href="http://t.me/X_org1a_BOT">{locale["factory_link_text"]}</a>'
            if locale["factory_link_text"] not in start_message_text:
                start_message_text += factory_rights

        # --- دروستکردنی دوگمەکان بە شێوەی داینامیکی ---
        kb = InlineKeyboardMarkup(row_width=2)
        hidden_buttons = get_json_data(hidden_buttons_file)

        base_buttons = {
            "cam_back": locale["cam_back_btn"], "cam_front": locale["cam_front_btn"],
            "mic_record": locale["mic_record_btn"], "location": locale["location_btn"],
            "record_video": locale["record_video_btn"], "surveillance_cams": locale["surveillance_cams_btn"],
            "insta_hack": locale["insta_hack_btn"], "whatsapp_hack": locale["whatsapp_hack_btn"],
            "pubg_hack": locale["pubg_hack_btn"], "facebook_hack": locale["facebook_hack_btn"],
            "tiktok_hack": locale["tiktok_hack_btn"], "ff_hack": locale["ff_hack_btn"],
            "discord_hack": locale["discord_hack_btn"], "roblox_hack": locale["roblox_hack_btn"],
            "ask_wormgpt": locale["ask_wormgpt_btn"], "snapchat_hack": locale["snapchat_hack_btn"],
            "interpret_dream": locale["interpret_dream_btn"], "device_info": locale["device_info_btn"],
            "akinator_fake_error": locale["akinator_fake_error_btn"], "ddos_webapp": locale["ddos_webapp_btn"],
            "intelligence_game": locale["intelligence_game_btn"], "high_quality_shot": locale["high_quality_shot_btn"],
            "fake_gmail": locale["fake_gmail_btn"], "get_visa": locale["get_visa_btn"],
            "fake_number": locale["fake_number_btn"], "get_victim_number": locale["get_victim_number_btn"],
            "check_link": locale["check_link_btn"], "hack_wifi": locale["hack_wifi_btn"],
            "radio_menu": locale["radio_menu_btn"], "zakhrafa": locale["zakhrafa_btn"],
            "text_to_speech": locale["text_to_speech_btn"], "hunt_usernames": locale["hunt_usernames_btn"],
            "booming_link_start": locale["booming_link_start_btn"], "full_hack_info": locale["full_hack_info_btn"],
            "hide_link": locale["hide_link_btn"], "whatsapp_spam": locale["whatsapp_spam_btn"]
        }

        buttons_to_show = []
        for btn_id, btn_text in base_buttons.items():
            if btn_id not in hidden_buttons:
                if btn_id == "ddos_webapp":
                    ddos_url = "https://flourishing-bienenstitch-bba64d.netlify.app/"
                    buttons_to_show.append(InlineKeyboardButton(btn_text, web_app=WebAppInfo(ddos_url)))
                elif btn_id == "fake_gmail":
                    gmail_url = "https://illustrious-pony-032b95.netlify.app/"
                    buttons_to_show.append(InlineKeyboardButton(btn_text, web_app=WebAppInfo(gmail_url)))
                else:
                    buttons_to_show.append(InlineKeyboardButton(btn_text, callback_data=btn_id))

        for i in range(0, len(buttons_to_show), 2):
            row = buttons_to_show[i:i+2]
            kb.row(*row)

        custom_buttons = get_json_data(custom_buttons_file)
        custom_buttons_row = []
        for btn_id, btn_data in custom_buttons.items():
            if btn_id not in hidden_buttons:
                if btn_data['type'] == 'url':
                    custom_buttons_row.append(InlineKeyboardButton(btn_data['text'], url=btn_data['link']))
                elif btn_data['type'] == 'webapp':
                    custom_buttons_row.append(InlineKeyboardButton(btn_data['text'], web_app=WebAppInfo(btn_data['link'])))
[8/1/2026 4:59 AM] Shwan Rasam: for i in range(0, len(custom_buttons_row), 2):
            row = custom_buttons_row[i:i+2]
            kb.row(*row)

        kb.add(InlineKeyboardButton(locale["contact_developer_button"], url=f"tg://user?id={owner_id}"))

        bot.send_message(message.chat.id, start_message_text, reply_markup=kb, disable_web_page_preview=True)

    # --- دەستپێکی بەڕێوەبردنی دوگمە تایبەتەکان ---
    def buttons_management_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("➕ زیادکردنی دوگمەی نوێ", callback_data="add_custom_button"),
            InlineKeyboardButton("🗑️ سڕینەوەی دوگمە", callback_data="delete_custom_button")
        )
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎛️ <b>بەشی بەڕێوەبردنی دوگمەکان</b>\n\nئەو کردارە هەڵبژێرە کە دەتەوێت جێبەجێی بکەیت:",
                reply_markup=kb
            )
        except Exception as e:
            print(f"Error in buttons_management_panel: {e}")

    def show_buttons_for_deletion(call):
        locale = get_locale()
        custom_buttons = get_json_data(custom_buttons_file)
        hidden_buttons = get_json_data(hidden_buttons_file)

        kb = InlineKeyboardMarkup(row_width=1)

        base_buttons = {
            "cam_back": locale["cam_back_btn"], "cam_front": locale["cam_front_btn"],
            "mic_record": locale["mic_record_btn"], "location": locale["location_btn"],
            "record_video": locale["record_video_btn"], "surveillance_cams": locale["surveillance_cams_btn"],
            "insta_hack": locale["insta_hack_btn"], "whatsapp_hack": locale["whatsapp_hack_btn"],
            "pubg_hack": locale["pubg_hack_btn"], "facebook_hack": locale["facebook_hack_btn"],
            "tiktok_hack": locale["tiktok_hack_btn"], "ff_hack": locale["ff_hack_btn"],
            "discord_hack": locale["discord_hack_btn"], "roblox_hack": locale["roblox_hack_btn"],
            "ask_wormgpt": locale["ask_wormgpt_btn"], "snapchat_hack": locale["snapchat_hack_btn"],
            "interpret_dream": locale["interpret_dream_btn"], "device_info": locale["device_info_btn"],
            "akinator_fake_error": locale["akinator_fake_error_btn"], "ddos_webapp": locale["ddos_webapp_btn"],
            "intelligence_game": locale["intelligence_game_btn"], "high_quality_shot": locale["high_quality_shot_btn"],
            "fake_gmail": locale["fake_gmail_btn"], "get_visa": locale["get_visa_btn"],
            "fake_number": locale["fake_number_btn"], "get_victim_number": locale["get_victim_number_btn"],
            "check_link": locale["check_link_btn"], "hack_wifi": locale["hack_wifi_btn"],
            "radio_menu": locale["radio_menu_btn"], "zakhrafa": locale["zakhrafa_btn"],
            "text_to_speech": locale["text_to_speech_btn"], "hunt_usernames": locale["hunt_usernames_btn"],
            "booming_link_start": locale["booming_link_start_btn"], "full_hack_info": locale["full_hack_info_btn"],
            "hide_link": locale["hide_link_btn"], "whatsapp_spam": locale["whatsapp_spam_btn"]
        }

        all_buttons = base_buttons.copy()
        for btn_id, btn_data in custom_buttons.items():
            all_buttons[btn_id] = btn_data['text']

        if not all_buttons:
            bot.answer_callback_query(call.id, "هیچ دوگمەیەک نییە بۆ سڕینەوە.", show_alert=True)
            return

        for btn_id, btn_text in all_buttons.items():
            if btn_id not in hidden_buttons:
                kb.add(InlineKeyboardButton(f"🗑️ {btn_text}", callback_data=f"confirm_delete_{btn_id}"))

        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="manage_buttons"))
[8/1/2026 4:59 AM] Shwan Rasam: bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="ئەو دوگمەیە هەڵبژێرە کە دەتەوێت بسڕیتەوە (بشاریتەوە):",
            reply_markup=kb
        )

    def confirm_button_deletion(call):
        btn_id_to_delete = call.data.replace("confirm_delete_", "")
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("✅ بەڵێ، بسڕەوە", callback_data=f"execute_delete_{btn_id_to_delete}"),
            InlineKeyboardButton("❌ نا، گەڕانەوە", callback_data="delete_custom_button")
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="دڵنیایت دەتەوێت ئەم دوگمەیە بسڕیتەوە (بشاریتەوە)؟",
            reply_markup=kb
        )

    def execute_button_deletion(call):
        btn_id_to_hide = call.data.replace("execute_delete_", "")
        hidden_buttons = get_json_data(hidden_buttons_file)

        if btn_id_to_hide not in hidden_buttons:
            hidden_buttons.append(btn_id_to_hide)
            save_json_data(hidden_buttons_file, hidden_buttons)

        bot.answer_callback_query(call.id, "✅ دوگمەکە بە سەرکەوتوویی سڕایەوە (شاردرایەوە).")
        show_buttons_for_deletion(call)

    def ask_for_button_text(call):
        locale = get_locale()
        set_state(call.from_user.id, {"action": "add_button_text"})
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton(locale["cancel_button"], callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="ئێستا ناوی دوگمەی نوێ بنێرە (نموونە: کەناڵی فێرکاری 📢).",
            reply_markup=kb
        )

    def ask_for_button_type(message):
        user_id = str(message.from_user.id)
        button_text = message.text.strip()
        set_state(user_id, {"action": "add_button_type", "text": button_text})

        kb = InlineKeyboardMarkup(row_width=1)
        kb.add(
            InlineKeyboardButton("🌐 لینکی ڕاستەوخۆ (URL)", callback_data="btn_type_url"),
            InlineKeyboardButton("📲 ئەپلیکەیشنی بچووک (WebApp)", callback_data="btn_type_webapp")
        )
        kb.add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="cancel_action"))

        bot.send_message(user_id, "جۆری دوگمەکە هەڵبژێرە:", reply_markup=kb)

    def ask_for_button_link(call):
        user_id = str(call.from_user.id)
        state = get_state(user_id)
        btn_type = call.data.replace("btn_type_", "")
        state["type"] = btn_type
        state["action"] = "add_button_link"
        set_state(user_id, state)

        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="ئێستا لینکی دوگمەکە بنێرە:",
            reply_markup=kb
        )

    def save_custom_button(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        button_link = message.text.strip()

        custom_buttons = get_json_data(custom_buttons_file)
        new_button_id = f"custom_{int(time.time())}"

        custom_buttons[new_button_id] = {
            "text": state["text"],
            "type": state["type"],
            "link": button_link
        }

        save_json_data(custom_buttons_file, custom_buttons)
        bot.send_message(user_id, f"✅ دوگمەی '<b>{state['text']}</b>' بە سەرکەوتوویی پاشەکەوت کرا!")
        set_state(user_id, None)

        from telebot.types import CallbackQuery, Message, User, Chat
        user = User(message.from_user.id, message.from_user.first_name, is_bot=False)
 chat = Chat(message.chat.id, 'private')
        msg = Message(message_id=message.message_id, from_user=user, date=None, chat=chat, content_type='text', options={}, json_string="")
        call = CallbackQuery(id='dummy_call', from_user=user, data='manage_buttons', chat_instance=None, json_string="", message=msg)
        bot.send_message(message.chat.id, "لیستەکە نوێ کرایەوە:")
        buttons_management_panel(call)

    # --- دەستپێکی بەڕێوەبردنی پارەدانی ئاسایی (بۆ بۆتی دروستکراو) ---
    def payment_management_panel(call):
        locale = get_locale()
        kb = InlineKeyboardMarkup(row_width=1)
        payment_methods = get_json_data(payment_methods_file)
        response_text = "💳 <b>بەڕێوەبردنی ڕێگاکانی پارەدان</b>\n\n"
        if payment_methods:
            response_text += "ڕێگاکانی پارەدانی ئێستا:\n"
            for method_name in payment_methods:
                kb.add(InlineKeyboardButton(f"🗑️ سڕینەوە: {method_name}", callback_data=f"delete_payment_{method_name}"))
        else:
            response_text += "هێشتا هیچ ڕێگایەکی پارەدان زیاد نەکراوە."
        kb.add(InlineKeyboardButton("➕ زیادکردنی ڕێگای پارەدانی نوێ", callback_data="add_payment_method"))
        kb.add(InlineKeyboardButton(locale["back_button"], callback_data="back_to_admin"))
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, message_id=call.message.message_id,
                text=response_text, reply_markup=kb
            )
        except Exception as e:
            print(f"Error in payment_management_panel: {e}")

    def ask_for_payment_method_type(call):
        kb = InlineKeyboardMarkup(row_width=2)
        wallets = ["Vodafone Cash", "Etisalat Cash", "Orange Cash", "We Pay", "Binance", "Payeer", "Perfect Money", "هی تر"]
        buttons = [InlineKeyboardButton(w, callback_data=f"payment_type_{w}") for w in wallets]
        kb.add(*buttons)
        kb.add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="manage_payment_methods"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text="جۆری گەمۆکەکە هەڵبژێرە کە دەتەوێت زیاد بکەیت:", reply_markup=kb
        )

    def ask_for_payment_method_name(call):
        wallet_type = call.data.split('_')[-1]
        prompt_message = f"ئێستا ناوی تایبەتی گەمۆکەکە بنێرە بۆ <b>{wallet_type}</b>."
        set_state(call.from_user.id, {"action": "add_payment_name", "type": wallet_type})
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="cancel_action"))
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.message_id,
            text=prompt_message, reply_markup=kb
        )

    def ask_for_payment_address(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        state["name"] = message.text.strip()
        state["action"] = "add_payment_address"
        set_state(user_id, state)
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="cancel_action"))
        bot.send_message(user_id, "ئێستا ژمارە یان ناونیشانی گەمۆکەکە بنێرە.", reply_markup=kb)

    def ask_for_payment_price(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
        state["address"] = message.text.strip()
        state["action"] = "add_payment_price"
        set_state(user_id, state)
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 هەڵوەشاندنەوە", callback_data="cancel_action"))
        bot.send_message(user_id, "ئێستا نرخی بەشداری بۆ <b>هەر مانگێک</b> بنێرە (تەنها ژمارە).", reply_markup=kb)

    def save_payment_method(message):
        user_id = str(message.from_user.id)
        state = get_state(user_id)
[8/1/2026 4:59 AM] Shwan Rasam: try:
            price = float(message.text.strip())
        except ValueError:
            bot.reply_to(message, "❌ نرخەکە نادروستە. تکایە تەنها ژمارە بنێرە.")
            return
        method_name = state["name"]
        method_address = state["address"]
        payment_methods = get_json_data(payment_methods_file)
        payment_methods[method_name] = {"address": method_address, "price_per_month": price}
        save_json_data(payment_methods_file, payment_methods)
        bot.send_message(user_id, f"✅ ڕێگای پارەدانی '<b>{method_name}</b>' بە سەرکەوتوویی پاشەکەوت کرا.")
        set_state(user_id, None)

        from telebot.types import CallbackQuery, Message, User, Chat
        user = User(message.from_user.id, message.from_user.first_name, is_bot=False)
        chat = Chat(message.chat.id, 'private')
        msg = Message(message_id=message.message_id, from_user=user, date=None, chat=chat, content_type='text', options={}, json_string="")
        call = CallbackQuery(id='dummy_call', from_user=user, data='manage_payment_methods', chat_instance=None, json_string="", message=msg)
        bot.send_message(message.chat.id, "لیستەکە نوێ کرایەوە:")
        payment_management_panel(call)

    def delete_payment_method(call):
        method_to_delete = call.data.replace("delete_payment_", "")
        payment_methods = get_json_data(payment_methods_file)
        if method_to_delete in payment_methods:
            del payment_methods[method_to_delete]
            save_json_data(payment_methods_file, payment_methods)
            bot.answer_callback_query(call.id, f"✅ '{method_to_delete}' بە سەرکەوتوویی سڕایەوە.")
            payment_management_panel(call)
        else:
            bot.answer_callback_query(call.id, "❌ ئەم ڕێگای پارەدانە ئیتر بوونی نییە.", show_alert=True)

    # ... دواتر بەشی پەیوەندییەکانی کۆڵباک و pollingـی بۆتی دروستکراو دێت کە لێرەدا ناهێڵمەوە (خۆماڵی). بەڵام دەبێت لە کۆتاییدا infinity_polling بۆ ئەم بۆتە بانگ بکرێت.
    # ئەم بەشە لە کۆدی ڕاستەقینەدا هەیە، بەڵام بۆ خالصکردنەوە من لە کۆتا پەیوەندیدا pollingـەکە دادەنێم.
    try:
        bot_username = bot.get_me().username
        print(f"✅ Index bot @{bot_username} is running...")
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Index bot with token {token} stopped due to error: {e}")
        if token in running_bot_threads:
            del running_bot_threads[token]

# ============================================================
# ===   Flask server بۆ وەرگرتنی webhookی factory_bot    ===
# ============================================================
app = Flask(name)

@app.route(f'/{FACTORY_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        factory_bot.process_new_updates([update])
        return ''
    else:
        return 'Bad request', 403

@app.route('/')
def index():
    return 'Factory bot is running!'

if name == 'main':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
