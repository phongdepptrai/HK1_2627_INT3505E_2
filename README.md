# Kiến trúc Hướng Dịch vụ (INT3505E)

> **Môn học**: Kiến trúc Hướng Dịch vụ (Service-Oriented Architecture)  
> **Lớp học phần**: INT3505E - Học kỳ 1, Năm học 2026 - 2027  
> **Đơn vị**: Trường Đại học Công nghệ - Đại học Quốc gia Hà Nội (VNU - UET)

Kho lưu trữ chứa toàn bộ mã nguồn, cấu hình và báo cáo thực hành xây dựng các dịch vụ Web theo phong cách kiến trúc RESTful API với **Python 3.12** và framework **Flask**.

---

## Cấu trúc thư mục dự án

```text
HK1_2627_INT3505E_2/
├── B1/                                # Lab 1: Cơ bản về RESTful API với Flask
│   ├── README.md                      # Báo cáo chi tiết và ảnh minh họa Lab 1
│   ├── appB1.py                       # Bài 1: Hello API (GET /)
│   ├── appB2.py                       # Bài 2: Health check & Echo API
│   ├── appB3.py                       # Bài 3: Quản lý học sinh (UUID & validation)
│   ├── appB4.py                       # Bài 4: Tìm kiếm sách (limit & query q)
│   ├── appB5.py                       # Bài 5: Xóa đơn hàng & xử lý xung đột 409
│   └── appB6.py                       # Bài 6: Full CRUD quản lý sách
│
├── B2/                                # Lab 2: Chuẩn hóa RESTful API, Phân trang & HATEOAS
    ├── README.md                      # Báo cáo chi tiết và ảnh minh họa Lab 2
    ├── appB1.py                       # Bài 1: List & Create (GET/POST với Location header)
    ├── appB2.py                       # Bài 2: PUT (thay thế) vs PATCH (cập nhật) & DELETE
    └── appB3.py                       # Bài 3: Phân trang nâng cao, Lọc & HATEOAS links
```

---

## Tổng quan các Lab thực hành

| Thư mục | Chủ đề chính | Các khái niệm trọng tâm | Báo cáo chi tiết |
| :--- | :--- | :--- | :--- |
| [**B1**](./B1) | **Nhập môn RESTful API** | Routing, HTTP Methods (`GET`, `POST`, `PUT`, `DELETE`), Status Codes (`200`, `201`, `204`, `400`, `404`, `409`), UUID generation. | [Xem README Lab 1](./B1/README.md) |
| [**B2**](./B2) | **Chuẩn hóa API & HATEOAS** | Chuẩn RESTful, phân biệt `PUT` (Full replacement) và `PATCH` (Partial update), Header `Location` & `Cache-Control`, Pagination (`page`, `size`), HATEOAS (`_links`). | [Xem README Lab 2](./B2/README.md) |

---

## Hướng dẫn cài đặt và chạy thử nghiệm

### 1. Kích hoạt môi trường ảo (Virtual Environment)
Mở PowerShell tại thư mục gốc của dự án:
```powershell
# Kích hoạt venv có sẵn
.\.venv\Scripts\Activate.ps1
```

*(Nếu chưa cài thư viện Flask):*
```powershell
pip install Flask
```

---

### 2. Chạy ứng dụng

#### Chạy bài trong Lab 1:
```powershell
python B1/appB6.py
```

#### Chạy bài trong Lab 2:
```powershell
python B2/appB3.py
```

---

### 3. Kiểm thử API bằng `curl`

Dưới đây là một số lệnh mẫu để kiểm thử các API:

```powershell
# 1. Lấy danh sách phân trang (mặc định page 1, size 20)
curl.exe -i "http://localhost:5000/books"

# 2. Phân trang với kích thước tùy chỉnh
curl.exe "http://localhost:5000/books?page=2&size=10"

# 3. Lọc theo tác giả
curl.exe "http://localhost:5000/books?author=Orwell"

# 4. Tìm kiếm từ khóa theo tiêu đề
curl.exe "http://localhost:5000/books?q=clean"

# 5. Cập nhật một phần bằng PATCH
curl.exe --% -X PATCH http://localhost:5000/books/1 -H "Content-Type: application/json" -d "{\"price\": 75}"

# 6. Xóa sách
curl.exe -i -X DELETE http://localhost:5000/books/1
```

---

## Báo cáo hình ảnh & Bằng chứng thực nghiệm

Mỗi thư mục lab đều đi kèm tài liệu hướng dẫn và bằng chứng chạy console chi tiết:
- [Tài liệu và hình ảnh Lab 1 (B1)](./B1/README.md)
- [Tài liệu và hình ảnh Lab 2 (B2)](./B2/README.md)
