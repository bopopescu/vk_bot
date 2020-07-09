import json

import mysql.connector
import requests
import vk_api
from flask import Flask
from vk_api.longpoll import VkLongPoll, VkEventType

app = Flask(__name__)

mydb = mysql.connector.connect(
    host='127.0.0.1',
    user='csn',
    passwd='4252',
    database='vk_bot'
)


def query_db(query):
    cursor = mydb.cursor()
    cursor.execute(query)
    res = cursor.fetchall()
    res = [i[0] if len(i) == 1 else i for i in res]
    return res


def insert_db(insert, value):
    cursor = mydb.cursor()
    cursor.execute(insert, value)
    mydb.commit()


api_key = '1639dc5f4da29d0eb1d289a6d511869e7986be516a4faf70d7da7b90ef7371b97d7a44c6f8a0a5183e266'
access_token = '486a446f486a446f486a446fab481aa93b4486a486a446f16e569472a84f996a20a18c5'

vk_session = vk_api.VkApi(token=api_key)
session_api = vk_session.get_api()
longpull = VkLongPoll(vk_session)
version = 5.103
owner_id = '-196641047'


def exec_api(method, params):
    init = {
        'access_token': access_token,
        'v': version,
        'owner_id': owner_id
    }
    init.update(params)

    return requests.get(f'https://api.vk.com/method/{method}', params=init).json()


def get_photo_id():
    photos = exec_api('photos.get', params={'album_id': '272028839'})['response']['items']
    photo_description = list()
    photo_ids = list()
    for item in photos:
        photo_description.append(str(item['text']))
    for item in photos:
        photo_ids.append('photo-' + str(str(item['owner_id']) + '_' + str(item['id']))[1:])
    return photo_ids, photo_description


def sender(usr_id, text, keyboard, photo):
    vk_session.method('messages.send',
                      {'user_id': usr_id, 'keyboard': keyboard, 'attachment': photo, 'message': text, 'random_id': 0})


def get_button(label, color, payload=''):
    return {
        "action": {
            "type": "text",
            "payload": json.dumps(payload),
            "label": label
        },
        'color': color
    }


keyboard_for_start = {
    'one_time': False,
    'buttons': [
        [
            get_button(label='Розыгрыш', color='primary'),
        ],
        [
            get_button(label='Правила', color='negative'),
            get_button(label='Реквизиты', color='positive'),
        ]
    ]
}

keyboard_for_start = json.dumps(keyboard_for_start, ensure_ascii=False).encode('utf-8')
keyboard_for_start = str(keyboard_for_start.decode('utf-8'))

keyboard_for_play = {
    'one_time': False,
    'buttons': [

        [
            get_button(label='Свободные номерки', color='positive'),
            get_button(label='Мои номерки', color='primary'),
        ],
        [
            get_button(label='Назад', color='negative'),
        ]

    ]
}

keyboard_for_play = json.dumps(keyboard_for_play, ensure_ascii=False).encode('utf-8')
keyboard_for_play = str(keyboard_for_play.decode('utf-8'))

keyboard_for_event = {
    'one_time': False,
    'buttons': [
        [
            get_button(label='Играть', color='positive'),
        ],
        [
            get_button(label='Что разыгрывается', color='positive'),
            get_button(label='Как занять номерок?', color='primary'),
        ],
        [
            get_button(label='Назад', color='negative'),
        ],

    ]
}

keyboard_for_event = json.dumps(keyboard_for_event, ensure_ascii=False).encode('utf-8')
keyboard_for_event = str(keyboard_for_event.decode('utf-8'))

