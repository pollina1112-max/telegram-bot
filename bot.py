import asyncio
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Настройки бота
BOT_TOKEN = "7074018540:AAHAzdTSapW6iLE5izqh7BKSFFufPmTufBs"
ADMINS = ["irinamokshantseva", "fdgdgdghj"]  # usernames администраторов без @

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Состояния для записи администратором
class AdminStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_name = State()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        name TEXT,
        phone TEXT,
        date TEXT,
        time TEXT,
        service TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        notified INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    conn.close()

# Добавление записи
def add_appointment(user_id, chat_id, name, phone, date, time, service="Занятие"):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO appointments (user_id, chat_id, name, phone, date, time, service)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, chat_id, name, phone, date, time, service))
    
    conn.commit()
    conn.close()

# Получение записи по номеру телефона
def get_appointment_by_phone(phone):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT * FROM appointments 
    WHERE phone = ? AND date >= ?
    ORDER BY date, time
    ''', (phone, datetime.now().strftime('%Y-%m-%d')))
    
    appointment = cursor.fetchone()
    conn.close()
    
    return appointment

# Получение записей на завтра
def get_tomorrow_appointments():
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    cursor.execute('''
    SELECT * FROM appointments 
    WHERE date = ? AND notified = 0
    ''', (tomorrow,))
    
    appointments = cursor.fetchall()
    conn.close()
    
    return appointments

# Отметка о отправленном уведомлении
def mark_as_notified(appointment_id):
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE appointments SET notified = 1 WHERE id = ?
    ''', (appointment_id,))
    
    conn.commit()
    conn.close()

# Проверка администратора
def is_admin(user):
    return user.username in ADMINS

# Главное меню
def get_main_keyboard(is_admin_user=False):
    keyboard = [
        [KeyboardButton(text="📅 Моя запись")],
        [KeyboardButton(text="🎓 Направления подготовки")],
        [KeyboardButton(text="📍 Адрес и связь")],
        [KeyboardButton(text="👤 Мой ID")]
    ]
    
    if is_admin_user:
        keyboard.append([KeyboardButton(text="👑 Панель администратора")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    admin_status = is_admin(message.from_user)
    
    welcome_text = (
        "✨ *Добро пожаловать в Школу каллиграфии «Формула письма»!*\n\n"
        "🧚‍♂ *Ваш проводник в мир красивого почерка*\n\n"
        "• Постановка и коррекция почерка\n"
        "• Нейрогимнастика\n" 
        "• Гигиена письма\n"
        "• Графомоторика\n"
        "• Коррекция дисграфии\n"
        "• Письмо цифр\n"
        "• Логопедия\n\n"
        "Выберите нужный вариант из меню:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(admin_status),
        parse_mode='Markdown'
    )

# Моя запись
@router.message(lambda message: message.text == "📅 Моя запись")
async def my_appointment(message: types.Message):
    await message.answer(
        "📞 *Для просмотра вашей записи введите номер телефона,*\n"
        "*который вы указывали при записи:*\n\n"
        "Формат: +7 (902) 342-48-58 или 89023424858",
        parse_mode='Markdown'
    )

# Обработка номера телефона для поиска записи
@router.message(lambda message: message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '').isdigit() and len(message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '')) >= 10)
async def process_phone_for_appointment(message: types.Message):
    phone = message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '')
    
    if phone.startswith('8') and len(phone) == 11:
        phone = '7' + phone[1:]
    elif phone.startswith('7') and len(phone) == 11:
        pass
    else:
        phone = '7' + phone[-10:]
    
    appointment = get_appointment_by_phone(phone)
    
    if appointment:
        app_id, user_id, chat_id, name, phone, date, time, service, created_at, notified = appointment
        appointment_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
        
        appointment_text = (
            f"✅ *Ваша запись:*\n\n"
            f"👤 *Имя:* {name}\n"
            f"📞 *Телефон:* +7 {phone[1:4]} {phone[4:7]}-{phone[7:9]}-{phone[9:11]}\n"
            f"📅 *Дата:* {appointment_date}\n"
            f"⏰ *Время:* {time}\n"
            f"🎯 *Занятие:* {service}\n\n"
            f"🏫 *Место:* Ульяновская улица, 54А, Пенза\n\n"
            f"🔔 *Напоминание придёт за день до занятия!*"
        )
    else:
        appointment_text = (
            "❌ *Запись не найдена*\n\n"
            "Возможно:\n"
            "• Вы ещё не записаны\n"
            "• Номер телефона указан неверно\n"
            "• Запись уже прошла\n\n"
            "📞 *Для записи свяжитесь с администратором:*\n"
            "+7 (902) 342-48-58"
        )
    
    await message.answer(appointment_text, parse_mode='Markdown')

