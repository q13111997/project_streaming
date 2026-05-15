import psycopg2
from psycopg2.extras import execute_values
from utils.config_parser import load_config

def connect_db():

    postgres_config = load_config()

    return psycopg2.connect(
        host=postgres_config['POSTGRES']['host'],
        port=postgres_config['POSTGRES']['port'],
        database=postgres_config['POSTGRES']['database'],
        user=postgres_config['POSTGRES']['user'],
        password=postgres_config['POSTGRES']['password'],
        connect_timeout=5
    )

def insert_db(cursor, table_name, columns, data, conflict_col):
    if not data:
        return
    
    placeholders = ", ".join(["%s"] * len(columns))
    columns_str = ", ".join(columns)
    
    query = f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES %s 
        ON CONFLICT ({conflict_col}) DO NOTHING
    """
    
    execute_values(cursor, query, data)

def process_partition(partition_iterator):
    print("Worker: Bắt đầu đọc dữ liệu từ Partition...")
    dim_product_set = set()
    dim_store_set = set()
    dim_location_set = set()
    dim_device_set = set()
    dim_referrer_set = set()
    fact_data_list = []
    has_data = False

    for row in partition_iterator:
        has_data = True
        r = row.asDict()

        if r.get('product_id'):
            dim_product_set.add((r['product_id'],))
            
        if r.get('store_id'):
            dim_store_set.add((r['store_id'], f"Store {r['store_id']}", r['domain']))
            
        if r.get('location_key'):
            dim_location_set.add((r['location_key'], r.get('city_name'), r.get('region_name'), r.get('country_name')))
            
        if r.get('device_key'):
            dim_device_set.add((r['device_key'], r.get('os'), r.get('browser'), r.get('resolution')))
            
        if r.get('referrer_key'):
            dim_referrer_set.add((r['referrer_key'], r.get('referrer_domain'), r.get('traffic_type')))

        fact_data_list.append((
            r['log_id'],
            r.get('date_key'), 
            r.get('time_key'), 
            r.get('product_id'), 
            r.get('store_id'), 
            r.get('location_key'), 
            r.get('device_key'), 
            r.get('referrer_key')
        ))

    if not has_data:
        print("Worker: Partition trống, bỏ qua!")
        return

    conn = None
    
    try:
        print(f"Worker: Đang cố gắng kết nối tới Database...")

        conn = connect_db()
        cursor = conn.cursor()

        print("Worker: Kết nối Database thành công. Bắt đầu insert dữ liệu...")

        insert_db(cursor, "dim_product", ["product_id"], list(dim_product_set), "product_id")
        insert_db(cursor, "dim_store", ["store_id", "store_name", "domain"], list(dim_store_set), "store_id")
        insert_db(cursor, "dim_location", ["location_key", "city_name", "region_name", "country_name"], list(dim_location_set), "location_key")
        insert_db(cursor, "dim_device", ["device_key", "os", "browser", "resolution"], list(dim_device_set), "device_key")
        insert_db(cursor, "dim_referrer", ["referrer_key", "referrer_domain", "traffic_type"], list(dim_referrer_set), "referrer_key")

        insert_db(
            cursor, 
            "fact_logs",
            ["log_id", "date_key", "time_key", "product_id", "store_id", "location_key", "device_key", "referrer_key"],
            fact_data_list, 
            "log_id"
        )
        
        conn.commit()
        cursor.close()

        print(f"Worker đã insert thành công {len(fact_data_list)} bản ghi vào Database.")

    except Exception as e:
        print(f"Lỗi khi kết nối hoặc insert vào Database: {e}")

        if conn:
            conn.rollback()
        raise e
    
    finally:
        if conn:
            conn.close()

def process_micro_batch(batch_df, batch_id):
    print(f"Bắt đầu xử lý Micro-batch {batch_id} với {batch_df.count()} bản ghi...")
    batch_df.foreachPartition(process_partition)
    print(f"Hoàn tất xử lý Micro-batch {batch_id}.")