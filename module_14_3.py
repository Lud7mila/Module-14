# Задача "Витамины для всех!"
# aiogram 3.15, python 3.11

# Импортируем классы Bot и Dispatcher из библиотеки aiogram, которые необходимы для создания и управления ботом.
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command, CommandStart
# Импортируем класс MemoryStorage для хранения состояний конечного автомата (FSM) в памяти.
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)
# новый импорт
from aiogram.utils.keyboard import InlineKeyboardBuilder

import asyncio
import logging
import config
import re

router = Router()

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

# Выделяет число из строки со словами.
# Например, из строки "мне 20 лет" - функция вернет число 20
def extract_number(text):
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    else:
        return None

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer('Введите <b>"Рассчитать"</b>, чтобы начать рассчет Вашей нормы калорий.',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[
                             [
                                 KeyboardButton(text="Рассчитать"),
                                 KeyboardButton(text="Информация"),
                             ],
                             [KeyboardButton(text="Купить")],
                         ],
                             resize_keyboard=True,
                             one_time_keyboard=True,
                             input_field_placeholder="Нажмите любую кнопку"
                         )
    )

@router.message(F.text=='Информация')
async def info(message, bot: Bot):
    # Чтобы иметь возможность показать ID-кнопку, у пользователя должен быть False флаг has_private_forwards
    user_id = message.from_user.id
    chat_info = await bot.get_chat(user_id)
    if not chat_info.has_private_forwards:
        builder = InlineKeyboardBuilder()
        # builder.row(types.InlineKeyboardButton(text="Оф. канал Telegram", url="tg://resolve?domain=telegram"))
        builder.row(InlineKeyboardButton(text="Ваши данные", url=f"tg://user?id={user_id}"))
        await message.answer('Доброго дня! Я бот, помогающий <b>Вашему</b> здоровью.', reply_markup=builder.as_markup())
    else:
        await message.answer('Доброго дня! Я бот, помогающий <b>Вашему</b> здоровью.')


@router.message(F.text=='Купить')
async def get_buying_list(message):
    builder = InlineKeyboardBuilder()
    isProduct = False
    for number in range(1, 5):
        try:
            image_from_pc = FSInputFile(f"files/image{number}.png")
            # print(result.photo[-1].file_id) - id самой лучшей версии картинки
            # photo_id = 'AgACAgIAAxkDAAIELmdZttDgr9mw_rqRjQPPXvWKqQLoAAJn9DEb1k_QSvQtFrgqtNRqAQADAgADeAADNgQ'
            await message.answer_photo(image_from_pc, #photo_id,
                             caption=f'Название: Урбеч {number} | Описание: описание {number} | Цена: {number * 100}')
            builder.add(InlineKeyboardButton(text=f"Урбеч {number}", callback_data="product_buying"))
            isProduct = True
        except:
            logger.error('FileNotFound', exc_info=True)
    if isProduct:
        await message.answer("Выберите урбеч для покупки:", reply_markup=builder.as_markup())
    else:
        await message.answer("К сожалению все товары распроданы! Приходите завтра!")


@router.callback_query(F.data == "product_buying")
async def send_confirm_message(callback: CallbackQuery):
    await callback.message.answer("Вы успешно приобрели продукт!")


@router.message(F.text=='Рассчитать')
async def main_menu(message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Рассчитать норму калорий", callback_data='calories'))
    builder.add(InlineKeyboardButton(text="Формула расчёта", callback_data='formulas'))
    #await message.answer("🎁", reply_markup=ReplyKeyboardRemove())
    await message.answer('Выберите опцию:', reply_markup=builder.as_markup())


@router.callback_query(F.data == "formulas")
async def get_formulas(callback: CallbackQuery):
    #await callback.message.answer("Вот ссылка на формулу рассчёта Миффлина-Сан Жеора: https://www.calc.ru/Formula-Mifflinasan-Zheora.html")
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Перейти по ссылке на формулу рассчёта",
                                     url="https://www.calc.ru/Formula-Mifflinasan-Zheora.html"))
    await callback.message.answer('Хотите узнать о формуле рассчёта Миффлина-Сан Жеора?', reply_markup=builder.as_markup())


@router.callback_query(F.data == "calories")
async def set_age(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Пожалуйста, введите свой возраст (годы):")
    await state.set_state(UserState.age)


@router.message(UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    check_age = extract_number(message.text)
    if not check_age or not (1 <= check_age <= 150):
        await message.reply('Пожалуйста, введите корректный возраст (число от 1 до 150).')
        return
    await state.update_data(age=check_age)
    await message.answer('Пожалуйста, введите свой рост (см):')
    await state.set_state(UserState.growth)

@router.message(UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    check_growth = extract_number(message.text)
    if not check_growth or not (10 <= check_growth <= 250):
        await message.reply('Пожалуйста, введите корректный рост (число от 10 до 250).')
        return
    await state.update_data(growth=check_growth)
    await message.answer('Пожалуйста, введите свой вес (кг):')
    await state.set_state(UserState.weight)

@router.message(UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    check_weight = extract_number(message.text)
    if not check_weight or not (1 <= check_weight <= 150):
        await message.reply('Пожалуйста, введите корректный вес (число от 1 до 150).')
        return
    data = await state.update_data(weight=check_weight)
    # Упрощенный вариант формулы Миффлина-Сан Жеора: 10 х вес (кг) + 6,25 x рост (см) – 5 х возраст (г) + 5
    counter = 10 * data["weight"] + 6.25 * data["growth"] - 5 * data["age"] + 5
    await message.answer(f'Ваша норма калорий (по упрощенному варианту формулы Миффлина-Сан Жеора): {counter}.')
    await state.clear()

# Эхо
@router.message()
async def all_message(message: types.Message):
    await message.answer(message.text + '\n' + 'Введите команду /start, чтобы начать общение.')


# Запуск процесса поллинга
async def main():
    # Диспетчер
    disp = Dispatcher(storage=MemoryStorage())
    # Объект бота
    bot = Bot(config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    disp.include_router(router)
    # пропускаем все накопленные входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await disp.start_polling(bot)

if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    # запускаем бота
    asyncio.run(main())

