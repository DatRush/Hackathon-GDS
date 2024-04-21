# 7018224927:AAGOfPzIlVHr2Hrk9U2YpLT1UxlZ431bD7Y

from telegram import InputMediaPhoto
from telegram.constants import ParseMode
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import psycopg2
import requests
import json 
import re
from html import unescape
import time

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

GOOGLE_API_KEY = 'AIzaSyD7xicoRah_jW46T0gOAhmISDVMua3QuSQ'

# Функция для подключения к базе данных
def connect_db():
    return psycopg2.connect(dbname="Hackathon", user="postgres", password="1234", host="localhost")

# Функция для получения популярных объявлений
def get_popular_ads():
    conn = connect_db()
    with conn.cursor() as cur:
        cur.execute("SELECT title, id FROM ads LIMIT 10")  
        ads = cur.fetchall()
    conn.close()
    return ads

def clean_html(raw_html):
    cleanr = re.compile(r'<.*?>|<br\s*/?>\s*')  # Паттерн для поиска HTML тегов и символов <br> с последующими пробелами
    cleantext = re.sub(cleanr, '', raw_html)  # Удаление HTML тегов и символов <br>
    cleantext = unescape(cleantext)  # Декодирование HTML сущностей
    return cleantext



def get_google_route(start, end):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        'origin': f"{start[0]},{start[1]}",
        'destination': f"{end[0]},{end[1]}",
        'language': 'ru',
        'mode': 'WALKING',
        'key': GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Google Maps API Error: {response.status_code} - {response.text}")
        return None
    
def generate_map_url(start, end, route_polyline):
    path = f"enc:{route_polyline}"
    markers = f"size:mid|color:green|label:S|{start[0]},{start[1]}&markers=size:mid|color:red|label:E|{end[0]},{end[1]}"
    return f"https://maps.googleapis.com/maps/api/staticmap?size=600x400&path={path}&markers={markers}&key={GOOGLE_API_KEY}"



# Команда старта бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Популярное", callback_data='popular')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Привет! Нажми на кнопку "Популярное", чтобы увидеть список популярных объявлений.', reply_markup=reply_markup)
    
async def show_details(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_details, image_url):
    query = update.callback_query
    if query:
        await query.answer()

    details_message = (
        f"<b>{ad_details[0]}</b>\n\n"  # Название
        f"<a href='{ad_details[1]}'>Ссылка на страницу</a>\n\n"  # URL места
        f"Адрес: {ad_details[2]}\n"  # Адрес
    )

    keyboard = [
    [InlineKeyboardButton("Описание", callback_data=f"description_{ad_details[4]}")],
    [InlineKeyboardButton("Расписание", callback_data=f"schedule_{ad_details[4]}")],
    [InlineKeyboardButton("Контактные данные", callback_data=f"contact_{ad_details[4]}")],
    [InlineKeyboardButton("Построить маршрут", callback_data=f'route_{ad_details[4]}')],
    [InlineKeyboardButton("Вернуться назад", callback_data='popular')],
]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=image_url,
            caption=details_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        # Удаление предыдущего сообщения с кнопками
        await query.message.delete()
    else:
        # Если функция вызвана напрямую через команду, то отправляем фото без удаления предыдущего сообщения
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=image_url,
            caption=details_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )


# Функция для отображения описания
async def show_description(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_details):
    query = update.callback_query
    if query:
        await query.answer()

    description_message = f"Описание: {ad_details[3]}"
    
    # Ваша кнопка "Назад" должна вести на детали места
    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=f"detail_{ad_details[4]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=description_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    
