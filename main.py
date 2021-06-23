import telebot
import os
import re
import threading
import feedparser
import sqlite3
import time
from config import TOKEN
from make_db import tablesName

bot = telebot.TeleBot(TOKEN)
bot_id = bot.get_me().id
bot_username = '@'+bot.get_me().username
url = "https://aosus.org/latest.rss"
sleep = 15


# Check for the existence of the database
if os.path.lexists("./db.sqlite3"):
    coon = sqlite3.connect('./db.sqlite3', check_same_thread=False)
    cursor = coon.cursor()
    lock = threading.Lock()
else:
    print("make database first form 'make_db.py'")
    quit()
if os.path.lexists("./last_id.txt"):
    pass
else:
    with open('./last_id.txt','w+') as f:
        pass

def insert(table_name:str, args_:tuple):
    """ Insert values into database

    Args:
        table_name (str): name of table you want insert to
        args_ (tuple): args of column
    """
    try:
        lock.acquire(True)
        args = tuple(map(str, args_))
        first_element = f"('{args[0]}')"
        cursor.execute(f"INSERT INTO {table_name} ({','.join(tablesName[table_name])}) VALUES {tuple(args) if len(args) > 1 else first_element}")
        coon.commit()
    finally:
        lock.release()

def get_column(table_name:str, column:str):
    """ Return all values in column

    Args:
        table_name (str): name of table you want get column from
        column (str): column name you want fetch

    Returns:
        list: list of values
    """
    try:
        lock.acquire(True)
        cursor.execute(f"SELECT {column} FROM {table_name}")
        return [val for table in cursor.fetchall() for val in table]
    finally:
        lock.release()


def del_row(table_name:str, column:str, value:str):
    """ Delete row from database

    Args:
        table_name (str): name of table you want delete from
        column (str): Column containing the value whose row you want to delete
        value (str): value whose row you want to delete
    """
    try:
        lock.acquire(True)
        cursor.execute(f"DELETE FROM {table_name} WHERE {column}='{value}'")
        coon.commit()
    finally:
        lock.release()

def get_latest_news():
    """ Return latest news from https://aosus.org/latest
        use rss

    Returns:
        dict: Details of the latest news
    """
    return feedparser.parse(url).entries[0]

def get_last_id():
    """ Return id from './last_id.txt'

    Returns:
        str: id of latest news
    """
    with open('./last_id.txt','r') as f:
        last_id = f.read()
        return last_id

def add_id(news_id:str):
    """ write news_id in './last_id.txt'

    Args:
        news_id (str): id of news
    """
    with open('./last_id.txt', 'w') as f:
        f.write(news_id)

def get_is_admin(chat_id:int, user_id:int):
    """ return if the user_id admin in chat_id

    Args:
        chat_id (int): chat_id
        user_id (int): user_id

    Returns:
        bool: user id admin in chat_id
    """
    if chat_id == user_id: # if is chat_id == user_id that mean is private
        return False
    else:
        return user_id in map(lambda user: user.user.id, bot.get_chat_administrators(chat_id))

def convert_status(chat_id:int, msg_id:int, new_status:str):
    """ convert the status of chat

    Args:
        chat_id (int): chat id
        msg_id (int): message id
        new_status (str): new chat status
    """
    status = 'on' if str(chat_id) in get_column('chats', 'id') else 'off'
    if status == new_status:
        bot.send_message(chat_id, "هذه هي حالة البوت في هذه المحادثة بالفعل",
                            reply_to_message_id=msg_id)
    else:
        if new_status == 'on':
            bot.send_message(chat_id, "تم تفعيل الاشتراك", reply_to_message_id=msg_id)
            insert('chats', (chat_id,))
        else:
            bot.send_message(chat_id, "تم الغاء تفعيل الاشتراك", reply_to_message_id=msg_id)
            del_row('chats', 'id', str(chat_id))

def cleanhtml(raw_html:str):
    """ clean html raw form tags

    Args:
        raw_html (str): html raw

    Returns:
        str: clean text
    """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def get_text(feed):
    """ Return text of news

    Args:
        feed ('feedparser.util.FeedParserDict'): rss
    """
    title = feed['title']
    author = feed['author']
    tag = feed['tags'][0]['term']
    summary = cleanhtml( feed['summary'])
    summary = summary[:summary.find(' ', 55)]+'...'
    link = feed['link']
    text = f"موضوع جديد على مجتمع اسس من {author} \n\n <b><a href='{link}'>{title}</a></b> \n\n <code>{summary}</code> \n\nالقسم:{tag}"
    return text

def send_to_users(feed):
    """ send to user the news

    Args:
        feed ('feedparser.util.FeedParserDict'): rss
    """
    text = get_text(feed)
    for chat_id in get_column('chats', 'id'):
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
        except Exception:
            pass

def main_loop():
    """Fetch latest news and sends to users"""
    while True:
        if len(get_column('chats', 'id')) != 0:
            feed = get_latest_news()
            if feed.id != get_last_id():
                add_id(feed.id)
                send_to_users(feed)
            else:
                pass
        else:
            pass
        time.sleep(sleep)

@bot.edited_message_handler(func= lambda msg: True)
@bot.message_handler(content_types=["new_chat_members"])
@bot.message_handler(func=lambda msg: True)
@bot.message_handler(func=lambda msg: True, commands=['start', 'help', 'on', 'off'])
def message_handler(message):
    """ just get chat id
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    msg_id = message.id
    is_private_chat = message.chat.type == "private"
    is_admin = get_is_admin(chat_id, user_id)
    new_chat_member_id = message.new_chat_members[0].id if message.new_chat_members else None
    start_msg = "اهلا بك <a href='tg://user?id={id}'>{name}</a>\nهذا البوت مخصص لارسال اخر المواضيع الخاصة بمجتمع اسس للبرامج الحرة والمفتوحة.\nلتفعيل الاشتراك: /on\nاذا اردت الغاء الاشتراك : /off\n\n\nhttps://aosus.org"
    text = message.text.replace(bot_username, '').lower() if message.text else None # replace bot username because commands like this
    if text: # Avoid error, 'NoneType' object has no attribute 'startswith'
        if text.startswith(('/on', '/off')):
            if is_private_chat:
                convert_status(chat_id, msg_id, text[1:]) # [1:] mean remove the /
            else:
                if is_admin:
                    convert_status(chat_id, msg_id, text[1:]) # [1:] mean remove the /on@bot_username
                else:
                    bot.reply_to(message, "يجب ان تكون ادمن لكي تقوم بهذا الامر")
        elif text.startswith('/start') and is_private_chat:
            text = start_msg.format(name=first_name, id=user_id)
            bot.reply_to(message, text, parse_mode="HTML")
        elif text.startswith('/help'):
            text = "اهلا بك في خدمة ارسال اخر المواضيع الخاصة بمجتمع اسس للبرامج الحرة والمفتوحة..\nللاشتراك ارسل: /on\nولالغاء الاشتراك ارسل: /off\n\n\nhttps://aosus.org"
            bot.reply_to(message, text)
        else:
            pass
    else:
        if new_chat_member_id == bot_id:
            text = f"شكرا <a href='tg://user?id={user_id}'>{first_name}</a> لاضافتي الى المحادثة 🌹\n{start_msg.format(name=first_name, id=user_id)}"
            bot.send_message(chat_id, text, parse_mode="HTML")

# Run bot
threading.Thread(target=main_loop).start()
while True:
    print(f"Start {bot.get_me().first_name}")
    try:
        bot.polling(none_stop=True, interval=0, timeout=0)
    except Exception as err:
        print(err)
        time.sleep(10)