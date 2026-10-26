# Báo Cáo Rà Soát Bảo Mật (Security Audit) - Lab 6

- **Môn học**: Kiến trúc Hướng Dịch vụ (INT3505E)
- **Tập tin đặc tả**: [`openapi.yaml`](./openapi.yaml)
- **Chủ đề**: Thiết kế bảo mật và phân quyền API (Chuẩn bị cho Buổi 07)

---

## 1. Thiết Kế Phân Quyền & Mã Trạng Thái HTTP

### 1.1. Nguyên tắc tách biệt AuthN và AuthZ
- **AuthN (401 Unauthorized)**: Thiếu token, token hết hạn, sai chữ ký số hoặc sai username/password khi login.
- **AuthZ (403 Forbidden)**: Đã xác thực danh tính thành công nhưng thiếu scope (`post:read`), sai quyền hạn hoặc không có quyền xem bài viết riêng tư.

### 1.2. Ba lớp kiểm tra quyền tại `GET /posts/{id}`
1. **Lớp 1 (AuthN)**: Kiểm tra JWT hợp lệ, còn hạn (`exp`), đúng chữ ký và `jti` chưa bị thu hồi $\rightarrow$ Nếu lỗi: `401 Unauthorized`.
2. **Lớp 2 (AuthZ - Scope)**: Kiểm tra token có chứa scope `post:read` $\rightarrow$ Nếu thiếu: `403 Forbidden`.
3. **Lớp 3 (Ownership / BOLA Policy)**: Kiểm tra quyền xem bài viết:
   - Bài viết `public`: Cho phép xem $\rightarrow$ `200 OK`.
   - Bài viết `private`: Chỉ tác giả (`author_id == current_user_id`) mới được xem $\rightarrow$ Nếu không phải tác giả: `403 Forbidden`.
   - Nếu bài viết không tồn tại trong DB $\rightarrow$ `404 Not Found`.

### 1.3. Bảng tổng hợp mã trạng thái HTTP

| Endpoint | HTTP Code | Kịch bản lỗi / Thành công |
| :--- | :---: | :--- |
| **`POST /auth/login`** | `200 OK` | Đăng nhập thành công, trả về Access Token + Refresh Token |
| | `400 Bad Request` | Thiếu `username` hoặc `password` |
| | `401 Unauthorized` | Sai tên đăng nhập hoặc mật khẩu |
| **`POST /auth/refresh`** | `200 OK` | Cấp Access Token mới thành công |
| | `400 Bad Request` | Thiếu `refresh_token` |
| | `401 Unauthorized` | Refresh Token hết hạn hoặc không hợp lệ |
| **`GET /posts/{id}`** | `200 OK` | Đọc bài viết thành công (thỏa mãn cả 3 lớp) |
| | `400 Bad Request` | ID bài viết không hợp lệ |
| | `401 Unauthorized` | Thiếu Bearer Token, token sai hoặc hết hạn (Lớp 1 AuthN) |
| | `403 Forbidden` | Thiếu scope `post:read` hoặc không có quyền xem bài viết riêng tư (Lớp 2, 3 AuthZ) |
| | `404 Not Found` | Bài viết không tồn tại |

---

## 2. Rà Soát 6 Điểm Nguy Cơ Rò Rỉ Dữ Liệu & Lỗ Hổng Bảo Mật

### Điểm 1: Lỗ hổng kiểm soát quyền cấp đối tượng (BOLA / IDOR - OWASP API1:2023)
- **Nguy cơ**: Tại `GET /posts/{id}`, backend chỉ kiểm tra user đã đăng nhập mà không kiểm tra người gọi có phải tác giả của bài viết riêng tư (`visibility = 'private'`) hay không.
- **Hậu quả**: Người dùng A chỉ cần thay đổi số `{id}` trên URL là có thể xem trộm bài viết riêng tư của người dùng B.
- **Khắc phục**: Triển khai Lớp 3 (Object-level check), so khớp `post.author_id == token.sub` trước khi trả về dữ liệu bài viết riêng tư.

