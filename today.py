from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
import datetime
import pytz
import re

# State conversation
Tahun, TanggalBulan, JumlahHari, ArahHari = range(4)

def escape_markdown_v2(text: str) -> str:
    """Escape karakter khusus MarkdownV2 kecuali backtick agar monospace tetap jalan."""
    escape_chars = r'\\_*[]()~>#+-=|{}.!'
    pattern = re.compile(f'([{re.escape(escape_chars)}])')
    return pattern.sub(r'\\\1', text)

def get_pasaran_jawa(date: datetime.date) -> str:
    acuan = datetime.date(2025, 5, 28)
    pasaran_list = ["legí", "pahing", "pon", "wage", "kliwon"]
    delta_days = (date - acuan).days
    pasaran_index = (4 + delta_days) % 5
    return pasaran_list[pasaran_index]

def bulan_masehi_id(month_num: int) -> str:
    bulan_map = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei",
        6: "Juni", 7: "Juli", 8: "Agustus", 9: "September",
        10: "Oktober", 11: "November", 12: "Desember"
    }
    return bulan_map.get(month_num, "Unknown")

def bulan_to_number(bulan_str: str) -> int:
    bulan_map = {
        "januari":1, "februari":2, "maret":3, "april":4, "mei":5, "juni":6,
        "juli":7, "agustus":8, "september":9, "oktober":10, "november":11, "desember":12
    }
    return bulan_map.get(bulan_str.lower(), 0)

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.datetime.now(tz)

    hari_indonesia = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }
    hari = hari_indonesia.get(now.strftime("%A"), now.strftime("%A"))
    tanggal_masehi = f"{now.day} {bulan_masehi_id(now.month)}"
    tanggal_jawa = get_pasaran_jawa(now.date())
    jam = now.strftime("%H:%M:%S")

    judul = "✨ DETAIL HARI ✨"

    pesan = (
        f"`{judul}`\n\n"
        f"🧮 `Tahun           : {now.year}`\n"
        f"💌 `Hari            : {hari}`\n"
        f"💌 `Tanggal Masehi  : {tanggal_masehi}`\n"
        f"📧 `Tanggal Jawa    : {tanggal_jawa}`\n"
        f"⌚ `Jam             : {jam}`"
    )

    pesan = escape_markdown_v2(pesan)
    await update.message.reply_text(pesan, parse_mode="MarkdownV2")

async def get_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_bot = await update.message.reply_text("Masukkan tahun :")
    context.user_data['messages_to_delete'] = [msg_bot.message_id, update.message.message_id]
    return Tahun

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "Halo! 👋🗿\n"
        "Selamat datang di bot cek hari dan tanggal.\n"
        "Klik tombol menu didawah ini untuk lihat beberapa perintah\n\n"
        "👇👇👇👇"
    )
    await update.message.reply_text(welcome_text)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                text="Hubungi Admin",
                url=f"https://t.me/Mayugoro?text=Bang%20lu%20ganteng🗿🗿"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Silakan hubungi admin melalui tombol berikut:", reply_markup=reply_markup)

async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = "https://i.imgur.com/qCmx5Bk.png"
    caption = "Sini yg banyak🗿"
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url, caption=caption)

