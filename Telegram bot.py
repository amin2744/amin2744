import telebot
import json
import os
import hashlib
from telebot import types

# --- إعدادات عامة ---
TOKEN = "7301740401:AAFJgJYcMz2A4klSo2MlIdsWKoVHeChzp1E"
ADMIN_PASSWORD = "tiktok1998"
ADMIN_HASH = hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()
ADMIN_IDS = {}  # {"user_id": "admin_name"}

def load_data():
    global ADMIN_IDS
    if not os.path.exists("config.json"):
        data = {
            "accounts": [],
            "users": {},
            "paid": [],
            "admin_added": [],
            "admins": {}
        }
        save_data(data)
    with open("config.json", "r") as f:
        data = json.load(f)
        ADMIN_IDS = data.get("admins", {})
    return data

def save_data(data):
    data["admins"] = ADMIN_IDS
    with open("config.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

bot = telebot.TeleBot(TOKEN)

# --- واجهة البدء ---
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("👤 مستخدم عادي", "👑 أدمن")
    bot.send_message(
        message.chat.id,
        "مرحباً بك! يرجى اختيار نوع الحساب:",
        reply_markup=keyboard
    )

# --- مسار المستخدم العادي ---
@bot.message_handler(func=lambda m: m.text == "👤 مستخدم عادي")
def regular_user(message):
    user_id = str(message.chat.id)
    data = load_data()
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "points": 0,
            "added": [],
            "followed": []
        }
        save_data(data)
    show_user_menu(message)

