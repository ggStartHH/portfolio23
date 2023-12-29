import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from tocken import tok

bot = telebot.TeleBot(tok)
user_search_results = {}



bot_info = (
    "🎵 **Бот предназначен для поиска, прослушивания и скачивания музыки.**\n\n"
    "🔍 **Команды:**\n"
    "/start - Начать использование бота\n"
    "/search - Поиск музыки\n"
    "/mylike - Показать понравившиеся треки\n"
    "/info - Получить информацию о боте \n"
    "📥 **Скачать песню можно в /mylist** \n"
    "🚨 **Проблема с треками:** Если вместо песни бот прислал json файл, это проблема бота.\n"
    "🆓 **Бот бесплатный!** Просто подпишитесь на канал №№№.\n"
)

class Album:
    def __init__(self, title, link):
        self.title = title
        self.link = link
        self.tracks = []

class Track:
    def __init__(self, title, link):
        self.title = title
        self.link = link

albums = []

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Поиск🔎', callback_data='search')
    btn2 = types.InlineKeyboardButton('Info❓', callback_data='info')
    markup.add(btn1, btn2)
    bot.send_photo(message.chat.id, open(r'D:\aio\print1.png', 'rb'), reply_markup=markup)

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id, bot_info)

@bot.callback_query_handler(func=lambda call: call.data == 'info')
def process_search_query(call):
    bot.send_message(call.message.chat.id, bot_info)


@bot.message_handler(commands=['search'])
def handle_search_command(message):
    user_search_results[message.chat.id] = {'query': None, 'results': []}
    bot.send_message(message.chat.id, "...")
    bot.register_next_step_handler(message, search_query)

def search_query(message):
    chat_id = message.chat.id
    query = message.text.strip()

    user_search_results[chat_id]['query'] = query
    user_search_results[chat_id]['results'] = search_muzyet(query)

    if user_search_results[chat_id]['results']:
        send_search_results(chat_id)
    else:
        bot.send_message(chat_id, "Произошла ошибка во время поиска.")

@bot.callback_query_handler(func=lambda call: call.data == 'search')
def process_search_query(call):
    user_search_results[call.message.chat.id] = {'query': None, 'results': []}
    bot.send_message(call.message.chat.id, "...")
    bot.register_next_step_handler(call.message, search_query)


liked_songs = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith('like_'))
def handle_like_callback(call):
    chat_id = call.message.chat.id
    song_index = int(call.data.split('_')[1])

    if chat_id in user_search_results and user_search_results[chat_id]['results']:
        selected_song = user_search_results[chat_id]['results'][song_index - 1]
        track_title = selected_song['title']
        track_link = selected_song['link']

        # Add the liked track information to the dictionary for this user
        liked_songs.setdefault(chat_id, []).append({'title': track_title, 'link': track_link})

        bot.send_message(chat_id, f"Вы лайкнули песню: {track_title}")
    else:
        bot.send_message(chat_id, "Произошла ошибка.")



def send_search_results(chat_id):
    results = user_search_results[chat_id]['results']
    markup = types.InlineKeyboardMarkup(row_width=2)

    for index, result in enumerate(results[:15], start=1):
        btn_text = f"{index}. {result['title']}"
        btn = types.InlineKeyboardButton(text=btn_text, callback_data=f'song_{index}')
        like_btn = types.InlineKeyboardButton(text='Like ❤️', callback_data=f'like_{index}')
        markup.add(btn, like_btn)

    bot.send_message(chat_id, "Выберите песню:", reply_markup=markup)

@bot.message_handler(commands=['mylike'])
def show_liked_songs(message):
    chat_id = message.chat.id

    if chat_id in liked_songs and liked_songs[chat_id]:
        for song in liked_songs[chat_id]:
            title = song.get('title', '').strip()
            link = song.get('link').strip()
            
            # Create a clickable link with the text "Скачать"
            message_text = f"{title}\n[Скачать]({link})"
            
            # Send the message with Markdown formatting
            bot.send_message(chat_id, message_text, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "У вас нет понравившихся треков.")



@bot.callback_query_handler(func=lambda call: call.data.startswith('song_'))
def handle_song_callback(call):
    chat_id = call.message.chat.id
    song_index = int(call.data.split('_')[1])

    if chat_id in user_search_results and user_search_results[chat_id]['results']:
        selected_song = user_search_results[chat_id]['results'][song_index - 1]
        audio_link = selected_song['link']
        track_title = selected_song['title']

        bot.send_audio(chat_id, audio_link, title=track_title, performer="")
    else:
        bot.send_message(chat_id, "Произошла ошибка.")

def search_muzyet(query):
    try:
        base_url = f'https://muzyet.net/search/{query}'
        response = requests.get(base_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('div', class_='list lista_play song_list')

        search_results = []
        for result in results[:15]:
            titles = result.find_all('span', class_='artist_name')
            links = result.find_all('div', class_='right')

            for title, link in zip(titles, links):
                title_text = title.text.strip()
                link_data_id = link.get('data-id').strip()
                search_results.append({'title': title_text, 'link': link_data_id})

        return search_results  # Вернуть список словарей

    except requests.exceptions.RequestException as e:
        print(f'Ошибка: {e}')
        return None

if __name__ == "__main__":
    bot.polling(none_stop=True)
