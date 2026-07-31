import os
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import telebot
from telebot import types

# --- RENDER UCHUN MITTI SERVER ---
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- SOZLAMALAR VA BAZALAR ---
TOKEN = "8819506227:AAFHhcQ0KWjiNiT4pgDR4301__WLMC9W2M4"
ADMIN_ID = 8980446304 # O'zingizning ID raqamingiz

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

user_balances = {}       # Balanslar 
pending_orders = {}      # Kutilayotgan to'lovlar
user_states = {}         # Foydalanuvchi qaysi bosqichdaligi
all_users = set()        # Statistika va rassilka uchun hamma foydalanuvchilar bazasi

PROOF_CHANNEL = "@So2servis_otziv"
SUPPORT_ADMIN = "@So2servis"
# --- ASOSIY MENYU VA O'YINLAR ---
@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    user_id = message.from_user.id
    all_users.add(user_id) 
    
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟡 Standoff 2", callback_data="buy_standoff"),
        types.InlineKeyboardButton("🪂 PUBG Mobile", callback_data="dev_mode"),
        types.InlineKeyboardButton("🟥 Roblox", callback_data="dev_mode"),
        types.InlineKeyboardButton("🔥 Free Fire", callback_data="dev_mode"),
        types.InlineKeyboardButton("🌵 Brawl Stars", callback_data="dev_mode")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Balansni tekshirish", callback_data="check_balance"),
        types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup")
    )
    markup.add(types.InlineKeyboardButton("📞 Aloqa va Isbotlar", callback_data="show_contacts"))
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="open_admin_panel"))

    bot.send_message(
        message.chat.id, 
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\nIltimos, o'zingizga kerakli xizmatni tanlang:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "dev_mode")
def dev_mode_callback(call):
    bot.answer_callback_query(call.id, "Tez orada ishga tushadi!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "show_contacts")
def show_contacts_callback(call):
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="return_main"))
    bot.edit_message_text(
        f"📞 **Aloqa:** {SUPPORT_ADMIN}\n📢 **Isbotlar kanali:** {PROOF_CHANNEL}",
        call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "return_main")
