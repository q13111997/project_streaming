import configparser
import os
from dotenv import load_dotenv

def load_config():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
    else:
        print("Cảnh báo: Không tìm thấy file cấu hình .env")

    config_path = os.path.join(project_root, 'config', 'spark.conf')
    config = configparser.ConfigParser()
    config.read(config_path)

    kafka_pwd = os.getenv("KAFKA_PASSWORD")
    kafka_user = os.getenv("KAFKA_USER")
    pg_pwd = os.getenv("POSTGRES_PASSWORD")
    pg_user = os.getenv("POSTGRES_USER")

    jaas_template = config['KAFKA']['sasl_jaas_config']

    config['KAFKA']['sasl_jaas_config'] = jaas_template.replace("${KAFKA_PASSWORD}", kafka_pwd).replace("${KAFKA_USER}", kafka_user)
    config['POSTGRES']['password'] = pg_pwd
    config['POSTGRES']['user'] = pg_user

    print(f"Thiết lập xong cấu hình kết nối Kafka, Postgres!")

    return config
