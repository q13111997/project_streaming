import psycopg2
from src.utils.config_parser import load_config

DDL_SQL = """
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key INT PRIMARY KEY,
        full_date DATE NOT NULL,
        day INT,
        month INT,
        year INT
    );

    CREATE TABLE IF NOT EXISTS dim_time (
        time_key INT PRIMARY KEY,
        hour INT,
        minute INT
    );

    CREATE TABLE IF NOT EXISTS dim_product (
        product_id VARCHAR(500) PRIMARY KEY
    );

    CREATE TABLE IF NOT EXISTS dim_store (
        store_id VARCHAR(500) PRIMARY KEY,
        store_name VARCHAR(500) NOT NULL,
        domain VARCHAR(255) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS dim_location (
        location_key VARCHAR(500) PRIMARY KEY,
        city_name VARCHAR(500),
        region_name VARCHAR(500),
        country_name VARCHAR(500)
    );

    CREATE TABLE IF NOT EXISTS dim_device (
        device_key VARCHAR(255) PRIMARY KEY,
        os VARCHAR(100),
        browser VARCHAR(100),
        resolution VARCHAR(50)
    );

    CREATE TABLE IF NOT EXISTS dim_referrer (
        referrer_key VARCHAR(255) PRIMARY KEY,
        referrer_domain VARCHAR(500),
        traffic_type VARCHAR(500)
    );

    CREATE TABLE IF NOT EXISTS fact_logs (
        log_id VARCHAR(500) PRIMARY KEY,
        date_key INT REFERENCES dim_date(date_key),
        time_key INT REFERENCES dim_time(time_key),
        product_id VARCHAR(500) REFERENCES dim_product(product_id),
        store_id VARCHAR(500) REFERENCES dim_store(store_id),
        location_key VARCHAR(500) REFERENCES dim_location(location_key),
        device_key VARCHAR(255) REFERENCES dim_device(device_key),
        referrer_key VARCHAR(255) REFERENCES dim_referrer(referrer_key)
);
"""

INIT_DATA_SQL = """
    INSERT INTO dim_date (
        date_key,
        full_date,
        day,
        month,
        year
    )
    SELECT
        TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
        d AS full_date,
        EXTRACT(DAY FROM d)::INT AS day,
        EXTRACT(MONTH FROM d)::INT AS month,
        EXTRACT(YEAR FROM d)::INT AS year
    FROM generate_series(
        DATE '2000-01-01',
        DATE '2030-12-31',
        INTERVAL '1 day'
    ) AS d
    ON CONFLICT (date_key)
    DO NOTHING;

    INSERT INTO dim_time (
        time_key,
        hour,
        minute
    )
    SELECT
        (h * 100 + m) AS time_key,
        h AS hour,
        m AS minute
    FROM generate_series(0, 23) AS h
    CROSS JOIN generate_series(0, 59) AS m
    ON CONFLICT (time_key)
    DO NOTHING;
"""

def setup_database():
    print("Đang kết nối tới Database...")

    conn = None

    try:
        postgres_config = load_config()
        conn = psycopg2.connect(
            host=postgres_config['POSTGRES']['host'],
            port=postgres_config['POSTGRES']['port'],
            database=postgres_config['POSTGRES']['database'],
            user=postgres_config['POSTGRES']['user'],
            password=postgres_config['POSTGRES']['password'],
            connect_timeout=5
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Bắt đầu tạo bảng fact, dim và init data cho bảng dim_date, dim_time!")
        cursor.execute(DDL_SQL)
        cursor.execute(INIT_DATA_SQL)
        print("Đã tạo bảng fact, dim và init data cho bảng dim_date, dim_time thành công!")
        
    except Exception as e:
        print(f"Lỗi kết nối Database hoặc chạy SQL: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()