import telebot
import os
import re
import threading
import feedparser
import sqlite3
import time
from config import TOKEN, super_users
from make_db import tablesName

bot = telebot.TeleBot(TOKEN)
bot_id = bot.get_me().id
bot_username = '@'+bot.get_me().username
url = "https://aosus.org/latest.rss"
sleep = 15


# التحقق من وجود قاعدة البيانات
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
    """ ادخال البيانات داخل قاعدة البيانات
    المتغيرات:
        table_name (str): اسم الجدول المراد ادخال البيانات فيه
        args_ (tuple): القيم التي سوف تملي بها الاعمدة الخاصة بالجدول
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
    """ ترجع لك جميع القيم التي في العامود المعطى
    المتغيرات:
        table_name (str): اسم الجدول اذي يوجد فيه العامود
        column (str): اسم العامود الذي تريد اسخراج جميع القيم التي به
    المخرجات:
        list: قائمة من عناصر العامود
    """
    try:
        lock.acquire(True)
        cursor.execute(f"SELECT {column} FROM {table_name}")
        return [val for table in cursor.fetchall() for val in table]
    finally:
        lock.release()


def del_row(table_name:str, column:str, value:str):
    """ حذف صف من قاعدة البيانات
    المتغيرات:
        table_name (str): اسم الجدول الذي يوجد به العامود
        column (str): اسم العامود الذي يوجد به الصف
        value (str): القيمة التي تريد مسحها الموجودة في العامود
    """
    try:
        lock.acquire(True)
        cursor.execute(f"DELETE FROM {table_name} WHERE {column}='{value}'")
        coon.commit()
    finally:
        lock.release()

def update(table_name:str, column:str, new_value:str, where_column:str, where_value:str) -> None:
    """ تعديل صف في قاعدة البيانات
    المتغيرات:
        table_name (str): اسم الجدول.
        column (str): العمود الذي تريد تحديثه.
        new_value (str): القيمة الجديدة.
        where_column (str): where_value العمود الذي يوجد به.
        where_value (str): where_column القيمة الموجودة في.
    """
    try:
        lock.acquire(True)
        cursor.execute(f"UPDATE {table_name} SET '{column}'= '{new_value}' WHERE {where_column} = '{where_value}'")
        coon.commit()
    finally:
        lock.release()

def row(table_name:str, column:str, word:str, want='*', lst=True):
    """ جلب صف من قاعدة البيانات
    المتغيرات:
        table_name (str): اسم الجدول الذي يوجد به العمود
        column (str): اسم العمود اذي يوجد به الصف
        word (str): القيمة الموجود في العمود
        want (str, optional): word العمود الذي تريده من الصف الذي يوجد به العمود الي قيمته. Defaults to '*'.
        lst (bool, optional): اخراج المعطيات كلستة ام تيبل. Defaults to 'True'.
    المخرجات:
        [list,tuple,str,None]: قائمة بالنتائج او عنصر او لاشي اذ لم تكن هناك نتائج
    """
    try:
        lock.acquire(True)
        cursor.execute(f"SELECT {want} FROM {table_name} WHERE {column}='{word}'")
        if lst:
            result = list(map(
                        lambda val: str(val).replace('<br>', '\n'),
                            [val for t in cursor.fetchall() for val in t]
                            ))
        else:
            result = list(map(
                        lambda t: tuple(str(val) for val in t),
                            [t for t in cursor.fetchall()]
            ))
        if lst:
            if (len(result) == 0):
                return None
            elif (len(result) == 1):
                return result[0] if lst else result[0][0]
            else:
                pass # سوف يتم تنفيد اخخر سطر وارجاع النتائج كلها
        else:
            pass # سوف يتم تنفيد اخخر سطر وارجاع النتائج كلها
        return result
    finally:
        lock.release()

def get_latest_news():
    """ https://aosus.org/latest ارجاع اخر موضوع من 

    المخرجات:
        dict: تفاصيل اخر موضوع
    """
    return feedparser.parse(url).entries[0]

def get_last_id():
    """ ارجاع ايدي اخر موضوع تم ارساله

    المخرجات:
        str: ايدي اخر موضوع تم ارساله
    """
    with open('./last_id.txt','r') as f:
        last_id = f.read()
        return last_id

def add_id(news_id:str):
    """ './last_id.txt' اضافة ايدي اخر منشور هنا

    المتغيرات:
        news_id (str): ايدي الموضوع الجديد
    """
    with open('./last_id.txt', 'w') as f:
        f.write(news_id)

def get_is_admin(chat_id:int, user_id:int):
    """ ارجاع اذا كان الشخص ادمن في المحادثة

    المتغيرات:
        chat_id (int): ايدي الرسالة
        user_id (int): ايدي الشخص

    المخرجات:
        bool: user id admin in chat_id
    """
    # اذا كان ايدي المحادثة هو ايدي الشخص
    # هذا يعني ان المحادثة خاصة
    if chat_id == user_id:
        # ارجاع صحيح لان الشخص ادمن في محادثته
        return True
    else:
        # وظيفة الماب هي ارجاع ايديات مشرفين المحادثة
        return user_id in map(lambda user: user.user.id, bot.get_chat_administrators(chat_id))

def convert_status(chat_id:int, new_status:str, msg_id:int = None):
    """ حذف او اضافة العضو الى قاعدة البيانات

    المتغيرات:
        chat_id (int): ايدي الشخص المراد حذفه او اضافته
        new_status (str): الحالة الجديدة (on, off)
        msg_id (int, optional): ايدي الرسالة للرد عليها. Defaults to None.
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
    """ html تنظيف النص من تاقات ال

    المتغيرات:
        raw_html (str): html نص ال

    Returns:
        str: html نص نظيف لايحتوي على تاقات ال
    """
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def get_last_text():
    """ ارجاع نص اخر موضوع
    
    المخرجات:
        str: نص اخر موضوع
    """
    feed = get_latest_news()
    title = feed['title']
    author = feed['author']
    tag = feed['tags'][0]['term']
    summary = cleanhtml( feed['summary']).strip()
    split_summary = summary.split()
    # picture_name@4x5444×3062 64.6 KB مسح اسم الصور مثل هذا
    if '@' in split_summary[0] and '×' in split_summary[0]:
        summary = ' '.join(split_summary[3:])
    else:
        pass
    # جلب اخر كلمة كاملة
    summary = summary[:summary.strip('\n').find(' ', 55)]+'...'
    link = feed['link']
    text = f"من {author} \n\n <b><a href='{link}'>{title}</a></b> \n\n <code>{summary}</code> \n\nالقسم:{tag}"
    return text

