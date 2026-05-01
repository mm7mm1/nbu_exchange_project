#імпорт бібліотек та налаштування змінних середовища
import os
import csv
import time
import requests
import psycopg2
from datetime import date, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

START_DATE  = date(2026, 1, 1)
CURRENCIES  = ["USD", "EUR", "GBP"]
API_URL = "https://bank.gov.ua/NBU_Exchange/exchange_site"
MAX_RETRIES = 3


#підключення до бази даних через докер, беручи паролі з файла .env
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


#створення таблиці у контейнері 
def init_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                exchange_date  DATE       NOT NULL,
                currency_code  TEXT       NOT NULL,
                currency_name  TEXT       NOT NULL,
                exchange_rate  FLOAT      NOT NULL,
                updated_at     TIMESTAMP  NOT NULL DEFAULT now(),
                PRIMARY KEY (exchange_date, currency_code)
            )
        """)
    conn.commit()


#отримання даних з API 
def get_rates(currency, from_date, to_date):
    params = {
        "valcode":        currency,
        "start":          from_date.strftime("%Y%m%d"),
        "end":            to_date.strftime("%Y%m%d"),
        "sort":           "exchangedate",
        "order":          "asc",
        "json":           "",
    }
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(API_URL, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            if not data:
                print(f"{currency}: порожня відповідь, спроба {attempt}/{MAX_RETRIES}")
                time.sleep(2 * attempt)
                continue

            return data

        except Exception as e:
            print(f"{currency}: помилка {e}, спроба {attempt}/{MAX_RETRIES}")
            time.sleep(2 * attempt)

    print(f"{currency}: всі спроби вичерпані, пропускаємо")
    return []

#перевірка пропущених дат
def get_existing_dates(conn, currency):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT exchange_date FROM exchange_rates WHERE currency_code = %s",
            (currency,)
        )
        return {row[0] for row in cur.fetchall()}


def find_missing_dates(existing_dates, today):
    all_dates = set()
    d = START_DATE
    while d <= today:
        all_dates.add(d)
        d += timedelta(days=1)
    return sorted(all_dates - existing_dates)

#оновлення або завантаження запису
def upsert(conn, exchange_date, currency_code, currency_name, exchange_rate):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO exchange_rates
                (exchange_date, currency_code, currency_name, exchange_rate, updated_at)
            VALUES (%s, %s, %s, %s, now())
            ON CONFLICT (exchange_date, currency_code) DO UPDATE SET
                exchange_rate = EXCLUDED.exchange_rate,
                updated_at    = now()
        """, (exchange_date, currency_code, currency_name, exchange_rate))

#завантаженя валюти
def load_currency(conn, currency, today):
    existing = get_existing_dates(conn, currency)
    missing  = find_missing_dates(existing, today)

    if not missing:
        print(f"{currency}: всі дані є в БД")
        return

    fetch_from = min(missing)
    fetch_to   = max(missing)
    print(f"{currency}: завантажую {fetch_from} → {fetch_to}")

    records = get_rates(currency, fetch_from, fetch_to)

    for item in records:
        upsert(
            conn,
            datetime.strptime(item["exchangedate"], "%d.%m.%Y").date(),
            item["cc"],
            item["txt"],
            float(item["rate"]),
        )

    conn.commit()
    print(f"{currency}: записано {len(records)} рядків")


def load_uah(conn, today):
    existing = get_existing_dates(conn, "UAH")
    missing  = find_missing_dates(existing, today)

    for d in missing:
        upsert(conn, d, "UAH", "Українська гривня", 1.0)

    conn.commit()
    print(f"UAH: записано {len(missing)} рядків")

#експорт у csv
def export_csv(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT exchange_date, currency_code, currency_name,
       ROUND(exchange_rate::numeric, 2) AS exchange_rate, updated_at
        FROM   exchange_rates
        ORDER  BY exchange_date, currency_code      
        """)
        rows = cur.fetchall()

    with open("exchange_rates.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["exchange_date", "currency_code", "currency_name",
                    "exchange_rate", "updated_at"])
        w.writerows(rows)

    print(f"CSV збережено: {len(rows)} рядків")


#виклик функцій
def main():
    today = date.today()
    conn  = get_conn()

    try:
        init_db(conn)

        for currency in CURRENCIES:
            load_currency(conn, currency, today)

        load_uah(conn, today)
        export_csv(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()