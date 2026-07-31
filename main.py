import os
import sys
import time
import math
import random
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# Render Web Service port talab qilgani uchun mitti HTTP server
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot status: ONLINE")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Veb-serverni orqa fonda ishga tushiramiz
threading.Thread(target=run_dummy_server, daemon=True).start()

# Logging tizimini sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("So2ServisBot")

# Telegram bot sozlamalari (TOKENNI O'ZGARTIRING)
TOKEN = "8819506227:AAFHhcQ0KWjiNiT4pgDR4301__WLMC9W2M4"
ADMIN_ID = 8980446304

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# --- XOTIRADAGI KENGAYTIRILGAN BAZALAR ---
user_balances = {}       
pending_orders = {}      
user_states = {}         
user_activity_log = {}   

# --- ASOSIY HAVOLALAR VA REKVIZITLAR ---
PROOF_CHANNEL = "@So2servis_otziv"
SUPPORT_ADMIN = "@So2servis"
SHOP_NAME = "So2servis Gold Shop"

CARD_DETAILS = {
    "number": "5614 6821 1244 8420",
    "holder": "Ergashev Sardor",
    "bank": "Uzcard / Humo"
}

# --- 2-QISM: Standoff 2 Dinamik Narx Hisoblash ---
def calculate_standoff_price(gold_amount: int) -> float:
    try:
        if gold_amount < 50:
            return 0.0
        base_calculation = (gold_amount / 4.0) * 5.0
        final_price = float(int(base_calculation)) + 0.23
        return round(final_price, 2)
    except Exception as e:
        logger.error(f"Narx hisoblashda xatolik: {e}")
        return 0.0

def validate_user_gold_input(text_input: str) -> int:
    clean_text = text_input.strip()
    if not clean_text.isdigit(): return -1
    amount = int(clean_text)
    if amount < 50: return -2
    return amount

# --- 3-QISM: Xavfsizlik va Dekoratorlar ---
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def log_user_action(user_id: int, action_name: str):
    user_activity_log[user_id] = time.time()
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

# --- 5-QISM: Aloqa va Navigatsiya ---
@bot.callback_query_handler(func=lambda call: call.data == "show_contacts")
def callback_show_contacts(call):
    user_id = call.from_user.id
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
    markup.add(
        types.InlineKeyboardButton("🟡 Standoff 2 (Gold)", callback_data="buy_standoff_menu"),
        types.InlineKeyboardButton("💳 Balansni tekshirish", callback_data="check_my_balance"),
        types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup"),
        types.InlineKeyboardButton("📞 Aloqa va Isbotlar", callback_data="show_contacts")
    )
    if is_admin(user_id): markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="open_admin_panel"))

    bot.answer_callback_query(call.id)
    bot.edit_message_text("🏠 **Asosiy menyu:**", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# --- 6-QISM: Balans Tizimi ---
@bot.callback_query_handler(func=lambda call: call.data == "check_my_balance")
def callback_check_balance(call):
    user_id = call.from_user.id
    current_balance = user_balances.get(user_id, 0.0)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="return_to_main")
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"💳 **Shaxsiy Hisobingiz:**\n\n• Joriy balans: **{current_balance:,.2f} so'm**\n• ID raqamingiz: `{user_id}`",
        call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
    ) 
    # --- 7-QISM: Standoff 2 Xarid va USP Gost Sharti ---
@bot.callback_query_handler(func=lambda call: call.data == "buy_standoff_menu")
def callback_standoff_menu(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🟡 **Standoff 2 Gold Xarid qilish**\n\n"
        "⚠️ **Muhim shart:** Goldlar bozorda **USP | Gost** skini orqali yetkaziladi!\n"
        "• Minimal miqdor: **50 gold**\n\n"
        "✍️ Iltimos, sotib olmoqchi bo'lgan **gold miqdorini raqamda** yozib yuboring:",
        parse_mode="Markdown"
    )
    user_states[user_id] = "awaiting_gold_input"
    bot.register_next_step_handler(msg, process_gold_amount_step)

