import logging
from aiogram import Bot, Dispatcher, executor, types
import os

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 654321098  # O'zingizning Telegram ID raqamingizni shu yerga yozing

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

users_balance = {}

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Assalomu alaykum! Do'konimizga xush kelibsiz. Balansingizni tekshirish uchun /balance buyrug'ini yuboring.")

@dp.message_handler(commands=['balance'])
async def check_balance(message: types.Message):
    user_id = message.from_user.id
    bal = users_balance.get(user_id, 0)
    await message.reply(f"💰 Sizning balansingiz: {bal} so'm")

@dp.message_handler(commands=['admin'])
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply("👨‍💻 Admin panelga xush kelibsiz!\nBalans qo'shish uchun format:\n/set [Mijoz_ID] [Summa]\n\nMasalan: /set 123456789 15000")
    else:
        await message.reply("❌ Sizda bu huquq yo'q!")

@dp.message_handler(commands=['set'])
async def set_balance(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        args = message.text.split()
        if len(args) == 3:
            target_id = int(args[1])
            amount = int(args[2])
            users_balance[target_id] = users_balance.get(target_id, 0) + amount
            await message.reply(f"✅ ID: {target_id} ning balansi {amount} so'mga o'zgartirildi.")
        else:
            await message.reply("⚠️ Xato format! Masalan: /set [ID] [Summa]")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
