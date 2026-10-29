import os
import asyncio
import logging
import urllib.request
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USER_LANGUAGES = {}

STRINGS = {
    "en": {
        "welcome": "⚡ **VORTEX INTERACTIVE TERMINAL v1.0** ⚡\n\n`System: Operational`\n`Network: Multilingual Node`\n\n🟢 **LIVE MARKET DATA:**\n• **BTC / USD:** `${btc_price}` 🟢\n\nSelect a professional analytical module from the dashboard below:",
        "btn_trading": "📈 Trading PnL & Risk",
        "btn_dca": "📊 DCA Strategy Calc",
        "btn_ton": "💎 TON Swap & Gas",
        "btn_rr": "🎯 Risk/Reward Ratio",
        "btn_history": "📜 Analytics History",
        "btn_lang": "🌐 Settings / Language",
        "btn_back": "⬅️ Back to Dashboard",
        "lang_select": "⚙️ **SYSTEM CONFIGURATION**\n\nSelect interface language / Выберите язык:",
        "trading_intro": "📊 **TRADING PnL & LEVERAGE ENGINE**\n\nEnter values in the exact format:\n`Entry_Price Exit_Price Leverage`\n\n*Example:* `2.5 3.0 10`"
    },
    "ru": {
        "welcome": "⚡ **ИНТЕРАКТИВНЫЙ ТЕРМИНАЛ VORTEX v1.0** ⚡\n\n`Система: Работает`\n`Сеть: Мультиязычный Узел`\n\n🟢 **РЫНОЧНЫЙ КУРС В РЕАЛЬНОМ ВРЕМЕНИ:**\n• **BTC / USD:** `${btc_price}` 🟢\n\nВыберите профессиональный аналитический модуль на панели:",
        "btn_trading": "📈 Трейдинг PnL и Риски",
        "btn_dca": "📊 Стратегия усреднения DCA",
        "btn_ton": "💎 TON Обмен и Газ",
        "btn_rr": "🎯 Риск / Прибыль (R:R)",
        "btn_history": "📜 История аналитики",
        "btn_lang": "🌐 Настройки / Language",
        "btn_back": "⬅️ Назад в терминал",
        "lang_select": "⚙️ **КОНФИГУРАЦИЯ СИСТЕМЫ**\n\nВыберите язык / Select interface language:",
        "trading_intro": "📊 **ДВИЖОК РАСЧЕТА PnL И ПЛЕЧА**\n\nВведите данные строго в формате:\n`Цена_Входа Цена_Выхода Плечо`\n\n*Пример:* `2.5 3.0 10`"
    }
}

# Функция для безопасного получения курса BTC в реальном времени
def fetch_btc_price():
    try:
        url = "https://coingecko.com"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            price = data["bitcoin"]["usd"]
            return f"{price:,}"
    except Exception as e:
        logger.error(f"Error fetching BTC price: {e}")
        return "80,715" # Запасной статичный курс на случай сбоя сети

def get_lang(user_id, message_lang=None):
    if user_id not in USER_LANGUAGES:
        USER_LANGUAGES[user_id] = "ru" if message_lang == "ru" else "en"
    return USER_LANGUAGES[user_id]

def build_menu(user_id, message_lang=None):
    lang = get_lang(user_id, message_lang)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_trading"], callback_data="mod_trading"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_dca"], callback_data="mod_coming"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_ton"], callback_data="mod_coming"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_rr"], callback_data="mod_coming"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_history"], callback_data="mod_coming"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_lang"], callback_data="mod_lang"))
    builder.adjust(2, 2, 2)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id, message.from_user.language_code)
    btc = fetch_btc_price()
    welcome_text = STRINGS[lang]["welcome"].replace("{btc_price}", btc)
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=build_menu(user_id))

@dp.callback_query(lambda c: c.data == "mod_lang")
async def inline_lang_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang_en"))
    builder.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_back"], callback_data="go_to_menu"))
    builder.adjust(2, 1)
    await callback_query.message.edit_text(STRINGS[lang]["lang_select"], reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data.startswith("set_lang_"))
async def set_user_language(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chosen_lang = "en" if "en" in callback_query.data else "ru"
    USER_LANGUAGES[user_id] = chosen_lang
    await callback_query.answer("Terminal configuration updated!")
    
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang_en"))
    builder.add(types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[chosen_lang]["btn_back"], callback_data="go_to_menu"))
    builder.adjust(2, 1)
    await callback_query.message.edit_text(STRINGS[chosen_lang]["lang_select"], reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data == "mod_trading")
async def inline_trading(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_back"], callback_data="go_to_menu"))
    await callback_query.message.edit_text(STRINGS[lang]["trading_intro"], parse_mode="Markdown", reply_markup=build_menu(user_id))

@dp.callback_query(lambda c: c.data == "mod_coming")
async def inline_coming_soon(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    alert_txt = "🛠️ Module under calibration. Will be unlocked in Phase 1." if lang == "en" else "🛠️ Модуль калибруется. Будет доступен в Фазе 1."
    await callback_query.answer(text=alert_txt, show_alert=True)

@dp.callback_query(lambda c: c.data == "go_to_menu")
async def inline_go_to_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    btc = fetch_btc_price()
    welcome_text = STRINGS[lang]["welcome"].replace("{btc_price}", btc)
    await callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=build_menu(user_id))

@dp.message()
async def process_calculations(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id)
    try:
        parts = message.text.replace(",", ".").split()
        if len(parts) == 3:
            entry = float(parts[0])
            exit_price = float(parts[1])
            leverage = float(parts[2])
            
            pnl_percent = ((exit_price - entry) / entry) * 100 * leverage
            liq_price = entry * (1 - 1 / leverage)

            if lang == "ru":
                res = (
                    f"🟩 **АНАЛИТИЧЕСКИЙ ОТЧЕТ VORTEX:**\n\n"
                    f"• **Чистый PnL:** `{pnl_percent:.2f}%`\n"
                    f"• **Цена ликвидации (Long):** `{liq_price:.4f}`\n\n"
                    f"`Статус операции: Успешно`"
                )
            else:
                res = (
                    f"🟩 **VORTEX ANALYTICAL REPORT:**\n\n"
                    f"• **Net PnL:** `{pnl_percent:.2f}%`\n"
                    f"• **Liquidation Price (Long):** `{liq_price:.4f}`\n\n"
                    f"`Operation Status: Success`"
                )
            await message.answer(res, parse_mode="Markdown", reply_markup=build_menu(user_id))
        else:
            raise ValueError
    except Exception:
        err = "❌ Invalid data format. Enter 3 variables." if lang == "en" else "❌ Ошибка формата. Введите 3 числа через пробел."
        await message.answer(err, reply_markup=build_menu(user_id))

async def main():
    logger.info("VORTEX Terminal Engine is online...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
