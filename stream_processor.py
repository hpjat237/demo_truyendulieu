import json
from kafka import KafkaConsumer
from pymongo import MongoClient

KAFKA_BROKER = 'kafka:9092'
CDC_TOPIC = 'cdc.mydatabase.transactions'
GROUP_ID = 'enrichment_group'
MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "mydatabase"
USERS_COLLECTION = "users"
SINK_COLLECTION = "enriched_transactions"

def get_user_info(db, user_id):
    users_collection = db[USERS_COLLECTION]
    user = users_collection.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "city": 1})
    return user if user else {"name": "Unknown", "city": "Unknown"}

def process_stream():
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    sink_collection = db[SINK_COLLECTION]
    sink_collection.delete_many({})

    consumer = KafkaConsumer(
        CDC_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    print(f"Đã kết nối Kafka consumer đến {KAFKA_BROKER}, topic: {CDC_TOPIC}")

    for message in consumer:
        print(f"Nhận được thông điệp: {message.value}")
        try:
            payload = message.value  # Sửa: Không cần .get('payload')
            if not payload or payload.get('op') != 'c':
                print(f"Bỏ qua thông điệp (op không phải 'c'): {payload}")
                continue
            transaction_data = json.loads(payload.get('after'))  # Parse chuỗi JSON trong 'after'
            if not transaction_data:
                print("Không có transaction_data trong payload")
                continue
            user_id = transaction_data.get('user_id')
            user_info = get_user_info(db, user_id)
            enriched_record = {
                "transaction_id": str(transaction_data.get('_id').get('$oid')),
                "user_id": user_id,
                "amount": transaction_data.get('amount'),
                "timestamp": transaction_data.get('timestamp').get('$date'),
                "user_name": user_info['name'],
                "user_city": user_info['city']
            }
            sink_collection.insert_one(enriched_record)
            print(f"Đã làm giàu và lưu: User '{user_info['name']}' ({user_info['city']}) mua {enriched_record['amount']}")
        except Exception as e:
            print(f"Lỗi khi xử lý thông điệp: {e}")

    mongo_client.close()

if __name__ == "__main__":
    process_stream()