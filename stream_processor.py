from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
import json

KAFKA_BROKER = 'kafka:9092'
CDC_TOPIC = 'cdc.mydatabase.transactions'
GROUP_ID = 'enrichment_group'
MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "mydatabase"
USERS_COLLECTION = "users"
SINK_COLLECTION = "enriched_transactions"

def process_stream():
    # Khởi tạo SparkSession
    spark = SparkSession.builder \
        .appName("DataEnrichment") \
        .config("spark.mongodb.input.uri", f"{MONGO_URI}{DB_NAME}.{USERS_COLLECTION}") \
        .config("spark.mongodb.output.uri", f"{MONGO_URI}{DB_NAME}.{SINK_COLLECTION}") \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1,org.apache.spark:spark-streaming-kafka-0-10_2.12:3.4.0") \
        .getOrCreate()

    # Khởi tạo StreamingContext với batch interval 5 giây
    ssc = StreamingContext(spark.sparkContext, 5)

    # Định nghĩa schema cho dữ liệu giao dịch
    transaction_schema = StructType([
        StructField("_id", StructType([StructField("$oid", StringType())])),
        StructField("user_id", IntegerType()),
        StructField("amount", DoubleType()),
        StructField("timestamp", StructType([StructField("$date", TimestampType())]))
    ])

    # Đọc dữ liệu từ Kafka sử dụng DStream
    kafka_stream = ssc.textFileStream(f"kafka://{KAFKA_BROKER}/{CDC_TOPIC}")

    # Parse JSON từ Kafka và lọc thao tác insert ('c')
    def process_rdd(rdd):
        if rdd.isEmpty():
            return

        # Chuyển RDD thành DataFrame
        df = spark.read.json(rdd)
        if 'op' not in df.columns or 'after' not in df.columns:
            print("Không tìm thấy các trường 'op' hoặc 'after' trong dữ liệu Kafka")
            return

        # Lọc các thao tác insert ('c')
        transaction_df = df.filter(df.op == 'c') \
            .select(spark.read.json(df.after, schema=transaction_schema).alias('data')) \
            .select(
                col("data._id.$oid").alias("transaction_id"),
                col("data.user_id"),
                col("data.amount"),
                col("data.timestamp.$date").alias("timestamp")
            )

        # Đọc dữ liệu người dùng từ MongoDB và đăng ký làm bảng tạm
        users_df = spark.read \
            .format("mongo") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{USERS_COLLECTION}") \
            .load() \
            .select("user_id", "name", "city")
        users_df.createOrReplaceTempView("users")

        # Đăng ký transaction_df làm bảng tạm
        transaction_df.createOrReplaceTempView("transactions")

        # Sử dụng Spark SQL để thực hiện phép join
        enriched_df = spark.sql("""
            SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, u.name AS user_name, u.city AS user_city
            FROM transactions t
            LEFT JOIN users u ON t.user_id = u.user_id
        """)

        # Ghi dữ liệu làm giàu vào MongoDB
        enriched_df.write \
            .format("mongo") \
            .mode("append") \
            .option("uri", f"{MONGO_URI}{DB_NAME}.{SINK_COLLECTION}") \
            .save()

        print(f"Đã làm giàu và lưu {enriched_df.count()} bản ghi vào {DB_NAME}.{SINK_COLLECTION}")

    # Áp dụng xử lý cho mỗi RDD trong DStream
    kafka_stream.foreachRDD(process_rdd)

    # Bắt đầu stream
    ssc.start()
    print(f"Đã bắt đầu stream làm giàu dữ liệu vào {DB_NAME}.{SINK_COLLECTION}")
    ssc.awaitTermination()

    spark.stop()

if __name__ == "__main__":
    process_stream()