def return_main_callback(call):
    user_states.pop(call.from_user.id, None) 
    handle_start(call.message)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def check_balance_callback(call):
    bal = user_balances.get(call.from_user.id, 0.0)
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("➕ To'ldirish", callback_data="start_topup"),
        types.InlineKeyboardButton("🔙 Orqaga", callback_data="return_main")
    )
    bot.edit_message_text(f"💳 **Sizning balansingiz:** {bal:,.2f} so'm", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    # --- STANDOFF 2 XARID (1 GOLD = 115 SO'M) ---
@bot.callback_query_handler(func=lambda call: call.data == "buy_standoff")
def standoff_menu(call):
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main"))
    msg = bot.send_message(
        call.message.chat.id,
        "🟡 **Standoff 2 Gold Xarid qilish**\n\n"
        "📈 **Narx:** 1 Gold = 115 so'm\n\n"
        "✍️ Qancha gold kerakligini faqat raqamlarda yozib yuboring (Masalan: 100):",
        reply_markup=markup, parse_mode="Markdown"
    )
    user_states[user_id] = "awaiting_gold"
    bot.register_next_step_handler(msg, process_gold_amount)

def process_gold_amount(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "awaiting_gold": return
    
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "❌ Faqat raqam yozing:")
        bot.register_next_step_handler(msg, process_gold_amount)
        return
        
    gold_amount = int(message.text)
    if gold_amount < 50:
        msg = bot.send_message(message.chat.id, "❌ Minimal miqdor 50 gold. Qaytadan yozing:")
        bot.register_next_step_handler(msg, process_gold_amount)
        return

    total_price = float(gold_amount * 115)
    
    user_balance = user_balances.setdefault(user_id, 0.0)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if user_balance >= total_price:
        markup.add(types.InlineKeyboardButton(f"✅ Balansdan to'lash", callback_data=f"pay_so2_{gold_amount}_{total_price}"))
    else:
        markup.add(types.InlineKeyboardButton("➕ Balans yetarli emas (To'ldirish)", callback_data="start_topup"))
    markup.add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main"))

    bot.send_message(
        message.chat.id, 
        f"🛒 **Siz so'ragan miqdor:** {gold_amount} Gold\n"
        f"💵 **Hisoblangan narx:** {total_price:,.2f} so'm\n"
        f"💳 **Balansingiz:** {user_balance:,.2f} so'm", 
        reply_markup=markup, parse_mode="Markdown"
    )
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_so2_"))
def process_so2_payment(call):
    _, _, gold, price = call.data.split("_")
    gold, price = int(gold), float(price)
    user_id = call.from_user.id
    
    if user_balances[user_id] >= price:
        user_balances[user_id] -= price
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main"))
        msg = bot.send_message(call.message.chat.id, f"✅ To'landi! Yechildi: **{price:,.2f} so'm**\n\n📸 Endi USP | Gost skinini marketga {price:,.2f} summasiga qo'yganingiz skrinshotini yuboring:", reply_markup=markup, parse_mode="Markdown")
        user_states[user_id] = f"wait_skin_{gold}"
        bot.register_next_step_handler(msg, process_skin_screen)
    else:
        bot.answer_callback_query(call.id, "Balans yetarli emas!", show_alert=True)

def process_skin_screen(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")
    if not state.startswith("wait_skin_"): return
    
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ Faqat rasm ko'rinishida yuboring!")
        bot.register_next_step_handler(msg, process_skin_screen)
        return
        
    gold = state.split("_")[2]
    username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
    
    admin_markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("✅ Gold berildi", callback_data=f"done_order_{user_id}"),
        types.InlineKeyboardButton("❌ Otkaz qilish", callback_data=f"cancel_order_{user_id}_{gold}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"🚨 **Yangi Zakaz!**\n👤 User: {username}\n🆔 ID: `{user_id}`\n🟡 Gold: **{gold} Gold**", reply_markup=admin_markup, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Skrinshot adminga ketdi! Kuting, gold tez orada yetkaziladi.")
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("done_order_"))
def done_order(call):
    if call.from_user.id != ADMIN_ID: return
    user_id = int(call.data.split("_")[2])
    bot.edit_message_caption("✅ **Yakunlandi (Gold berildi)**", call.message.chat.id, call.message.message_id)
    try: bot.send_message(user_id, "🎉 **Zakazingiz topshirildi!** O'yiningizga kirib tekshiring.")
    except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_order_"))
def cancel_order(call):
    if call.from_user.id != ADMIN_ID: return
    user_id = int(call.data.split("_")[2])
    bot.edit_message_caption("❌ **Otkaz qilindi (Bekor qilingan)**", call.message.chat.id, call.message.message_id)
    try: bot.send_message(user_id, "❌ Zakazingiz admin tomonidan rad etildi. Sababini bilish uchun adminga yozing.")
    except: pass
        # --- HISOB TO'LDIRISH VA CHEK YUBORISH ---
@bot.callback_query_handler(func=lambda call: call.data == "start_topup")
def topup_start(call):
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main"))
    msg = bot.send_message(call.message.chat.id, "✍️ Qancha summa to'ldirmoqchisiz? (Faqat raqam yozing):", reply_markup=markup)
    user_states[call.from_user.id] = "wait_topup"
    bot.register_next_step_handler(msg, process_topup_amount)

def process_topup_amount(message):
    user_id = message.from_user.id
    if user_states.get(user_id) != "wait_topup": return
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "❌ Faqat raqam yozing:")
        bot.register_next_step_handler(msg, process_topup_amount)
        return
        
    amount = float(message.text)
    inv_id = random.randint(1000, 9999)
    pending_orders[inv_id] = {"id": user_id, "amount": amount}
    
    markup = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("📤 Chek rasmini yuborish", callback_data=f"receipt_{inv_id}"),
        types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main")
    )
    bot.send_message(message.chat.id, f"💳 **Rekvizit:** 8600 0000 0000 0000\n💵 **Summa:** {amount:,.2f} so'm\n\nTo'lov qilib pastdagi tugmani bosing:", reply_markup=markup, parse_mode="Markdown")
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("receipt_"))
def wait_receipt(call):
    inv_id = call.data.split("_")[1]
    msg = bot.send_message(call.message.chat.id, "📸 To'lov qilganingizni tasdiqlovchi chek skrinshotini yuboring:")
    user_states[call.from_user.id] = f"wait_receipt_{inv_id}"
    bot.register_next_step_handler(msg, process_receipt)

