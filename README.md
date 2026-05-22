# Course Registration Testing Project

Dự án **Course Registration Testing Project** là hệ thống đăng ký học phần được xây dựng phục vụ bài tập lớn môn **Kiểm thử phần mềm**.  
Mục tiêu của dự án là mô phỏng các nghiệp vụ cơ bản của hệ thống đăng ký môn học, đồng thời xây dựng bộ kiểm thử gồm **unit test**, **integration test**, **selenium smoke test** và tài liệu kiểm thử.

## Mục tiêu bài tập lớn

Dự án tập trung vào hai phần chính:

1. Phát triển hệ thống đăng ký học phần bằng Flask.
2. Thiết kế và thực thi kiểm thử phần mềm cho các chức năng chính của hệ thống.

Các nghiệp vụ chính bao gồm:

- Đăng nhập, đăng xuất theo vai trò.
- Phân quyền sinh viên và admin.
- Sinh viên xem danh sách lớp học phần.
- Sinh viên đăng ký học phần.
- Sinh viên hủy đăng ký học phần.
- Kiểm tra ràng buộc tín chỉ tối thiểu và tối đa.
- Kiểm tra môn tiên quyết.
- Kiểm tra trùng lịch học.
- Kiểm tra lớp học phần đã đủ số lượng.
- Kiểm tra thời gian đăng ký theo học kỳ/ngành.
- Admin quản lý lớp học phần.
- Kiểm thử tự động bằng pytest và selenium.

## Công nghệ sử dụng

- Python 3.11+
- Flask
- Flask-Login
- Flask-SQLAlchemy
- MySQL
- PyMySQL
- HTML, CSS, JavaScript
- Pytest
- Pytest-cov
- Selenium
- GitHub Actions

## Cấu trúc thư mục

```text
CourseRegistrationTestingProject/
│
├── app/
│   ├── repositories/          # Lớp truy vấn dữ liệu
│   ├── routes/                # Định nghĩa route cho main, auth, student, admin
│   ├── services/              # Xử lý nghiệp vụ
│   ├── static/                # CSS, JS, image
│   ├── templates/             # Giao diện HTML
│   ├── __init__.py            # Khởi tạo Flask app
│   ├── config.py              # Cấu hình hệ thống
│   ├── extensions.py          # Khởi tạo db, login_manager
│   ├── models.py              # Định nghĩa database models
│   └── utils.py               # Hàm tiện ích, phân quyền
││
├── tests/
│   ├── integration/           # Integration test cho route
│   ├── selenium/              # Selenium smoke test
│   ├── unit/                  # Unit test cho service/repository/app
│   └── conftest.py            # Cấu hình fixture cho pytest
│
├── .github/workflows/         # Cấu hình CI bằng GitHub Actions
├── .env.example               # File mẫu cấu hình biến môi trường
├── .gitignore
├── pytest.ini                 # Cấu hình pytest
├── requirements.txt           # Danh sách thư viện
├── run.py                     # File chạy app, init db, seed data
└── README.md
```

## Chức năng chính

### 1. Xác thực và phân quyền

- Đăng nhập bằng username và password.
- Phân quyền theo vai trò:
  - `STUDENT`
  - `ADMIN`
- Sinh viên chỉ được truy cập các trang dành cho sinh viên.
- Admin chỉ được truy cập trang quản lý.
- Người dùng đã đăng nhập quay lại trang login sẽ được điều hướng về dashboard phù hợp.
- Sau khi logout, hệ thống hạn chế hiển thị lại trang bảo vệ qua nút Back của trình duyệt.

### 2. Chức năng sinh viên

Sinh viên có thể:

- Xem dashboard cá nhân.
- Xem danh sách lớp học phần đang mở.
- Xem danh sách môn đã học.
- Đăng ký lớp học phần.
- Hủy đăng ký học phần.
- Xác nhận đăng ký học kỳ.

Các ràng buộc nghiệp vụ:

- Chỉ được đăng ký trong thời gian đăng ký hợp lệ.
- Không được đăng ký lớp đã đủ số lượng.
- Không được đăng ký lại lớp đã đăng ký.
- Không được đăng ký cùng một môn ở lớp khác.
- Không được đăng ký môn đã học hoàn thành.
- Không được đăng ký nếu thiếu môn tiên quyết.
- Không được đăng ký nếu bị trùng lịch học.
- Tổng số tín chỉ không được vượt quá 25.
- Khi xác nhận học kỳ, tổng số tín chỉ phải đạt tối thiểu 12.
- Không được hủy học phần nếu đã quá hạn hủy.
- Không được hủy học phần nếu đã có điểm giữa kỳ.

### 3. Chức năng admin

Admin có thể:

- Xem danh sách lớp học phần.
- Tạo lớp học phần mới.
- Cập nhật thông tin lớp học phần.
- Xóa lớp học phần.