def show_user_menu(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🚀 زيادة المتابعات", "➕ إضافة حساب", "🏆 نقاطي")
    bot.send_message(
        message.chat.id,
        "مرحباً بك في نظام زيادة المتابعات!",
        reply_markup=keyboard
    )

# --- مسار الأدمن ---
@bot.message_handler(func=lambda m: m.text == "👑 أدمن")
def admin_login(message):
    msg = bot.send_message(
        message.chat.id,
        "🔒 الرجاء إدخال كلمة سر الأدمن:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, verify_admin)

def verify_admin(message):
    user_id = str(message.chat.id)
    password_hash = hashlib.sha256(message.text.encode()).hexdigest()
    if password_hash == ADMIN_HASH:
        msg = bot.send_message(
            message.chat.id,
            "✅ تم التحقق بنجاح! الرجاء إدخال اسمك للأدمن:"
        )
        bot.register_next_step_handler(msg, lambda m: save_admin(m, user_id))
    else:
        bot.send_message(
            message.chat.id,
            "❌ كلمة السر خاطئة!",
            reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 مستخدم عادي", "👑 أدمن")
        )

def save_admin(message, user_id):
    ADMIN_IDS[str(user_id)] = message.text
    save_data(load_data())
    bot.send_message(
        message.chat.id,
        f"✅ تم تسجيلك كأدمن: {message.text}",
        reply_markup=types.ReplyKeyboardRemove()
    )
    show_admin_panel(message)

def show_admin_panel(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "📊 الإحصائيات", "📌 إضافة مدفوع",
        "👥 إدارة المستخدمين", "✏️ تعديل حساب",
        "🗑️ حذف حساب", "🚪 تسجيل خروج"
    ]
    keyboard.add(*buttons)
    admin_name = ADMIN_IDS.get(str(message.chat.id), "")
    bot.send_message(
        message.chat.id,
        f"👑 مرحباً {admin_name}",
        reply_markup=keyboard
    )

@bot.message_handler(func=lambda m: m.text == "🚪 تسجيل خروج" and is_admin(m.chat.id))
def admin_logout(message):
    user_id = str(message.chat.id)
    if user_id in ADMIN_IDS:
        del ADMIN_IDS[user_id]
        save_data(load_data())
    bot.send_message(
        message.chat.id,
        "✅ تم تسجيل الخروج بنجاح",
        reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add("👤 مستخدم عادي", "👑 أدمن")
    )

# --- وظائف المستخدم العادي ---
@bot.message_handler(func=lambda m: m.text == "➕ إضافة حساب" and not is_admin(m.chat.id))
def add_account(message):
    user_id = str(message.chat.id)
    data = load_data()
    if len(data["users"][user_id]["added"]) >= 1:
        bot.send_message(message.chat.id, "❌ يمكنك إضافة حساب واحد فقط")
        return
    msg = bot.send_message(message.chat.id, "أرسل اسم الحساب (مثال: @username):")
    bot.register_next_step_handler(msg, lambda m: save_account(m, user_id))

def save_account(message, user_id):
    username = message.text.strip().lower()
    if not username.startswith("@"):
        return bot.send_message(message.chat.id, "⚠ يجب أن يبدأ الحساب ب @")
    data = load_data()
    if username in data["accounts"] + data["paid"] + data["admin_added"]:
        return bot.send_message(message.chat.id, "⚠ الحساب موجود مسبقاً")
    data["accounts"].append(username)
    data["users"][user_id]["added"].append(username)
    save_data(data)
    bot.send_message(message.chat.id, f"✅ تمت إضافة {username}")

@bot.message_handler(func=lambda m: m.text == "🚀 زيادة المتابعات" and not is_admin(m.chat.id))
def show_accounts(message):
    user_id = str(message.chat.id)
    data = load_data()
    accounts = (
        [acc for acc in data["paid"] if acc not in data["users"][user_id]["followed"]] +
        [acc for acc in data["admin_added"] if acc not in data["users"][user_id]["followed"]] +
        [acc for acc in data["accounts"] if acc not in data["users"][user_id]["followed"]]
    )[:5]
    if not accounts:
        return bot.send_message(message.chat.id, "⏳ لا توجد حسابات متاحة حالياً")
    for acc in accounts:
        bot.send_message(message.chat.id, f"تابع هذا الحساب: {acc}")
        data["users"][user_id]["followed"].append(acc)
        data["users"][user_id]["points"] = data["users"][user_id].get("points", 0) + 5
    save_data(data)
    bot.send_message(message.chat.id, f"🎯 لقد حصلت على {5*len(accounts)} نقطة!")

@bot.message_handler(func=lambda m: m.text == "🏆 نقاطي" and not is_admin(m.chat.id))
def show_points(message):
    user_id = str(message.chat.id)
    data = load_data()
    points = data["users"].get(user_id, {}).get("points", 0)
    bot.send_message(message.chat.id, f"🎯 لديك {points} نقطة")

# --- وظائف الأدمن ---
@bot.message_handler(func=lambda m: m.text == "📊 الإحصائيات" and is_admin(m.chat.id))
def bot_stats(message):
    data = load_data()
    stats = f"""📈 إحصائيات البوت:

👥 المستخدمون: {len(data['users'])}
📌 الحسابات: {len(data['accounts'])+len(data['paid'])+len(data['admin_added'])}
💎 المدفوعة: {len(data['paid'])}
🛡 أدمن: {len(data['admin_added'])}
📊 عادية: {len(data['accounts'])}
"""
    bot.send_message(message.chat.id, stats)

@bot.message_handler(func=lambda m: m.text == "📌 إضافة مدفوع" and is_admin(m.chat.id))
def add_paid_account(message):
    msg = bot.send_message(message.chat.id, "أرسل اسم الحساب المدفوع (مثال: @username):")
    bot.register_next_step_handler(msg, process_paid_account)

def process_paid_account(message):
    username = message.text.strip().lower()
    data = load_data()
    if username in data['paid']:
        bot.send_message(message.chat.id, "⚠️ هذا الحساب مضاف مسبقاً")
    else:
        data['paid'].append(username)
        save_data(data)
        bot.send_message(message.chat.id, f"✅ تمت إضافة {username} كحساب مدفوع")

@bot.message_handler(func=lambda m: m.text == "👥 إدارة المستخدمين" and is_admin(m.chat.id))
def manage_users(message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("عرض المستخدمين", callback_data="list_users"),
        types.InlineKeyboardButton("ترقية أدمن", callback_data="promote_user")
    )
    bot.send_message(message.chat.id, "اختر إجراء:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "list_users")
def list_users(call):
    data = load_data()
    users_info = "👥 قائمة المستخدمين:\n\n"
    for user_id, info in data["users"].items():
        users_info += f"🆔 {user_id}\n⭐ نقاط: {info['points']}\n📌 حسابات: {len(info['added'])}\n\n"
    bot.send_message(call.message.chat.id, users_info)

@bot.callback_query_handler(func=lambda call: call.data == "promote_user")
def promote_user(call):
    msg = bot.send_message(call.message.chat.id, "أرسل ID المستخدم لترقيته:")
    bot.register_next_step_handler(msg, process_promotion)

def process_promotion(message):
    user_id = message.text.strip()
    if user_id in ADMIN_IDS:
        bot.send_message(message.chat.id, "⚠️ هذا المستخدم أدمن بالفعل")
    else:
        msg = bot.send_message(message.chat.id, "أرسل اسم الأدمن الجديد:")
        bot.register_next_step_handler(msg, lambda m: save_promotion(m, user_id))

def save_promotion(message, user_id):
    ADMIN_IDS[user_id] = message.text
    save_data(load_data())
    bot.send_message(message.chat.id, f"✅ تم ترقية {user_id} إلى أدمن")

@bot.message_handler(func=lambda m: m.text == "✏️ تعديل حساب" and is_admin(m.chat.id))
def edit_account(message):
    msg = bot.send_message(message.chat.id, "أرسل اسم الحساب الحالي:")
    bot.register_next_step_handler(msg, process_edit)

def process_edit(message):
    old_username = message.text.strip().lower()
    data = load_data()
    account_type = None
    if old_username in data['paid']:
        account_type = 'paid'
    elif old_username in data['admin_added']:
        account_type = 'admin_added'
    elif old_username in data['accounts']:
        account_type = 'accounts'
    if not account_type:
        bot.send_message(message.chat.id, "❌ الحساب غير موجود")
        return
    msg = bot.send_message(message.chat.id, "أرسل الاسم الجديد:")
    bot.register_next_step_handler(msg, lambda m: save_edit(m, old_username, account_type))

def save_edit(message, old_username, account_type):
    new_username = message.text.strip().lower()
    data = load_data()
    data[account_type].remove(old_username)
    data[account_type].append(new_username)
    save_data(data)
    bot.send_message(message.chat.id, f"✅ تم تغيير {old_username} إلى {new_username}")

@bot.message_handler(func=lambda m: m.text == "🗑️ حذف حساب" and is_admin(m.chat.id))
def delete_account(message):
    msg = bot.send_message(message.chat.id, "أرسل اسم الحساب لحذفه:")
    bot.register_next_step_handler(msg, process_delete)

def process_delete(message):
    username = message.text.strip().lower()
    data = load_data()
    deleted = False
    for account_type in ['paid', 'admin_added', 'accounts']:
        if username in data[account_type]:
            data[account_type].remove(username)
            deleted = True
            break
    if deleted:
        save_data(data)
        bot.send_message(message.chat.id, f"✅ تم حذف {username} بنجاح")
    else:
        bot.send_message(message.chat.id, "❌ الحساب غير موجود")

# --- تشغيل البوت بالـ polling ---
if __name__ == "__main__":
    print("🤖 البوت يعمل الآن ...")
    bot.polling()
