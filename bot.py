
import os
import asyncio
import logging
import json
import urllib.request
from decimal import Decimal, InvalidOperation

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError


# =========================
# CONFIGURATION
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("VORTEX")

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Add it to your hosting environment variables."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

USER_LANGUAGES = {}
USER_STATES = {}

MAX_LEVERAGE = Decimal("125")
MAX_PRICE = Decimal("1000000000000")

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd"
)


# =========================
# TRANSLATIONS
# =========================

STRINGS = {
    "en": {
        "welcome": (
            "⚡ **VORTEX INTERACTIVE TERMINAL v1.0** ⚡\n\n"
            "`System: Operational`\n"
            "`Core: Multilingual Async Node`\n\n"
            "🟢 **LIVE MARKET DATA:**\n"
            "• **BTC / USD:** ${btc_price}\n\n"
            "Select a professional analytical module:"
        ),
        "btn_trading": "📈 Trading PnL & Risk",
        "btn_dca": "📊 DCA Strategy Calc",
        "btn_ton": "💎 TON Swap & Gas",
        "btn_rr": "🎯 Risk/Reward Ratio",
        "btn_history": "📜 Analytics History",
        "btn_lang": "🌐 Settings / Language",
        "btn_back": "⬅️ Back to Dashboard",
        "lang_select": (
            "⚙️ **SYSTEM CONFIGURATION**\n\n"
            "Select interface language / Выберите язык:"
        ),
        "trading_intro": (
            "📊 **TRADING PnL & LEVERAGE ENGINE**\n\n"
            "Enter values in this format:\n"
            "`Entry_Price Exit_Price Leverage [Direction]`\n\n"
            "Example: `2.5 3.0 10 long`\n"
            "Short example: `2.5 2.0 10 short`\n\n"
            "Direction is optional; defaults to long.\n"
            "Leverage: 1–125x. Decimal separator: dot or comma."
        ),
        "invalid_format": (
            "❌ Invalid format.\n"
            "Send: `Entry Exit Leverage [long/short]`\n"
            "Example: `2.5 3.0 10 long`"
        ),
        "invalid_values": (
            "❌ Prices must be positive finite numbers. "
            "Leverage must be between 1 and 125."
        ),
        "invalid_direction": (
            "❌ Direction must be `long` or `short`."
        ),
        "report": (
            "🟩 **VORTEX ANALYTICAL REPORT**\n\n"
            "• **Direction:** `{direction}`\n"
            "• **Entry Price:** `{entry}`\n"
            "• **Exit Price:** `{exit}`\n"
            "• **Leverage:** `{leverage}x`\n"
            "• **Price Change:** `{price_change:.2f}%`\n"
            "• **Leveraged PnL:** `{pnl:.2f}%` of initial margin\n"
            "• **PnL per 1 unit of initial margin:** `{pnl_cash:.4f}`\n"
            "• **Estimated Liquidation Price:** `{liq}`\n\n"
            "`Fees, funding and maintenance margin excluded.`"
        ),
        "liq_unavailable": "Not estimated at 1x",
        "price_unavailable": "Unavailable",
        "module_coming": "🛠️ This module is under development.",
        "language_changed": "Terminal reconfigured!",
        "operation_error": "❌ An error occurred. Please try again.",
    },

    "ru": {
        "welcome": (
            "⚡ **ИНТЕРАКТИВНЫЙ ТЕРМИНАЛ VORTEX v1.0** ⚡\n\n"
            "`Система: Работает`\n"
            "`Ядро: Мультиязычный асинхронный узел`\n\n"
            "🟢 **РЫНОЧНЫЙ КУРС В РЕАЛЬНОМ ВРЕМЕНИ:**\n"
            "• **BTC / USD:** ${btc_price}\n\n"
            "Выберите аналитический модуль:"
        ),
        "btn_trading": "📈 Трейдинг PnL и риски",
        "btn_dca": "📊 Стратегия усреднения DCA",
        "btn_ton": "💎 TON Обмен и Gas",
        "btn_rr": "🎯 Риск / Прибыль (R:R)",
        "btn_history": "📜 История аналитики",
        "btn_lang": "🌐 Настройки / Language",
        "btn_back": "⬅️ Назад в терминал",
        "lang_select": (
            "⚙️ **КОНФИГУРАЦИЯ СИСТЕМЫ**\n\n"
            "Выберите язык / Select interface language:"
        ),
        "trading_intro": (
            "📊 **ДВИЖОК РАСЧЕТА PnL И ПЛЕЧА**\n\n"
            "Введите данные в формате:\n"
            "`Цена_Входа Цена_Выхода Плечо [Направление]`\n\n"
            "Пример: `2.5 3.0 10 long`\n"
            "Для Short: `2.5 2.0 10 short`\n\n"
            "Направление необязательно; по умолчанию long.\n"
            "Плечо: 1–125x. Разделитель дроби: точка или запятая."
        ),
        "invalid_format": (
            "❌ Неверный формат.\n"
            "Введите: `Вход Выход Плечо [long/short]`\n"
            "Пример: `2.5 3.0 10 long`"
        ),
        "invalid_values": (
            "❌ Цены должны быть положительными конечными числами. "
            "Плечо должно быть от 1 до 125."
        ),
        "invalid_direction": (
            "❌ Направление должно быть `long` или `short`."
        ),
        "report": (
            "🟩 **АНАЛИТИЧЕСКИЙ ОТЧЕТ VORTEX**\n\n"
            "• **Направление:** `{direction}`\n"
            "• **Цена входа:** `{entry}`\n"
            "• **Цена выхода:** `{exit}`\n"
            "• **Плечо:** `{leverage}x`\n"
            "• **Изменение цены:** `{price_change:.2f}%`\n"
            "• **PnL с плечом:** `{pnl:.2f}%` от начальной маржи\n"
            "• **PnL на 1 единицу начальной маржи:** `{pnl_cash:.4f}`\n"
            "• **Ориентировочная цена ликвидации:** `{liq}`\n\n"
            "`Комиссии, funding и поддерживающая маржа не учтены.`"
        ),
        "liq_unavailable": "Не рассчитывается при плече 1x",
        "price_unavailable": "Недоступен",
        "module_coming": "🛠️ Этот модуль находится в разработке.",
        "language_changed": "Терминал перенастроен!",
        "operation_error": "❌ Произошла ошибка. Попробуйте ещё раз.",
    },
}


