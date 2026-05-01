# NBU Exchange Rate ETL
Скрипт завантажує офіційні курси валют НБУ (USD, EUR, GBP, UAH) з 01.01.2026 і зберігає їх у контейнері PostgreSQL.

## Структура проєкту
```text
.
├── docs/                     # Візуалізація та технічні підтвердження
│   ├── connecting_to_container.png    # Зв'язок з PostgreSQL (крок 1)
│   ├── connectring_to_container_2.png # Зв'язок з PostgreSQL (крок 2)
│   ├── currency_exchange_rates_dashboard.png  # Загальний вигляд дашборду
│   └── currency_exchange_rates_dashboard2.png # Робочий стан візуалізації
├── scripts/                  # Скрипти
│   ├── nbu_exchange.py       # Python-скрипт
│   └── monthly_report.sql    # SQL-запит
├── .env.example              # Шаблон конфігурації середовища
├── .gitignore                # Налаштування виключень Git
├── docker-compose.yml        # Оркестрація контейнера PostgreSQL
├── exchange_rates.csv        # Результат останнього успішного вивантаження
├── LICENSE                   # MIT Ліцензія
├── requirements.txt          # Перелік Python бібліотек
└── README.md                 # Головна документація проєкту
```

## Візуалізація
Для візуалізації я завантажила готову таблицю у Databricks, оскільки мені зручно працювати з їхніми дашбордами. Там створила дашборд
![DashBoard](docs/currency_exchange_rates_dashboard.png)

* Також посилання на дашборд 
[DataBricks дашборд](https://dbc-a003dee5-a87a.cloud.databricks.com/dashboardsv3/01f1455da5d91a85b93eeeabcc9b5936/published?o=7474655757405789)

## Вимоги
- Python 3.11+
- Docker

## Запуск проекту
1. docker-compose up -d #щоб підняти контейнер
2. python nbu_exchange.py #в терміналі 
3. Створюється файл з таблицею
4. Підключення до контейнеру та таблиці через SQL Tools 
5. SQL запит до таблиці
АБО
4. docker exec -i nbu_laba_postgres psql -U admin -d nbu_db < monthly_report.sql #в терміналі (виведе 20 рядків результату SQL запиту)

## Опис скрипту
Скрипт:
- Завантажує курси USD, EUR, GBP з API НБУ
- Генерує курс UAH = 1.0
- Перевіряє пропущені дати і дозавантажує їх
- Зберігає дані у PostgreSQL
- Експортує результат у `exchange_rates.csv`


## License
This project is licensed under the MIT License. You are free to use, modify, and share this project with proper attribution.