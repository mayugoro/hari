from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters
import datetime
import pytz
import json
import os

# Load bulan hijriah map dari file JSON
with open(os.path.join(os.path.dirname(__file__), "bulan_hijriah_map.json"), "r", encoding="utf-8") as f:
    bulan_map = json.load(f)

# State conversation
Tahun, TanggalBulan = range(2)

def get_pasaran_jawa(date: datetime.date) -> str:
    acuan = datetime.date(2025, 5, 28)
    pasaran_list = ["legí", "pahing", "pon", "wage", "kliwon"]
    delta_days = (date - acuan).days
    pasaran_index = (4 + delta_days) % 5
    return pasaran_list[pasaran_index]

def get_javanese_date() -> str:
    tz = pytz.timezone("Asia/Jakarta")
    today = datetime.datetime.now(tz).date()
    return get_pasaran_jawa(today)

def get_hijri_date_from_local(day: int, month_en: str, year: int) -> str:
    month_id = bulan_map.get(month_en, month_en)
    return f"{day} {month_id} {year} H"

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

# Contoh data manual tanggal hijriah
data_hijriah_manual = {
    "28-05-2025": {"day": 1, "month": "Dhū al-Ḥijjah", "year": 1446},
    # Tambahkan data lain sesuai kebutuhan
}

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz = pytz.timezone("Asia/Jakarta")
    now = datetime.datetime.now(tz)

    tahun = now.year
    hari_eng = now.strftime("%A").lower()
    hari_indonesia = {
        "monday": "Senin", "tuesday": "Selasa", "wednesday": "Rabu",
        "thursday": "Kamis", "friday": "Jumat", "saturday": "Sabtu",
        "sunday": "Minggu",
    }
    hari = hari_indonesia.get(hari_eng, hari_eng)

    tanggal_masehi = f"{now.day} {bulan_masehi_id(now.month)}"
    tanggal_str = now.strftime("%d-%m-%Y")

    hijri_info = data_hijriah_manual.get(tanggal_str)
    if hijri_info:
        tanggal_hijriah = get_hijri_date_from_local(hijri_info["day"], hijri_info["month"], hijri_info["year"])
    else:
        tanggal_hijriah = "Data Hijriah tidak tersedia"

    tanggal_jawa = get_javanese_date()
    jam = now.strftime("%H:%M:%S")

    pesan = (
        "           DETAIL HARI\n"
        "<pre>"
        f"Tahun           : {tahun}\n"
        f"Hari            : {hari}\n"
        f"Tanggal Masehi  : {tanggal_masehi}\n"
        f"Tanggal Hijriah : {tanggal_hijriah}\n"
        f"Tanggal Jawa    : {tanggal_jawa}\n"
        f"Jam             : {jam}\n"
        "</pre>"
    )
    await update.message.reply_text(pesan, parse_mode="HTML")

async def get_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_bot = await update.message.reply_text("Masukkan tahun :")
    context.user_data['messages_to_delete'] = [msg_bot.message_id, update.message.message_id]
    return Tahun

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

    tanggal_str = tanggal_input.strftime("%d-%m-%Y")
    hijri_info = data_hijriah_manual.get(tanggal_str)
    if hijri_info:
        tanggal_hijriah = get_hijri_date_from_local(hijri_info["day"], hijri_info["month"], hijri_info["year"])
    else:
        tanggal_hijriah = "Data Hijriah tidak tersedia"

    tanggal_jawa = get_pasaran_jawa(tanggal_input)

    hari_indonesia = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu",
        "Sunday": "Minggu",
    }
    hari = hari_indonesia.get(tanggal_input.strftime("%A"), tanggal_input.strftime("%A"))

    tanggal_masehi = f"{tanggal_input.day} {bulan_masehi_id(tanggal_input.month)}"

    pesan = (
    "           DETAIL HARI\n"  # Menampilkan DETAIL HARI di luar <pre>
    "<pre>"
    f"Tahun           : {tanggal_input.year}\n"
    f"Hari            : {hari}\n"
    f"Tanggal Masehi  : {tanggal_masehi}\n"
    f"Tanggal Hijriah : {tanggal_hijriah}\n"
    f"Tanggal Jawa    : {tanggal_jawa}\n"
    "</pre>"
)

    # Hanya hapus pesan bot yang tersimpan
    chat_id = update.message.chat_id
    for msg_id in context.user_data.get('messages_to_delete', []):
        try:
            # Hapus hanya pesan bot yang tersimpan
            if msg_id != update.message.message_id:  # Jangan hapus pesan dari user
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except:
            pass

    # Kirim hasil akhir
    await context.bot.send_message(chat_id=chat_id, text=pesan, parse_mode="HTML")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah dibatalkan.")
    return ConversationHandler.END

def main():
    token = "8193850177:AAH0IgjxhIEi-zKt4UdpP7FN_woRb9HnVas"
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('get', get_start)],
        states={
            Tahun: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tahun)],
            TanggalBulan: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tanggal_bulan)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(CommandHandler("today", today))
    app.add_handler(conv_handler)

    print("Bot berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
