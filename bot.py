import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, datetime, timedelta
from pytz import timezone

API_TOKEN = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Хранилище пользователей
users = []
scheduler = AsyncIOScheduler()
# Категории и продукты
categories = {
    "Для тела": [
        "Скраб", "Пилинг", "Крем", "Масло", "Баттер для тела",
        "Молочко для тела", "Мист", "Лосьон для тела",
        "Солнцезащитный крем", "Спрей", "Масло для кутикулы"
    ],
    "Для волос": [
        "Пилинг для кожи головы", "Масло для роста волос", "Маска для волос",
        "Бальзам для волос", "Скраб для кожи головы", "Масло для волос",
        "Термозащита", "Крем для волос", "Сыворотка для волос", "Кондиционер для волос"
    ],
    "Для лица": [
        "Смыть макияж", "Гидрофильное масло", "Пенка для умывания", "Гель для умывания",
        "Тоник", "Тонер", "Эссенция для лица", "Пэды для лица", "Мист для лица",
        "Крем для лица", "Крем под глаза", "Патчи под глаза", "Маска глиняная",
        "Маска тканевая", "Пилинг для лица", "Скраб для лица", "Лосьон для лица",
        "Патчи от прыщей", "Маска для губ", "Бальзам для губ", "Скраб для губ",
        "Сыворотка для роста ресниц", "Солнцезащитный крем"
    ],
}




# Функция для добавления нового пользователя
def add_user(user_id):
    f = 0
    for user in users:
        if user["id"] == user_id:
            f = 1
            start = user["start_count"] + 1

    if f == 0:
        users.append({"id": user_id, "start_count": 1, "products": [], "category": None, "time": None, "days": [],
                      "period": None})
    else:
        users.append({"id": user_id, "start_count": start, "products": [], "category": None, "time": None, "days": [],
                      "period": None})

def is_digit(s):
    if s.isdigit():
        return 1
    else:
        return 0

# Генерация клавиатуры времени
def generate_time_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=4)
    current_time = datetime.now()
    test_button_time = current_time + timedelta(minutes=2)
    formatted_test_button_time = test_button_time.strftime("%H:%M")
    times = [formatted_test_button_time]+[f"{hour:02d}:{minute:02d}" for hour in range(6, 24) for minute in (0, 30)]
    for time in times:
        keyboard.insert(InlineKeyboardButton(time, callback_data=f"time_{time}"))
    return keyboard


# Генерация клавиатуры дней недели
def generate_days_keyboard():
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = InlineKeyboardMarkup(row_width=2)
    for day in days:
        keyboard.insert(InlineKeyboardButton(day, callback_data=f"day_{day}"))
    keyboard.add(InlineKeyboardButton("Готово", callback_data="days_done"))
    return keyboard

# Генерация клавиатуры периодов
def generate_period_keyboard():
    periods = [
        "7 дней", "14 дней", "21 день", "1 месяц", "2 месяца",
        "3 месяца", "4 месяца", "5 месяцев", "6 месяцев", "7 месяцев",
        "8 месяцев", "9 месяцев", "10 месяцев", "11 месяцев", "1 год"
    ]
    keyboard = InlineKeyboardMarkup(row_width=2)
    for period in periods:
        keyboard.insert(InlineKeyboardButton(period, callback_data=f"period_{period}"))
    return keyboard

def categorie_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories.keys():
        markup.add(KeyboardButton(category))
    return markup

