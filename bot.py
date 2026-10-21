import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8168185766:AAEaE2V5kwjMXE1GSFguL0daePSk2yAez9g"

# Твой ID администратора
ADMIN_ID = 7912203759  

CHANNEL_URL = "https://t.me/+TKXNi-Evmr4zMWJi"  # Твой ТГК
WORK_CHAT_URL = "https://t.me/+OnSQP70Guv0wMzQy"  # Рабочий чат
# ===================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния анкеты (FSM)
class Application(StatesGroup):
    username = State()
    volume = State()
    experience = State()
    topics = State()


# 1. Приветствие и кнопка продолжить
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    text = (
        f"👋 **Привет! Добро пожаловать в TrusterTraffik!**\n\n"
        f"Мы ищем сильных трафферов в команду.\n"
        f"Для продолжения необходимо подписаться на наш Telegram-канал."
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на ТГК", url=CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я подписался / Продолжить", callback_data="check_subscription"
                )
            ],
        ]
    )

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


# Переход к анкете
@dp.callback_query(F.data == "check_subscription")
async def check_sub(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "🚀 **Отлично! Заполним анкету.**\n\n"
        "**1. Укажи твой Telegram username** (например: @username):"
    )
    await state.set_state(Application.username)


# 2. Сбор данных анкеты
@dp.message(Application.username)
async def process_username(message: types.Message, state: FSMContext):
    await state.update_data(username=message.text)
    await message.answer("📊 **2. Сколько трафика можешь приводить в день?**")
    await state.set_state(Application.volume)


@dp.message(Application.volume)
async def process_volume(message: types.Message, state: FSMContext):
    await state.update_data(volume=message.text)
    await message.answer(
        "💼 **3. Есть ли опыт работы?** (Опиши кратко источники/опыт)"
    )
    await state.set_state(Application.experience)


@dp.message(Application.experience)
async def process_experience(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer(
        "🎯 **4. С какими тематиками готов работать?**"
    )
    await state.set_state(Application.topics)


@dp.message(Application.topics)
async def process_topics(message: types.Message, state: FSMContext):
    await state.update_data(topics=message.text)
    user_data = await state.get_data()
    await state.clear()

    await message.answer(
        "✅ **Заявка принята!** Она отправлена на рассмотрение администратору. Ожидай ответа."
    )

    # Формируем заявку для админа
    applicant_id = message.from_user.id
    admin_text = (
        f"📩 **Новая заявка в TrusterTraffik!**\n\n"
        f"👤 **Пользователь:** [{message.from_user.first_name}](tg://user?id={applicant_id})\n"
        f"🔗 **Юзернейм:** {user_data['username']}\n"
        f"📈 **Объём трафика/день:** {user_data['volume']}\n"
        f"💼 **Опыт работы:** {user_data['experience']}\n"
        f"🎯 **Тематики:** {user_data['topics']}\n\n"
        f"🆔 `ID: {applicant_id}`"
    )

    admin_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять", callback_data=f"accept_{applicant_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить", callback_data=f"decline_{applicant_id}"
                ),
            ]
        ]
    )

    # Отправляем анкету админу
    if ADMIN_ID != 0:
        await bot.send_message(
            chat_id=ADMIN_ID, text=admin_text, reply_markup=admin_kb, parse_mode="Markdown"
        )


# 3. Решение админа (Принять / Отклонить)
@dp.callback_query(F.data.startswith("accept_"))
async def accept_worker(callback: types.CallbackQuery):
    applicant_id = int(callback.data.split("_")[1])

    user_msg = (
        f"🎉 **Поздравляем! Твоя заявка в TrusterTraffik одобрена!**\n\n"
        f"Вступай в наш рабочий чат по ссылке ниже:\n{WORK_CHAT_URL}"
    )

    try:
        await bot.send_message(chat_id=applicant_id, text=user_msg, parse_mode="Markdown")
        await callback.message.edit_text(
            callback.message.text + "\n\n🟢 **СТАТУС: ПРИНЯТ**"
        )
        await callback.answer("Заявка одобрена, ссылка отправлена!")
    except Exception:
        await callback.answer("Ошибка при отправке сообщения юзеру.", show_alert=True)


@dp.callback_query(F.data.startswith("decline_"))
async def decline_worker(callback: types.CallbackQuery):
    applicant_id = int(callback.data.split("_")[1])

    try:
        await bot.send_message(
            chat_id=applicant_id,
            text="❌ К сожалению, твоя заявка в команду TrusterTraffik отклонена.",
        )
        await callback.message.edit_text(
            callback.message.text + "\n\n🔴 **СТАТУС: ОТКЛОНЕН**"
        )
        await callback.answer("Заявка отклонена.")
    except Exception:
        await callback.answer("Ошибка при отправке сообщения юзеру.", show_alert=True)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())