for event in longpull.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:

            msg = event.text.lower()
            user_id = event.user_id
            request_api = exec_api('users.get', params={'user_ids': user_id})['response'][0]
            username = request_api['first_name'] + ' ' + request_api['last_name']

            if msg == 'начать':
                text_msg = 'Добро пожаловть!'
                sender(user_id, text_msg, keyboard_for_start, photo=None)

            elif msg == 'правила':
                text_msg = open('description')
                sender(user_id, text_msg.read(), keyboard_for_start, photo=None)

            elif msg == 'реквизиты':
                text_msg = open('requisites')
                sender(user_id, text_msg.read(), keyboard_for_start, photo=None)

            elif msg == 'розыгрыш':
                text_msg = '🔥Чтобы принять учстие в розыгрыше, напишите номер талончика, который хотите занять👇🏻'
                sender(user_id, text_msg, keyboard_for_event, photo=None)

            elif msg == 'назад':
                text_msg = 'Основная страница'
                sender(user_id, text_msg, keyboard_for_start, photo=None)

            elif msg == 'что разыгрывается':
                text_msg = get_photo_id()[1]
                text_msg = '\n\n'.join(text_msg)
                photo_id = get_photo_id()[0]
                photo_id = ','.join(photo_id)
                sender(user_id, text_msg, keyboard_for_event, photo_id)

            elif msg == 'как занять номерок?':
                text_msg = '✅Для того, чтобы занять талончик, пишите в чат номерок, который выбрали. \n\n' \
                           '‼ОЧЕНЬ ВАЖНО‼ \n\n' \
                           'Не надо писть по несколько номерков одновременно! \n\n' \
                           'Если хотите занять несколько, пишите каждый номерок в отдельном сообщении'
                sender(user_id, text_msg, keyboard_for_event, photo=None)

            elif msg == 'играть':
                text_msg = 'Для того, чтобы занять талончик, пишите в чат номерок, который выбрали.'
                sender(user_id, text_msg, keyboard_for_play, photo=None)

            elif msg == 'свободные номерки':
                all_number = query_db(f'SELECT number FROM play')
                result = [int(item) + int(0) for item in all_number]
                user_list = list()
                for item in range(1, 41):
                    user_list.append(item)
                for item in result:
                    user_list.remove(item)

                result = [str(item) for item in user_list]
                result = ' '.join(result)
                text_msg = f'💦Свободные \n\n {result}'
                sender(user_id, text_msg, keyboard_for_play, photo=None)

            elif msg == 'мои номерки':
                user_numbers = query_db(f'SELECT number FROM play WHERE name="{username}"')
                list_user_number = list()
                for number in user_numbers:
                    list_user_number.append(number)

                result = [str(item) for item in list_user_number]
                result = ' '.join(result)
                if result is None:
                    text_msg = '🚫Вы не занимали талончики!'
                    sender(user_id, text_msg, keyboard_for_play, photo=None)
                else:
                    text_msg = f'🔥Номерки, которые вы заняли: \n\n {result}'
                    sender(user_id, text_msg, keyboard_for_play, photo=None)

            elif len(msg) <= 2:
                number = int(msg)
                if number < 1:
                    text_msg = '🚫Введите положительное число!'
                    sender(user_id, text_msg, keyboard_for_play, photo=None)
                elif number > 40:
                    text_msg = '🚫Ваше число превышает колличество талончиков!'
                    sender(user_id, text_msg, keyboard_for_play, photo=None)
                else:
                    username = exec_api('users.get', params={'user_ids': user_id})['response'][0]
                    username = username['first_name'] + ' ' + username['last_name']
                    review = query_db(f'SELECT number FROM play WHERE number={number}')
                    if review:
                        text_msg = '🚫Данный талончик уже занят!'
                        sender(user_id, text_msg, keyboard_for_play, photo=None)
                    else:
                        text_msg = f'✅Вы заняли талончик №{number}'
                        insert_db('INSERT INTO play (number, name) VALUE (%s, %s)', (number, username))
                        sender(user_id, text_msg, keyboard_for_play, photo=None)

            else:
                text_msg = 'Скорее всего, вы ввели что-то не верно. \n\n ' \
                           'Помните, что в игре учавствует всего 40 талончиков🔥 \n\n' \
                           'Используйте клавиатуру бота и внимаьельно читайте инфрмацию'
                sender(user_id, text_msg, keyboard_for_event, photo=None)

if __name__ == '__main__':
    app.run()