def delete_keyboard(user_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for user in users:
        if user_id == user["id"]:
            summary = (
                f" {user['category']}\n"
                f" {', '.join(user['products'])}\n"
                f" {user['time']}\n"
                f" {', '.join(user['days'])}\n"
                f" {user['period']}"
                f" {user['start_count']}\n"
            )
            markup.add(KeyboardButton(summary))
    return markup

async def send_scheduled_message(chat_id: int, text: str):
    await bot.send_message(chat_id=chat_id, text=text)


def schedule_message(chat_id: int, text: str, days: list, time: str, start_date: str, end_date: str, start_count: int):
    scheduler.add_job(
        send_scheduled_message,
        trigger=CronTrigger(
            day_of_week=",".join(days),  # Дни недели ('mon', 'tue', 'wed', etc.)
            hour=int(time.split(':')[0]),  # Час
            minute=int(time.split(':')[1]),  # Минута
            start_date=start_date,  # Начало периода
            end_date=end_date,  # Конец периода
            timezone=timezone("Europe/Moscow")
        ),
        kwargs={'chat_id': chat_id, 'text': text},  # Аргументы функции
        id=str(chat_id)+"_"+str(start_count)
    )

def try_user_id(user_id):
    f = 0
    for ind in range(len(users) - 1, -1, -1):
        user = users[ind]
        if user["id"] == user_id:
            user = users[ind]
            f = 1
            break
    if f == 0:
        user = None
    return user


# Хендлер для команды /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.chat.id
    user = try_user_id(user_id)
    if user == None:
        add_user(user_id)
        await message.answer("Добро пожаловать! Выберите категорию:", reply_markup=categorie_keyboard())
        return
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for button in ["Добавить", "Удалить", "Посмотреть все записи"]:
            markup.add(KeyboardButton(button))
        await message.answer("Добро пожаловать! Вы хотите удалить, добавить или посмотреть записи?", reply_markup=markup)
        return

@dp.message_handler(lambda message: message.text in ["Добавить", "Удалить", "Посмотреть все записи"])
async def choose_category(message: types.Message):
    user_id = message.chat.id
    user = try_user_id(user_id)

    if user is None:
        await message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return

    answer = message.text

    if answer == "Удалить":
        await message.answer("Добро пожаловать! Выберите запись для удаления:", reply_markup=delete_keyboard(user_id))
        return
    elif answer == "Посмотреть все записи":
        for user_from_users in users:
            # Формируем итоговое сообщение
            if user["id"] == user_from_users["id"]:
                summary = (
                    "----------------------------------------\n"
                    f"Категория: {user_from_users['category']}\n"
                    f"Продукты: {', '.join(user_from_users['products'])}\n"
                    f"Время: {user_from_users['time']}\n"
                    f"Дни недели: {', '.join(user_from_users['days'])}\n"
                    f"Период: {user_from_users['period']}\n"
                    "----------------------------------------\n"
                )
                await message.answer(summary)
        return
    else:
        add_user(user_id)
        await message.answer("Добро пожаловать! Выберите категорию:", reply_markup=categorie_keyboard())
        return


@dp.message_handler(lambda message: is_digit(str(message.text.split()[-1])))
async def choose_line_to_del(message: types.Message):
    user_id = message.chat.id
    user = try_user_id(user_id)

    if user is None:
        await message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return
    start_count = int(message.text.split()[-1])
    for ind in range(len(users)):
        user = users[ind]
        if user["id"] == user_id and user["start_count"] == start_count:
            users.pop(ind)
            scheduler.remove_job(str(user_id)+"_"+str(start_count))
            break
    await message.answer("Запись удалена", reply_markup=types.ReplyKeyboardRemove())
    return

# Хендлер для выбора категории
@dp.message_handler(lambda message: message.text in categories.keys())
async def choose_category(message: types.Message):
    user_id = message.chat.id
    user = try_user_id(user_id)

    if user is None:
        await message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return

    user["category"] = message.text
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for product in categories[message.text]:
        markup.add(KeyboardButton(product))
    markup.add(KeyboardButton("Готово"))
    await message.answer(f"Вы выбрали категорию '{message.text}'. Теперь выберите продукты:", reply_markup=markup)


# Хендлер для выбора продуктов
@dp.message_handler(lambda message: message.text in sum(categories.values(), []) or message.text == "Готово")
async def choose_product(message: types.Message):
    user_id = message.chat.id
    user = try_user_id(user_id)

    if user is None:
        await message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return

    if message.text == "Готово":
        selected_products = user["products"]
        if selected_products:
            await message.answer(f"Вы выбрали следующие продукты: {', '.join(selected_products)}.", reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer("Вы не выбрали ни одного продукта.", reply_markup=types.ReplyKeyboardRemove())
        await message.answer("Теперь выберите время:", reply_markup=generate_time_keyboard())
        return

    if message.text not in user["products"]:
        user["products"].append(message.text)
        await message.answer(f"Продукт '{message.text}' добавлен в ваш список.")
    else:
        await message.answer(f"Продукт '{message.text}' уже был добавлен.")


# Хендлер для выбора времени
@dp.callback_query_handler(lambda call: call.data.startswith("time_"))
async def choose_time(call: types.CallbackQuery):
    user_id = call.message.chat.id
    user = try_user_id(user_id)
    if user is None:
        await call.message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return
    selected_time = call.data.split("_")[1]
    user["time"] = selected_time
    await call.message.answer(f"Вы выбрали время: {selected_time}. Теперь выберите дни недели:",
                              reply_markup=generate_days_keyboard())



# Хендлер для выбора дней недели
@dp.callback_query_handler(lambda call: call.data.startswith("day_") or call.data == "days_done")
async def choose_days(call: types.CallbackQuery):
    user_id = call.message.chat.id
    user = try_user_id(user_id)
    if user is None:
        await call.message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return

    if call.data == "days_done":
        # Если пользователь завершает выбор дней
        if not user["days"]:
            await call.message.answer("Вы не выбрали ни одного дня недели. Выберите хотя бы один день.")
            return
        await call.message.answer(f"Вы выбрали дни недели: {', '.join(user['days'])}. Теперь выберите период:",
                                  reply_markup=generate_period_keyboard())
        return

    # Если пользователь выбирает конкретный день
    selected_day = call.data.split("_")[1]
    if selected_day not in user["days"]:
        user["days"].append(selected_day)
        await call.answer(f"День '{selected_day}' добавлен.")
    else:
        user["days"].remove(selected_day)  # Позволяем пользователю снять выбор
        await call.answer(f"День '{selected_day}' удален.")


# Хендлер для выбора периода
@dp.callback_query_handler(lambda call: call.data.startswith("period_"))
async def choose_period(call: types.CallbackQuery):
    user_id = call.message.chat.id
    user = try_user_id(user_id)
    if user is None:
        await call.message.answer("Вы не зарегистрированы. Введите /start для начала.")
        return

    # Сохраняем выбранный период
    selected_period = call.data.split("_")[1]
    user["period"] = selected_period
    await call.message.answer(f"Итог ваших настроек:\n")
    # Формируем итоговое сообщение
    summary = (
        "----------------------------------------\n"
        f"Категория: {user['category']}\n"
        f"Продукты: {', '.join(user['products'])}\n"
        f"Время: {user['time']}\n"
        f"Дни недели: {', '.join(user['days'])}\n"
        f"Период: {user['period']}\n"
        "----------------------------------------\n"
    )
    await call.message.answer(summary)
    await call.message.answer("Настройка завершена!")
    message_text = f"Пора сделать {', '.join(user['products'])}"

    days_of_week = []
    for day in user["days"]:
        if day == "Понедельник":
            days_of_week.append('mon')
        elif day == "Вторник":
            days_of_week.append('tue')
        elif day == "Среда":
            days_of_week.append('wed')
        elif day == "Четверг":
            days_of_week.append('thu')
        elif day == "Пятница":
            days_of_week.append('fri')
        elif day == "Суббота":
            days_of_week.append('sat')
        elif day == "Воскресенье":
            days_of_week.append('sun')

    current_date = date.today()
    selected_period = selected_period.split()
    if selected_period[1] in ["дней", "день"]:
        end_date = current_date+timedelta(days=int(selected_period[0]))
    elif selected_period[1] == "год":
        end_date = current_date + timedelta(days=365)
    else:
        end_date = current_date + timedelta(days=((int(selected_period[0])*30)))
    if not scheduler.running:
        scheduler.start()
    schedule_message(user_id, message_text, days_of_week, user["time"], current_date, end_date, user["start_count"])

# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
