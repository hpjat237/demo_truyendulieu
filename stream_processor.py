import json
from kafka import KafkaConsumer
from pymongo import MongoClient

# Cấu hình Kafka
KAFKA_BROKER = 'localhost:9093' # Cổng EXTERNAL
CDC_TOPIC = 'cdc.mydatabase.transactions'
GROUP_ID = 'enrichment_group'

# Cấu hình MongoDB (Nguồn dữ liệu tĩnh VÀ Nơi lưu kết quả)
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "mydatabase"
USERS_COLLECTION = "users"
SINK_COLLECTION = "enriched_transactions"


def get_user_info(db, user_id):
    """Truy vấn MongoDB để lấy thông tin người dùng tĩnh."""
    users_collection = db[USERS_COLLECTION]
    user = users_collection.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "city": 1})
    return user if user else {"name": "Unknown", "city": "Unknown"}

def process_stream():
    # 1. Kết nối MongoDB
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    sink_collection = db[SINK_COLLECTION]
    sink_collection.delete_many({}) # Xóa dữ liệu cũ cho demo
    
    # 2. Kết nối Kafka Consumer
    consumer = KafkaConsumer(
        CDC_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print(f"🔄 Đang chờ giao dịch mới từ Kafka topic: {CDC_TOPIC}...")

    for message in consumer:
        try:
            # Sự kiện Debezium: Value chứa payload CDC
            payload = message.value.get('payload')
            
            if not payload or payload.get('op') != 'c':
                # Chỉ xử lý sự kiện 'c' (create/insert)
                continue

            # 'after' chứa tài liệu sau khi thay đổi (tức là tài liệu vừa được chèn)
            transaction_data = payload.get('after')
            
            if not transaction_data:
                continue

            # Lấy user_id từ dữ liệu giao dịch
            user_id = transaction_data.get('user_id')
            
            # --- BƯỚC 3 & 4: JOIN/ENRICHMENT ---
            user_info = get_user_info(db, user_id)
            
            # Tạo bản ghi đã được làm giàu
            enriched_record = {
                "transaction_id": str(transaction_data.get('_id')),
                "user_id": user_id,
                "amount": transaction_data.get('amount'),
                "timestamp": transaction_data.get('timestamp'),
                "user_name": user_info['name'],
                "user_city": user_info['city']
            }
            
            # --- BƯỚC 5: LƯU KẾT QUẢ ---
            sink_collection.insert_one(enriched_record)

            print(f"✅ Đã làm giàu và lưu: User '{user_info['name']}' ({user_info['city']}) mua {enriched_record['amount']}")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý thông điệp: {e}")
            
    mongo_client.close()

if __name__ == "__main__":
    process_stream()