async def get_tahun(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tahun = update.message.text.strip()
    if not tahun.isdigit():
        await update.message.reply_text("Tahun harus berupa angka. Silakan coba lagi:")
        context.user_data['messages_to_delete'].append(update.message.message_id)
        return Tahun

    context.user_data['tahun'] = int(tahun)

    msg_bot = await update.message.reply_text("Masukkan tanggal dan bulan :")
    context.user_data['messages_to_delete'].extend([msg_bot.message_id, update.message.message_id])
    return TanggalBulan

async def get_tanggal_bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("Format salah. Contoh yang benar: 1 mei")
        context.user_data['messages_to_delete'].append(update.message.message_id)
        return TanggalBulan

    tanggal_str, bulan_str = parts
    if not tanggal_str.isdigit():
        await update.message.reply_text("Tanggal harus angka. Contoh: 1 mei")
        context.user_data['messages_to_delete'].append(update.message.message_id)
        return TanggalBulan

    tanggal = int(tanggal_str)
    bulan = bulan_to_number(bulan_str)
    if bulan == 0:
        await update.message.reply_text("Nama bulan tidak valid. Contoh: januari, februari, mei, dll.")
        context.user_data['messages_to_delete'].append(update.message.message_id)
        return TanggalBulan

    tahun = context.user_data.get('tahun')
    if not tahun:
        await update.message.reply_text("Terjadi kesalahan. Silakan mulai ulang dengan /get")
        return ConversationHandler.END

    try:
        tanggal_input = datetime.date(tahun, bulan, tanggal)
    except ValueError:
        await update.message.reply_text("Tanggal tidak valid untuk bulan tersebut. Silakan coba lagi:")
        context.user_data['messages_to_delete'].append(update.message.message_id)
        return TanggalBulan

    return await kirim_detail_tanggal(update, context, tanggal_input)

async def kirim_detail_tanggal(update: Update, context: ContextTypes.DEFAULT_TYPE, tanggal_input: datetime.date):
    tz = pytz.timezone("Asia/Jakarta")
    jam = datetime.datetime.now(tz).strftime("%H:%M:%S")

    tanggal_jawa = get_pasaran_jawa(tanggal_input)

    hari_indonesia = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }
    hari = hari_indonesia.get(tanggal_input.strftime("%A"), tanggal_input.strftime("%A"))

    tanggal_masehi = f"{tanggal_input.day} {bulan_masehi_id(tanggal_input.month)}"

    judul = "✨ DETAIL HARI ✨"

    pesan = (
        f"`{judul}`\n\n"
        f"🧮 `Tahun           : {tanggal_input.year}`\n"
        f"💌 `Hari            : {hari}`\n"
        f"💌 `Tanggal Masehi  : {tanggal_masehi}`\n"
        f"📧 `Tanggal Jawa    : {tanggal_jawa}`\n"
        f"⌚ `Jam             : {jam}`"
    )
    pesan = escape_markdown_v2(pesan)

    chat_id = update.effective_chat.id
    for msg_id in context.user_data.get('messages_to_delete', []):
        try:
            if msg_id != update.message.message_id:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass

    await update.message.reply_text(pesan, parse_mode="MarkdownV2")
    return ConversationHandler.END

async def get_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['arah'] = 'plus'
    await update.message.reply_text("Mau maju berapa hari?")
    return JumlahHari

async def get_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['arah'] = 'minus'
    await update.message.reply_text("Mau mundur berapa hari?")
    return JumlahHari

async def proses_jumlah_hari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jumlah = update.message.text.strip()
    if not jumlah.isdigit():
        await update.message.reply_text("Masukkan jumlah hari dalam angka.")
        return JumlahHari

    jumlah = int(jumlah)
    arah = context.user_data.get('arah')
    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.datetime.now(tz).date()
    if arah == 'plus':
        tanggal_target = today + datetime.timedelta(days=jumlah)
    else:
        tanggal_target = today - datetime.timedelta(days=jumlah)

    return await kirim_detail_tanggal(update, context, tanggal_target)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah dibatalkan.")
    return ConversationHandler.END

def main():
    token = "_____" 
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('get', get_start)],
        states={
            Tahun: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tahun)],
            TanggalBulan: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tanggal_bulan)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_plus_minus = ConversationHandler(
        entry_points=[
            CommandHandler('maju', get_plus),
            CommandHandler('mundur', get_minus),
        ],
        states={
            JumlahHari: [MessageHandler(filters.TEXT & ~filters.COMMAND, proses_jumlah_hari)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("donate", donate))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(conv_handler)
    app.add_handler(conv_plus_minus)

    print("\033[32mBOT JALANNNN!!\033[0m")
    app.run_polling()

if __name__ == "__main__":
    main()
