import time
import random
from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://mongodb:27017/"
DB_NAME = "mydatabase"
TRANSACTIONS_COLLECTION = "transactions"

def stream_transactions():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    transactions_collection = db[TRANSACTIONS_COLLECTION]
    
    print("⏳ Bắt đầu giả lập luồng giao dịch...")

    while True:
        # Giả lập giao dịch
        transaction = {
            "user_id": random.randint(1, 3), # Chỉ có user_id, cần join để lấy tên/thành phố
            "amount": round(random.uniform(10.0, 500.0), 2),
            "timestamp": datetime.now()
        }

        # Chèn vào MongoDB
        transactions_collection.insert_one(transaction)
        
        print(f"➡️ Giao dịch mới: User ID {transaction['user_id']}, Amount: {transaction['amount']}")

        # Chờ 1 giây cho giao dịch tiếp theo
        time.sleep(1)

if __name__ == "__main__":
    stream_transactions()