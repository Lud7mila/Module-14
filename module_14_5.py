# Задача "Продуктовая база"
# aiogram 3.15, python 3.11

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.storage.memory import MemoryStorage # будем хранить FSM в памяти.
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile
)
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.keyboard import InlineKeyboardBuilder

import asyncio
#import logging
import re

import config
from crud_functions_5 import *


router = Router()

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()
    balance = State(1000)

# Выделяет число из строки со словами.
# Например, из строки "мне 20 лет" - функция вернет число 20
def extract_number(text):
    match = re.search(r'\b(\d+)\b', text)
    if match:
        return int(match.group(1))
    else:
        return None

# Проверяет состоит ли имя только из латинских букв
def validate_name(name: str) -> bool:
    valid_pattern = re.compile(r"^[a-z]+$", re.I)
    return bool(valid_pattern.match(name))

# Проверяет состоит ли имя только из латинских букв
def validate_email(email: str) -> bool:
    valid_pattern = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(valid_pattern.match(email))

@router.message(CommandStart())
async def send_welcome(message: types.Message):
    await message.answer('Введите <b>"Рассчитать"</b>, чтобы начать рассчет Вашей нормы калорий.',
                         reply_markup=ReplyKeyboardMarkup(keyboard=[
                             [
                                 KeyboardButton(text="Рассчитать"),
                                 KeyboardButton(text="Информация"),
                             ],
                             [
                                KeyboardButton(text="Купить"),
                                KeyboardButton(text="Регистрация"),
                             ],
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
    # получаем данные с базы данных о товарах
    productsData = get_all_products() #crud_functions_4.get_all_products()
    if not productsData:
        await message.answer("Не удаётся получить доступ к информации о товарах")
        return

    builder = InlineKeyboardBuilder()
    isProduct = False
    number = 1
    for product in productsData:
        try:
            image_from_pc = FSInputFile(f"files/image{number}.png")
            await message.answer_photo(photo=image_from_pc,
                                        caption=f'Название: {product["title"]} | ' +
                                                f'Описание: {product["description"]} | \n' +
                                                f'Цена: {product["price"]}')
            builder.add(InlineKeyboardButton(text=product["title"],
                                             callback_data="product_buying"))
            isProduct = True
            number += 1
        except:
            logger.error(f'File not found: files/image{number}.png') #, exc_info=True)

    if isProduct:
        await message.answer("Выберите урбеч для покупки:", reply_markup=builder.as_markup())
    else:
        await message.answer("К сожалению все товары распроданы! Приходите завтра!")


@router.callback_query(F.data == "product_buying")
async def send_confirm_message(callback: CallbackQuery):
    await callback.message.answer("Вы успешно приобрели продукт!")


@router.message(F.text=='Регистрация')
async def sing_up(message, state: FSMContext):
    await message.answer('Введите имя пользователя (только латинский алфавит):')
    await state.set_state(RegistrationState.username)

@router.message(RegistrationState.username)
async def set_username(message: Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.reply('Пользователь уже существует в БД, введите другое имя:')
        return
    if not validate_name(username):
        await message.reply('Пожалуйста, введите корректное имя (только латинский алфавит):')
        return
    await state.update_data(username=username)
    await message.answer('Пожалуйста, введите свой email:')
    await state.set_state(RegistrationState.email)

@router.message(RegistrationState.email)
async def set_email(message: Message, state: FSMContext):
    email = message.text
    if not validate_email(email):
        await message.reply('Пожалуйста, введите корректный email:')
        return
    await state.update_data(email=email)
    await message.answer('Пожалуйста, введите свой возраст:')
    await state.set_state(RegistrationState.age)

@router.message(RegistrationState.age)
async def set_age(message: Message, state: FSMContext):
    check_age = extract_number(message.text)
    if not check_age or not (1 <= check_age <= 150):
        await message.reply('Пожалуйста, введите корректный возраст (число от 1 до 150).')
        return
    data = await state.update_data(age=check_age)
    add_user(data['username'], data['email'], data['age'])
    await message.answer('Регистарация прошла успешно!')
    await state.clear()


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
async def set_growth(message: Message, state: FSMContext):
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
    bot = Bot(config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True) # пропускаем все накопленные входящие сообщения
    disp = Dispatcher(storage=MemoryStorage())
    disp.include_router(router)
    await disp.start_polling(bot)

if __name__ == "__main__":
    # Включаем логирование, чтобы не пропустить важные сообщения
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    initiate_db()

    # запускаем бота
    asyncio.run(main())

    connectionUsers.close()
    connectionProd.close()

