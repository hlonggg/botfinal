#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import logging
import asyncio
from datetime import datetime

import requests
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

# -------------------- CẤU HÌNH LOGGING --------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------- API KEYS (lấy từ biến môi trường) --------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY")  # không bắt buộc

if not TELEGRAM_TOKEN:
    raise ValueError("Bạn phải đặt biến môi trường TELEGRAM_BOT_TOKEN")

# -------------------- CÁC HÀM CHỨC NĂNG --------------------

# 1. Lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Chào mừng bạn đến với Bot đa năng!\n"
        "Sử dụng /help để xem danh sách lệnh."
    )
    await update.message.reply_text(welcome_text)

# 2. Lệnh /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 *Danh sách lệnh*\n\n"
        "/start - Khởi động bot\n"
        "/help - Hiển thị trợ giúp này\n"
        "/time - Xem thời gian hiện tại\n"
        "/dice - Tung xúc xắc (xí ngầu)\n"
        "/random <min> <max> - Số ngẫu nhiên trong khoảng\n"
        "/weather <tên thành phố> - Thời tiết hiện tại\n"
        "/exchange <số tiền> <mã nguồn> <mã đích> - Chuyển đổi tiền tệ\n"
        "/joke - Nhận một câu đùa vui\n"
        "/quote - Danh ngôn ngẫu nhiên\n"
        "/poll <câu hỏi> | <lựa chọn 1> | <lựa chọn 2> ... - Tạo thăm dò ý kiến"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# 3. Lệnh /time
async def time_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    await update.message.reply_text(f"🕒 Bây giờ là: {now}")

# 4. Lệnh /dice
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Gửi emoji xúc xắc, Telegram sẽ tự động hiển thị hoạt ảnh tung xúc xắc
    await update.message.reply_dice(emoji="🎲")

# 5. Lệnh /random
async def random_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            raise ValueError("Cần đúng 2 tham số")
        min_val = int(context.args[0])
        max_val = int(context.args[1])
        if min_val > max_val:
            min_val, max_val = max_val, min_val  # hoán đổi nếu nhập sai thứ tự
        result = random.randint(min_val, max_val)
        await update.message.reply_text(f"🎲 Số ngẫu nhiên từ {min_val} đến {max_val}: {result}")
    except (ValueError, IndexError):
        await update.message.reply_text("⚠️ Sử dụng: /random <số nhỏ nhất> <số lớn nhất>\nVí dụ: /random 1 100")

# 6. Lệnh /weather (yêu cầu OpenWeatherMap API key)
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not OPENWEATHER_API_KEY:
        await update.message.reply_text("⚠️ Chức năng thời tiết chưa được kích hoạt. Vui lòng đặt API key OpenWeatherMap.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Vui lòng nhập tên thành phố. Ví dụ: /weather Hanoi")
        return

    city = " ".join(context.args)
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=vi"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("cod") != 200:
            await update.message.reply_text(f"❌ Không tìm thấy thành phố: {city}")
            return

        desc = data["weather"][0]["description"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        city_name = data["name"]

        message = (
            f"🌤 *Thời tiết tại {city_name}*\n"
            f"🌡 Nhiệt độ: {temp}°C (cảm giác {feels_like}°C)\n"
            f"💧 Độ ẩm: {humidity}%\n"
            f"💨 Gió: {wind} m/s\n"
            f"📝 Mô tả: {desc}"
        )
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Lỗi lấy thời tiết: {e}")
        await update.message.reply_text("❌ Có lỗi xảy ra khi lấy dữ liệu thời tiết.")

# 7. Lệnh /exchange (chuyển đổi tiền tệ, không cần API key)
async def exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 3:
        await update.message.reply_text("⚠️ Sử dụng: /exchange <số tiền> <mã tiền nguồn> <mã tiền đích>\nVí dụ: /exchange 100 USD VND")
        return

    try:
        amount = float(context.args[0])
        from_currency = context.args[1].upper()
        to_currency = context.args[2].upper()
    except ValueError:
        await update.message.reply_text("⚠️ Số tiền phải là một con số.")
        return

    # Sử dụng API miễn phí không cần key
    url = f"https://open.er-api.com/v6/latest/{from_currency}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("result") != "success":
            await update.message.reply_text("❌ Mã tiền nguồn không hợp lệ.")
            return
        rates = data["rates"]
        if to_currency not in rates:
            await update.message.reply_text(f"❌ Mã tiền đích {to_currency} không được hỗ trợ.")
            return
        converted = amount * rates[to_currency]
        await update.message.reply_text(
            f"💱 {amount:,.2f} {from_currency} = {converted:,.2f} {to_currency}"
        )
    except Exception as e:
        logger.error(f"Lỗi chuyển đổi tiền tệ: {e}")
        await update.message.reply_text("❌ Có lỗi khi tra cứu tỉ giá.")

# 8. Lệnh /joke (truyện cười từ icanhazdadjoke.com)
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = {"Accept": "application/json", "User-Agent": "TelegramBot"}
    try:
        response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=10)
        data = response.json()
        await update.message.reply_text(f"😄 {data['joke']}")
    except Exception as e:
        logger.error(f"Lỗi lấy joke: {e}")
        await update.message.reply_text("❌ Không thể lấy truyện cười lúc này.")

# 9. Lệnh /quote (danh ngôn từ api.quotable.io)
async def quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get("https://api.quotable.io/random", timeout=10)
        data = response.json()
        text = f"💬 *{data['content']}*\n— _{data['author']}_"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Lỗi lấy quote: {e}")
        await update.message.reply_text("❌ Không lấy được danh ngôn.")

# 10. Lệnh /poll (tạo cuộc thăm dò)
async def create_poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Người dùng gửi: /poll Câu hỏi? | Lựa chọn A | Lựa chọn B | ...
    raw_text = " ".join(context.args)
    if not raw_text:
        await update.message.reply_text("⚠️ Sử dụng: /poll <câu hỏi> | <lựa chọn 1> | <lựa chọn 2> ...")
        return

    # Tách câu hỏi và các lựa chọn bằng dấu |
    parts = [p.strip() for p in raw_text.split("|")]
    if len(parts) < 3:  # cần ít nhất 1 câu hỏi + 2 lựa chọn
        await update.message.reply_text("⚠️ Cần ít nhất 1 câu hỏi và 2 lựa chọn, phân cách bằng dấu |")
        return

    question = parts[0]
    options = parts[1:]

    try:
        await update.message.reply_poll(
            question=question,
            options=options,
            is_anonymous=True,
            type=Poll.REGULAR
        )
    except Exception as e:
        logger.error(f"Lỗi tạo poll: {e}")
        await update.message.reply_text("❌ Không thể tạo cuộc thăm dò. Hãy kiểm tra lại cú pháp.")

# -------------------- HÀM CHÍNH --------------------
def main():
    # Tạo Application
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Đăng ký các handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_now))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("random", random_number))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("exchange", exchange))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("quote", quote))
    app.add_handler(CommandHandler("poll", create_poll))

    logger.info("Bot đang chạy...")
    app.run_polling()

if __name__ == "__main__":
    main()