Các ràng buộc nghiệp vụ:

- Chỉ admin mới được quản lý lớp học phần.
- Số sinh viên tối đa của mỗi lớp không vượt quá 50.
- Số sinh viên tối đa không được vượt quá sức chứa phòng học.
- Không được tạo hoặc cập nhật lớp có lịch học trùng phòng.
- Không được xóa lớp nếu đã có sinh viên đăng ký.
- Mã lớp học phần không được trùng.

## Cài đặt và chạy dự án

### 1. Clone project

```bash
git clone https://github.com/tranbaominh205/CourseRegistrationTestingProject.git
cd CourseRegistrationTestingProject
```

Nếu đang làm theo nhánh phát triển mới nhất:

```bash
git checkout dev
```

### 2. Tạo môi trường ảo

Trên Windows PowerShell:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Trên macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài thư viện

```bash
pip install -r requirements.txt
```

### 4. Cấu hình biến môi trường

Tạo file `.env` từ file mẫu:

```bash
copy .env.example .env
```

Hoặc trên macOS/Linux:

```bash
cp .env.example .env
```

Cấu hình ví dụ:

```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=change-me

DB_USERNAME=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=course_registration_db
```

### 5. Tạo database MySQL

Đăng nhập MySQL và tạo database:

```sql
CREATE DATABASE course_registration_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Khởi tạo bảng

```bash
flask --app run.py init-db
```

### 7. Thêm dữ liệu mẫu

```bash
flask --app run.py seed-data
```

### 8. Chạy ứng dụng

```bash
python run.py
```

Sau đó mở trình duyệt tại:

```text
http://127.0.0.1:5000
```

## Tài khoản mẫu

Sau khi chạy seed data, có thể sử dụng các tài khoản mẫu sau:

| Vai trò | Username | Password | Ghi chú |
|---|---|---|---|
| Admin | `admin01` | `123456` | Quản lý lớp học phần |
| Student | `student01` | `123456` | Sinh viên có dữ liệu đăng ký mẫu |
| Student | `student02` | `123456` | Sinh viên dùng để test thời gian đăng ký đã hết hạn |
| Student | `student03` | `123456` | Sinh viên dùng để test thời gian đăng ký chưa mở |
| Student locked | `locked01` | `123456` | Tài khoản bị khóa |

## Kiểm thử

Dự án sử dụng `pytest` để chạy kiểm thử tự động.

### Chạy toàn bộ test

```bash
pytest
```

### Chạy unit test

```bash
pytest tests/unit
```

### Chạy integration test

```bash
pytest tests/integration
```

### Chạy selenium smoke test

```bash
pytest tests/selenium
```

### Chạy test kèm đo coverage

```bash
pytest --cov=app
```

Hoặc xuất báo cáo coverage dạng terminal:

```bash
pytest --cov=app --cov-report=term-missing
```

## Phạm vi kiểm thử

### Unit test

Kiểm thử các hàm nghiệp vụ độc lập, ví dụ:

- Xác thực tài khoản.
- Tính tổng số tín chỉ đã đăng ký.
- Kiểm tra giới hạn tín chỉ.
- Kiểm tra trùng lịch học.
- Kiểm tra môn tiên quyết.
- Kiểm tra điều kiện hủy học phần.
- Kiểm tra nghiệp vụ admin khi tạo, sửa, xóa lớp học phần.

### Integration test

Kiểm thử route và luồng xử lý giữa nhiều thành phần, ví dụ:

- Login thành công/thất bại.
- Điều hướng sau login.
- Truy cập trang sinh viên.
- Đăng ký học phần qua route.
- Hủy học phần qua route.
- Truy cập trang admin.
- Tạo, sửa, xóa lớp học phần qua route.

### Selenium test

Kiểm thử nhanh giao diện trên trình duyệt thật, ví dụ:

- Mở trang login.
- Đăng nhập.
- Truy cập các trang chính.
- Kiểm tra giao diện cơ bản không bị lỗi nghiêm trọng.


## CI/CD

Dự án có cấu hình GitHub Actions để tự động:

- Cài đặt Python.
- Cài đặt dependencies từ `requirements.txt`.
- Chạy `pytest` khi push hoặc tạo pull request vào các nhánh chính.


## Trạng thái dự án

Dự án hiện đã có các thành phần chính:

- Flask application.
- Database models.
- Student module.
- Admin module.
- Authentication module.
- Unit test.
- Integration test.
- Selenium smoke test.
- GitHub Actions CI.
- File cấu hình môi trường mẫu.



## Tác giả

- Sinh viên thực hiện: Trần Bảo Minh
- Môn học: Kiểm thử phần mềm
- Đề tài: Hệ thống đăng ký học phần

## License

Dự án phục vụ mục đích học tập và làm bài tập lớn môn Kiểm thử phần mềm.