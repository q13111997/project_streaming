import os
from pyspark.sql import SparkSession    
from utils.config_parser import load_config
from utils.transform_function import parse_json, transform_raw_df
from utils.db_process import process_micro_batch

def main():

    print("Bắt đầu ứng dụng Spark Streaming!")

    config = load_config()
    
    spark = SparkSession.builder \
        .appName("SparkStreamingApp") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.postgresql:postgresql:42.6.0") \
        .config("spark.executorEnv.PYTHONPATH", "/workspace/src") \
        .config("spark.yarn.appMasterEnv.PYTHONPATH", "/workspace/src") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")

    bin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/IP-COUNTRY-REGION-CITY.BIN'))

    spark.sparkContext.addFile(bin_path)

    print("Bắt đầu đọc dữ liệu từ Kafka!")

    reset_marker = "/tmp/reset_kafka_marker"
    
    if os.path.exists(reset_marker):

        print("Phát hiện lệnh reset-offset từ hệ thống: Ép buộc đọc dữ liệu Kafka từ đầu ('earliest')!")
        starting_offsets_value = "earliest"
        
        try:
            os.remove(reset_marker)
            print("Đã dọn dẹp file marker trạng thái.")
        except Exception as e:
            print(f"Không thể xóa file marker: {e}")
    else:
        starting_offsets_value = config['KAFKA']['starting_offsets']
    
    df_raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", config['KAFKA']['bootstrap_servers']) \
        .option("subscribe", config['KAFKA']['topic']) \
        .option("startingOffsets", starting_offsets_value) \
        .option("kafka.security.protocol", config['KAFKA']['security_protocol']) \
        .option("kafka.sasl.mechanism", config['KAFKA']['sasl_mechanism']) \
        .option("kafka.sasl.jaas.config", config['KAFKA']['sasl_jaas_config']) \
        .load() 
    
    df_parsed = parse_json(df_raw)
    
    print("Bắt đầu clean và enrich raw data!")
    
    df_transformed = transform_raw_df(df_parsed)
    
    print("Bắt đầu ghi dữ liệu xuống db!")

    query = df_transformed.writeStream \
        .outputMode("append") \
        .foreachBatch(process_micro_batch) \
        .trigger(processingTime=config['SPARK']['trigger_processing_time']) \
        .option("checkpointLocation", config['SPARK']['checkpoint_dir']) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()