import urllib.parse
from pyspark import SparkFiles
import IP2Location
from user_agents import parse
from pyspark.sql.types import StringType, StructType, StructField
from pyspark.sql.functions import (
    concat, lit, udf, col, from_json, md5, concat_ws, to_timestamp, 
    date_format, year, month, dayofmonth, hour, minute
)

def parse_json(df):
    json_schema = StructType([
        StructField("id", StringType(), True), 
        StructField("ip", StringType(), True),
        StructField("user_agent", StringType(), True),
        StructField("resolution", StringType(), True),
        StructField("store_id", StringType(), True),
        StructField("local_time", StringType(), True),
        StructField("current_url", StringType(), True),
        StructField("referrer_url", StringType(), True),
        StructField("collection", StringType(), True),
        StructField("product_id", StringType(), True)
    ])

    df_parsed = df.selectExpr("CAST(value AS STRING) as json_string") \
        .select(from_json(col("json_string"), json_schema).alias("data")) \
        .select("data.*")
    
    return df_parsed

def parse_device_info(ua_str):
    if not ua_str:
        return ("Unknown", "Unknown")
    try:
        ua = parse(ua_str)
        return (ua.os.family, ua.browser.family)
    except Exception:
        return ("Unknown", "Unknown")
    
device_info_schema = StructType([
    StructField("os", StringType(), True),
    StructField("browser", StringType(), True)
])

parse_ua_udf = udf(parse_device_info, device_info_schema)

def parse_referrer(current_url, referrer_url):
    if current_url:
        parsed_current = urllib.parse.urlparse(current_url)
        domain = parsed_current.netloc
    referrer_domain = "Direct"
    traffic_type = "Direct"
    if referrer_url:
        parsed_referrer = urllib.parse.urlparse(referrer_url)
        referrer_domain = parsed_referrer.netloc
        if referrer_domain != domain:
            traffic_type = "Referral"
        elif "glamira" in referrer_domain:
            traffic_type = "Internal"
        else:
            traffic_type = "Direct"
    return (domain, referrer_domain, traffic_type)

referrer_schema = StructType([
    StructField("domain", StringType(), True),
    StructField("referrer_domain", StringType(), True),
    StructField("traffic_type", StringType(), True)
])

parse_referrer_udf = udf(parse_referrer, referrer_schema)

def parse_ip_location(ip):
    if not ip:
        return ("Unknown", "Unknown", "Unknown")
    try:
        bin_path = SparkFiles.get("IP-COUNTRY-REGION-CITY.BIN")
        ip2location = IP2Location.IP2Location(bin_path)
        response = ip2location.get_all(ip)
        country = response.country_long if response.country_long != "-" else "Unknown"
        region = response.region if response.region != "-" else "Unknown"
        city = response.city if response.city != "-" else "Unknown"
        return (country, region, city)
    except Exception:
        return ("Unknown", "Unknown", "Unknown")

ip_location_schema = StructType([
    StructField("country_name", StringType(), True),
    StructField("region_name", StringType(), True),
    StructField("city_name", StringType(), True)
])

parse_ip_location_udf = udf(parse_ip_location, ip_location_schema)

def transform_raw_df(df):
    df_filtered = df.filter(col("collection") == "view_product_detail")
    df_transformed = df_filtered.withColumnRenamed("id", "log_id") \
                                .withColumn("ua_struct", parse_ua_udf(col("user_agent"))) \
                                .withColumn("os", col("ua_struct.os")) \
                                .withColumn("browser", col("ua_struct.browser")) \
                                .withColumn("traffic_info", parse_referrer_udf(col("current_url"), col("referrer_url"))) \
                                .withColumn("domain", col("traffic_info.domain")) \
                                .withColumn("referrer_domain", col("traffic_info.referrer_domain")) \
                                .withColumn("traffic_type", col("traffic_info.traffic_type")) \
                                .withColumn("location_info", parse_ip_location_udf(col("ip"))) \
                                .withColumn("country_name", col("location_info.country_name")) \
                                .withColumn("region_name", col("location_info.region_name")) \
                                .withColumn("city_name", col("location_info.city_name")) \
                                .withColumn("timestamp_obj", to_timestamp(col("local_time"), "yyyy-MM-dd HH:mm:ss")) \
                                .withColumn("date_key", date_format(col("timestamp_obj"), "yyyyMMdd").cast("int")) \
                                .withColumn("full_date", col("timestamp_obj").cast("date")) \
                                .withColumn("day", dayofmonth(col("timestamp_obj"))) \
                                .withColumn("month", month(col("timestamp_obj"))) \
                                .withColumn("year", year(col("timestamp_obj"))) \
                                .withColumn("time_key", date_format(col("timestamp_obj"), "HHmm").cast("int")) \
                                .withColumn("hour", hour(col("timestamp_obj"))) \
                                .withColumn("minute", minute(col("timestamp_obj"))) \
                                .withColumn("device_key", md5(concat_ws("#", col("os"), col("browser"), col("resolution")))) \
                                .withColumn("location_key", md5(concat_ws("#", col("city_name"), col("region_name"), col("country_name")))) \
                                .withColumn("referrer_key", md5(concat_ws("#", col("referrer_domain"), col("traffic_type"))))
    return df_transformed