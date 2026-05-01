-- курс до долара в кінці кожного місяця
WITH month_last_days AS (
    SELECT
        DATE_TRUNC('month', exchange_date) AS month_start,
        MAX(exchange_date)                 AS last_date
    FROM   exchange_rates
    WHERE  currency_code = 'USD'
    GROUP  BY DATE_TRUNC('month', exchange_date)
),
usd_rates AS (
    SELECT mld.last_date, er.exchange_rate AS usd_rate
    FROM   month_last_days mld
    JOIN   exchange_rates er
           ON  er.exchange_date = mld.last_date
           AND er.currency_code = 'USD'
)
SELECT
    u.last_date   AS last_month_date,
    er.currency_code,
    CASE er.currency_code
        WHEN 'USD' THEN 1.0
        ELSE ROUND((er.exchange_rate / u.usd_rate)::numeric, 6)
    END           AS exchange_rate
FROM   usd_rates u
JOIN   exchange_rates er ON er.exchange_date = u.last_date
ORDER  BY u.last_date, er.currency_code;