def process_gold_amount_step(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "awaiting_gold_input": return
    
    val_res = validate_user_gold_input(message.text)
    if val_res == -1:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Noto'g'ri format! Faqat raqam:"), process_gold_amount_step)
        return
    elif val_res == -2:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Minimal miqdor 50 gold:"), process_gold_amount_step)
        return

    gold_amount = val_res
    calc_price = calculate_standoff_price(gold_amount)
    user_balance = user_balances.setdefault(user_id, 0.0)

    markup = types.InlineKeyboardMarkup(row_width=1)
    if user_balance >= calc_price:
        markup.add(types.InlineKeyboardButton(f"✅ Balansdan to'lash ({calc_price:,.2f} so'm)", callback_data=f"pay_so2_bal_{gold_amount}_{calc_price}"))
    else:
        markup.add(types.InlineKeyboardButton("➕ Balans yetarli emas (To'ldirish)", callback_data="start_topup"))
    markup.add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_to_main"))

    bot.send_message(message.chat.id, f"🛒 **Mahsulot:** {gold_amount} Gold\n💰 **Narx:** {calc_price:,.2f} so'm\n💳 **Balansingiz:** {user_balance:,.2f} so'm", reply_markup=markup, parse_mode="Markdown")
    user_states.pop(user_id, None)

# --- 8-QISM: To'lov va USP Gost Skrinshoti ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_so2_bal_"))
def callback_pay_so2_balance(call):
    gold_amount, total_price = int(call.data.split("_")[3]), float(call.data.split("_")[4])
    user_id = call.from_user.id
    user_balances.setdefault(user_id, 0.0)

    if user_balances[user_id] >= total_price:
        user_balances[user_id] -= total_price
        order_ref = random.randint(100000, 999999)
        bot.answer_callback_query(call.id, "Mablag' yechildi! Endi skrinshot yuboring.")
        msg = bot.send_message(
            call.message.chat.id,
            f"✅ **To'landi!** Yechildi: **{total_price:,.2f} so'm**\n"
            f"📸 **Oxirgi qadam:** Marketga **USP | Gost** skinini {total_price:,.2f} ga qo'yganingiz skrinshotini yuboring:",
            parse_mode="Markdown"
        )
        user_states[user_id] = f"waiting_usp_skin_screenshot_{order_ref}_{gold_amount}"
        bot.register_next_step_handler(msg, process_usp_skin_screenshot)
    else:
        bot.answer_callback_query(call.id, "Balansingiz yetarli emas!", show_alert=True)

def process_usp_skin_screenshot(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")
    if not state.startswith("waiting_usp_skin_screenshot_"): return

    if not message.photo:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ USP | Gost skini skrinshotini yuboring:"), process_usp_skin_screenshot)
        return

    order_ref, gold_amount = state.split("_")[4], state.split("_")[5]
    admin_notify = f"🚨 **Yangi USP Gost Zakazi! (#{order_ref})**\n👤 Mijoz ID: `{user_id}`\n🟡 Gold: **{gold_amount} Gold**"
    
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(types.InlineKeyboardButton("✅ Gold berildi", callback_data=f"admin_complete_order_{user_id}_{gold_amount}"))

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_notify, reply_markup=admin_markup, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Skrinshot adminga yuborildi!")
    user_states.pop(user_id, None) 
    # --- 9-QISM: Hisobni To'ldirish va Cheklar ---
@bot.callback_query_handler(func=lambda call: call.data == "start_topup")
def callback_start_topup(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "➕ **Hisobni to'ldirish bo'limi**\n\n✍️ Balansingizni qancha summaga to'ldirmoqchisiz?", parse_mode="Markdown")
    user_states[user_id] = "awaiting_topup_amount"
    bot.register_next_step_handler(msg, process_topup_amount_step)

def process_topup_amount_step(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "awaiting_topup_amount": return
    clean_text = message.text.strip().replace(" ", "").replace(",", "")
    if not clean_text.replace('.', '', 1).isdigit():
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Faqat raqam kiriting:"), process_topup_amount_step)
        return

    amount = float(clean_text)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("Karta orqali to'lash", callback_data=f"pay_method_karta_{amount}"))
    bot.send_message(message.chat.id, f"💵 Summa: **{amount:,.2f} so'm**\n💳 To'lov turini tanlang:", reply_markup=markup, parse_mode="Markdown")
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_method_"))
def callback_select_payment_method(call):
    amount = float(call.data.split("_")[3])
    invoice_id = random.randint(10000, 99999)
    pending_orders[invoice_id] = {"user_id": call.from_user.id, "amount": amount}

    payment_info = f"💳 **Rekvizitlar:**\n• Summa: **{amount:,.2f} so'm**\n📌 Karta: `{CARD_DETAILS['number']}`\n👤 Ega: {CARD_DETAILS['holder']}"
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("📤 Chek rasmini yuborish", callback_data=f"upload_receipt_{invoice_id}"))
    bot.edit_message_text(payment_info, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload_receipt_"))
def callback_upload_receipt(call):
    invoice_id = int(call.data.split("_")[2])
    msg = bot.send_message(call.message.chat.id, "📸 To'lov cheki skrinshotini yuboring:")
    user_states[call.from_user.id] = f"waiting_receipt_photo_{invoice_id}"
    bot.register_next_step_handler(msg, process_receipt_photo_step)

def process_receipt_photo_step(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")
    if not state.startswith("waiting_receipt_photo_"): return
    invoice_id = int(state.split("_")[3])
    if not message.photo:
        bot.register_next_step_handler(bot.send_message(message.chat.id, "❌ Faqat rasm (chek) yuboring:"), process_receipt_photo_step)
        return

    admin_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"admin_approve_pay_{invoice_id}"))
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📥 **Yangi To'lov (#{invoice_id})**", reply_markup=admin_markup)
    bot.send_message(message.chat.id, "✅ Chek adminga yuborildi!")
    user_states.pop(user_id, None)

# --- 10-QISM: Admin Panel va Ishga tushirish ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_approve_pay_"))
def callback_admin_approve_payment(call):
    if not is_admin(call.from_user.id): return
    invoice_id = int(call.data.split("_")[3])
    order_info = pending_orders.get(invoice_id)
    if order_info:
        user_balances.setdefault(order_info["user_id"], 0.0)
        user_balances[order_info["user_id"]] += order_info["amount"]
        bot.edit_message_caption("✅ **To'lov Tasdiqlandi!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_complete_order_"))
def callback_admin_complete_order(call):
    if not is_admin(call.from_user.id): return
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(int(call.data.split("_")[3]), "🎉 **Zakazingiz muvaffaqiyatli yakunlandi!**", parse_mode="Markdown")

if __name__ == '__main__':
    print("🚀 So2servis Gold Shop boti muvaffaqiyatli ishga tushdi!")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            logger.critical(f"Kritik xato: {e}")
            time.sleep(5)