# =========================
# LANGUAGE AND KEYBOARDS
# =========================

def get_lang(user_id: int, message_lang=None) -> str:
    if user_id not in USER_LANGUAGES:
        USER_LANGUAGES[user_id] = (
            "ru"
            if (message_lang or "").lower().startswith("ru")
            else "en"
        )
    return USER_LANGUAGES[user_id]


def build_menu(user_id: int, message_lang=None):
    lang = get_lang(user_id, message_lang)
    s = STRINGS[lang]

    builder = InlineKeyboardBuilder()
    builder.button(text=s["btn_trading"], callback_data="mod_trading")
    builder.button(text=s["btn_dca"], callback_data="mod_coming")
    builder.button(text=s["btn_ton"], callback_data="mod_coming")
    builder.button(text=s["btn_rr"], callback_data="mod_coming")
    builder.button(text=s["btn_history"], callback_data="mod_coming")
    builder.button(text=s["btn_lang"], callback_data="mod_lang")
    builder.adjust(2, 2, 2)

    return builder.as_markup()


def build_back_button(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=STRINGS[get_lang(user_id)]["btn_back"],
        callback_data="go_to_menu",
    )
    return builder.as_markup()


def build_language_menu(user_id: int):
    lang = get_lang(user_id)
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇸 English", callback_data="set_lang_en")
    builder.button(text="🇷🇺 Русский", callback_data="set_lang_ru")
    builder.button(
        text=STRINGS[lang]["btn_back"],
        callback_data="go_to_menu",
    )
    builder.adjust(2, 1)

    return builder.as_markup()


# =========================
# BTC PRICE
# =========================

def _fetch_btc_price_sync():
    request = urllib.request.Request(
        COINGECKO_URL,
        headers={
            "User-Agent": "VORTEX-Telegram-Bot/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status != 200:
                return None

            data = json.loads(response.read().decode("utf-8"))

        price = Decimal(str(data["bitcoin"]["usd"]))

        if not price.is_finite() or price <= 0:
            return None

        return f"{price:,.2f}"

    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        InvalidOperation,
        json.JSONDecodeError,
    ) as exc:
        logger.warning("BTC API error: %s", exc)
        return None


async def fetch_btc_price():
    # Network access does not block Telegram's event loop.
    return await asyncio.to_thread(_fetch_btc_price_sync)


async def make_welcome(user_id: int):
    lang = get_lang(user_id)
    price = await fetch_btc_price()

    return STRINGS[lang]["welcome"].format(
        btc_price=price or STRINGS[lang]["price_unavailable"]
    )


# =========================
# TRADING CALCULATOR
# =========================

def parse_positive_decimal(value: str) -> Decimal:
    number = Decimal(value.replace(",", "."))

    if not number.is_finite() or number <= 0:
        raise ValueError("Number must be positive and finite")

    return number


def format_decimal(value: Decimal) -> str:
    return f"{value:.8f}".rstrip("0").rstrip(".")


def calculate_trade(entry, exit_price, leverage, direction):
    if (
        entry > MAX_PRICE
        or exit_price > MAX_PRICE
        or leverage < Decimal("1")
        or leverage > MAX_LEVERAGE
    ):
        raise ValueError("Input outside allowed range")

    if direction == "long":
        price_change = (exit_price - entry) / entry * 100
        liquidation = (
            entry * (1 - Decimal("1") / leverage)
            if leverage > 1
            else None
        )
    elif direction == "short":
        price_change = (entry - exit_price) / entry * 100
        liquidation = (
            entry * (1 + Decimal("1") / leverage)
            if leverage > 1
            else None
        )
    else:
        raise ValueError("Invalid direction")

    pnl = price_change * leverage

    return {
        "entry": entry,
        "exit": exit_price,
        "leverage": leverage,
        "direction": direction,
        "price_change": float(price_change),
        "pnl": float(pnl),
        "pnl_cash": float(pnl / 100),
        "liq": liquidation,
    }


# =========================
# DASHBOARD
# =========================

async def show_dashboard(message, user_id: int, edit=False):
    text = await make_welcome(user_id)
    markup = build_menu(user_id)

    try:
        if edit:
            await message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        else:
            await message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=markup,
            )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.warning("Dashboard error: %s", exc)


