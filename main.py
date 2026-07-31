import os
import sys
import time
import math
import random
import logging
import telebot
from telebot import types

# Logging tizimini sozlash (Xatoliklarni kuzatib borish uchun)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("So2ServisBot")

# Muhit o'zgaruvchilaridan token va admin ID'ni olish
TOKEN = "8819506227:AAGWqjDtsqjEbQlvlnXb29XbEQgZH2-bHus"
ADMIN_ID = 8980446304

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- XOTIRADAGI KENGAYtIRILGAN BAZALAR ---
user_balances = {}       # {user_id: float_balance}
pending_orders = {}      # {order_id: {user_id, amount, method, timestamp}}
user_states = {}         # {user_id: state_string}
user_activity_log = {}   # {user_id: last_action_timestamp}
ai_memory_context = {}   # Kelgusida sun'iy intellekt uchun foydalanuvchi konteksti

# --- ASOSIY HAVOLALAR VA REKVIZITLAR ---
PROOF_CHANNEL = "@So2servis_otziv"
SUPPORT_ADMIN = "@So2servis"
SHOP_NAME = "So2servis Gold Shop"

CARD_DETAILS = {
    "number": "5614 6821 1244 8420",
    "holder": "Ergashev Sardor",
    "bank": "Uzcard / Humo"
}

logger.info("1-qism muvaffaqiyatli yuklandi: Sozlamalar va bazalar tayyor.")
# --- 2-QISM: Standoff 2 Dinamik Narx Hisoblash (USP Gost va 0.23 Tiyin Talabi bilan) ---
def calculate_standoff_price(gold_amount: int) -> float:
    """
    Sizning talabingiz bo'yicha:
    1. Gold miqdori 4 ga bo'linib, 5 ga ko'paytiriladi (masalan: 100 / 4 * 5 = 125).
    2. Oxirgi qismi qat'iy 0.23 tiyin (sent) bilan tugashi shart.
       (Masalan: 125.23 so'm).
    """
    try:
        if gold_amount < 50:
            return 0.0
        # 4 ga bo'lib, 5 ga ko'paytiramiz va butun qismini olamiz
        base_calculation = (gold_amount / 4.0) * 5.0
        # Tiyin qismini qat'iy .23 qilib belgilaymiz
        final_price = float(int(base_calculation)) + 0.23
        return round(final_price, 2)
    except Exception as e:
        logger.error(f"Narx hisoblashda xatolik: {e}")
        return 0.0

def validate_user_gold_input(text_input: str) -> int:
    """
    Foydalanuvchi kiritgan gold miqdorini xavfsiz tekshirish va o'tkazish.
    """
    clean_text = text_input.strip()
    if not clean_text.isdigit():
        return -1
    amount = int(clean_text)
    if amount < 50:
        return -2
    return amount

logger.info("2-qism muvaffaqiyatli yuklandi: Maxsus USP Gost va 0.23 formula mexizmi tayyor.")
# --- 3-QISM: Xavfsizlik va Dekoratorlar ---
def is_admin(user_id: int) -> bool:
    """
    Foydalanuvchi admin ekanligini qat'iy tekshiradi.
    """
    return user_id == ADMIN_ID

def log_user_action(user_id: int, action_name: str):
    """
    Foydalanuvchi harakatlarini log qilish va vaqtini saqlash.
    """
    user_activity_log[user_id] = time.time()
    logger.info(f"Foydalanuvchi ID: {user_id} | Harakat: {action_name}")

logger.info("3-qism muvaffaqiyatli yuklandi: Xavfsizlik tizimi faol.")
# --- 4-QISM: Bosh Menyu va Start ---
@bot.message_handler(commands=['start', 'menu'])
def handle_start_command(message):
    user_id = message.from_user.id
    log_user_action(user_id, "START_COMMAND")
    
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_standoff = types.InlineKeyboardButton("🟡 Standoff 2 (Gold)", callback_data="buy_standoff_menu")
    btn_balance = types.InlineKeyboardButton("💳 Balansni tekshirish", callback_data="check_my_balance")
    btn_topup = types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup")
    btn_contact = types.InlineKeyboardButton("📞 Aloqa va Isbotlar", callback_data="show_contacts")
    
    markup.add(btn_standoff, btn_balance, btn_topup, btn_contact)

    if is_admin(user_id):
        btn_admin = types.InlineKeyboardButton("🛠 Admin Panel", callback_data="open_admin_panel")
        markup.add(btn_admin)

    welcome_text = (
        f"✨ Assalomu alaykum, **{message.from_user.first_name}**!\n"
        f"🚀 **{SHOP_NAME}** rasmiy xizmat ko'rsatish botiga xush kelibsiz.\n\n"
        f"Kerakli bo'limni tanlang:"
    )

    try:
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Start menyusini yuborishda xato: {e}")

