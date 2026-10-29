import os
import asyncio
import logging
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
        "welcome": "🖥️ **VORTEX | Smart Computational Node**\n\nSelect a calculation module from the menu below:",
        "btn_trading": "📈 Trading PnL & Risk",
        "btn_lang": "🌐 Language / Язык",
        "btn_back": "⬅️ Back to Menu",
        "lang_select": "Select your language / Выберите язык:",
        "trading_intro": "📊 **PnL & Risk Calculator**\n\nEnter values in the format:\n`Entry_Price Exit_Price Leverage`\n\n*Example:* `2.5 3.0 10`"
    },
    "ru": {
        "welcome": "🖥️ **VORTEX | Умный Вычислительный Модуль**\n\nВыберите модуль калькулятора в меню ниже:",
        "btn_trading": "📈 Трейдинг PnL и Риски",
        "btn_lang": "🌐 Язык / Language",
        "btn_back": "⬅️ Назад в меню",
        "lang_select": "Выберите язык / Select your language:",
        "trading_intro": "📊 **Калькулятор PnL и Рисков**\n\nВведите данные в формате:\n`Цена_Входа Цена_Выхода Плечо`\n\n*Пример:* `2.5 3.0 10`"
    }
}

def get_lang(user_id, message_lang=None):
    if user_id not in USER_LANGUAGES:
        USER_LANGUAGES[user_id] = "ru" if message_lang == "ru" else "en"
    return USER_LANGUAGES[user_id]

def build_menu(user_id, message_lang=None):
    lang = get_lang(user_id, message_lang)
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_trading"], callback_data="mod_trading"))
    builder.add(types.InlineKeyboardButton(text=STRINGS[lang]["btn_lang"], callback_data="mod_lang"))
    builder.adjust(1)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    lang = get_lang(user_id, message.from_user.language_code)
    await message.answer(STRINGS[lang]["welcome"], parse_mode="Markdown", reply_markup=build_menu(user_id))

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
    # Исправлено: берем точное значение из конца строки ('en' или 'ru')
    chosen_lang = "en" if "en" in callback_query.data else "ru"
    USER_LANGUAGES[user_id] = chosen_lang
    
    await callback_query.answer("Language updated! / Язык обновлен!")
    
    # Перерисовываем меню с новым выбранным языком
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
    await callback_query.message.edit_text(STRINGS[lang]["trading_intro"], parse_mode="Markdown", reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data == "go_to_menu")
async def inline_go_to_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    lang = get_lang(user_id)
    await callback_query.message.edit_text(STRINGS[lang]["welcome"], parse_mode="Markdown", reply_markup=build_menu(user_id))

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
                    f"🟩 **Результаты расчета VORTEX:**\n\n"
                    f"• Профит/Убыток: `{pnl_percent:.2f}%`\n"
                    f"• Цена Ликвидации (Long): `{liq_price:.4f}`\n\n"
                    f"Вычисления произведены успешно."
                )
            else:
                res = (
                    f"🟩 **VORTEX Calculation Results:**\n\n"
                    f"• Profit/Loss: `{pnl_percent:.2f}%`\n"
                    f"• Liquidation Price (Long): `{liq_price:.4f}`\n\n"
                    f"Calculations completed successfully."
                )
            await message.answer(res, parse_mode="Markdown", reply_markup=build_menu(user_id))
        else:
            raise ValueError
    except Exception:
        err = "❌ Invalid format. Please enter 3 numbers." if lang == "en" else "❌ Неверный формат. Введите 3 числа через пробел."
        await message.answer(err, reply_markup=build_menu(user_id))

async def main():
    logger.info("VORTEX Calculator Core is online...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
