<img width="1452" height="692" alt="Screenshot 2025-10-08 090348" src="https://github.com/user-attachments/assets/b76516d4-8331-4ff2-bc93-5fade3b7958a" />---
# Hệ thống làm giàu dữ liệu thời gian thực

## Giới thiệu

Dự án này mô phỏng một hệ thống **Real-Time ETL** sử dụng **MongoDB**, **Debezium**, **Kafka**, **Spark**, và **Python**.  
Nguồn dữ liệu giao dịch được giả lập qua script `transaction_streamer.py`, gửi đến MongoDB, được Debezium theo dõi thay đổi và truyền qua Kafka, sau đó được làm giàu bằng thông tin tĩnh từ MongoDB sử dụng **Spark Streaming (DStream)** và **Spark SQL**, rồi lưu vào collection mới.

---

## Mô tả hệ thống

Hệ thống bao gồm các thành phần chính:

- **MongoDB**: Lưu trữ dữ liệu giao dịch (`mydatabase.transactions`) và thông tin người dùng tĩnh (`mydatabase.users`).
- **Debezium**: Theo dõi thay đổi trong MongoDB (oplog) và gửi dữ liệu đến Kafka topic `cdc.mydatabase.transactions`.
- **Kafka**: Hàng đợi tin nhắn để truyền dữ liệu giao dịch thời gian thực.
- **Spark**: Sử dụng Spark Streaming (DStream) và Spark SQL để làm giàu dữ liệu bằng cách join dữ liệu giao dịch với thông tin người dùng.
- **Python**: Các script để chèn dữ liệu, tạo giao dịch giả lập, và làm giàu dữ liệu.
- **Kafka Connect**: Chạy connector Debezium để kết nối MongoDB với Kafka.

---

## Luồng chạy demo

Hệ thống hoạt động theo các bước sau:

1. **Khởi tạo dữ liệu tĩnh**: Script `init_data.py` chèn thông tin người dùng (Alice, Bob, Charlie) vào collection `mydatabase.users`.
2. **Giả lập luồng giao dịch**: Script `transaction_streamer.py` tạo các giao dịch giả lập (user_id, amount, timestamp) và chèn vào `mydatabase.transactions`.
3. **Theo dõi thay đổi**: Debezium connector giám sát oplog của MongoDB và gửi các giao dịch mới đến topic Kafka `cdc.mydatabase.transactions`.
4. **Làm giàu dữ liệu**: Script `stream_processor.py` sử dụng Spark Streaming (DStream) để đọc dữ liệu từ topic Kafka, chuyển thành DataFrame, join với thông tin người dùng từ `mydatabase.users` sử dụng Spark SQL, và lưu kết quả vào `mydatabase.enriched_transactions`.
5. **Kiểm tra kết quả**: Collection `enriched_transactions` chứa dữ liệu đã làm giàu (transaction_id, user_id, amount, timestamp, user_name, user_city).

---

## Cấu trúc dự án

```
data_enrichment_system/
├── docker-compose.yml      # Cấu hình Docker
├── debezium_config.json    # Cấu hình Debezium connector
├── init_data.py            # Chèn dữ liệu tĩnh
├── transaction_streamer.py # Giả lập luồng giao dịch
├── stream_processor.py     # Làm giàu dữ liệu với Spark Streaming
└── README.md               # Tài liệu hướng dẫn
```

---

## Yêu cầu