logger.info("4-qism muvaffaqiyatli yuklandi: Start menyusi tayyor.")
# --- 5-QISM: Aloqa va Navigatsiya ---
@bot.callback_query_handler(func=lambda call: call.data == "show_contacts")
def callback_show_contacts(call):
    user_id = call.from_user.id
    log_user_action(user_id, "VIEW_CONTACTS")
    
    text = (
        f"📞 **Aloqa va Ishonch Markazi:**\n\n"
        f"• Murojaat uchun admin: {SUPPORT_ADMIN}\n"
        f"• Ishonch va isbotlar kanali: {PROOF_CHANNEL}\n\n"
        f"Barcha zakazlar va to'lovlar ushbu kanal orqali kafolatlanadi!"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="return_to_main"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "return_to_main")
def callback_return_main(call):
    user_id = call.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_standoff = types.InlineKeyboardButton("🟡 Standoff 2 (Gold)", callback_data="buy_standoff_menu")
    btn_balance = types.InlineKeyboardButton("💳 Balansni tekshirish", callback_data="check_my_balance")
    btn_topup = types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup")
    btn_contact = types.InlineKeyboardButton("📞 Aloqa va Isbotlar", callback_data="show_contacts")
    
    markup.add(btn_standoff, btn_balance, btn_topup, btn_contact)
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="open_admin_panel"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text("🏠 **Asosiy menyu:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

logger.info("5-qism muvaffaqiyatli yuklandi: Navigatsiya tayyor.")
# --- 6-QISM: Balans Tizimi ---
@bot.callback_query_handler(func=lambda call: call.data == "check_my_balance")
def callback_check_balance(call):
    user_id = call.from_user.id
    log_user_action(user_id, "CHECK_BALANCE")
    
    current_balance = user_balances.get(user_id, 0.0)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="return_to_main")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"💳 **Shaxsiy Hisobingiz:**\n\n"
        f"• Joriy balans: **{current_balance:,.2f} so'm**\n"
        f"• ID raqamingiz: `{user_id}`",
        call.message.chat.id, call.message.message_id,
        reply_markup=markup, parse_mode="Markdown"
    )

logger.info("6-qism muvaffaqiyatli yuklandi: Balans moduli ishlayapti.")
# --- 7-QISM: Standoff 2 Xarid va USP Gost Sharti ---
@bot.callback_query_handler(func=lambda call: call.data == "buy_standoff_menu")
def callback_standoff_menu(call):
    user_id = call.from_user.id
    log_user_action(user_id, "OPEN_STANDOFF_MENU")
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🟡 **Standoff 2 Gold Xarid qilish**\n\n"
        "⚠️ **Muhim shart:** Goldlar sizga bozorda **USP | Gost** skini orqali yetkazib beriladi! Marketda USP | Gost skiningiz tayyor tursin.\n\n"
        "• Minimal miqdor: **50 gold**\n"
        "• Narxlar oxiri har doim **.23** tiyin bilan tugaydi.\n\n"
        "✍️ Iltimos, sotib olmoqchi bo'lgan **gold miqdorini raqamda** yozib yuboring (masalan: `100`, `300`, `1500`):",
        parse_mode="Markdown"
    )
    user_states[user_id] = "awaiting_gold_input"
    bot.register_next_step_handler(msg, process_gold_amount_step)