# Направления подготовки
@router.message(lambda message: message.text == "🎓 Направления подготовки")
async def show_directions(message: types.Message):
    directions_text = (
        "🎓 *Направления подготовки:*\n\n"
        "🏫 *Подготовка к школе:*\n"
        "🗣 *Логопедия:*\n"
        "✍️ *Коррекция почерка:*\n"
        "🎨 *Творческие МК:*\n"
        "📞 *Запись:* +7 (902) 342-48-58"
    )
    
    await message.answer(directions_text, parse_mode='Markdown')

# Адрес и связь
@router.message(lambda message: message.text == "📍 Адрес и связь")
async def show_contact(message: types.Message):
    contact_text = (
        "<b>📍 Адрес и контакты:</b>\n\n"
        "<b>🏫 Адрес:</b>\n"
        "Ульяновская улица, 54А, Пенза\n\n"
        "<b>📞 Телефон для записи:</b>\n"
        "+7 (902) 342-48-58\n\n"
        "<b>🌐 Социальные сети:</b>\n"
        "• VK: https://vk.link/formula_pisma\n"
        "• Telegram: https://t.me/formula_pisma\n\n"
    )
    
    await message.answer(contact_text, parse_mode='HTML')

# Показать ID пользователя
@router.message(lambda message: message.text == "👤 Мой ID")
async def show_user_id(message: types.Message):
    admin_status = "👑 *Администратор*" if is_admin(message.from_user) else "👤 *Клиент*"
    
    user_info = (
        f"📋 *Ваша информация:*\n\n"
        f"🆔 *ID:* `{message.from_user.id}`\n"
        f"📧 *Username:* @{message.from_user.username}\n"
        f"👤 *Имя:* {message.from_user.first_name}\n"
        f"🔰 *Статус:* {admin_status}\n\n"
        f"💡 *ID нужен для обращения к администратору*"
    )
    
    await message.answer(user_info, parse_mode='Markdown')

# Панель администратора
@router.message(lambda message: message.text == "👑 Панель администратора")
async def admin_panel(message: types.Message):
    if not is_admin(message.from_user):
        await message.answer("❌ Доступ запрещен")
        return
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить запись")],
            [KeyboardButton(text="📋 Список записей")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )
    
    await message.answer("👑 *Панель администратора*", reply_markup=keyboard, parse_mode='Markdown')

# Главное меню
@router.message(lambda message: message.text == "🔙 Главное меню")
async def back_to_main(message: types.Message):
    await cmd_start(message)

# Добавить запись
@router.message(lambda message: message.text == "➕ Добавить запись")
async def add_record(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user):
        await message.answer("❌ Доступ запрещен")
        return
    
    await state.set_state(AdminStates.waiting_for_phone)
    await message.answer("📱 Введите номер телефона клиента:")

