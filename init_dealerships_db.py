import sqlite3

def init_dealerships_db():
    conn = sqlite3.connect('dealerships.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS dealerships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            brand TEXT,
            website_url TEXT UNIQUE,
            phone TEXT,
            zip_code TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("[DB] dealerships.db initialized.")

if __name__ == "__main__":
    init_dealerships_db()