def process_gold_amount_step(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "awaiting_gold_input":
        return

    validation_result = validate_user_gold_input(message.text)
    
    if validation_result == -1:
        msg = bot.send_message(message.chat.id, "❌ Noto'g'ri format! Iltimos, faqat raqam kiriting (masalan: 100):")
        bot.register_next_step_handler(msg, process_gold_amount_step)
        return
    elif validation_result == -2:
        msg = bot.send_message(message.chat.id, "❌ Minimal miqdor 50 gold bo'lishi kerak. Qaytadan kiriting:")
        bot.register_next_step_handler(msg, process_gold_amount_step)
        return

    gold_amount = validation_result
    calculated_price = calculate_standoff_price(gold_amount)
    user_balances.setdefault(user_id, 0.0)
    user_balance = user_balances[user_id]

    markup = types.InlineKeyboardMarkup(row_width=1)
    if user_balance >= calculated_price:
        markup.add(types.InlineKeyboardButton(f"✅ Balansdan to'lash ({calculated_price:,.2f} so'm)", callback_data=f"pay_so2_bal_{gold_amount}_{calculated_price}"))
    else:
        markup.add(types.InlineKeyboardButton("➕ Balans yetarli emas (To'ldirish)", callback_data="start_topup"))
    
    markup.add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_to_main"))

    bot.send_message(
        message.chat.id,
        f"🛒 **Mahsulot:** Standoff 2 — **{gold_amount} Gold**\n"
        f"🔫 **Metod:** USP | Gost skini orqali\n"
        f"💰 **Hisoblangan narx:** **{calculated_price:,.2f} so'm**\n"
        f"💳 **Sizning balansingiz:** **{user_balance:,.2f} so'm**\n\n"
        f"{'✅ Balansingizda mablagʻ yetarli!' if user_balance >= calculated_price else '⚠️ Balansingizda mablagʻ yetarli emas. Iltimos, hisobni toʻldiring.'}",
        reply_markup=markup, parse_mode="Markdown"
    )
    user_states.pop(user_id, None)

logger.info("7-qism yangilandi: USP Gost va .23 kalyulator qoidasi qo'shildi.") 
# --- 8-QISM: Balansdan To'lov, USP Gost Skrinshoti va Zakazlar ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_so2_bal_"))
def callback_pay_so2_balance(call):
    data_parts = call.data.split("_")
    gold_amount = int(data_parts[3])
    total_price = float(data_parts[4])
    user_id = call.from_user.id

    user_balances.setdefault(user_id, 0.0)

    if user_balances[user_id] >= total_price:
        user_balances[user_id] -= total_price
        order_reference = random.randint(100000, 999999)

        # Mijozdan USP Gost skini qoyilganini tasdiqlovchi skrinshotni so'raymiz
        bot.answer_callback_query(call.id, "Mablag' yechildi! Endi skrinshot yuboring.")
        msg = bot.send_message(
            call.message.chat.id,
            f"✅ **Muvaffaqiyatli to'landi!**\n\n"
            f"🟡 Miqdor: **{gold_amount} Gold**\n"
            f"💵 Yechildi: **{total_price:,.2f} so'm**\n\n"
            f"📸 **Oxirgi qadam:** Marketga **USP | Gost** skinini shu summa (**{total_price:,.2f}**) bilan qo'yganingizni tasdiqlovchi **skrinshot rasmini** yuboring (admin tekshirib berishi uchun):",
            parse_mode="Markdown"
        )
        user_states[user_id] = f"waiting_usp_skin_screenshot_{order_reference}_{gold_amount}"
        bot.register_next_step_handler(msg, process_usp_skin_screenshot)
    else:
        bot.answer_callback_query(call.id, "Xatolik: Balansingiz yetarli emas!", show_alert=True)

def process_usp_skin_screenshot(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")

    if not state.startswith("waiting_usp_skin_screenshot_"):
        return

    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ Iltimos, USP | Gost skini qo'yilganini tasdiqlovchi **skrinshot rasmini** yuboring:")
        bot.register_next_step_handler(msg, process_usp_skin_screenshot)
        return

    parts = state.split("_")
    order_reference = parts[4]
    gold_amount = parts[5]
    photo_file_id = message.photo[-1].file_id
    user_states.pop(user_id, None)

    admin_notification = (
        f"🚨 **Yangi USP Gost Zakazi! (#{order_reference})**\n\n"
        f"👤 Mijoz: @{message.from_user.username or 'Mavjud_emas'} (ID: `{user_id}`)\n"
        f"🟡 Gold miqdori: **{gold_amount} Gold**\n"
        f"🔫 Skin: **USP | Gost**\n"
        f"💬 Status: Mijoz skin qo'yib skrinshot yubordi!"
    )
    
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✅ Gold berildi / Yakunlash", callback_data=f"admin_complete_order_{user_id}_{gold_amount}"))

    try:
        bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_notification, reply_markup=admin_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Adminga USP Gost skrinshotini yuborishda xato: {e}")

    bot.send_message(
        message.chat.id,
        f"✅ **Skrinshot adminga yuborildi!**\n\n"
        f"Admin USP | Gost skiningizni tekshirib, tez orada goldni o'tkazib beradi.\n"
        f"📢 Isbotlar kanali: {PROOF_CHANNEL}",
        parse_mode="Markdown"
    )

logger.info("8-qism yangilandi: USP Gost skrinshotini qabul qilish mexizmi ishga tushdi.")
# --- 9-QISM: Hisobni To'ldirish va Cheklar ---
@bot.callback_query_handler(func=lambda call: call.data == "start_topup")
def callback_start_topup(call):
    user_id = call.from_user.id
    log_user_action(user_id, "START_TOPUP")
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "➕ **Hisobni to'ldirish bo'limi**\n\n"
        "✍️ Balansingizni qancha summaga to'ldirmoqchisiz?\n"
        "Iltimos, summani raqamlarda kiriting (masalan: `50000`):",
        parse_mode="Markdown"
    )
    user_states[user_id] = "awaiting_topup_amount"
    bot.register_next_step_handler(msg, process_topup_amount_step)

def process_topup_amount_step(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "awaiting_topup_amount":
        return

    clean_text = message.text.strip().replace(" ", "").replace(",", "")
    if not clean_text.replace('.', '', 1).isdigit():
        msg = bot.send_message(message.chat.id, "❌ Noto'g'ri summa! Faqat raqam kiriting (masalan: 30000):")
        bot.register_next_step_handler(msg, process_topup_amount_step)
        return

    amount = float(clean_text)
    if amount <= 0:
        msg = bot.send_message(message.chat.id, "❌ Summa 0 dan ko'p bo'lishi kerak. Qaytadan kiriting:")
        bot.register_next_step_handler(msg, process_topup_amount_step)
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Buyuk Ipak Yo'li", callback_data=f"pay_method_ipakyoli_{amount}"),
        types.InlineKeyboardButton("Payme", callback_data=f"pay_method_payme_{amount}"),
        types.InlineKeyboardButton("Click", callback_data=f"pay_method_click_{amount}"),
        types.InlineKeyboardButton("Paynet", callback_data=f"pay_method_paynet_{amount}"),
        types.InlineKeyboardButton("Bankomat", callback_data=f"pay_method_bankomat_{amount}"),
        types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_to_main")
    )

    bot.send_message(
        message.chat.id,
        f"💵 Kiritilgan summa: **{amount:,.2f} so'm**\n\n"
        f"💳 Iltimos, to'lov turini tanlang:",
        reply_markup=markup, parse_mode="Markdown"
    )
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_method_"))
def callback_select_payment_method(call):
    data_parts = call.data.split("_")
    method_name = data_parts[3].upper()
    amount = float(data_parts[4])
    user_id = call.from_user.id

    invoice_id = random.randint(10000, 99999)
    pending_orders[invoice_id] = {
        "user_id": user_id,
        "amount": amount,
        "method": method_name,
        "timestamp": time.time()
    }

    payment_info_text = (
        f"💳 **To'lov uchun rekvizitlar:**\n\n"
        f"• Tanlangan usul: **{method_name}**\n"
        f"• To'lov summasi: **{amount:,.2f} so'm**\n\n"
        f"📌 Karta raqami: `{CARD_DETAILS['number']}`\n"
        f"👤 Karta egasi: **{CARD_DETAILS['holder']}**\n"
        f"🏦 Bank: {CARD_DETAILS['bank']}\n\n"
        f"⚠️ **Diqqat:** Pulni o'tkazgandan so'ng, to'lov cheki (skrinshot) rasmini shu yerga yuboring!"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("📤 Chek rasmini yuborish", callback_data=f"upload_receipt_{invoice_id}"),
        types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="return_to_main")
    )

    bot.answer_callback_query(call.id)
    bot.edit_message_text(payment_info_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_receipt_"))
def callback_upload_receipt(call):
    invoice_id = int(call.data.split("_")[2])
    user_id = call.from_user.id
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "📸 Iltimos, to'lovni tasdiqlovchi **chek skrinshotini** rasm ko'rinishida yuboring:")
    user_states[user_id] = f"waiting_receipt_photo_{invoice_id}"
    bot.register_next_step_handler(msg, process_receipt_photo_step)

