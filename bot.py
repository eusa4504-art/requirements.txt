import logging
import sqlite3
import asyncio
import random
import time
import aiohttp
import json
from flask import Flask
from threading import Thread
from urllib.parse import quote_plus
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ===============================
# KEEP-ALIVE SERVER (Render-এর জন্য)
# ===============================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ===============================
# 1️⃣ CONFIGURATION
# ===============================
API_TOKEN = '8646581161:AAHVnFBJuSDgIRyHZQXm9S3tp1bVuE7dzJ4'
MID = "53274682"  
M_KEY = "7db51ea436df4f9281fc13d8b1a4b7b6"  
UPI_ID = "BHARATPE.8Q0I0Z6E9Q43217@fbpe" 
ADMIN_LOG_GROUP = -1003774723818 
SUPPORT_USER = "@Narxm"
REFERRAL_BONUS = 2.0
PROOF_CHANNEL_LINK = "https://t.me/want_to_see_proof"

PRODUCTS_DATA = {
    "CXP": {"price": 149, "link": "https://t.me/your_link_1"},
    "DESI": {"price": 99, "link": "https://t.me/your_link_2"},
    "FOREIGN": {"price": 99, "link": "https://t.me/your_link_3"},
    "GAY/LESBIAN": {"price": 99, "link": "https://t.me/your_link_4"}
}

# ===============================
# 2️⃣ DATABASE SETUP
# ===============================
db = sqlite3.connect("automated_store.db")
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
    (user_id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, 
    deposits REAL DEFAULT 0, purchases INTEGER DEFAULT 0, 
    referrals INTEGER DEFAULT 0)''')
db.commit()

class Form(StatesGroup):
    amt = State()

# ===============================
# 3️⃣ AUTOMATIC API CHECKER
# ===============================
async def verify_payment_api(order_id):
    url = "https://securegw.paytm.in/v3/order/status"
    payload = {"body": {"mid": MID, "orderId": order_id}}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as response:
                res = await response.json()
                status = res.get("body", {}).get("resultInfo", {}).get("resultStatus")
                return status == "TXN_SUCCESS"
        except Exception as e:
            logging.error(f"API Error: {e}")
            return False

# ===============================
# 4️⃣ BOT INITIALIZATION
# ===============================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🛍 Products"), KeyboardButton(text="👤 Account"))
    kb.row(KeyboardButton(text="💳 Deposit"), KeyboardButton(text="👥 Refer"))
    kb.row(KeyboardButton(text="📞 Contact Support"), KeyboardButton(text="✅ Proofs"))
    kb.row(KeyboardButton(text="🔥 Best Sellers"))
    return kb.as_markup(resize_keyboard=True)

def ensure_user(uid):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, balance, deposits, purchases, referrals) VALUES (?, 0, 0, 0, 0)", (uid,))
        db.commit()

# --- (বাকি সব হ্যান্ডলার আপনার কোড অনুযায়ী থাকবে) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    ensure_user(uid)
    
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != uid:
            ensure_user(ref_id)
            cursor.execute("UPDATE users SET balance = balance + ?, referrals = referrals + 1 WHERE user_id = ?", (REFERRAL_BONUS, ref_id))
            db.commit()
            try: await bot.send_message(ref_id, f"💰 <b>Referral Bonus!</b> ₹{REFERRAL_BONUS} added to your balance.", parse_mode="HTML")
            except: pass

    await message.answer("✨ <b>Welcome to the Premium Automated Store.</b>\n\nInstant delivery and 100% trusted services.", parse_mode="HTML", reply_markup=main_kb())

@dp.message(F.text == "👥 Refer")
async def view_refer(message: types.Message):
    uid = message.from_user.id
    me = await bot.get_me()
    ref_link = f"https://t.me/{me.username}?start={uid}"
    await message.answer(f"👥 <b>Refer & Earn</b>\n🔗 <b>Your Link:</b> <code>{ref_link}</code>", parse_mode="HTML")

@dp.message(F.text == "👤 Account")
async def view_acc(message: types.Message):
    uid = message.from_user.id
    ensure_user(uid)
    cursor.execute("SELECT balance, deposits, referrals FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    await message.answer(f"👤 <b>Your Account</b>\n💰 Balance: ₹{res[0]}\n📥 Deposits: ₹{res[1]}", parse_mode="HTML")

@dp.message(F.text == "🛍 Products")
async def view_prod(message: types.Message):
    builder = InlineKeyboardBuilder()
    for name, data in PRODUCTS_DATA.items():
        builder.row(InlineKeyboardButton(text=f"{name} - ₹{data['price']}", callback_data=f"info_{name}"))
    await message.answer("🛒 <b>Available Products:</b>", reply_markup=builder.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("info_"))
async def product_info(call: types.CallbackQuery):
    p_name = call.data.split("_")[1]
    price = PRODUCTS_DATA[p_name]["price"]
    btn = InlineKeyboardBuilder()
    btn.row(InlineKeyboardButton(text=f"✅ Confirm & Pay ₹{price}", callback_data=f"buy_{p_name}"))
    await call.message.edit_text(f"📦 <b>Selection:</b> {p_name}\n💰 <b>Price:</b> ₹{price}", reply_markup=btn.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def final_buy(call: types.CallbackQuery):
    p_name = call.data.split("_")[1]
    price = PRODUCTS_DATA[p_name]["price"]
    link = PRODUCTS_DATA[p_name]["link"]
    uid = call.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cursor.fetchone()[0]
    if balance >= price:
        cursor.execute("UPDATE users SET balance = balance - ?, purchases = purchases + 1 WHERE user_id = ?", (price, uid))
        db.commit()
        await call.message.edit_text(f"✅ <b>Purchase Successful!</b>\n🔗 <b>Link:</b> {link}", parse_mode="HTML")
    else:
        await call.answer("❌ Low Balance!", show_alert=True)

@dp.message(F.text == "💳 Deposit")
async def dep_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.amt)
    await message.answer("💳 <b>Enter Amount to Deposit:</b>", parse_mode="HTML")

@dp.message(Form.amt)
async def dep_amt(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return
    amt = int(message.text)
    order_id = f"ID{int(time.time())}"
    upi_link = f"upi://pay?pa={UPI_ID}&pn=PremiumStore&am={amt}&cu=INR&tr={order_id}"
    qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote_plus(upi_link)}"
    btn = InlineKeyboardBuilder()
    btn.row(InlineKeyboardButton(text="🔄 Verify Payment", callback_data=f"check_{order_id}_{amt}"))
    await message.answer_photo(photo=qr, caption=f"💰 Pay ₹{amt} and click verify.", reply_markup=btn.as_markup(), parse_mode="HTML")
    await state.clear()

@dp.callback_query(F.data.startswith("check_"))
async def auto_verify(call: types.CallbackQuery):
    _, order_id, amt = call.data.split("_")
    uid = call.from_user.id
    is_paid = await verify_payment_api(order_id)
    if is_paid:
        cursor.execute("UPDATE users SET balance = balance + ?, deposits = deposits + ? WHERE user_id = ?", (amt, amt, uid))
        db.commit()
        await call.message.answer(f"✅ ₹{amt} added!")
    else:
        await call.answer("❌ Payment not found!", show_alert=True)

# ===============================
# MAIN EXECUTION
# ===============================
async def main():
    keep_alive() # Flask সার্ভার চালু করবে
    print("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
