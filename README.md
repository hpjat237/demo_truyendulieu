Hệ Thống Xử Lý Luồng Giao Dịch Thời Gian Thực
Hệ thống này mô phỏng một pipeline xử lý dữ liệu thời gian thực sử dụng MongoDB, Kafka, và Debezium để làm giàu dữ liệu giao dịch.
Yêu Cầu Hệ Thống

Docker và Docker Compose (để chạy MongoDB, Kafka, và Debezium)
Python 3.8+
Các thư viện Python:
pymongo
kafka-python
python-dateutil


MongoDB (phiên bản 6.0)
Java (để chạy Kafka và Debezium)

Cài đặt các thư viện Python cần thiết:
pip install pymongo kafka-python python-dateutil

Cấu Trúc Dự Án

transaction_streamer.py: Mô phỏng luồng giao dịch, chèn dữ liệu vào MongoDB.
stream_processor.py: Lắng nghe các giao dịch từ Kafka, làm giàu dữ liệu với thông tin người dùng từ MongoDB, và lưu kết quả vào collection enriched_transactions.
init_data.py: Khởi tạo dữ liệu người dùng tĩnh trong MongoDB.
docker-compose.yml: Cấu hình các dịch vụ MongoDB, Kafka, Zookeeper, và Debezium Connect.
debezium_config.json: Cấu hình Debezium để theo dõi thay đổi trong MongoDB và gửi đến Kafka.

Hướng Dẫn Chạy Demo
Bước 1: Khởi động các dịch vụ Docker

Đảm bảo Docker đang chạy.
Trong thư mục dự án, chạy lệnh sau để khởi động Zookeeper, Kafka, MongoDB và Debezium Connect:

docker-compose up -d


Kiểm tra trạng thái các container:

docker-compose ps

Bước 2: Cấu hình Debezium Connector

Đợi khoảng 30 giây để các dịch vụ khởi động hoàn toàn.
Đăng ký connector Debezium để theo dõi collection transactions trong MongoDB:

curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors


Kiểm tra trạng thái connector:

curl http://localhost:8083/connectors/mongodb-connector/status

Bước 3: Khởi tạo dữ liệu người dùng
Chạy script để chèn dữ liệu người dùng tĩnh vào MongoDB:
python init_data.py

Kết quả: 3 bản ghi người dùng (Alice, Bob, Charlie) sẽ được chèn vào collection users.
Bước 4: Chạy bộ mô phỏng giao dịch
Mở một terminal mới và chạy script để tạo luồng giao dịch giả lập:
python transaction_streamer.py

Script này sẽ liên tục chèn các giao dịch vào collection transactions trong MongoDB, với user_id, amount, và timestamp.
Bước 5: Chạy bộ xử lý luồng
Mở một terminal khác và chạy script để xử lý và làm giàu dữ liệu từ Kafka:
python stream_processor.py

Script này sẽ:

Lắng nghe topic cdc.mydatabase.transactions từ Kafka.
Join dữ liệu giao dịch với thông tin người dùng từ collection users.
Lưu kết quả đã làm giàu vào collection enriched_transactions.

Bước 6: Kiểm tra kết quả

Mở MongoDB shell hoặc công cụ như MongoDB Compass.
Kết nối tới mongodb://localhost:27017 và kiểm tra collection enriched_transactions trong database mydatabase.
Các bản ghi sẽ có dạng:

{
  "transaction_id": "<MongoDB ObjectId>",
  "user_id": 1,
  "amount": 123.45,
  "timestamp": "2023-10-10T12:34:56.789Z",
  "user_name": "Alice",
  "user_city": "New York"
}

Bước 7: Dừng demo

Dừng các script Python bằng Ctrl+C.
Tắt các container Docker:

docker-compose down

Lưu Ý

Đảm bảo các cổng 2181, 27017, 8083, 9092, và 9093 không bị chiếm dụng.
Nếu gặp lỗi kết nối MongoDB, kiểm tra xem MongoDB đã khởi động và replica set đã được cấu hình đúng.
Debezium yêu cầu MongoDB được cấu hình với replica set (đã được xử lý trong docker-compose.yml).

Xử Lý Lỗi

Kafka connection error: Kiểm tra xem Kafka broker đã chạy (docker-compose ps) và cổng 9093 có thể truy cập.
Debezium connector fails: Xem log của container connect (docker logs connect) để tìm lỗi chi tiết.
MongoDB replica set issues: Đảm bảo healthcheck trong docker-compose.yml hoàn tất thành công.

Tùy Chỉnh

Thêm dữ liệu người dùng mới trong init_data.py.
Điều chỉnh tần suất giao dịch trong transaction_streamer.py bằng cách thay đổi giá trị trong time.sleep().
Sửa topic hoặc cấu hình Kafka trong stream_processor.py và debezium_config.json nếu cần.