# Функция для отображения контактных данных
async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_details):
    query = update.callback_query
    if query:
        await query.answer()

    contacts_message = (
        f"Телефон: {ad_details[1]}\n"  # Телефон
        f"Адрес: {ad_details[2]}"  # Адрес
    )

    keyboard = [
        [InlineKeyboardButton("Назад", callback_data=f"detail_{ad_details[4]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=contacts_message, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    

    
async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, ad_details):
    query = update.callback_query
    if query:
        await query.answer()

    schedule_message = f"Расписание:\n{ad_details['schedule']}"  # предполагаем, что расписание хранится в ad_details['schedule']

    # Кнопка для возвращения к деталям места
    keyboard = [
        [InlineKeyboardButton("Вернуться назад", callback_data=f"detail_{ad_details['id']}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если у сообщения есть подпись, обновляем подпись, иначе обновляем текст
    if query.message.caption:
        await query.edit_message_caption(caption=schedule_message, reply_markup=reply_markup)
    else:
        await query.edit_message_text(text=schedule_message, reply_markup=reply_markup)
        

    
def setup_handlers(application):
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location))
    
async def request_location(query, context: ContextTypes.DEFAULT_TYPE):
    # Так как InlineKeyboardButton не поддерживает запрос геолокации, используем обычное сообщение
    keyboard = [[KeyboardButton("Отправить моё местоположение", request_location=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    # Изменяем подпись текущего сообщения, чтобы показать инструкцию для пользователя
    await query.edit_message_caption(
        caption="Пожалуйста, нажмите на кнопку ниже, чтобы поделиться вашим местоположением.",
        reply_markup=None  # Удаляем предыдущие кнопки
    )

    # Отправляем новое сообщение с запросом на геолокацию
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="Поделитесь вашим местоположением:",
        reply_markup=reply_markup
    )

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_location = update.message.location
    if not user_location:
        await update.message.reply_text("Не удалось получить геолокацию.")
        return
    
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id - 1)
    except Exception as e:
        logging.error(f"Не удалось удалить сообщение: {e}")

    context.user_data['user_location'] = (user_location.latitude, user_location.longitude)
    destination = context.user_data.get('destination')

    if destination and 'id' in destination:
        route_response = get_google_route((user_location.latitude, user_location.longitude), (destination['latitude'], destination['longitude']))
        if route_response and route_response.get('routes'):
            route_info = route_response['routes'][0]['legs'][0]
            duration = route_info['duration']['text']
            distance = route_info['distance']['text']
            instructions = "Ваш маршрут:\n"
            for step in route_info['steps']:
                instruction_text = clean_html(step['html_instructions'])  # Очищаем HTML из инструкций
                duration_text = step['duration']['text']
                instructions += f"{instruction_text}, {duration_text}\n" 
                
            polyline = route_response['routes'][0]['overview_polyline']['points']
            map_url = generate_map_url((user_location.latitude, user_location.longitude), (destination['latitude'], destination['longitude']), polyline)
            
            keyboard = [
                [InlineKeyboardButton("Вернуться назад", callback_data=f"detail_{destination['id']}")],
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_photo(photo=map_url, caption=f"Дистанция: {distance}, Продолжительность: {duration}\n{instructions}", reply_markup=reply_markup)
        else:
            logging.error(f"Google Maps API Error: No routes found. Response was: {route_response}")
            await update.message.reply_text("Не удалось построить маршрут. Возможно, маршрут не доступен.")
    else:
        await update.message.reply_text("Место назначения не определено. Пожалуйста, выберите место еще раз.")






# Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    coords = None
    
    if data == 'popular':
        ads = get_popular_ads()
        message_text = "Выберите место:\n"
        keyboard = [
            [InlineKeyboardButton(ad[0], callback_data=f"detail_{ad[1]}")] for ad in ads
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=message_text, reply_markup=reply_markup)
    
    elif data.startswith('detail_'):
        place_id = data.split('_')[1]
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT title, url, address, description, id, image_url FROM ads WHERE id = %s", (place_id,))
            ad_details = cur.fetchone()
        conn.close()
        
        if ad_details:
            await show_details(update, context, ad_details, ad_details[5])

    elif data.startswith('description_'):
        place_id = data.split('_')[1]
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT description FROM ads WHERE id = %s", (place_id,))
            description = cur.fetchone()[0]
        conn.close()
        
        description_message = f"Описание: {description}"
        keyboard = [
            [InlineKeyboardButton("Вернуться назад", callback_data=f"detail_{place_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.caption:
            await query.edit_message_caption(caption=description_message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=description_message, reply_markup=reply_markup)

    elif data.startswith('contact_'):
        place_id = data.split('_')[1]
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT phone, address FROM ads WHERE id = %s", (place_id,))
            contact_details = cur.fetchone()
        conn.close()

        contacts_message = f"Телефон: {contact_details[0]}\nАдрес: {contact_details[1]}"
        keyboard = [
            [InlineKeyboardButton("Вернуться назад", callback_data=f"detail_{place_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.caption:
            await query.edit_message_caption(caption=contacts_message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=contacts_message, reply_markup=reply_markup)
            
    elif data.startswith('route_'):
        place_id = data.split('_')[1]
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT latitude, longitude FROM ads WHERE id = %s", (place_id,))
            coords = cur.fetchone()
        conn.close()

    if coords:
        context.user_data['destination'] = {'latitude': coords[0], 'longitude': coords[1], 'id': place_id}
        # Вызов функции request_location для изменения текста и отображения кнопки
        await request_location(query, context)

    
    elif data.startswith('schedule_'):
        place_id = data.split('_')[1]
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT schedule FROM ads WHERE id = %s", (place_id,))
            schedule = cur.fetchone()[0]
        conn.close()
        
        schedule_message = f"Расписание: {schedule}"
        keyboard = [
            [InlineKeyboardButton("Вернуться назад", callback_data=f"detail_{place_id}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if query.message.caption:
            await query.edit_message_caption(caption=schedule_message, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=schedule_message, reply_markup=reply_markup)
            
    elif data == 'back_to_list':
        ads = get_popular_ads()
        message_text = "Выберите место из списка популярных мест:\n"
        keyboard = [
            [InlineKeyboardButton(ad[0], callback_data=f"detail_{ad[1]}")] for ad in ads
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if query.message.photo:
            await query.edit_message_caption(caption=message_text, reply_markup=reply_markup)
        else:
            await query.edit_message_text(text=message_text, reply_markup=reply_markup)



            


# Основная функция для запуска бота
def main():
    application = Application.builder().token("7018224927:AAGOfPzIlVHr2Hrk9U2YpLT1UxlZ431bD7Y").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    # application.add_handler(CallbackQueryHandler(handle_send_location, pattern='^send_location$'))
    application.add_handler(MessageHandler(filters.LOCATION, handle_location)) 
    application.run_polling()

if __name__ == '__main__':
    main()