def process_receipt(message):
    user_id = message.from_user.id
    state = user_states.get(user_id, "")
    if not state.startswith("wait_receipt_"): return
    
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ Rasm yuboring:")
        bot.register_next_step_handler(msg, process_receipt)
        return
        
    inv_id = int(state.split("_")[2])
    order = pending_orders.get(inv_id)
    if not order: return
    
    username = f"@{message.from_user.username}" if message.from_user.username else "Yo'q"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"accept_pay_{inv_id}"),
        types.InlineKeyboardButton("❌ Otkaz qilish", callback_data=f"reject_pay_{inv_id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📥 **To'lov cheki!**\n👤 User: {username}\n🆔 ID: `{user_id}`\n💵 Summa: **{order['amount']:,.2f} so'm**", reply_markup=markup, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ Chek adminga yuborildi! Kuting.")
    user_states.pop(user_id, None)

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_pay_"))
def accept_pay(call):
    if call.from_user.id != ADMIN_ID: return
    inv_id = int(call.data.split("_")[2])
    order = pending_orders.get(inv_id)
    if order:
        user_balances.setdefault(order['id'], 0.0)
        user_balances[order['id']] += order['amount']
        bot.edit_message_caption("✅ **Tasdiqlandi va balansga qo'shildi!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        try: bot.send_message(order['id'], f"✅ Balansingizga {order['amount']:,.2f} so'm qo'shildi!")
        except: pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_pay_"))
def reject_pay(call):
    if call.from_user.id != ADMIN_ID: return
    inv_id = int(call.data.split("_")[2])
    order = pending_orders.get(inv_id)
    if order:
        bot.edit_message_caption("❌ **Otkaz qilindi (Rad etildi)**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        try: bot.send_message(order['id'], "❌ To'lovingiz tasdiqlanmadi (Otkaz qilindi). Iltimos, admin bilan bog'laning.")
        except: pass
            # --- TO'LIQ KENGAYTIRILGAN ADMIN PANEL ---
@bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 Jadval (Mijozlar)", callback_data="admin_list"),
        types.InlineKeyboardButton("💰 Balans (+/-)", callback_data="admin_mod_bal")
    )
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Xabar tarqatish", callback_data="admin_broadcast")
    )
    markup.add(types.InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="return_main"))
    
    bot.edit_message_text("🛠 **Boshqaruv Paneli (Admin):**\n\nKerakli bo'limni tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="open_admin_panel"))
    text = f"📊 **Bot Statistikasi:**\n\n👥 Botdan foydalanuvchilar soni: **{len(all_users)} ta**"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def admin_list(call):
    if call.from_user.id != ADMIN_ID: return
    text = "📊 **Foydalanuvchilar Jadvali:**\n\n"
    if not user_balances:
        text += "Hozircha hech kimning balansi yo'q."
    else:
        for uid, bal in user_balances.items():
            text += f"🆔 `{uid}` — **{bal:,.2f} so'm**\n"
            
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="open_admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_mod_bal")
def admin_mod_bal(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="open_admin_panel"))
    msg = bot.send_message(call.message.chat.id, "✍️ Format: `ID SUMMA`\n*(Masalan: `123456789 50000` yoki ayirish uchun `123456789 -10000`)*", parse_mode="Markdown", reply_markup=markup)
    user_states[call.from_user.id] = "wait_mod"
    bot.register_next_step_handler(msg, process_mod_bal)

