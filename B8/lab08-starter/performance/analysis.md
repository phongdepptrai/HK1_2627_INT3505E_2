# Lab 4 — Phân tích kết quả Load Test với Locust

## Bảng tổng hợp số liệu đo thực tế

| Kịch bản | Users | Spawn rate | Duration | Tổng reqs | Aggregated p95 (ms) | POST `/books` p95 (ms) | Failure rate (tổng) | RPS |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10 | 2/s | 30s | 134 | 19 | 160 | 0.75% (1/134) | 4.73 |
| B | 50 | 5/s | 60s | 1,317 | 180 | 530 | 0.30% (4/1,317) | 22.88 |
| C | 200 | 50/s | 30s | 2,758 | 470 | 740 | 0.40% (11/2,758) | 93.97 |

> **Lưu ý về dữ liệu đo:** Số liệu trên được đo trực tiếp khi chạy Locust `--headless` đối diện Books API (Flask development server + SQLite `instance/books.db`) trên máy local. Lỗi ghi nhận ở cả 3 kịch bản toàn bộ thuộc về `GET /books?year={year}` do client-side fault injection (`1%`), không phải HTTP 500 từ server.

---

## 1. Kịch bản có p95 cao nhất và nguyên nhân

- **Kịch bản C (Spike test: 200 users, spawn rate 50/s, 30s)** có chỉ số p95 cao nhất:
  - **Aggregated p95 = 470 ms** (cao gấp **2.6 lần** kịch bản B với 180 ms và gấp **24.7 lần** kịch bản A với 19 ms).
  - Riêng endpoint ghi `POST /books` đạt **p95 = 740 ms** (p99 = 2,100 ms, max = 4,040 ms).
- **Nguyên nhân:**
  1. Lưu lượng tăng vọt lên **93.97 req/s** với 200 user sinh đồng thời trong vòng 4 giây (`50 users/s`).
  2. Flask development server (Werkzeug single-process, đa luồng chịu giới hạn bởi Python GIL) và SQLite (chỉ cho phép một thao tác ghi tại một thời điểm thông qua file-level write lock) bị tranh chấp tài nguyên.
  3. Khi nhiều `POST /books` đến cùng lúc, các request phải xếp hàng chờ giải phóng khóa ghi SQLite và chia sẻ CPU với chính tiến trình Locust trên cùng một máy, đẩy tail latency (p95/p99) tăng mạnh.

---

## 2. Endpoint có tỉ lệ lỗi & Phân biệt lỗi thực vs lỗi giả lập

- **Quan sát thực tế:**
  - Các endpoint `GET /books`, `GET /books/{id}`, và `POST /books` đạt **0.00% failure rate** ở cả 3 kịch bản A, B, C.
  - Endpoint duy nhất có failure là `GET /books?year={year}`:
    - Kịch bản A: `1 / 40` (`2.50%`)
    - Kịch bản B: `4 / 343` (`1.17%`)
    - Kịch bản C: `11 / 698` (`1.58%`)
- **Phân biệt lỗi HTTP thực và lỗi đánh dấu trong Locust:**
  - Toàn bộ các lỗi trên đều là **lỗi đánh dấu phía client** qua `response.failure("Simulated 1% HTTP 500 error (client-side fault injection)")` trong `performance/locustfile.py` khi server vẫn trả `HTTP 200`. Vì xác suất tiêm lỗi cố định ở mức `1%`, tỉ lệ lỗi **không tăng theo số lượng user** mà chỉ dao động thống kê quanh ~1% (ở kịch bản A con số 2.50% chỉ do cỡ mẫu nhỏ `N = 40`).
- **Dự đoán lỗi thực nếu tăng tải cao hơn nữa dựa trên mã nguồn (`app.py`, `models.py`):**
  - Endpoint có nguy cơ tăng fail rate thực đầu tiên là **`POST /books`** (và `PUT /books/{id}`), vì gọi `db.session.commit()` ghi vào SQLite: khi concurrency vượt ngưỡng chờ khóa (SQLite busy timeout), SQLAlchemy sẽ ném `sqlite3.OperationalError: database is locked` và Flask trả **HTTP 500 thực**.