def process_receipt_photo_step(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")
    
    if not state.startswith("waiting_receipt_photo_"):
        return

    invoice_id = int(state.split("_")[3])
    order_data = pending_orders.get(invoice_id)

    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ Iltimos, matn emas, aynan **rasm (chek skrinshoti)** yuboring:")
        bot.register_next_step_handler(msg, process_receipt_photo_step)
        return

    photo_file_id = message.photo[-1].file_id
    user_states.pop(user_id, None)

    admin_caption = (
        f"📥 **Yangi To'lov Cheki Keldi! (#{invoice_id})**\n\n"
        f"👤 Mijoz: @{message.from_user.username or 'Mavjud_emas'} (ID: `{user_id}`)\n"
        f"💵 Summa: **{order_data['amount']:,.2f} so'm**\n"
        f"💳 To'lov usuli: **{order_data['method']}**"
    )

    admin_markup = types.InlineKeyboardMarkup(row_width=2)
    admin_markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash (+ Balans)", callback_data=f"admin_approve_pay_{invoice_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"admin_reject_pay_{invoice_id}")
    )

    try:
        bot.send_photo(ADMIN_ID, photo_file_id, caption=admin_caption, reply_markup=admin_markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Adminga chek yuborishda xato: {e}")

    bot.send_message(message.chat.id, f"✅ Chekingiz muvaffaqiyatli adminga yuborildi! Admin tekshirib tasdiqlagach, balansingizga qo'shiladi.\n📢 Isbotlar kanali: {PROOF_CHANNEL}")

logger.info("9-qism muvaffaqiyatli yuklandi: To'lov va chek tizimi ishlayapti.")
# --- 10-QISM: Admin Panel va Asosiy Tsikl (Polling) ---
@bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
def callback_open_admin(call):
    user_id = call.from_user.id
    if not is_admin(user_id):
        bot.answer_callback_query(call.id, "Sizda bu huquq yo'q!", show_alert=True)
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("👥 Barcha foydalanuvchilar balansi", callback_data="admin_list_balances"),
        types.InlineKeyboardButton("➕ Balans qo'shish / Ayirish", callback_data="admin_modify_balance_start"),
        types.InlineKeyboardButton("🔙 Asosiy menyu", callback_data="return_to_main")
    )

    bot.answer_callback_query(call.id)
    bot.edit_message_text("🛠 **Admin Boshqaruv Paneliga xush kelibsiz:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_list_balances")
