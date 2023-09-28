import requests
import logging
import telebot
from telebot import types
from bs4 import BeautifulSoup
import time

# Здесь нужно указать ваш токен Telegram бота
YOUR_TELEGRAM_TOKEN = ''

URL_RESIPES = 'https://globalcook.ru/categories/'
URL_FILMS = 'https://kino.mail.ru/cinema/all/2023/'
URL_NEWS = 'https://new-science.ru/category/tehnologii/'

# Настройки логгирования для телеграм-бота
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)

def get_food_categories():
    """Функция парсит html со страницы с категориями блюд, записывает в список, затем возвращает его"""
    r = requests.get(URL_RESIPES)
    soup = BeautifulSoup(r.text, "html.parser")

    # Ищем и сохраняем категории блюд
    food_categories = soup.findAll('a', class_='category-tile')
    categories = []

    for dish in food_categories:
        category_name = dish.find('h3').text
        link_to_category = dish.get('href')
        categories.append((category_name, link_to_category))

    return categories

# Глобальные переменные
link_to_category = None
keyboard_categories = None
keyboard_dishes = None
current_page = 1
current_page_news = 1

# Основная функция для запуска бота
def run_by_time_bot(token: str) -> None:
    """Run a simple Telegram bot."""
    bot = telebot.TeleBot(token, parse_mode=None)

    # Обработчик команды /start
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        """ Respond to a /start message. """
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button_1 = types.KeyboardButton(text="Выбрать рецепт")
        buttons.add(button_1)
        button_2 = types.KeyboardButton(text="Выбрать фильм")
        buttons.add(button_2)
        button_4 = types.KeyboardButton(text='Читать новости о технологиях')
        buttons.add(button_4)

        with open('hello.png', 'rb') as picture:
            bot.send_photo(message.chat.id, picture, "Привет {0.first_name}, очень рад знакомству!\nЯ бот, предназначенный для приятного времяпровождения.\nЗдесь ты можешь:\n1. Выбрать рецепт из 17-ти различных категорий.\n2. Выбрать фильм 2023 года по жанру и стране\n3. Почитать новости из мира технологий.\nЯ к твоим услугам, выбирай!".format(message.from_user), reply_markup=buttons)

    # Обработчик кнопки "Выбрать рецепт"
    @bot.message_handler(func=lambda message: message.text == "Выбрать рецепт")
    def select_recipe(message):
        """Функция вызывает функцию с категориями, забирает список категорий с линками и циклом по списку
        создает кнопки с текстом названия категории и callback_data для дальнейшей обработки после выбора категории"""
        categories_for_keyboard = get_food_categories()
        keyboard_categories = types.InlineKeyboardMarkup()

        # Создаем кнопки для каждой категории блюд
        for category_name, link_to_category in categories_for_keyboard:
            keyboard_categories.add(types.InlineKeyboardButton(
                text=category_name,
                callback_data=f'category_{link_to_category}'))

        # Отправляем пользователю сообщение с картинкой и кнопками
        with open('logo.png', 'rb') as photo:
            bot.send_photo(message.from_user.id, photo,"Выбери категорию блюд:", reply_markup=keyboard_categories)

    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        """В функции предназначенной для обработки всех callback-запросов обрабатываются нажатия на кнопки с категориями блюд.
         После нажатия на выбранную категорию удаляется префикс перед ссылкой, затем делаем запрос на извлеченную ссылку и парсим названия блюд,
         затем делаем кнопки с текстом из названий блюд и вшитых линков. Отправляем пользователю кнопки со всеми блюдами на странице с выбранной категорией."""
        if call.data.startswith('category_'):
            # Получаем ссылку на выбранную категорию блюд удаляя префикс
            category_link = call.data.replace('category_', '')

            # Отправляем запрос на страницу категории и получаем содержимое
            r_dishes = requests.get(category_link)
            soup_dishes = BeautifulSoup(r_dishes.text, "html.parser")

            # Ищем блюда внутри выбранной категории
            dishes = soup_dishes.findAll('h3', class_='entry-title')

            keyboard_dishes = types.InlineKeyboardMarkup()

            # Создаем кнопки для каждого блюда в категории
            for dish in dishes:
                dish_name = dish.find('a').text
                link_to_dish = dish.find('a').get('href')

                keyboard_dishes.add(types.InlineKeyboardButton(text=dish_name, url=link_to_dish))

            # Отправляем пользователю сообщение с кнопками выбора блюда
            bot.send_message(call.message.from_user.id, 'Выберите блюдо:', reply_markup=keyboard_dishes)


    # Обработчик кнопки "Выбрать фильм"
    @bot.message_handler(func=lambda message: message.text == "Выбрать фильм")
    def select_film(message):
        """Эта функция после нажатия на кнопку выбрать фильм делает запрос начиная с первой страницы с фильмами 2023 года, парсит страницу,
        циклом собирает все данные о 10-ти фильмах, затем собираются кнопки из названия, жанра и страны со вшитыми линками. Переменная страницы глобальная,
        поэтому каждое нажатие на кнопку возвращает пользователю 10 первых фильмов с текущей страницы."""
        global current_page  # Объявляем, что используем глобальную переменную
        data = []
        button_films = types.InlineKeyboardMarkup()
        url = f"{URL_FILMS}?page={current_page}"  # Используем текущую страницу
        response = requests.get(url)
        time.sleep(1)
        soup = BeautifulSoup(response.text, 'html.parser')
        films = soup.findAll('div', class_='p-itemevent-small js-event margin_bottom_30')

        for index, film in enumerate(films):
            link = 'https://kino.mail.ru' + film.find('a', class_='link link_inline link-holder link-holder_itemevent link-holder_itemevent_small').get('href')
            name = film.find('a', class_='link link_inline link-holder link-holder_itemevent link-holder_itemevent_small').text
            country = film.find('div', class_='margin_top_5').text
            callback_data = f'film_{current_page}_{index}'  # Уникальный callback_data для каждого фильма

            data.append([link, name, country, callback_data])
            if len(data) >= 10:  # Ограничиваем количество фильмов на одной странице
                break

        for link_film, name_film, country_film, callback_data in data:
            button_films.add(types.InlineKeyboardButton(
                text=f'{name_film}\n{country_film}',
                url=link_film  # Используем уникальный callback_data
            ))

        # Увеличиваем значение текущей страницы для следующего раза
        current_page += 1

        bot.send_message(message.from_user.id, "Выберите фильм:",  reply_markup=button_films)

        # Обработчик кнопки "Читать новости о технологиях"
    @bot.message_handler(func=lambda message: message.text == 'Читать новости о технологиях')
    def read_technology_news(message):
        """Эта функция после нажатия на кнопку 'читать новости о технологиях' делает запрос на страницу с новостями, затем парсит данные
        о дате, заголовке, кратком описании новости и линк на эту новость, затем отдает пользователю 5 новостей со страницы и кнопку с вшитым
        линком на эту новость. Функция как и предыдущая, при каждом нажатии на кнопку 'читать новости о технологиях' шагает по страницам с новостями,
        возвращая 5 верхних новостей с одной страницы"""
        global current_page_news
        data_news = []
        buttons_news = types.InlineKeyboardMarkup()  # Создаем общую клавиатуру для всех новостей
        url_news = f"{URL_NEWS}page/{current_page_news}/"
        response = requests.get(url_news)
        soup_news = BeautifulSoup(response.text, 'html.parser')
        news = soup_news.find_all('div', class_="post-details")

        for index_new, new in enumerate(news):
            link_news = 'https://new-science.ru' + new.find('a').get('href')
            date = new.find('span', class_='date meta-item tie-icon').text
            title = new.find('h2', class_='post-title').text
            short_news = new.find('p', class_="post-excerpt").text

            # Формируем текст для каждой новости
            news_text = f"{date}\n{title}\n{short_news}"

            # Создаем инлайн-кнопку "Читать эту новость" для каждой новости
            buttons_news.add(types.InlineKeyboardButton(
                text="Читать эту новость",
                url=link_news  # Устанавливаем ссылку для кнопки
            ))

            data_news.append([news_text, buttons_news])
            if len(data_news) >= 5:  # Ограничиваем количество новостей
                break

        for text, button in data_news:
            bot.send_message(message.from_user.id, text, reply_markup=button)

        current_page_news += 1

    # Обработчик всех остальных текстовых сообщений
    @bot.message_handler(func=lambda message: True)
    def handle_text(message):
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Воспользуйся кнопками или напиши /start.")

        # запустим бота
    bot.infinity_polling()

if __name__ == '__main__':
    run_by_time_bot(YOUR_TELEGRAM_TOKEN)

