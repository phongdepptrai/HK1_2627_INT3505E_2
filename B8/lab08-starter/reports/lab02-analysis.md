# Lab 2 — Phân tích OpenAPI & Spectral Linting

## 1. Giải thích Custom Rule trong `.spectral.yml`

Custom rule `response-200-non-empty-schema`:
- **Mục đích**: Kiểm tra mọi response HTTP `200` có kiểu `application/json` trong file OpenAPI (`$.paths[*][*].responses['200'].content['application/json'].schema`) bắt buộc phải khai báo ít nhất 1 trường dữ liệu (`minProperties: 1`).
- **Trường hợp bắt được**:
  - Endpoint trả về `200 OK` nhưng khai báo `schema: {}` hoặc `schema: { type: object }` không có `properties`, hoặc `properties: {}` (0 trường).
  - Endpoint trả về mảng (`type: array`) nhưng `items` không có `properties` hoặc `items.properties` rỗng.
  - Giúp phát hiện sớm các đặc tả API thiếu chi tiết hợp đồng dữ liệu (contract-first gap) trước khi sinh code hoặc chia sẻ cho team frontend/QA.

Ngoài ra `.spectral.yml` còn có 2 rule đối chiếu quy ước thiết kế của project:
- `no-204-response-body`: Chặn các response `204 No Content` khai báo `content` body (vi phạm chuẩn HTTP RFC 9110).
- `book-year-integer`: Đảm bảo `Book.year` sử dụng kiểu `integer` khớp với model SQLAlchemy (`db.Integer`).

---

## 2. Câu hỏi phân tích

> **Câu hỏi:** Nếu file spec đã hợp lệ (Spectral pass) nhưng code Flask thực tế lại trả về sai field, loại test nào sẽ bắt được lỗi này và bạn sẽ viết test như thế nào?

### Trả lời:

1. **Nguyên nhân Spectral không bắt được:**
   - **Spectral** là công cụ **static linting** chạy trên file đặc tả `openapi.yaml`. Nó chỉ kiểm tra cú pháp OpenAPI 3.x và các quy tắc thiết kế trên tài liệu YAML, hoàn toàn **không chạy ứng dụng Flask** và **không đối chiếu JSON response thực tế**.

2. **Loại test bắt được lỗi này:**
   - **Contract Test / Schema Validation Integration Test** (kiểm thử hợp đồng API tự động bằng `pytest` + `jsonschema` hoặc công cụ contract-testing như `Schemathesis`, `openapi-core`, `Dredd`).
   - Loại test này gọi trực tiếp vào các endpoint Flask (qua `test_client` hoặc HTTP thực), lấy JSON response thực tế và kiểm định nó khớp 100% với JSON Schema trích xuất từ `openapi.yaml` (đặc biệt với `additionalProperties: false` và `required`).

3. **Cách viết test (ví dụ với `pytest` + `jsonschema` trên Books API):**
   ```python
   import copy
   from jsonschema import validate
   from tools import get_book_schema

   def test_get_book_matches_openapi_contract(client, sample_book):
       resp = client.get(f"/books/{sample_book}")
       assert resp.status_code == 200

       schema = copy.deepcopy(get_book_schema())
       for prop in schema.get("properties", {}).values():
           if prop.pop("nullable", False) and isinstance(prop.get("type"), str):
               prop["type"] = [prop["type"], "null"]

       # Fails immediately if Flask returns wrong field name, wrong data type,
       # misses a required field, or leaks an extra unexpected field.
       validate(instance=resp.get_json(), schema=schema)
   ```
   Nếu Flask trả về sai tên trường (ví dụ `book_title` thay vì `title`), sai kiểu dữ liệu (`"2021"` thay vì `2021`), hoặc rò rỉ thêm field lạ (`password_hash`), hàm `jsonschema.validate()` sẽ ném ra `ValidationError` và đánh dấu test FAIL ngay lập tức trong CI.