# =========================
# /START
# =========================

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    get_lang(user_id, message.from_user.language_code)
    USER_STATES[user_id] = "menu"

    await show_dashboard(message, user_id)


# =========================
# LANGUAGE SETTINGS
# =========================

@dp.callback_query(F.data == "mod_lang")
async def inline_lang_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = get_lang(user_id)

    try:
        await callback.message.edit_text(
            STRINGS[lang]["lang_select"],
            parse_mode="Markdown",
            reply_markup=build_language_menu(user_id),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.warning("Language menu error: %s", exc)

    await callback.answer()


@dp.callback_query(F.data.startswith("set_lang_"))
async def set_user_language(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    chosen_lang = callback.data.removeprefix("set_lang_")

    if chosen_lang not in STRINGS:
        await callback.answer("Unknown language", show_alert=True)
        return

    USER_LANGUAGES[user_id] = chosen_lang

    try:
        await callback.message.edit_text(
            STRINGS[chosen_lang]["lang_select"],
            parse_mode="Markdown",
            reply_markup=build_language_menu(user_id),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.warning("Language selection error: %s", exc)

    await callback.answer(STRINGS[chosen_lang]["language_changed"])


# =========================
# TRADING MENU
# =========================

@dp.callback_query(F.data == "mod_trading")
async def inline_trading(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = get_lang(user_id)

    USER_STATES[user_id] = "input_trading"

    try:
        await callback.message.edit_text(
            STRINGS[lang]["trading_intro"],
            parse_mode="Markdown",
            reply_markup=build_back_button(user_id),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            logger.warning("Trading menu error: %s", exc)

    await callback.answer()


# =========================
# COMING SOON MODULES
# =========================

@dp.callback_query(F.data == "mod_coming")
async def inline_coming_soon(callback: types.CallbackQuery):
    lang = get_lang(callback.from_user.id)

    await callback.answer(
        STRINGS[lang]["module_coming"],
        show_alert=True,
    )


# =========================
# RETURN TO DASHBOARD
# =========================

@dp.callback_query(F.data == "go_to_menu")
async def inline_go_to_menu(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    USER_STATES[user_id] = "menu"

    await show_dashboard(callback.message, user_id, edit=True)
    await callback.answer()


# =========================
# PROCESS USER MESSAGES
# =========================

@dp.message()
async def process_calculations(message: types.Message):
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    lang = get_lang(user_id, message.from_user.language_code)
    s = STRINGS[lang]

    if USER_STATES.get(user_id, "menu") != "input_trading":
        await show_dashboard(message, user_id)
        return

    parts = message.text.strip().split()

    if len(parts) not in (3, 4):
        await message.answer(
            s["invalid_format"],
            parse_mode="Markdown",
            reply_markup=build_back_button(user_id),
        )
        return

    try:
        entry = parse_positive_decimal(parts[0])
        exit_price = parse_positive_decimal(parts[1])
        leverage = parse_positive_decimal(parts[2])
    except (InvalidOperation, ValueError):
        await message.answer(
            s["invalid_values"],
            reply_markup=build_back_button(user_id),
        )
        return

    direction = parts[3].lower() if len(parts) == 4 else "long"

    if direction not in ("long", "short"):
        await message.answer(
            s["invalid_direction"],
            parse_mode="Markdown",
            reply_markup=build_back_button(user_id),
        )
        return

    try:
        result = calculate_trade(entry, exit_price, leverage, direction)
    except ValueError:
        await message.answer(
            s["invalid_values"],
            reply_markup=build_back_button(user_id),
        )
        return

    liquidation = (
        format_decimal(result["liq"])
        if result["liq"] is not None
        else s["liq_unavailable"]
    )

    report = s["report"].format(
        direction=result["direction"].upper(),
        entry=format_decimal(result["entry"]),
        exit=format_decimal(result["exit"]),
        leverage=format_decimal(result["leverage"]),
        price_change=result["price_change"],
        pnl=result["pnl"],
        pnl_cash=result["pnl_cash"],
        liq=liquidation,
    )

    USER_STATES[user_id] = "menu"

    await message.answer(
        report,
        parse_mode="Markdown",
        reply_markup=build_menu(user_id),
    )


# =========================
# GLOBAL ERROR HANDLER
# =========================

@dp.errors()
async def handle_errors(event):
    exception = event.exception
    logger.error(
        "Unhandled update error",
        exc_info=(
            type(exception),
            exception,
            exception.__traceback__,
        ) if exception else None,
    )
    return True


# =========================
# MAIN
# =========================

async def main():
    logger.info("VORTEX Terminal Engine is starting...")

    try:
        # Remove any webhook so polling can be used.
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("VORTEX Terminal Engine stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("VORTEX shutdown requested.")