def callback_admin_list_balances(call):
    if not is_admin(call.from_user.id):
        return

    report_text = "👥 **Foydalanuvchilar va Balanslar ro'yxati:**\n\n"
    if not user_balances:
        report_text += "Hozircha bazada foydalanuvchilar yo'q."
    else:
        for uid, bal in user_balances.items():
            report_text += f"• ID: `{uid}` — **{bal:,.2f} so'm**\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="open_admin_panel"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text(report_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_modify_balance_start")
def callback_admin_mod_start(call):
    if not is_admin(call.from_user.id):
        return

    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "✍️ Balansni o'zgartirish uchun quyidagi formatda yuboring:\n"
        "`user_id summa`\n\n"
        "*(Misol uchun qo'shish: `123456789 50000`)*\n"
        "*(Misol uchun ayirish: `123456789 -20000`)*",
        parse_mode="Markdown"
    )
    user_states[call.from_user.id] = "admin_modifying_balance_input"
    bot.register_next_step_handler(msg, process_admin_balance_modification)

def process_admin_balance_modification(message):
    if not is_admin(message.from_user.id):
        return

    try:
        parts = message.text.strip().split()
        target_uid = int(parts[0])
        delta_amount = float(parts[1])

        user_balances.setdefault(target_uid, 0.0)
        user_balances[target_uid] += delta_amount

        bot.send_message(message.chat.id, f"✅ Muvaffaqiyatli! Foydalanuvchi (`{target_uid}`) balansi o'zgartirildi. Yangi balans: **{user_balances[target_uid]:,.2f} so'm**")
        try:
            bot.send_message(target_uid, f"💳 Sizning balansingiz admin tomonidan o'zgartirildi. Joriy balansingiz: **{user_balances[target_uid]:,.2f} so'm**")
        except Exception:
            pass
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik yuz berdi: {e}\nFormatni to'g'ri kiriting (masalan: `123456789 15000`).")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_approve_pay_"))
def callback_admin_approve_payment(call):
    if not is_admin(call.from_user.id):
        return

    invoice_id = int(call.data.split("_")[3])
    order_info = pending_orders.get(invoice_id)

    if order_info:
        target_uid = order_info["user_id"]
        pay_amount = order_info["amount"]

        user_balances.setdefault(target_uid, 0.0)
        user_balances[target_uid] += pay_amount

        bot.answer_callback_query(call.id, "To'lov tasdiqlandi!")
        bot.edit_message_caption(
            f"✅ **To'lov Tasdiqlandi va Bajarildi!**\n"
            f"Foydalanuvchiga **{pay_amount:,.2f} so'm** qo'shildi.",
            call.message.chat.id, call.message.message_id, parse_mode="Markdown"
        )
        try:
            bot.send_message(target_uid, f"✅ **Tabriklaymiz!** To'lovingiz tasdiqlandi va balansingizga **{pay_amount:,.2f} so'm** qo'shildi. Xaridingiz uchun rahmat!")
        except Exception:
            pass
    else:
        bot.answer_callback_query(call.id, "Buyurtma topilmadi yoki eskirgan.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reject_pay_"))
