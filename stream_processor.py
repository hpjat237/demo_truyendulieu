from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import col
from pymongo import MongoClient
from pyspark.sql import SparkSession

from datetime import datetime
import pytz
import queue
import threading
import time
import collections

MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "mydatabase"
TRANSACTIONS_COLLECTION = "transactions"
USERS_COLLECTION = "users"
SINK_COLLECTION = "enriched_transactions"

client = MongoClient("mongodb://mongodb:27017/")
db = client["mydatabase"]
def process_stream():
    # Khởi tạo SparkSession
    spark = (SparkSession.builder
        .appName("DataEnrichment")
        .config("spark.mongodb.read.connection.uri", "mongodb://mongo:27017/mydatabase.users")
        .config("spark.mongodb.write.connection.uri", "mongodb://mongo:27017/mydatabase.enriched_transactions")
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.1.1")
        .getOrCreate()
    )
    # Khởi tạo StreamingContext với batch interval 5 giây
    ssc = StreamingContext(spark.sparkContext, 5)

    # Định nghĩa schema cho dữ liệu giao dịch
    transaction_schema = StructType([
        StructField("transaction_id", StringType()),
        StructField("user_id", IntegerType()),
        StructField("amount", DoubleType()),
        StructField("timestamp", TimestampType())
    ])

    # Biến trạng thái để theo dõi timestamp cuối cùng
    last_timestamp = [datetime(1970, 1, 1, tzinfo=pytz.UTC)]

    # Hàng đợi cho RDD
    rdd_queue = collections.deque()
    rdd_queue.append(spark.sparkContext.emptyRDD())

    # Hàm đọc dữ liệu từ MongoDB
    def fetch_mongo_data():
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[TRANSACTIONS_COLLECTION]
        
        while True:
            try:
                # Lấy các bản ghi mới hơn last_timestamp
                records = list(collection.find(
                    {"timestamp": {"$gt": last_timestamp[0]}},
                    {"_id": 1, "user_id": 1, "amount": 1, "timestamp": 1}
                ).sort("timestamp", 1).limit(100))  # Giới hạn để tránh quá tải
                
                if records:
                    # Cập nhật last_timestamp
                    last_timestamp[0] = max(record["timestamp"] for record in records)
                    
                    # Chuẩn bị dữ liệu cho RDD
                    rdd_data = [
                        (
                            str(record["_id"]),
                            record["user_id"],
                            record["amount"],
                            record["timestamp"]
                        )
                        for record in records
                    ]
                    # Tạo RDD và thêm vào hàng đợi
                    rdd = spark.sparkContext.parallelize(rdd_data)
                    rdd_queue.append(rdd)
                    print(f"Đã thêm {len(rdd_data)} bản ghi vào RDD queue")
                else:
                    # Thêm RDD rỗng nếu không có dữ liệu mới
                    rdd_queue.append(spark.sparkContext.emptyRDD())
                    print("Không có bản ghi mới, thêm RDD rỗng")
                
                time.sleep(5)  # Đồng bộ với batch interval
            except Exception as e:
                print(f"Lỗi khi lấy dữ liệu từ MongoDB: {str(e)}")
                time.sleep(5)

    # Chạy fetch_mongo_data trong thread riêng
    threading.Thread(target=fetch_mongo_data, daemon=True).start()

    # Đợi ngắn để đảm bảo rdd_queue có dữ liệu
    time.sleep(2)

    # Tạo QueueInputDStream từ rdd_queue
    queue_stream = ssc.queueStream(rdd_queue, oneAtATime=True)
    # Hàm xử lý từng RDD
    def process_rdd(rdd):
        if rdd.isEmpty():
            print("RDD rỗng, không có dữ liệu mới từ MongoDB")
            return

        # Chuyển RDD thành DataFrame
        try:
            transaction_df = spark.createDataFrame(rdd, transaction_schema) \
                .select(
                    col("transaction_id"),
                    col("user_id"),
                    col("amount"),
                    col("timestamp")
                )
            print("Dữ liệu giao dịch (transaction_df):")
            transaction_df.show(truncate=False)
        except Exception as e:
            print(f"Lỗi khi chuyển RDD thành DataFrame: {str(e)}")
            return

        # Đọc dữ liệu người dùng từ MongoDB
        try:
            users_df = spark.read \
                .format("mongo") \
                .option("uri", f"{MONGO_URI}{DB_NAME}.{USERS_COLLECTION}") \
                .load() \
                .select("user_id", "name", "city")
            users_df.createOrReplaceTempView("users")
            print("Dữ liệu người dùng (users_df):")
            users_df.show(truncate=False)
        except Exception as e:
            print(f"Lỗi khi đọc users từ MongoDB: {str(e)}")
            return

        # Đăng ký transaction_df làm bảng tạm
        transaction_df.createOrReplaceTempView("transactions")

        # Sử dụng Spark SQL để thực hiện phép join
        try:
            enriched_df = spark.sql("""
                SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, u.name AS user_name, u.city AS user_city
                FROM transactions t
                LEFT JOIN users u ON t.user_id = u.user_id
            """)
            print("Dữ liệu làm giàu (enriched_df):")
            enriched_df.show(truncate=False)

            # Ghi dữ liệu làm giàu vào MongoDB
            enriched_df.write \
                .format("mongo") \
                .mode("append") \
                .option("uri", f"{MONGO_URI}{DB_NAME}.{SINK_COLLECTION}") \
                .save()
            print(f"Đã làm giàu và lưu {enriched_df.count()} bản ghi vào {DB_NAME}.{SINK_COLLECTION}")
        except Exception as e:
            print(f"Lỗi khi thực hiện join hoặc lưu vào MongoDB: {str(e)}")

    # Áp dụng xử lý cho mỗi RDD trong DStream
    queue_stream.foreachRDD(process_rdd)

    # Bắt đầu stream
    ssc.start()
    print(f"Đã bắt đầu stream làm giàu dữ liệu vào {DB_NAME}.{SINK_COLLECTION}")
    try:
        ssc.awaitTermination()
    except KeyboardInterrupt:
        print("Ngừng stream...")
        ssc.stop(stopSparkContext=True, stopGraceFully=True)
        spark.stop()

if __name__ == "__main__":
    process_stream()