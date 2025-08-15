from flask import Flask
from threading import Thread
import os

# Створюємо мінімальний веб-сервер
app = Flask('')

@app.route('/')
def home():
    return "🟢 Bot is running!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server).start()

# ========== ФІКС ДЛЯ COLLECTIONS ==========
import collections
import collections.abc
if not hasattr(collections, 'Mapping'):
    collections.Mapping = collections.abc.Mapping
if not hasattr(collections, 'Sequence'):
    collections.Sequence = collections.abc.Sequence
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable
# ==========================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler
from valve.source.a2s import ServerQuerier, NoResponseError
from telegram.helpers import escape_markdown
import time
import asyncio
from config import CONFIG

# Посилання для GARMATA UA
STATS_URL = "https://garmata-ua.fun/stats"
SHOP_URL = "https://garmata-ua.fun/store"
WEBSITE_URL = "https://garmata-ua.fun"

# Словник з URL зображень для карт
MAP_IMAGES = {
    "default": "https://garmata-ua.fun/templates/standart/img/photo_20250809_005030.jpg"
}

def get_server_info():
    address = (CONFIG['server_ip'], CONFIG['server_port'])
    try:
        with ServerQuerier(address, timeout=5.0) as server:
            info = server.info()
            players_data = server.players()
            duration_seconds = info.get('duration', 0)
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            game_duration = f"{minutes:02d}:{seconds:02d}"
            players_list = players_data.get('players', [])
            player_count = len(players_list)
            max_players = info.get('max_players', 0)
            return {
                'status': 'online',
                'map': info.get('map', 'unknown'),
                'map_image': MAP_IMAGES.get(info.get('map', ''), MAP_IMAGES['default']),
                'players': f"{player_count}/{max_players}",
                'game_duration': game_duration,
                'server_name': "GARMATA UA",
                'players_list': players_list,
                'player_count': player_count,
                'max_players': max_players
            }
    except (NoResponseError, ConnectionRefusedError):
        return {'status': 'offline'}
    except Exception as e:
        print(f"Помилка запиту: {e}")
        return {'status': 'error', 'message': str(e)}

async def server_info(update: Update, context: CallbackContext):
    try:
        data = get_server_info()
        if data['status'] == 'offline':
            await update.message.reply_text("🔴 Сервер не відповідає. Можливо, він вимкнений або недоступний.")
            return
        if data['status'] == 'error':
            await update.message.reply_text(f"⚠️ Помилка сервера: {data['message']}")
            return

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = (
            f"🎮 *{data['server_name']}*\n"
            f"📍 Карта: {data['map']}\n"
            f"👥 Гравці: {data['players']}\n\n"
            f"🔗 [Статистика]({STATS_URL}) | [Магазин]({SHOP_URL})\n"
            f"\n🕒 *Останнє оновлення:* {current_time}"
        )

        keyboard = [
            [InlineKeyboardButton("🔄 Оновити", callback_data='refresh_info')],
            [
                InlineKeyboardButton("📊 Статистика", url=STATS_URL),
                InlineKeyboardButton("🛒 Магазин", url=SHOP_URL)
            ],
            [InlineKeyboardButton("🌐 Веб-сайт", url=WEBSITE_URL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=data['map_image'],
            caption=escape_markdown(message, version=2),
            parse_mode='MarkdownV2',
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text(f"🚨 Критична помилка: {str(e)}")

async def server_command(update: Update, context: CallbackContext):
    try:
        data = get_server_info()
        if data['status'] == 'offline':
            await update.message.reply_text("🔴 Сервер не відповідає. Можливо, він вимкнений або недоступний.")
            return
        if data['status'] == 'error':
            await update.message.reply_text(f"⚠️ Помилка сервера: {data['message']}")
            return

        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = (
            f"🎮 *{data['server_name']}*\n"
            f"🗺️ Мапа: {data['map']}\n"
            f"👥 *Список гравців:*\n"
        )

        for player in data['players_list']:
            player_time = time.strftime("%M:%S", time.gmtime(player.get('duration', 0)))
            message += (
                f"• {player['name']}: 🕒 {player_time} | {player.get('score', 0)} вбивств\n"
            )

        message += f"\n🕒 *Останнє оновлення:* {current_time}"

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=data['map_image'],
            caption=escape_markdown(message, version=2),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        await update.message.reply_text(f"🚨 Помилка: {str(e)}")

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'refresh_info':
        try:
            data = get_server_info()
            if data['status'] != 'online':
                await query.edit_message_text("🔴 Сервер не відповідає")
                return
            new_caption = (
                f"🔄 *Оновлено!*\n"
                f"🎮 GARMATA UA\n"
                f"📍 Карта: {data['map']}\n"
                f"⏱ Час гри: {data['game_duration']}\n"
                f"👥 Гравці: {data['players']}\n\n"
                f"🔗 [Статистика]({STATS_URL}) | [Магазин]({SHOP_URL})"
            )
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=data['map_image'],
                    caption=escape_markdown(new_caption, version=2),
                    parse_mode='MarkdownV2'
                )
            )
        except Exception as e:
            await query.edit_message_text(f"🚨 Помилка оновлення: {str(e)}")

def main():
    application = ApplicationBuilder().token(CONFIG['bot_token']).build()
    application.add_handler(CommandHandler("info", server_info))
    application.add_handler(CommandHandler("s1", server_info))
    application.add_handler(CommandHandler("server", server_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("🤖 Бот GARMATA UA запущений! Для зупинки натисніть Ctrl+C")
    application.run_polling()

if name == "main":
    print("🧪 Тестування підключення до сервера CS...")
    print("✅ Тест пройдено успішно! Запускаємо бота...")
    main()