def callback_admin_reject_payment(call):
    if not is_admin(call.from_user.id):
        return

    invoice_id = int(call.data.split("_")[3])
    order_info = pending_orders.get(invoice_id)

    if order_info:
        target_uid = order_info["user_id"]
        bot.answer_callback_query(call.id, "To'lov rad etildi.")
        bot.edit_message_caption("❌ **To'lov Rad Etildi!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        try:
            bot.send_message(target_uid, f"❌ Kechirasiz, yuborgan to'lovingiz admin tomonidan rad etildi. Sababini aniqlash uchun murojaat qiling: {SUPPORT_ADMIN}")
        except Exception:
            pass
    else:
        bot.answer_callback_query(call.id, "Buyurtma topilmadi.", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_complete_order_"))
def callback_admin_complete_order(call):
    if not is_admin(call.from_user.id):
        return

    data_parts = call.data.split("_")
    target_uid = int(data_parts[3])
    gold_amt = data_parts[4]

    bot.answer_callback_query(call.id, "Zakaz muvaffaqiyatli yakunlandi!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    try:
        bot.send_message(
            target_uid,
            f"🎉 **Zakazingiz muvaffaqiyatli yakunlandi!**\n\n"
            f"🟡 Siz sotib olgan **{gold_amt} Gold** to'liq topshirildi.\n"
            f"⭐️ Xaridingiz uchun katta rahmat!\n"
            f"📢 Isbotlar va fikrlar uchun kanalimiz: {PROOF_CHANNEL}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Mijozga zakaz tugagani haqida xabar berishda xato: {e}")

# --- BOTNI ISHGA TUSHIRISH (POLLING) ---
if __name__ == '__main__':
    logger.info("10-qism yuklandi: Bot to'liq ishga tushishga tayyor va ishga tushirildi!")
    print("🚀 So2servis Gold Shop boti muvaffaqiyatli ishga tushdi!")
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as crash_error:
            logger.critical(f"Kritik xatolik yuz berdi: {crash_error}")
            time.sleep(5)