---

## 3. Đánh giá SLO `p95 < 300 ms` & Đề xuất mức tải CI gate

- **So sánh với ngưỡng SLO p95 < 300 ms:**
  - **Kịch bản A**: **Đạt hoàn toàn** (Aggregated p95 = **19 ms**; endpoint chậm nhất là `POST /books` cũng chỉ **160 ms** < 300 ms).
  - **Kịch bản B**: Aggregated p95 = **180 ms** (< 300 ms), nhưng **không đạt ở cấp từng endpoint** vì `POST /books` có p95 = **530 ms** (> 300 ms).
  - **Kịch bản C**: **Không đạt** cả mức tổng hợp (**470 ms**) lẫn từng endpoint (`GET /books` = 370 ms, `GET /books/{id}` = 460 ms, `GET /books?year={year}` = 470 ms, `POST /books` = 740 ms).
- **Giới hạn của phép đo:**
  - Phép đo dùng **Flask development server + SQLite** trên máy cá nhân (Locust và Flask cùng dùng chung CPU/disk), vì vậy **không thể dùng kết quả này để khẳng định hay phủ nhận SLO trên production** (nơi chạy multi-worker WSGI như Gunicorn + PostgreSQL). Kết quả chỉ dùng để phát hiện điểm nghẽn tương đối và hồi quy hiệu năng.
- **Đề xuất mức tải baseline cho CI gate:**
  - Sử dụng cấu hình tương đương **Kịch bản A (`10–15` users, spawn rate `2/s`, thời lượng `20–30s`)** làm **smoke/regression gate** trong CI/CD: đủ nhanh để không làm chậm pipeline, nhưng vẫn đủ lưu lượng đọc/ghi để phát hiện sớm thoái hóa truy vấn (như N+1 query hoặc lock bất thường) trước khi merge code.

---

## 4. Câu hỏi Bonus: Giới hạn Database Connection Pool = 5 khi 200 user truy cập đồng thời

- **Điều gì sẽ xảy ra:**
  1. Tại một thời điểm chỉ tối đa **5 kết nối DB** phục vụ được request; các thread web server phục vụ phần lớn trong số 200 user còn lại sẽ bị **chặn (block) ở hàng đợi `QueuePool.checkout()`** chờ kết nối được trả về.
  2. Độ trễ (`p95`, `p99`) tăng vọt theo cấp số nhân do thời gian chờ trong pool (queueing delay), đồng thời thông lượng (RPS) chạm trần bão hòa của 5 kết nối dù tăng thêm user.
  3. Khi thời gian chờ vượt quá `pool_timeout` (mặc định 30s trong SQLAlchemy hoặc ngắn hơn nếu cấu hình), pool ném ngoại lệ `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 0 reached, connection timed out`, làm Flask phát sinh **HTTP 500 thực tế hàng loạt** trên tất cả các endpoint có truy vấn DB (`GET /books`, `POST /books`, v.v.).
- **Cách xác nhận hiện tượng này bằng Locust:**
  1. Chạy thử nghiệm đối chứng ở mức **200 users** với cấu hình engine giới hạn pool (`pool_size=5, max_overflow=0, pool_timeout=5`, áp dụng trên DB hỗ trợ connection pooling như PostgreSQL hoặc cấu hình `QueuePool` trong SQLAlchemy).
  2. Quan sát 3 tín hiệu trong báo cáo HTML của Locust (`reports/`):
     - **Đồ thị Response Time (p95/p99)**: Tăng vọt lên xấp xỉ ngưỡng `pool_timeout` ngay khi ramp-up vượt qua điểm bão hòa.
     - **Đồ thị RPS**: Đi ngang (plateau) không tăng thêm dù số user tăng từ 50 lên 200.
     - **Tab Failures / Errors**: Xuất hiện lỗi **HTTP 500 thực từ server** (khác với chuỗi lỗi giả lập client-side của `search_by_year`) trên cả các route `GET` lẫn `POST` ngay khi vượt `pool_timeout`.