def add_replies(key:str, value:str):
    """ اضافة رد الى قاعدة البيانات 

    المتغيرات:
        key (str): الامر لاستدعاء الرد
        value (str): الرد
    """
    key = str(key).replace('\n', '<br>')
    value = str(value).replace('\n', '<br>')
    key = key if key.startswith('/') else '/'+key
    insert('replies', (key, value))

def del_replies(word: str):
    """ مسح رد من قاعدة البيانات

    المتغيرات:
        word (str): الكلمة الذي تشير الى الرد
    """
    del_row("replies", "key", word)

def update_replies(word: str, new_val: str):
    """ تعديل على محتوى الرد

    المتغيرات:
        word (str): الكلمة التي تشير الى الرد المراد تعديله
        new_val (str): القيمة الجديدة للرد
    """
    update("replies", 'value', str(new_val).replace('\n', '<br>'), 'key', word)

def get_replies(word: str = None):
    """ جلب الرد من قاعدة البيانات

    المتغيرات:
        word (str): الكلمة التي تشير الى الرد
    """
    if word:
        return str(row("replies", 'key', word, 'value')).replace('<br>', '\n')
    else:
        return get_column("replies", 'key')

def replie(word: str, status: str, rep: str = None):
    """ دالة لادارة جدول الردور

    المتغيرات:
        word (str): الكلمة التي تشير الى الرد
        status (str): الحالة ["add", "del", "update"] or 1, 2, 3
        rep (str, optional): الرد الخاص بالكلمة. Defaults to None.

    Raises:
        ValueError: قيمة خاطئة للحالة
    """
    status_cases = ["add", "del", "update", 1, 2, 3]
    find_word = any(map(lambda w: w == word,
                            get_replies()))
    if status in status_cases:
        if status in ["add", 1]:
            if find_word:
                return False
            else:
                add_replies(word, rep)
                return True
        elif status in ["del", 2]:
            if not find_word:
                return False
            else:
                del_replies(word)
                return True
        else:
            if not find_word:
                return False
            else:
                update_replies(word, rep)
                return True
    else:
        raise ValueError("Invalid value, status must be {}".format(' or '.join(status_cases)))

def send_to_users():
    """
    ارسال الموضوع الى مستخدمين البوت
    """
    text = "موضوع جديد على مجتمع اسس "+get_last_text()
    for chat_id in get_column('chats', 'id'):
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
        # في حالة طرد او اغلاق البوت يتم ازالة العضو من قاعدة البيانات
        except Exception:
            convert_status(chat_id, new_status='off')

def main_loop():
    """
    يتم عمل حلقة لانهائية هنا واذ تم العثور على ايدي
    موضوع جديد يتم نشره
    """
    while True:
        # التحقق من وجود اعضاء في قاعدة البيانات
        if len(get_column('chats', 'id')) != 0:
            feed = get_latest_news()
            if feed.id != get_last_id():
                add_id(feed.id)
                send_to_users()
            else:
                pass
        else:
            pass
        time.sleep(sleep)

