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
        args = list()
        for arg in args_:
            args.append(str(arg))
        cursor.execute(f"INSERT INTO {table_name} ({','.join(tablesName[table_name])}) VALUES ({','.join(args)})")
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
    summary = cleanhtml( feed['summary'][:55])+'...'
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

@bot.message_handler(content_types=["new_chat_members"])
@bot.message_handler(func=lambda msg: True)
@bot.message_handler(func=lambda msg: True, commands=['start'])
def message_handler(message):
    """ just get chat name
    """
    chat_id = message.chat.id
    if chat_id in get_column('chats', 'id'):
        pass
    else:
        insert('chats', [chat_id])

# Run bot
threading.Thread(target=main_loop).start()
while True:
    print(f"Start {bot.get_me().first_name}")
    try:
        bot.polling(none_stop=True, interval=0, timeout=0)
    except Exception as err:
        print(err)
        time.sleep(10)