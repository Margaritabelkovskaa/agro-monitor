import sqlite3
import hashlib

DB_NAME = "agro_monitor.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, fio TEXT, login TEXT UNIQUE, password_hash TEXT, role TEXT, email TEXT, status TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS plots (id TEXT PRIMARY KEY, name TEXT, area REAL)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS sensors (id TEXT PRIMARY KEY, type TEXT, plot_id TEXT, status TEXT, last_reading TEXT)")
    cursor.execute("""CREATE TABLE IF NOT EXISTS cultures (
            id TEXT PRIMARY KEY, name TEXT, sort TEXT, plot_id TEXT, planting_date TEXT, 
            growth_phase TEXT, state_rating TEXT, soil_moisture TEXT, soil_moisture_rating TEXT, 
            temperature TEXT, temperature_rating TEXT, light TEXT, light_rating TEXT)""")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS norms (id INTEGER PRIMARY KEY AUTOINCREMENT, culture_name TEXT, growth_phase TEXT, moisture_min INT, moisture_max INT, temp_min INT, temp_max INT, UNIQUE(culture_name, growth_phase))")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS observations (id TEXT PRIMARY KEY, culture_id TEXT, datetime TEXT, type TEXT, author TEXT, record TEXT)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS problems (id TEXT PRIMARY KEY, culture_id TEXT, description TEXT, status TEXT, detected_at TEXT)")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS notifications (id TEXT PRIMARY KEY, culture_id TEXT, time TEXT, message TEXT, importance TEXT, is_read INTEGER DEFAULT 0)")

    conn.commit()

    if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        _seed_data(conn)
    conn.close()


def _seed_data(conn):
    cur = conn.cursor()
    pwd = hashlib.sha256("123".encode("utf-8")).hexdigest()

    cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", [
        ("u1", "Иванов Андрей", "ivanov", pwd, "Агроном", "ivanov@farm.example", "Активен"),
        ("u2", "Петров Сергей", "petrov", pwd, "РаботникПоля", "petrov@farm.example", "Активен"),
        ("u3", "Сидоров Павел", "sidorov", pwd, "РаботникПоля", "sidorov@farm.example", "Заблокирован"),
        ("u4", "Смирнова Ольга", "smirnova", pwd, "Руководитель", "smirnova@farm.example", "Активен"),
    ])

    cur.executemany("INSERT INTO plots VALUES (?, ?, ?)", [
        ("p1", "Поле №1", 10.0), ("p2", "Поле №2", 15.0), ("p5", "Поле №5", 20.0), ("p7", "Поле №7", 12.0)
    ])

    cur.executemany("INSERT INTO sensors VALUES (?, ?, ?, ?, ?)", [
        ("Д-021", "Влажность почвы", "p5", "Активен", "18 %"),
        ("Д-022", "Температура", "p5", "Активен", "+21 °C"),
        ("Д-041", "Влажность почвы", "p2", "Активен", "25 %"),
        ("Д-051", "Влажность почвы", "p7", "Активен", "10 %"),
        ("Д-061", "Влажность почвы", "p1", "Активен", "30 %"),
        ("Д-031", "Влажность почвы", None, "Не активен", "17 %"),
    ])

    cur.executemany(
        "INSERT INTO norms (culture_name, growth_phase, moisture_min, moisture_max, temp_min, temp_max) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Пшеница", "Всходы", 30, 60, 15, 25), ("Пшеница", "Вегетация", 25, 55, 18, 27),
            ("Пшеница", "Цветение", 25, 55, 20, 28), ("Пшеница", "Созревание", 20, 50, 20, 30),
            ("Ячмень", "Всходы", 30, 60, 15, 25), ("Ячмень", "Вегетация", 25, 55, 18, 27),
            ("Ячмень", "Цветение", 25, 55, 20, 28), ("Ячмень", "Созревание", 20, 50, 20, 30),
            ("Кукуруза", "Всходы", 30, 60, 15, 25), ("Кукуруза", "Вегетация", 25, 55, 18, 27),
            ("Кукуруза", "Цветение", 25, 55, 20, 28), ("Кукуруза", "Созревание", 20, 50, 20, 30),
            ("Подсолнечник", "Всходы", 30, 60, 15, 25), ("Подсолнечник", "Вегетация", 25, 55, 18, 27),
            ("Подсолнечник", "Цветение", 25, 55, 20, 28), ("Подсолнечник", "Созревание", 20, 50, 20, 30),
            ("Овес", "Всходы", 25, 55, 15, 25), ("Овес", "Вегетация", 20, 50, 18, 27),
            ("Овес", "Цветение", 20, 50, 20, 28), ("Овес", "Созревание", 15, 45, 20, 30),
        ])

    cur.executemany("INSERT INTO cultures VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        ("c1", "Пшеница", "Безостая 1", "p5", "2026-04-12", "Созревание", "Удовлетворительное", "18 %", "Низкая",
         "+21 °C", "Нормальная", "54 000 люкс", "Нормальная"),
        ("c2", "Ячмень", "Ковалер", "p2", "2026-05-01", "Цветение", "Требует внимания", "25 %", "Нормальная", "+24 °C",
         "Высокая", "60 000 люкс", "Нормальная"),
        ("c3", "Кукуруза", "Росс 199", "p7", "2026-05-10", "Вегетация", "Критическое", "10 %", "Критическая", "+28 °C",
         "Высокая", "45 000 люкс", "Низкая"),
        ("c4", "Подсолнечник", "Ясон", "p1", "2026-06-01", "Всходы", "Удовлетворительное", "30 %", "Нормальная",
         "+20 °C", "Нормальная", "50 000 люкс", "Нормальная"),
    ])

    conn.commit()