# Обработка телефона
@router.message(AdminStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.replace(' ', '').replace('(', '').replace(')', '').replace('-', '').replace('+', '')
    
    if phone.startswith('8') and len(phone) == 11:
        phone = '7' + phone[1:]
    elif phone.startswith('7') and len(phone) == 11:
        pass
    else:
        phone = '7' + phone[-10:]
    
    await state.update_data(phone=phone)
    await state.set_state(AdminStates.waiting_for_date)
    await message.answer("📅 Введите дату занятия (ДД.ММ.ГГГГ):")

# Обработка даты
@router.message(AdminStates.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        date_obj = datetime.strptime(message.text, '%d.%m.%Y')
        await state.update_data(date=date_obj.strftime('%Y-%m-%d'))
        await state.set_state(AdminStates.waiting_for_time)
        await message.answer("⏰ Введите время занятия (ЧЧ:ММ):")
    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ")

# Обработка времени
@router.message(AdminStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    try:
        time_obj = datetime.strptime(message.text, '%H:%M')
        await state.update_data(time=time_obj.strftime('%H:%M'))
        await state.set_state(AdminStates.waiting_for_name)
        await message.answer("👤 Введите имя клиента:")
    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ")

# Сохранение записи
@router.message(AdminStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Сохраняем запись
    add_appointment(
        0,  # user_id
        message.chat.id,  # chat_id администратора
        message.text,  # имя клиента
        user_data['phone'],
        user_data['date'],
        user_data['time']
    )
    
    await state.clear()
    
    # Форматируем дату для красивого отображения
    appointment_date = datetime.strptime(user_data['date'], '%Y-%m-%d').strftime('%d.%m.%Y')
    phone_formatted = f"+7 {user_data['phone'][1:4]} {user_data['phone'][4:7]}-{user_data['phone'][7:9]}-{user_data['phone'][9:11]}"
    
    success_text = (
        f"✅ *Запись добавлена!*\n\n"
        f"👤 *Клиент:* {message.text}\n"
        f"📞 *Телефон:* {phone_formatted}\n"
        f"📅 *Дата:* {appointment_date}\n"
        f"⏰ *Время:* {user_data['time']}\n"
        f"🏫 *Место:* Ульяновская ул., 54А\n\n"
        f"📋 Клиенту будет отправлено напоминание за день до занятия."
    )
    
    await message.answer(success_text, parse_mode='Markdown')

# Список записей
@router.message(lambda message: message.text == "📋 Список записей")
async def show_appointments(message: types.Message):
    if not is_admin(message.from_user):
        await message.answer("❌ Доступ запрещен")
        return
    
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    # Будущие записи
    cursor.execute('''
    SELECT * FROM appointments 
    WHERE date >= ? 
    ORDER BY date, time
    ''', (datetime.now().strftime('%Y-%m-%d'),))
    
    appointments = cursor.fetchall()
    conn.close()
    
    if not appointments:
        await message.answer("📭 Нет предстоящих записей")
        return
    
    response = "📋 *Предстоящие записи:*\n\n"
    
    for app in appointments:
        app_date = datetime.strptime(app[5], '%Y-%m-%d').strftime('%d.%m.%Y')
        phone_formatted = f"+7 {app[4][1:4]} {app[4][4:7]}-{app[4][7:9]}-{app[4][9:11]}"
        response += f"👤 {app[3]} ({phone_formatted})\n"
        response += f"📅 {app_date} ⏰ {app[6]}\n"
        response += f"🎯 {app[7]}\n"
        response += "─" * 20 + "\n"
    
    # Разбиваем на части если слишком длинное
    if len(response) > 4000:
        parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in parts:
            await message.answer(part, parse_mode='Markdown')
            await asyncio.sleep(1)
    else:
        await message.answer(response, parse_mode='Markdown')

# Статистика
@router.message(lambda message: message.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if not is_admin(message.from_user):
        await message.answer("❌ Доступ запрещен")
        return
    
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE notified = 1')
    notified = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE date >= ?', 
                  (datetime.now().strftime('%Y-%m-%d'),))
    upcoming = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM appointments WHERE date < ?', 
                  (datetime.now().strftime('%Y-%m-%d'),))
    past = cursor.fetchone()[0]
    
    conn.close()
    
    stats_text = (
        f"📊 *Статистика записей:*\n\n"
        f"📋 Всего записей: *{total}*\n"
        f"✅ Напоминаний отправлено: *{notified}*\n"
        f"📅 Предстоящих занятий: *{upcoming}*\n"
        f"📆 Проведенных занятий: *{past}*\n\n"
        f"👑 Администраторы: @{ADMINS[0]}, @{ADMINS[1]}"
    )
    
    await message.answer(stats_text, parse_mode='Markdown')

# Отправка напоминаний
async def send_reminders():
    while True:
        try:
            appointments = get_tomorrow_appointments()
            
            for appointment in appointments:
                app_id, user_id, chat_id, name, phone, date, time, service, created_at, notified = appointment
                
                # Форматируем дату
                appointment_date = datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m.%Y')
                phone_formatted = f"+7 {phone[1:4]} {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
                
                reminder_text = (
                    f"🔔 *Напоминание о занятии!*\n\n"
                    f"У вас занятие на *завтра*:\n"
                    f"📅 *Дата:* {appointment_date}\n"
                    f"⏰ *Время:* {time}\n"
                    f"🎯 *Занятие:* {service}\n"
                    f"👤 *Ученик:* {name}\n\n"
                    f"🏫 *Место:* Ульяновская улица, 54А, Пенза\n"
                    f"📞 *Телефон:* +7 (902) 342-48-58\n\n"
                    f"💡 *Если не можете прийти - пожалуйста, предупредите заранее!*"
                )
                
                try:
                    # Отправляем напоминание администратору
                    admin_notification = (
                        f"🔔 Напоминание для клиента:\n"
                        f"👤 {name} ({phone_formatted})\n"
                        f"📅 {appointment_date} ⏰ {time}\n"
                        f"🎯 {service}"
                    )
                    await bot.send_message(chat_id, admin_notification)
                    
                    mark_as_notified(app_id)
                    print(f"✅ Напоминание отправлено для {name}")
                except Exception as e:
                    print(f"❌ Ошибка отправки: {e}")
            
            await asyncio.sleep(1800)  # Проверяем каждые 30 минут
            
        except Exception as e:
            print(f"❌ Ошибка в send_reminders: {e}")
            await asyncio.sleep(300)

# Запуск бота
async def main():
    init_db()
    asyncio.create_task(send_reminders())
    
    print("✅ Бот запущен!")
    print(f"🤖 Токен: {BOT_TOKEN}")
    print(f"👑 Администраторы: @{ADMINS[0]}, @{ADMINS[1]}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
