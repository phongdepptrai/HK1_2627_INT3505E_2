# Lab 4: Đặc tả RESTful API với OpenAPI Specification (OAS 3.0)

Thực hành viết đặc tả OpenAPI 3.0.3 (định dạng YAML) mô tả chuẩn hóa tài nguyên RESTful API, áp dụng kỹ thuật tái sử dụng schema (`$ref`), định danh hàm sinh mã (`operationId`), xử lý phản hồi lỗi chuẩn và khai báo cơ chế xác thực bảo mật (`securitySchemes`).

---

## 1. Bài 1: Đặc tả OpenAPI YAML cho Pet Store API

- **Tập tin đặc tả**: [`appB1.yaml`](./appB1.yaml) (hoặc [`openapi.yaml`](./openapi.yaml))
- **Chuẩn đặc tả**: OpenAPI 3.0.3
- **Base URL**: `http://localhost:5000/api/v1`

### 1.1. Các endpoint được khai báo

| Method | Endpoint | operationId | Mô tả | Request Body | Response thành công | Error Responses |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/pets` | `listPets` | Lấy danh sách thú cưng (hỗ trợ phân trang qua query `limit`) | N/A | `200 OK` (`Pets`) | `400`, `default` (`Error`) |
| `POST` | `/pets` | `createPets` | Thêm thú cưng mới vào cửa hàng | `NewPet` | `201 Created` (`Pet`) | `400`, `default` (`Error`) |
| `GET` | `/pets/{petId}` | `showPetById` | Xem thông tin chi tiết một thú cưng theo ID | N/A | `200 OK` (`Pet`) | `404`, `default` (`Error`) |
| `DELETE` | `/pets/{petId}` | `deletePet` | Xóa thú cưng khỏi hệ thống | N/A | `204 No Content` | `404`, `default` (`Error`) |