@bot.edited_message_handler(func= lambda msg: msg.text)
@bot.message_handler(content_types=["new_chat_members"])
@bot.message_handler(func=lambda msg: msg.text)
def message_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    msg_id = message.id
    is_private_chat = message.chat.type == "private"
    is_admin = get_is_admin(chat_id, user_id)
    is_superuser = user_id in super_users
    reply_text = message.reply_to_message.html_text if message.reply_to_message else None
    new_chat_member_id = message.new_chat_members[0].id if message.new_chat_members else None
    start_msg = "\nهذا البوت مخصص لارسال اخر المواضيع الخاصة بمجتمع اسس للبرامج الحرة والمفتوحة.\nلتفعيل الاشتراك: /on\nاذا اردت الغاء الاشتراك : /off\n\n\nhttps://aosus.org"
    add_replies_help = "لاضافة او تعديل رد\nيمكنك عمل ربلي على الرسالة بـ 'اضافة/تعديل رد-<اسم الرد>'\nمثال: اضافة/تعديل رد-تجربة\nلاضافة بدون ربلي 'اضافة/تعديل رد-<الرد>-<محتوى الرد>'\nمثال: اضافة رد-تجربة-هذا الرد للتجربة\n للمسح: مسح رد <اسم الرد>"
    if not new_chat_member_id:
        # ازالة معرف البوت من الامر ان وجد
        text = message.text.replace(bot_username, '').lower()
        # النص مقسم
        s_text = text.split('-')
        if s_text[0].strip() in ['اضافة رد', 'تعديل رد', 'مسح رد'] and is_superuser:
            status = ['اضافة رد', 'مسح رد', 'تعديل رد'].index(s_text[0].strip()) + 1
            if len(s_text) >= 2:
                if len(s_text) == 2 and not reply_text and status != 2: # او مسح رد
                    bot.reply_to(message, "يوجد خطأ لمعرفة طريقة الاستخدام ارسل \n /help")
                else:
                    word = s_text[1].strip()
                    rep = s_text[2].strip() if len(s_text) >= 3 else reply_text if reply_text else None
                    done = replie(word, status, rep)
                    if done:
                        bot.reply_to(message, "تم {} الرد بنجاج".format(
                            s_text[0].split()[0]
                        ))
                    else:
                        bot.reply_to(message, "هناك مشكلة، لايمكن {} {} {}".format(
                                s_text[0].split()[0], word,
                                    "موجود بالفعل" if status == 1 else "ليس موجود",
                                    ))
            else:
                bot.reply_to(message, "يوجد خطأ لمعرفة طريقة الاستخدام ارسل \n /help")
        if text.startswith(('/on', '/off')):
            if is_private_chat:
                # [1:] تعني ازالة الخط المائل او سلاش او علامة القسمة
                convert_status(chat_id, new_status=text[1:], msg_id=msg_id)
            else:
                if is_admin:
                    # [1:] تعني ازالة الخط المائل او سلاش او علامة القسمة
                    convert_status(chat_id, new_status=text[1:], msg_id=msg_id)
                else:
                    bot.reply_to(message, "يجب ان تكون ادمن لكي تقوم بهذا الامر")
        # امر البداية يعمل في المحادثات الخاصة فقط
        elif text.startswith('/start') and is_private_chat:
            text = f"اهلا بك <a href='tg://user?id={user_id}'>{first_name}</a>"+start_msg.format(name=first_name, id=user_id)
            bot.reply_to(message, text, parse_mode="HTML")
        #امر المساعدة يعمل في المحادثة العامة والخاصة
        elif text.startswith('/help'):
            text = "اهلا بك في خدمة ارسال اخر المواضيع الخاصة بمجتمع اسس للبرامج الحرة والمفتوحة..\nللاشتراك ارسل: /on\nولالغاء الاشتراك ارسل: /off\nلرؤية الردود: الردود\n\n\n"
            if is_superuser:
                text = text+add_replies_help
            else:
                text = text+"https://aosus.org"
            bot.reply_to(message, text)
        #امر اخر موضوع يعمل في المحادثة العامة والخاصة
        elif text.startswith('/last_topic'):
            if is_admin:
                bot.reply_to(message, get_last_text(), parse_mode="HTML")
            else:
                bot.reply_to(message, "يجب ان تكون ادمن لكي تقوم بهذا الامر")
        else:
            if text == 'الردود':
                if len(get_replies()) != 0:
                    text = telebot.util.smart_split('\n'.join(get_replies()), 3000)
                    for t in text:
                        bot.reply_to(message,t)
                else:
                    bot.reply_to(message, "لايوجد ردود في البوت")
            elif text in get_replies():
                bot.reply_to(message, get_replies(text), parse_mode="HTML")
    else:
        # اذا كان اخر عضو هو البوت
        if new_chat_member_id == bot_id:
            text = f"شكرا <a href='tg://user?id={user_id}'>{first_name}</a> لاضافتي الى المحادثة 🌹\n{start_msg.format(name=first_name, id=user_id)}"
            bot.send_message(chat_id, text, parse_mode="HTML")
        else:
            pass

# تشغيل البوت
threading.Thread(target=main_loop).start()
while True:
    print(f"Start {bot.get_me().first_name}")
    try:
        bot.polling(none_stop=True, interval=0, timeout=0)
    except Exception as err:
        print(err)
        time.sleep(10)