### Điểm 2: Chấp nhận `alg=none` hoặc tấn công Algorithm Confusion (HS256 vs RS256)
- **Nguy cơ**: Thư viện xác thực JWT đọc thuật toán từ header của token do client gửi lên.
- **Hậu quả**: Kẻ tấn công có thể đổi thuật toán sang `none` để bypass chữ ký, hoặc đổi từ `RS256` sang `HS256` rồi dùng khóa công khai (Public Key) của server để ký giả mạo token quản trị.
- **Khắc phục**: Ghim cứng thuật toán xác thực ở backend (`algorithms=["RS256"]`), cấm tuyệt đối `alg: none`.

### Điểm 3: Lưu Token trong localStorage và truyền qua URL Query String
- **Nguy cơ**: Client lưu Access/Refresh Token trong `localStorage`, hoặc server hỗ trợ nhận token qua URL `?token=...`.
- **Hậu quả**: Script độc hại dễ dàng đánh cắp token nếu trang dính lỗi XSS; token trên URL bị lộ trong lịch sử duyệt web và log của server.
- **Khắc phục**: Lưu Refresh Token trong Cookie `HttpOnly, Secure, SameSite=Strict`. Access Token truyền duy nhất qua header `Authorization: Bearer <token>`.

### Điểm 4: Đặt thông tin nhạy cảm vào Payload của JWT
- **Nguy cơ**: Đưa mật khẩu, `password_hash`, email, số điện thoại hoặc dữ liệu cá nhân (PII) vào Payload của JWT vì nghĩ JWT được mã hóa bí mật.
- **Hậu quả**: JWT chuẩn JWS chỉ được mã hóa Base64URL, bất kỳ ai cũng có thể giải mã và đọc nội dung plaintext trên `jwt.io`.
- **Khắc phục**: Payload JWT chỉ chứa các claim tối thiểu (`sub`, `iss`, `aud`, `exp`, `jti`, `scope`). Tuyệt đối không để dữ liệu nhạy cảm vào JWT.

### Điểm 5: Access Token sống quá dài và thiếu cơ chế thu hồi (Revocation)
- **Nguy cơ**: Đặt hạn Access Token kéo dài (vài ngày/vài tuần) và không có danh sách thu hồi (`jti` blocklist).
- **Hậu quả**: Khi token bị lộ hoặc người dùng đăng xuất/đổi mật khẩu, kẻ tấn công vẫn tiếp tục sử dụng token đó cho đến khi hết hạn tự nhiên.
- **Khắc phục**: Đặt thời gian sống Access Token ngắn (10 - 15 phút). Áp dụng Refresh Token Rotation (RTR) và lưu `jti` đã thu hồi vào Redis.

### Điểm 6: Lộ sự tồn tại của tài khoản (User Enumeration) và thiếu Rate Limiting
- **Nguy cơ**: Trả về thông báo lỗi quá chi tiết như *"Tài khoản không tồn tại"* vs *"Mật khẩu không đúng"*, đồng thời không giới hạn số lần gọi endpoint login.
- **Hậu quả**: Kẻ tấn công có thể dò quét tài khoản có thật trên hệ thống để thực hiện tấn công vét cạn (Brute-force) hoặc Credential Stuffing.
- **Khắc phục**: Luôn trả về thông báo chung `"Invalid username or password"` (HTTP 401) và áp dụng Rate Limiting (HTTP 429) cho endpoint `POST /auth/login`.

---

## 3. Kết Luận
Báo cáo và file [`openapi.yaml`](./openapi.yaml) đã hoàn thiện việc chuẩn hóa bảo mật theo chuẩn bài học: phân định rõ AuthN (401) vs AuthZ (403), áp dụng 3 lớp kiểm tra quyền cho `GET /posts/{id}`, và phòng tránh các lỗ hổng OWASP API phổ biến, sẵn sàng làm cơ sở cài đặt Auth Service ở Buổi 07.
