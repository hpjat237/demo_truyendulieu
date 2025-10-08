---
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

5. **Cài đặt thư viện trong container `spark`**:

   ```bash
   docker exec -it spark bash
   pip install pymongo pytz
   exit
   ```

### Đăng ký Debezium Connector

6. **Đăng ký connector**:

   ```bash
   curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors
   ```

7. **Kiểm tra trạng thái connector**:

   ```bash
   curl http://localhost:8083/connectors/mongodb-connector/status
   ```

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

   **Kỳ vọng**: Tạo các giao dịch mới trong `mydatabase.transactions`. Nhấn `Ctrl+C` để dừng.

10. **Làm giàu dữ liệu** (mở terminal riêng):

    ```bash
    docker exec -it spark spark-submit /app/stream_processor.py
    ```

    **Kỳ vọng**: Đọc dữ liệu từ topic `cdc.mydatabase.transactions`, làm giàu bằng Spark Streaming và Spark SQL, lưu vào `mydatabase.enriched_transactions`.

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

    **Kỳ vọng**:
    - `users`: 3 bản ghi (Alice, Bob, Charlie).
    - `transactions`: Các giao dịch với timestamp +07:00.
    - `enriched_transactions`: Dữ liệu làm giàu với `user_name` và `user_city`.

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