- **Git**: Để clone dự án.
- **Docker & Docker Compose**: Chạy các container MongoDB, Kafka, Spark, và Python.
- **MongoDB Shell (`mongosh`)** hoặc **MongoDB Compass**: Kiểm tra dữ liệu trong MongoDB.  
  Tải MongoDB Compass: [Link tải](https://downloads.mongodb.com/compass/mongodb-compass-1.46.10-win32-x64.exe)

---

## Cài đặt và chạy demo

### Cài đặt môi trường

1. **Clone dự án**:

   ```bash
   git clone https://github.com/hpjat237/demo_truyendulieu.git
   cd demo_truyendulieu
   ```

2. **Khởi động các container**:

   ```bash
   docker-compose up -d
   ```

   > **Lưu ý**: Đảm bảo các container `mongodb`, `kafka`, `zookeeper`, `connect`, `python-app`, và `spark` đang chạy. Kiểm tra bằng:
   > ```bash
   > docker ps
   > ```
   <img width="1460" height="361" alt="Screenshot 2025-10-08 083720" src="https://github.com/user-attachments/assets/ce9ac719-fd13-4f75-9b92-c037799230ff" />

3. **Khởi tạo replica set cho MongoDB**:

   ```bash
   docker exec -it mongodb mongosh
   ```

   ```javascript
   rs.initiate({_id: 'rs0', members: [{ _id: 0, host: 'mongodb:27017' }]})
   exit
   ```
   <img width="1452" height="652" alt="Screenshot 2025-10-08 083751" src="https://github.com/user-attachments/assets/07c0cd72-cb0d-41e8-9795-27b9ed4a506a" />

4. **Cài đặt thư viện Python trong container `python-app`**:

   ```bash
   docker exec -it python-app bash
   pip install pymongo kafka-python pytz
   exit
   ```
   <img width="1450" height="537" alt="Screenshot 2025-10-08 083838" src="https://github.com/user-attachments/assets/193b87d6-1317-4e20-a0f2-d71fc7f24546" />

5. **Cài đặt thư viện trong container `spark`**:

   ```bash
   docker exec -it spark bash
   pip install pymongo pytz
   exit
   ```
   <img width="1457" height="381" alt="Screenshot 2025-10-08 083946" src="https://github.com/user-attachments/assets/4142b367-817d-4eed-985f-5a54f9b87159" />

### Đăng ký Debezium Connector

6. **Đăng ký connector**:

   ```bash
   curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors
   ```

7. **Kiểm tra trạng thái connector**:

   ```bash
   curl http://localhost:8083/connectors/mongodb-connector/status
   ```
   <img width="1452" height="280" alt="Screenshot 2025-10-08 084021" src="https://github.com/user-attachments/assets/d8029d08-7765-476d-9ebd-b85ecfa4e108" />

   > **Kỳ vọng**: Trạng thái `RUNNING`. Nếu gặp lỗi, kiểm tra log:
   > ```bash
   > docker logs connect
   > ```

### Chạy các script Python

8. **Khởi tạo dữ liệu người dùng**:

   ```bash
   docker exec -it python-app python /app/init_data.py
   ```

   **Kỳ vọng**: Chèn 3 bản ghi (Alice, Bob, Charlie) vào `mydatabase.users`.

9. **Giả lập luồng giao dịch** (mở terminal riêng):

   ```bash
   docker exec -it python-app python /app/transaction_streamer.py
   ```

   <img width="1102" height="485" alt="Screenshot 2025-10-08 000304" src="https://github.com/user-attachments/assets/f32aafca-4338-4b9d-a592-3d738b66d793" />


10. **Làm giàu dữ liệu** (mở terminal riêng):

    ```bash
    docker exec -it spark spark-submit /app/stream_processor.py
    ```

    <img width="1446" height="675" alt="Screenshot 2025-10-08 130819" src="https://github.com/user-attachments/assets/0656aab8-3f1a-40d7-9603-f505394e3593" />
    <img width="1408" height="656" alt="Screenshot 2025-10-08 084404" src="https://github.com/user-attachments/assets/4ef73077-1f9b-4f11-9477-5002c39c035d" />
    
### Kiểm tra kết quả

11. **Kiểm tra dữ liệu trong MongoDB**:

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

    <img width="1408" height="656" alt="Screenshot 2025-10-08 084404" src="https://github.com/user-attachments/assets/4ef73077-1f9b-4f11-9477-5002c39c035d" />
    <img width="796" height="673" alt="Screenshot 2025-10-08 084647" src="https://github.com/user-attachments/assets/8e9ed717-ad6a-4031-a645-201de559016d" />


12. **Kiểm tra dữ liệu trong Kafka topic**:

    ```bash
    docker exec -it connect /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic cdc.mydatabase.transactions --from-beginning
    ```

    **Kỳ vọng**: Thấy các thông điệp JSON từ Debezium.

13. **Kiểm tra Spark UI** (tùy chọn):

    Mở trình duyệt tại `http://localhost:8080` để xem trạng thái Spark job.

14. **Clean hệ thống**:

    Sau khi chạy demo xong, dọn dẹp tài nguyên để tránh chiếm dung lượng:

    ```bash
    docker-compose down -v
    ```

---

## Giải thích code: Phép join với DStream và Spark SQL

### Tổng quan
Script `stream_processor.py` thực hiện bước **Transform** trong quy trình ETL thời gian thực bằng cách sử dụng **Spark Streaming (DStream)** và **Spark SQL**:
- **Extract**: Đọc dữ liệu từ Kafka topic `cdc.mydatabase.transactions` sử dụng DStream.
- **Transform**: Chuyển DStream thành DataFrame, join với dữ liệu tĩnh từ MongoDB sử dụng Spark SQL.
- **Load**: Lưu kết quả làm giàu vào MongoDB collection `enriched_transactions`.

### Chi tiết phép join
1. **Đọc dữ liệu từ Kafka (DStream)**:
   - Sử dụng `StreamingContext.textFileStream` để đọc dữ liệu từ Kafka topic.
   - Dữ liệu được xử lý theo từng batch (mỗi 5 giây) dưới dạng RDD.

2. **Chuyển DStream thành DataFrame**:
   - Mỗi RDD trong DStream được chuyển thành DataFrame bằng `spark.read.json(rdd)`.
   - Parse JSON từ trường `after` của Debezium với schema xác định trước (`transaction_schema`).
   - Lọc các thao tác insert (`op = 'c'`) và trích xuất các trường `transaction_id`, `user_id`, `amount`, `timestamp`.

3. **Đọc dữ liệu tĩnh từ MongoDB**:
   - Sử dụng MongoDB Spark Connector để đọc collection `users` thành DataFrame (`users_df`) với các trường `user_id`, `name`, `city`.

4. **Phép join với Spark SQL**:
   - Đăng ký `transaction_df` và `users_df` làm bảng tạm (`transactions` và `users`).
   - Thực hiện truy vấn SQL:
     ```sql
     SELECT t.transaction_id, t.user_id, t.amount, t.timestamp, u.name AS user_name, u.city AS user_city
     FROM transactions t
     LEFT JOIN users u ON t.user_id = u.user_id
     ```
   - Kết quả là DataFrame `enriched_df` chứa dữ liệu làm giàu.

5. **Lưu kết quả**:
   - Ghi `enriched_df` vào MongoDB collection `enriched_transactions` sử dụng MongoDB Spark Connector.

### Lợi ích của DStream và Spark SQL
- **DStream**: Phù hợp với các ứng dụng streaming truyền thống, xử lý dữ liệu theo batch nhỏ.
- **Spark SQL**: Cung cấp cú pháp SQL dễ đọc, đơn giản hóa logic join so với cách tiếp cận vòng lặp thủ công.
- **MongoDB Spark Connector**: Tích hợp mượt mà với MongoDB, hỗ trợ cả đọc và ghi dữ liệu.

---

## Công nghệ sử dụng

- **MongoDB**: 6.0
- **Kafka**: Confluent 7.4.0
- **Debezium**: 2.3.0.Final
- **Spark**: 3.4.0 (Spark Streaming và Spark SQL)
- **Python**: 3.9 (pymongo, kafka-python, pytz, pyspark)
- **MongoDB Spark Connector**: 10.1.1
- **Docker & Docker Compose**
---
