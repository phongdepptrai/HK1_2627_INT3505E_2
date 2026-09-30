# Lab 3: Thiết kế RESTful API - Nền tảng Blog đơn giản

Tài liệu thiết kế cấu trúc RESTful API hoàn chỉnh cho nền tảng blog đơn giản và mã nguồn triển khai mẫu cho tài nguyên `/posts`.

---

## 1. Xác định resources trong miền (Domain Resources)

Dựa vào bài toán thực tế của nền tảng blog, các tài nguyên (resources) cốt lõi bao gồm:

1. **User (`users`)**: Người dùng của hệ thống (có thể là tác giả viết bài hoặc độc giả tương tác).
2. **Profile (`profiles`)**: Hồ sơ cá nhân của người dùng (tiểu sử/bio, ảnh đại diện/avatar, liên kết cá nhân,...).
3. **Post (`posts`)**: Bài viết do người dùng đăng tải (tiêu đề, nội dung, ngày tạo, tác giả).
4. **Comment (`comments`)**: Bình luận của người dùng trên từng bài viết cụ thể.
5. **Tag (`tags`)**: Thẻ phân loại/chủ đề gắn vào bài viết để dễ dàng tìm kiếm và nhóm nội dung.
6. **Follow (`followers` / `following`)**: Mối quan hệ theo dõi giữa người dùng và tác giả khác.

---

## 2. Phân loại Collection / Item / Sub-resource

Trong thiết kế RESTful API:
- **Collection**: Tập hợp danh sách các tài nguyên cùng loại.
- **Item**: Một tài nguyên cụ thể đơn lẻ (thường xác định bởi `{id}`).
- **Sub-resource**: Tài nguyên phụ thuộc, nằm trong ngữ cảnh của một tài nguyên cha.

| Loại tài nguyên | Endpoint URI mẫu | Ý nghĩa / Mô tả |
| :--- | :--- | :--- |
| **Collection** | `/users` | Danh sách toàn bộ người dùng |
| **Item** | `/users/{user_id}` | Thông tin chi tiết một người dùng cụ thể |
| **Sub-resource (Item)** | `/users/{user_id}/profile` | Hồ sơ cá nhân của người dùng `{user_id}` |
| **Collection** | `/posts` | Danh sách toàn bộ bài viết |
| **Item** | `/posts/{post_id}` | Chi tiết một bài viết cụ thể |
| **Sub-resource (Collection)** | `/posts/{post_id}/comments` | Danh sách bình luận thuộc bài viết `{post_id}` |
| **Sub-resource (Item)** | `/posts/{post_id}/comments/{comment_id}` | Một bình luận cụ thể của bài viết `{post_id}` |
| **Collection** | `/tags` | Danh sách toàn bộ các thẻ trong hệ thống |
| **Item** | `/tags/{tag_id}` | Chi tiết một thẻ cụ thể |
| **Sub-resource (Collection)** | `/posts/{post_id}/tags` | Danh sách thẻ gắn vào bài viết `{post_id}` |
| **Sub-resource (Item)** | `/posts/{post_id}/tags/{tag_id}` | Một thẻ cụ thể được gắn vào bài viết `{post_id}` |
| **Sub-resource (Collection)** | `/users/{user_id}/followers` | Danh sách người đang theo dõi `{user_id}` |
| **Sub-resource (Collection)** | `/users/{user_id}/following` | Danh sách các tác giả mà `{user_id}` đang theo dõi |
| **Sub-resource (Item)** | `/users/{user_id}/following/{target_user_id}` | Trạng thái theo dõi giữa `{user_id}` và `{target_user_id}` |

---

## 3. Sơ đồ cây endpoint và Quyết định version segment

### 3.1. Quyết định Version Segment

- **Lựa chọn**: Sử dụng **URI Path Versioning** với tiền tố `/api/v1` (ví dụ: `/api/v1/posts`).
- **Lý do lựa chọn**:
  - **Rõ ràng, trực quan**: Phiên bản hiển thị trực tiếp trên đường dẫn, dễ đọc hiểu cho người dùng và lập trình viên.
  - **Dễ định tuyến**: Thuận tiện cho các bộ cân bằng tải hoặc API Gateway (Nginx, Kong) phân luồng sang các phiên bản dịch vụ backend khác nhau.
  - **Dễ kiểm thử và tài liệu hóa**: Dễ dàng gọi qua lệnh `curl`, trình duyệt hoặc Swagger UI mà không cần can thiệp tùy biến header phức tạp.

### 3.2. Sơ đồ cây endpoint (Endpoint Tree)

```text
/api/v1
│
├── /users
│   ├── GET                          # Lấy danh sách tài khoản người dùng
│   ├── POST                         # Tạo tài khoản người dùng mới
│   └── /{user_id}
│       ├── GET                      # Lấy thông tin chi tiết một tài khoản người dùng
│       ├── PUT / PATCH              # Cập nhật thông tin tài khoản người dùng
│       ├── DELETE                   # Xóa tài khoản người dùng
│       ├── /profile
│       │   ├── GET                  # Lấy hồ sơ người dùng
│       │   └── PUT / PATCH          # Cập nhật hồ sơ người dùng
│       ├── /followers
│       │   └── GET                  # Lấy danh sách người theo dõi tài khoản này
│       └── /following
│           ├── GET                  # Lấy danh sách tài khoản mà user này đang theo dõi
│           └── /{target_user_id}
│               ├── PUT              # Follow tài khoản này
│               └── DELETE           # Unfollow tài khoản này
│
├── /posts
│   ├── GET                          # Lấy danh sách bài viết
│   ├── POST                         # Đăng bài viết mới
│   └── /{post_id}
│       ├── GET                      # Đọc chi tiết bài viết
│       ├── PUT                      # Cập nhật toàn bộ bài viết
│       ├── PATCH                    # Cập nhật một phần bài viết
│       ├── DELETE                   # Xóa bài viết
│       ├── /comments
│       │   ├── GET                  # Lấy danh sách bình luận của bài viết
│       │   └── POST                 # Thêm bình luận vào bài viết
│       │   └── /{comment_id}
│       │       ├── GET              # Chi tiết một bình luận
│       │       ├── PUT / PATCH      # Chỉnh sửa bình luận
│       │       └── DELETE           # Xóa bình luận
│       └── /tags
│           ├── GET                  # Lấy danh sách thẻ của bài viết
│           ├── POST                 # Gắn thẻ vào bài viết
│           └── /{tag_id}
│               └── DELETE           # Gỡ thẻ khỏi bài viết
│
└── /tags
    ├── GET                          # Lấy danh sách tất cả các thẻ
    ├── POST                         # Tạo thẻ mới
    └── /{tag_id}
        ├── GET                      # Chi tiết thẻ
        ├── PUT / PATCH              # Cập nhật thẻ
        └── DELETE                   # Xóa thẻ
```

---

## 4. Triển khai Flask routes cho collection `/posts`

Tập tin triển khai: [`appB1.py`](./appB1.py)

Mã nguồn được viết ngắn gọn, chuẩn RESTful, xử lý đầy đủ các mã trạng thái HTTP chuẩn:
- `200 OK`: Truy vấn hoặc cập nhật thành công.
- `201 Created`: Tạo bài viết mới thành công kèm header `Location: /posts/<id>`.
- `204 No Content`: Xóa bài viết thành công (body rỗng).
- `404 Not Found`: Không tìm thấy bài viết theo `id`.
- `415 Unsupported Media Type`: Khi request body không phải định dạng JSON.
- `422 Unprocessable Entity`: Khi thiếu các trường dữ liệu bắt buộc (`title`, `content`, `author_id`).

