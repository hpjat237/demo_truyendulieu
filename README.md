---

# Hệ thống làm giàu dữ liệu thời gian thực

![Banner](https://via.placeholder.com/800x200.png?text=Hệ+thống+làm+giàu+dữ+liệu+thời+gian+thực)  
*Hình ảnh minh họa hệ thống (thay thế bằng hình ảnh thực tế nếu có)*

## 🚀 Giới thiệu

Dự án này mô phỏng một hệ thống làm giàu dữ liệu thời gian thực sử dụng **MongoDB**, **Debezium**, **Kafka**, và **Python**.  
Nguồn dữ liệu giao dịch được giả lập qua script `transaction_streamer.py`, gửi đến MongoDB, được Debezium theo dõi thay đổi và truyền qua Kafka, sau đó được làm giàu bằng thông tin tĩnh từ MongoDB và lưu vào collection mới.

---

## 📑 Mục lục

- [📋 Mô tả hệ thống](#-mô-tả-hệ-thống)
- [🔹 Luồng chạy demo](#-luồng-chạy-demo)
- [📋 Cấu trúc dự án](#-cấu-trúc-dự-án)
- [🔹 Yêu cầu](#-yêu-cầu)
- [📥 Cài đặt và chạy demo](#-cài-đặt-và-chạy-demo)
  - [Cài đặt môi trường](#cài-đặt-môi-trường)
  - [Đăng ký Debezium Connector](#đăng-ký-debezium-connector)
  - [Chạy các script Python](#chạy-các-script-python)
  - [Kiểm tra kết quả](#kiểm-tra-kết-quả)
- [🔹 Lưu ý](#-lưu-ý)
- [🔹 Khắc phục sự cố](#-khắc-phục-sự-cố)
- [🔹 Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [📧 Liên hệ](#-liên-hệ)

---

## 📋 Mô tả hệ thống

Hệ thống bao gồm các thành phần chính:

- **MongoDB**: Lưu trữ dữ liệu giao dịch (`mydatabase.transactions`) và thông tin người dùng tĩnh (`mydatabase.users`).
- **Debezium**: Theo dõi thay đổi trong MongoDB (oplog) và gửi dữ liệu đến Kafka topic `cdc.mydatabase.transactions`.
- **Kafka**: Hàng đợi tin nhắn để truyền dữ liệu giao dịch thời gian thực.
- **Python**: Các script để chèn dữ liệu, tạo giao dịch giả lập, và làm giàu dữ liệu.
- **Kafka Connect**: Chạy connector Debezium để kết nối MongoDB với Kafka.

![System Architecture](https://via.placeholder.com/600x300.png?text=Kiến+trúc+hệ+thống)  
*Hình ảnh kiến trúc hệ thống (thay thế bằng hình ảnh thực tế nếu có)*

---

## 🔹 Luồng chạy demo

Hệ thống hoạt động theo các bước sau:

1. **Khởi tạo dữ liệu tĩnh**: Script `init_data.py` chèn thông tin người dùng (Alice, Bob, Charlie) vào collection `mydatabase.users`.
2. **Giả lập luồng giao dịch**: Script `transaction_streamer.py` tạo các giao dịch giả lập (user_id, amount, timestamp) và chèn vào `mydatabase.transactions`.
3. **Theo dõi thay đổi**: Debezium connector giám sát oplog của MongoDB và gửi các giao dịch mới đến topic Kafka `cdc.mydatabase.transactions`.
4. **Làm giàu dữ liệu**: Script `stream_processor.py` đọc dữ liệu từ topic Kafka, kết hợp với thông tin người dùng từ `mydatabase.users`, và lưu kết quả vào `mydatabase.enriched_transactions`.
5. **Kiểm tra kết quả**: Collection `enriched_transactions` chứa dữ liệu đã làm giàu (transaction_id, user_id, amount, timestamp, user_name, user_city).

---

## 📋 Cấu trúc dự án

```
data_enrichment_system/
├── docker-compose.yml      # Cấu hình Docker
├── debezium_config.json    # Cấu hình Debezium connector
├── init_data.py            # Chèn dữ liệu tĩnh
├── transaction_streamer.py # Giả lập luồng giao dịch
├── stream_processor.py     # Làm giàu dữ liệu
└── README.md               # Tài liệu hướng dẫn
```

---

## 🔹 Yêu cầu

- **Git**: Để clone dự án.
- **Docker & Docker Compose**: Chạy các container MongoDB, Kafka, và Python.
- **MongoDB Shell (`mongosh`)** hoặc **MongoDB Compass**: Kiểm tra dữ liệu trong MongoDB.  
  Tải MongoDB Compass: [Link tải](https://downloads.mongodb.com/compass/mongodb-compass-1.46.10-win32-x64.exe)

---

## 📥 Cài đặt và chạy demo

### Cài đặt môi trường

1. **Clone dự án**:

   ```bash
   git clone https://github.com/your_username/data_enrichment_system.git
   cd data_enrichment_system
   ```

   ![Clone Project](https://via.placeholder.com/600x200.png?text=Clone+Project)  
   *Hình ảnh minh họa clone dự án*

2. **Khởi động các container**:

   ```bash
   docker-compose up -d
   ```

   > **Lưu ý**: Đảm bảo các container `mongodb`, `kafka`, `zookeeper`, `connect`, và `python-app` đang chạy. Kiểm tra bằng:
   > ```bash
   > docker ps
   > ```

3. **Khởi tạo replica set cho MongoDB**:

   ```bash
   docker exec -it mongodb mongosh
   ```

   ```javascript
   rs.initiate({_id: 'rs0', members: [{ _id: 0, host: 'mongodb:27017' }]})
   exit
   ```

4. **Cài đặt thư viện Python trong container `python-app`**:

   ```bash
   docker exec -it python-app bash
   pip install pymongo kafka-python pytz
   exit
   ```

### Đăng ký Debezium Connector

5. **Đăng ký connector**:

   ```bash
   curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors
   ```

6. **Kiểm tra trạng thái connector**:

   ```bash
   curl http://localhost:8083/connectors/mongodb-connector/status
   ```

   > **Kỳ vọng**: Trạng thái `RUNNING`. Nếu gặp lỗi, kiểm tra log:
   > ```bash
   > docker logs connect
   > ```

### Chạy các script Python

7. **Khởi tạo dữ liệu người dùng**:

   ```bash
   docker exec -it python-app python /app/init_data.py
   ```

   **Kỳ vọng**: Chèn 3 bản ghi (Alice, Bob, Charlie) vào `mydatabase.users`.

   ![Init Data](https://via.placeholder.com/600x200.png?text=Chèn+dữ+liệu+tĩnh)  
   *Hình ảnh minh họa chạy init_data.py*

8. **Giả lập luồng giao dịch** (mở terminal riêng):

   ```bash
   docker exec -it python-app python /app/transaction_streamer.py
   ```

   **Kỳ vọng**: Tạo các giao dịch mới trong `mydatabase.transactions`. Nhấn `Ctrl+C` để dừng.

9. **Làm giàu dữ liệu** (mở terminal riêng):

   ```bash
   docker exec -it python-app python /app/stream_processor.py
   ```

   **Kỳ vọng**: Đọc dữ liệu từ topic `cdc.mydatabase.transactions`, làm giàu, và lưu vào `mydatabase.enriched_transactions`.

   ![Stream Processor](https://via.placeholder.com/600x200.png?text=Làm+giàu+dữ+liệu)  
   *Hình ảnh minh họa chạy stream_processor.py*

### Kiểm tra kết quả

10. **Kiểm tra dữ liệu trong MongoDB**:

    ```bash
    docker exec -it mongodb mongosh
    ```

    ```javascript
    use mydatabase
    db.users.find().pretty()
    db.transactions.find().limit(5).pretty()
    db.enriched_transactions.find().pretty()
    exit
    ```

    **Kỳ vọng**:
    - `users`: 3 bản ghi (Alice, Bob, Charlie).
    - `transactions`: Các giao dịch với timestamp +07:00.
    - `enriched_transactions`: Dữ liệu làm giàu với `user_name` và `user_city`.

    ![MongoDB Check](https://via.placeholder.com/600x200.png?text=Kiểm+tra+MongoDB)  
    *Hình ảnh minh họa dữ liệu MongoDB*

11. **Kiểm tra dữ liệu trong Kafka topic**:

    ```bash
    docker exec -it connect /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic cdc.mydatabase.transactions --from-beginning
    ```

    **Kỳ vọng**: Thấy các thông điệp JSON từ Debezium.

---

## 🔹 Lưu ý

- Timestamp trong MongoDB được lưu ở múi giờ +07:00 (ICT) nhờ sử dụng `pytz` trong `transaction_streamer.py`.
- Nếu gặp lỗi `getaddrinfo failed`, kiểm tra `docker-compose.yml` để đảm bảo port mapping (`27017:27017`, `9093:9093`, `8083:8083`).
- Nếu topic `cdc.mydatabase.transactions` rỗng, kiểm tra log `connect` và trạng thái replica set MongoDB.

---

## 🔹 Khắc phục sự cố

- **Connector không chạy**:
  - Đảm bảo plugin `debezium-connector-mongodb` đã cài trong container `connect`:
    ```bash
    docker exec -it connect bash
    ls /kafka/connect
    ```
  - Cài lại plugin nếu cần:
    ```bash
    curl -O https://repo1.maven.org/maven2/io/debezium/debezium-connector-mongodb/2.3.0.Final/debezium-connector-mongodb-2.3.0.Final-plugin.tar.gz
    tar -xzf debezium-connector-mongodb-2.3.0.Final-plugin.tar.gz -C /kafka/connect
    rm debezium-connector-mongodb-2.3.0.Final-plugin.tar.gz
    exit
    docker-compose restart connect
    ```

- **Không có dữ liệu trong topic**:
  - Reset offset consumer group:
    ```bash
    docker exec -it connect /kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group enrichment_group --reset-offsets --to-earliest --topic cdc.mydatabase.transactions --execute
    ```

- **Collection `enriched_transactions` rỗng**:
  - Thêm debug vào `stream_processor.py`:
    ```python
    print(f"Received message: {message.value}")
    ```
  - Kiểm tra topic và log `connect`.

---

## 🔹 Công nghệ sử dụng

- **MongoDB**: 6.0
- **Kafka**: Confluent 7.4.0
- **Debezium**: 2.3.0.Final
- **Python**: 3.9 (pymongo, kafka-python, pytz)
- **Docker & Docker Compose**

---