def process_mod_bal(message):
    if message.from_user.id != ADMIN_ID: return
    if user_states.get(message.from_user.id) != "wait_mod": return
    try:
        uid, amt = message.text.split()
        uid, amt = int(uid), float(amt)
        user_balances.setdefault(uid, 0.0)
        user_balances[uid] += amt
        bot.send_message(message.chat.id, f"✅ Bajarildi! ID `{uid}` egasining yangi balansi: **{user_balances[uid]:,.2f} so'm**", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Xato format! Balans o'zgartirilmadi.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="open_admin_panel"))
    msg = bot.send_message(call.message.chat.id, "📢 Hamma mijozlarga tarqatish uchun xabar matnini yuboring:", reply_markup=markup)
    user_states[call.from_user.id] = "wait_broadcast"
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    if user_states.get(message.from_user.id) != "wait_broadcast": return
    
    text = message.text
    success = 0
    for uid in all_users:
        try:
            bot.send_message(uid, f"📢 **Yangi xabar:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass
            
    bot.send_message(message.chat.id, f"✅ Xabar **{success} ta** odamga yetkazildi!")
    user_states.pop(message.from_user.id, None)

# --- ISHGA TUSHIRISH ---
if __name__ == '__main__':
    print("🚀 Bot ishga tushdi!")
    bot.infinity_polling(skip_pending=True)
    # --- TO'LIQ KENGAYTIRILGAN ADMIN PANEL ---
@bot.callback_query_handler(func=lambda call: call.data == "open_admin_panel")
def admin_panel(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👥 Jadval (Mijozlar)", callback_data="admin_list"),
        types.InlineKeyboardButton("💰 Balans (+/-)", callback_data="admin_mod_bal")
    )
    markup.add(
        types.InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Xabar tarqatish", callback_data="admin_broadcast")
    )
    markup.add(types.InlineKeyboardButton("🔙 Menyuga qaytish", callback_data="return_main"))
    
    bot.edit_message_text("🛠 **Boshqaruv Paneli (Admin):**\n\nKerakli bo'limni tanlang:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_stats")
def admin_stats(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="open_admin_panel"))
    text = f"📊 **Bot Statistikasi:**\n\n👥 Botdan foydalanuvchilar soni: **{len(all_users)} ta**"
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_list")
def admin_list(call):
    if call.from_user.id != ADMIN_ID: return
    text = "📊 **Foydalanuvchilar Jadvali:**\n\n"
    if not user_balances:
        text += "Hozircha hech kimning balansi yo'q."
    else:
        for uid, bal in user_balances.items():
            text += f"🆔 `{uid}` — **{bal:,.2f} so'm**\n"
            
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Admin Panel", callback_data="open_admin_panel"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "admin_mod_bal")
def admin_mod_bal(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="open_admin_panel"))
    msg = bot.send_message(call.message.chat.id, "✍️ Format: `ID SUMMA`\n*(Masalan: `123456789 50000` yoki ayirish uchun `123456789 -10000`)*", parse_mode="Markdown", reply_markup=markup)
    user_states[call.from_user.id] = "wait_mod"
    bot.register_next_step_handler(msg, process_mod_bal)

def process_mod_bal(message):
    if message.from_user.id != ADMIN_ID: return
    if user_states.get(message.from_user.id) != "wait_mod": return
    try:
        uid, amt = message.text.split()
        uid, amt = int(uid), float(amt)
        user_balances.setdefault(uid, 0.0)
        user_balances[uid] += amt
        bot.send_message(message.chat.id, f"✅ Bajarildi! ID `{uid}` egasining yangi balansi: **{user_balances[uid]:,.2f} so'm**", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Xato format! Balans o'zgartirilmadi.")
    user_states.pop(message.from_user.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast")
def admin_broadcast(call):
    if call.from_user.id != ADMIN_ID: return
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="open_admin_panel"))
    msg = bot.send_message(call.message.chat.id, "📢 Hamma mijozlarga tarqatish uchun xabar matnini yuboring:", reply_markup=markup)
    user_states[call.from_user.id] = "wait_broadcast"
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.from_user.id != ADMIN_ID: return
    if user_states.get(message.from_user.id) != "wait_broadcast": return
    
    text = message.text
    success = 0
    for uid in all_users:
        try:
            bot.send_message(uid, f"📢 **Yangi xabar:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            pass
            
    bot.send_message(message.chat.id, f"✅ Xabar **{success} ta** odamga yetkazildi!")
    user_states.pop(message.from_user.id, None)

# --- ISHGA TUSHIRISH ---
if __name__ == '__main__':
    print("🚀 Bot ishga tushdi!")
    bot.infinity_polling(skip_pending=True)
    # 1. /start komandasida foydalanuvchini bazaga qo'shib saqlash
@bot.message_handler(commands=['start', 'menu'])
def handle_start(message):
    user_id = message.from_user.id
    is_new = False
    
    if user_id not in all_users:
        all_users.add(user_id)
        is_new = True
    
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
        is_new = True
        
    if is_new:
        save_data() # Yangi odam qo'shilsa faylga yozish

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🟡 Standoff 2", callback_data="buy_standoff"),
        types.InlineKeyboardButton("🪂 PUBG Mobile", callback_data="dev_mode"),
        types.InlineKeyboardButton("🟥 Roblox", callback_data="dev_mode"),
        types.InlineKeyboardButton("🔥 Free Fire", callback_data="dev_mode"),
        types.InlineKeyboardButton("🌵 Brawl Stars", callback_data="dev_mode")
    )
    markup.add(
        types.InlineKeyboardButton("💳 Balansni tekshirish", callback_data="check_balance"),
        types.InlineKeyboardButton("➕ Hisobni to'ldirish", callback_data="start_topup")
    )
    markup.add(types.InlineKeyboardButton("📞 Aloqa va Isbotlar", callback_data="show_contacts"))
    
    if user_id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("🛠 Admin Panel", callback_data="open_admin_panel"))

    bot.send_message(
        message.chat.id, 
        f"👋 Assalomu alaykum, {message.from_user.first_name}!\n\nIltimos, o'zingizga kerakli xizmatni tanlang:", 
        reply_markup=markup
    )

