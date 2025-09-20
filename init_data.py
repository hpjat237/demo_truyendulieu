from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "mydatabase"

# Dữ liệu tĩnh người dùng
user_data = [
    {"user_id": 1, "name": "Alice", "city": "New York"},
    {"user_id": 2, "name": "Bob", "city": "London"},
    {"user_id": 3, "name": "Charlie", "city": "Paris"},
    # Thêm user khác nếu cần
]

def initialize_data():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db["users"]

    # Xóa dữ liệu cũ và chèn dữ liệu mới
    users_collection.delete_many({})
    users_collection.insert_many(user_data)

    print(f"✅ Đã chèn {len(user_data)} bản ghi vào collection 'users'.")
    client.close()

if __name__ == "__main__":
    initialize_data()