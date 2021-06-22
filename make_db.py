import sqlite3
from config import TOKEN

# Set names for tables and their respective columns
tablesName = {
        'chats':['id']
            }
def main():
    """
    Create database
    """
    if TOKEN == "":
        return False
    else:
        coon = sqlite3.connect('db.sqlite3')
        cursor = coon.cursor()
        for table, columns in tablesName.items():
            cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{table}'(
                            {columns[0]}
                            )""")
            coon.commit()
    return True

if __name__ == '__main__':
    if main():
        print("Database created successfully.")
    else:
        print("You must fill the variables in 'config.py'")