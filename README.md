<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ thống làm giàu dữ liệu thời gian thực</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0 auto;
            max-width: 800px;
            padding: 20px;
            background-color: #f9f9f9;
        }
        h1, h2, h3 {
            color: #333;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            font-family: Consolas, monospace;
        }
        .note {
            background-color: #e7f3fe;
            border-left: 4px solid #2196F3;
            padding: 10px;
            margin: 10px 0;
        }
        .step {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <h1>Hệ thống làm giàu dữ liệu thời gian thực</h1>
    <p>Đây là một hệ thống demo sử dụng MongoDB, Debezium, Kafka và Python để làm giàu dữ liệu thời gian thực. Hệ thống mô phỏng luồng giao dịch người dùng, theo dõi thay đổi trong MongoDB, gửi dữ liệu qua Kafka, và làm giàu dữ liệu bằng cách kết hợp thông tin tĩnh từ MongoDB.</p>

    <h2>Mô tả hệ thống</h2>
    <p>Hệ thống bao gồm các thành phần chính:</p>
    <ul>
        <li><strong>MongoDB</strong>: Lưu trữ dữ liệu giao dịch (`mydatabase.transactions`) và thông tin người dùng tĩnh (`mydatabase.users`).</li>
        <li><strong>Debezium</strong>: Theo dõi thay đổi trong MongoDB (oplog) và gửi dữ liệu đến Kafka topic `cdc.mydatabase.transactions`.</li>
        <li><strong>Kafka</strong>: Hàng đợi tin nhắn để truyền dữ liệu giao dịch thời gian thực.</li>
        <li><strong>Python</strong>: Các script để chèn dữ liệu, tạo giao dịch giả lập, và làm giàu dữ liệu.</li>
        <li><strong>Kafka Connect</strong>: Chạy connector Debezium để kết nối MongoDB với Kafka.</li>
    </ul>

    <h2>Luồng chạy demo</h2>
    <p>Hệ thống hoạt động theo các bước sau:</p>
    <ol>
        <li><strong>Khởi tạo dữ liệu tĩnh</strong>: Script <code>init_data.py</code> chèn thông tin người dùng (Alice, Bob, Charlie) vào collection <code>mydatabase.users</code>.</li>
        <li><strong>Giả lập luồng giao dịch</strong>: Script <code>transaction_streamer.py</code> tạo các giao dịch giả lập (user_id, amount, timestamp) và chèn vào <code>mydatabase.transactions</code>.</li>
        <li><strong>Theo dõi thay đổi</strong>: Debezium connector giám sát oplog của MongoDB và gửi các giao dịch mới đến topic Kafka <code>cdc.mydatabase.transactions</code>.</li>
        <li><strong>Làm giàu dữ liệu</strong>: Script <code>stream_processor.py</code> đọc dữ liệu từ topic Kafka, kết hợp với thông tin người dùng từ <code>mydatabase.users</code>, và lưu kết quả vào <code>mydatabase.enriched_transactions</code>.</li>
        <li><strong>Kiểm tra kết quả</strong>: Collection <code>enriched_transactions</code> chứa dữ liệu đã làm giàu (transaction_id, user_id, amount, timestamp, user_name, user_city).</li>
    </ol>

    <h2>Cấu trúc thư mục</h2>
    <pre><code>
data_enrichment_system/
├── docker-compose.yml
├── debezium_config.json
├── init_data.py
├── transaction_streamer.py
└── stream_processor.py
    </code></pre>

    <h2>Cài đặt và chạy demo</h2>
    <p>Để chạy demo, bạn cần có Docker, Docker Compose, và Python 3.9+ trên máy tính.</p>

    <h3>1. Cài đặt môi trường</h3>
    <div class="step">
        <p><strong>Bước 1</strong>: Clone repository về máy tính:</p>
        <pre><code>git clone https://github.com/your_username/data_enrichment_system.git
cd data_enrichment_system</code></pre>
    </div>
    <div class="step">
        <p><strong>Bước 2</strong>: Khởi động các container bằng Docker Compose:</p>
        <pre><code>docker-compose up -d</code></pre>
        <p class="note">Đảm bảo các container <code>mongodb</code>, <code>kafka</code>, <code>zookeeper</code>, <code>connect</code>, và <code>python-app</code> đang chạy (<code>docker ps</code>).</p>
    </div>
    <div class="step">
        <p><strong>Bước 3</strong>: Khởi tạo replica set cho MongoDB:</p>
        <pre><code>docker exec -it mongodb mongosh
rs.initiate({_id: 'rs0', members: [{ _id: 0, host: 'mongodb:27017' }]})
exit</code></pre>
    </div>
    <div class="step">
        <p><strong>Bước 4</strong>: Cài đặt thư viện Python trong container <code>python-app</code>:</p>
        <pre><code>docker exec -it python-app bash
pip install pymongo kafka-python pytz
exit</code></pre>
    </div>

    <h3>2. Đăng ký Debezium Connector</h3>
    <div class="step">
        <p>Đăng ký connector để Debezium theo dõi MongoDB:</p>
        <pre><code>curl -X POST -H "Content-Type: application/json" --data @debezium_config.json http://localhost:8083/connectors</code></pre>
        <p>Kiểm tra trạng thái connector:</p>
        <pre><code>curl http://localhost:8083/connectors/mongodb-connector/status</code></pre>
        <p class="note">Đảm bảo trạng thái là <code>RUNNING</code>. Nếu gặp lỗi, kiểm tra log: <code>docker logs connect</code>.</p>
    </div>

    <h3>3. Chạy các script Python</h3>
    <div class="step">
        <p><strong>Khởi tạo dữ liệu người dùng</strong>:</p>
        <pre><code>docker exec -it python-app python /app/init_data.py</code></pre>
        <p><strong>Kỳ vọng</strong>: Chèn 3 bản ghi (Alice, Bob, Charlie) vào <code>mydatabase.users</code>.</p>
    </div>
    <div class="step">
        <p><strong>Giả lập luồng giao dịch</strong> (chạy trong terminal riêng):</p>
        <pre><code>docker exec -it python-app python /app/transaction_streamer.py</code></pre>
        <p><strong>Kỳ vọng</strong>: Tạo các giao dịch mới trong <code>mydatabase.transactions</code>. Nhấn <code>Ctrl+C</code> để dừng.</p>
    </div>
    <div class="step">
        <p><strong>Làm giàu dữ liệu</strong> (chạy trong terminal riêng):</p>
        <pre><code>docker exec -it python-app python /app/stream_processor.py</code></pre>
        <p><strong>Kỳ vọng</strong>: Đọc dữ liệu từ topic <code>cdc.mydatabase.transactions</code>, làm giàu, và lưu vào <code>mydatabase.enriched_transactions</code>.</p>
    </div>

    <h3>4. Kiểm tra kết quả</h3>
    <div class="step">
        <p>Kiểm tra dữ liệu trong MongoDB:</p>
        <pre><code>docker exec -it mongodb mongosh
use mydatabase
db.users.find().pretty()
db.transactions.find().limit(5).pretty()
db.enriched_transactions.find().pretty()
exit</code></pre>
    </div>
    <div class="step">
        <p>Kiểm tra dữ liệu trong Kafka topic:</p>
        <pre><code>docker exec -it connect /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic cdc.mydatabase.transactions --from-beginning</code></pre>
    </div>

    <h2>Lưu ý</h2>
    <ul>
        <li>Timestamp trong MongoDB được lưu ở múi giờ +07:00 (ICT) nhờ sử dụng <code>pytz</code> trong <code>transaction_streamer.py</code>.</li>
        <li>Nếu gặp lỗi <code>getaddrinfo failed</code>, kiểm tra <code>docker-compose.yml</code> để đảm bảo port mapping (<code>27017:27017</code>, <code>9093:9093</code>, <code>8083:8083</code>).</li>
        <li>Nếu topic <code>cdc.mydatabase.transactions</code> rỗng, kiểm tra log <code>connect</code> và trạng thái replica set MongoDB.</li>
    </ul>

    <h2>Khắc phục sự cố</h2>
    <ul>
        <li><strong>Connector không chạy</strong>: Đảm bảo plugin <code>debezium-connector-mongodb</code> đã cài trong container <code>connect</code>.</li>
        <li><strong>Không có dữ liệu trong topic</strong>: Reset offset consumer group:
            <pre><code>docker exec -it connect /kafka/bin/kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group enrichment_group --reset-offsets --to-earliest --topic cdc.mydatabase.transactions --execute</code></pre>
        </li>
        <li><strong>Collection <code>enriched_transactions</code> rỗng</strong>: Kiểm tra log trong <code>stream_processor.py</code> và đảm bảo topic có dữ liệu.</li>
    </ul>

    <h2>Công nghệ sử dụng</h2>
    <ul>
        <li>MongoDB: 6.0</li>
        <li>Kafka: Confluent 7.4.0</li>
        <li>Debezium: 2.3.0.Final</li>
        <li>Python: 3.9 (pymongo, kafka-python, pytz)</li>
        <li>Docker & Docker Compose</li>
    </ul>

    <h2>Liên hệ</h2>
    <p>Nếu bạn có câu hỏi hoặc cần hỗ trợ, hãy mở issue trên repository GitHub.</p>
</body>
</html>
