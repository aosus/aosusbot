import sqlite3
from config import TOKEN

# Set names for tables and their respective columns
tablesName = {
        'chats':['id'],
            'replies': ['key', 'value'],
            }
def make():
    """
    دالة انشاء قاعدة البيانات
    """
    # التحقق من انه تم وضع التوكن الخاص بالبوت ام لا
    if TOKEN == "":
        raise Exception("config يجب عليك وضع التوكن الخاص بالبوت في ملف")
    else:
        coon = sqlite3.connect('db.sqlite3')
        cursor = coon.cursor()
        for table in tablesName:
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{table}'(
                                {','.join(tablesName.get(table))}
                            )""")
            coon.commit()

if __name__ == '__main__':
    make()
    print("Database created successfully.")