# 2. Balansdan pul yechilganda (Standoff 2 xarid qilish)
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_so2_"))
def process_so2_payment(call):
    _, _, gold, price = call.data.split("_")
    gold, price = int(gold), float(price)
    user_id = call.from_user.id
    
    if user_balances[user_id] >= price:
        user_balances[user_id] -= price
        save_data() # Balans kamayganini saqlash
        
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 Bekor qilish", callback_data="return_main"))
        msg = bot.send_message(call.message.chat.id, f"✅ To'landi! Yechildi: **{price:,.2f} so'm**\n\n📸 Endi USP | Gost skinini marketga {price:,.2f} summasiga qo'yganingiz skrinshotini yuboring:", reply_markup=markup, parse_mode="Markdown")
        user_states[user_id] = f"wait_skin_{gold}"
        bot.register_next_step_handler(msg, process_skin_screen)
    else:
        bot.answer_callback_query(call.id, "Balans yetarli emas!", show_alert=True)

# 3. Admin to'lov chekini tasdiqlaganda (Balansga pul qo'shish)
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_pay_"))
def accept_pay(call):
    if call.from_user.id != ADMIN_ID: return
    inv_id = int(call.data.split("_")[2])
    order = pending_orders.get(inv_id)
    if order:
        user_balances.setdefault(order['id'], 0.0)
        user_balances[order['id']] += order['amount']
        save_data() # Balans oshganini saqlash
        
        bot.edit_message_caption("✅ **Tasdiqlandi va balansga qo'shildi!**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        try: bot.send_message(order['id'], f"✅ Balansingizga {order['amount']:,.2f} so'm qo'shildi!")
        except: pass

# 4. Admin balansni qo'lda o'zgartirganda (+/-)
def process_mod_bal(message):
    if message.from_user.id != ADMIN_ID: return
    if user_states.get(message.from_user.id) != "wait_mod": return
    try:
        uid, amt = message.text.split()
        uid, amt = int(uid), float(amt)
        user_balances.setdefault(uid, 0.0)
        user_balances[uid] += amt
        save_data() # O'zgarishni saqlash
        
        bot.send_message(message.chat.id, f"✅ Bajarildi! ID `{uid}` egasining yangi balansi: **{user_balances[uid]:,.2f} so'm**", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Xato format! Balans o'zgartirilmadi.")
    user_states.pop(message.from_user.id, None)
    # --- 8-BÖLAK: Xavfsiz ishga tushirish va ulanishni saqlash ---
if __name__ == '__main__':
    print("🚀 So2servis SHOP boti muvaffaqiyatli ishga tushdi va server faol!")
    while True:
        try:
            # Internet uzilib qolsa yoki Telegram serveri javob bermasa, bot o'chib qolmaydi
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Aloqada xatolik yuz berdi: {e}")
            print("🔄 5 soniyadan so'ng qayta ulanishga harakat qilinmoqda...")
            time.sleep(5)
            
