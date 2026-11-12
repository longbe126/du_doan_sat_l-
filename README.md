# Hệ thống giám sát và mô phỏng nguy cơ sạt lở đất

Đồ án xây dựng một hệ thống thử nghiệm để minh họa cách kết hợp dữ liệu địa hình, dữ liệu mưa và học máy trong việc phân tích nguy cơ sạt lở. Hệ thống gồm bảng điều khiển Streamlit, giao diện web React hiển thị bản đồ 2D/địa hình 3D, dịch vụ API FastAPI và quy trình huấn luyện, đánh giá mô hình bằng scikit-learn và XGBoost.

> **Cảnh báo về dữ liệu:** Đây là sản phẩm nghiên cứu/mô phỏng, không phải hệ thống cảnh báo thiên tai vận hành thực tế. Địa hình, mưa, độ ẩm, lớp phủ, các điểm khu vực, sự kiện lịch sử và nhãn dùng để huấn luyện hiện được tạo theo quy tắc mô phỏng cố định. Tên địa danh chỉ dùng để minh họa, không xác nhận vị trí hay sự kiện quan trắc. Các điểm số không thể hiện xác suất hoặc kết luận địa chất đã được kiểm chứng. Không dùng kết quả để ra quyết định an toàn, sơ tán hay ứng phó khẩn cấp.

## Mục tiêu đồ án

- Tổ chức một quy trình minh họa từ sinh dữ liệu, huấn luyện và đánh giá mô hình đến hiển thị kết quả trên bản đồ.
- So sánh một mô hình tuyến tính với hai mô hình tổ hợp cây trên cùng bộ đặc trưng.
- Cho phép thay đổi cường độ mưa và mốc phân loại để quan sát cách điểm nguy cơ mô phỏng thay đổi theo thời gian.
- Cung cấp giao diện trực quan để xem địa hình, phân bố mức nguy cơ, các khu vực minh họa, diễn biến 24 giờ và báo cáo đánh giá mô hình.
- Tách phần tính toán Python khỏi giao diện React thông qua API FastAPI; đồng thời cung cấp giao diện nhiều trang thuần Streamlit.

## Chức năng chính

### Bảng điều khiển giám sát

- Hiển thị bản đồ lưới và địa hình mô phỏng, hỗ trợ chuyển giữa chế độ 2D và 3D ở giao diện React.
- Tổng hợp điểm nguy cơ, mức thấp/trung bình/cao, lượng mưa, khu vực có điểm cao và thay đổi so với mốc thời gian trước.
- Mô phỏng kịch bản mưa trong 24 giờ. Hệ số mưa tăng theo thời gian; người dùng có thể thay đổi cường độ kịch bản và các ngưỡng phân loại.
- Hiển thị chuỗi thời gian, thông tin khu vực và các mốc sự kiện được suy ra từ thay đổi trong mô phỏng.

### Tra cứu sự kiện

Trang lịch sử trình bày danh sách và thống kê sự kiện minh họa, có thể tìm kiếm, lọc theo nguyên nhân và sắp xếp theo thời gian, địa điểm hoặc độ cao. Dữ liệu sự kiện mặc định được sinh trong môi trường mô phỏng; API cũng có endpoint đọc tối đa 50 bản ghi từ SQLite `data/landslide.db` nếu cơ sở dữ liệu đó được cung cấp.

### Đánh giá mô hình

Trang đánh giá đọc báo cáo `reports/evaluation.json`, so sánh các chỉ số của mô hình, kiểm định chéo, ma trận nhầm lẫn, đường ROC, hiệu chuẩn và tầm quan trọng đặc trưng (nếu có trong báo cáo). Giao diện có cảnh báo khi bộ dữ liệu được đánh dấu là mô phỏng hoặc khi chưa có thông tin xác minh nguồn.

## Dữ liệu và mô hình

### Bộ dữ liệu và đầu vào

Script `scripts/generate_demo_data.py` tạo mặc định 5.000 dòng dữ liệu mô phỏng vào `data/processed/demo_dataset.csv`. Các đặc trưng được dùng trong mô hình gồm:

| Đặc trưng | Ý nghĩa |
| --- | --- |
| `slope_deg` | Độ dốc (độ) |
| `elevation_m` | Độ cao (mét) |
| `rainfall_mm` | Lượng mưa (mm) |
| `soil_moisture` | Độ ẩm đất |
| `landcover` | Nhóm lớp phủ đất |

Nhãn mục tiêu là `landslide` (0/1). Trong dữ liệu demo, nhãn được sinh xác suất từ một quy luật mô phỏng có nhiễu; đây không phải công thức địa chất đã được hiệu chứng. Cùng quy luật mô phỏng được dùng để tạo dữ liệu bản đồ đầu vào nhằm minh họa việc áp mô hình lên không gian.

Lưới bản đồ minh họa có kích thước 72 × 72, gồm 12 khu vực đặt tên để quan sát và 46 sự kiện mô phỏng. Dữ liệu cơ sở được tạo với seed cố định để có thể tái lập. Lưới nguy cơ sử dụng điểm dự đoán của mô hình; phần tổng hợp khu vực và ô lưới được dùng để trực quan hóa, không phải phân tích GIS thực địa.

### Huấn luyện và đánh giá

`app/core/train_models.py` huấn luyện ba mô hình:

1. Hồi quy logistic (`LogisticRegression`)
2. Rừng ngẫu nhiên (`RandomForestClassifier`)
3. XGBoost (`XGBClassifier`)

Quy trình tiền xử lý điền giá trị thiếu (trung vị cho dữ liệu số, giá trị phổ biến nhất cho dữ liệu phân loại), chuẩn hóa đặc trưng số và mã hóa one-hot đặc trưng phân loại. Dữ liệu được chia train/test theo tỷ lệ 80/20; mặc định dùng chia phân tầng và kiểm định chéo 5 phần. Nếu dữ liệu có cột nhóm không gian như `block_id`, `spatial_block` hoặc `group`, quy trình sẽ dùng nhóm đó để chia tập và kiểm định chéo theo khối nhằm hỗ trợ đánh giá tránh rò rỉ giữa các vùng.

Báo cáo bao gồm accuracy, precision, recall, F1, ROC-AUC, PR-AUC, Brier score và các dữ liệu phục vụ biểu đồ/kiểm định. Mô hình được chọn cho bảng điều khiển theo ROC-AUC trung bình trong kiểm định chéo. Các pipeline mô hình được lưu trong `models/`; báo cáo được lưu trong `reports/evaluation.json`.

## Kiến trúc

```text
scripts/generate_demo_data.py
          │
          ▼
data/processed/demo_dataset.csv ──► app/core/train_models.py
                                          │
                            models/*.pkl + reports/evaluation.json
                                          │
                 ┌────────────────────────┴────────────────────┐
                 ▼                                             ▼
       Ứng dụng Streamlit                          FastAPI (server/main.py)
       streamlit_app.py                             /api/*
                                                               │
                                                     Giao diện React + Three.js
```

### Các thành phần chính

- `streamlit_app.py`: điều hướng các trang Streamlit: tổng quan, lịch sử sạt lở và đánh giá AI.
- `app/main.py`, `app/pages/`: nội dung bảng điều khiển và các trang chức năng Streamlit.
- `app/core/data_engine.py`: tạo lưới địa hình/lớp phủ/mưa mô phỏng và tính điểm bằng mô hình đã huấn luyện.
- `app/core/train_models.py`: tiền xử lý, huấn luyện, kiểm định và xuất báo cáo.
- `app/core/model_loader.py`: nạp mô hình được chọn; tự gọi pipeline huấn luyện khi chưa có mô hình hoặc báo cáo phù hợp.
- `server/main.py`: API FastAPI cho dữ liệu nền, địa hình, mô phỏng, chuỗi 24 giờ, báo cáo mô hình và sự kiện SQLite.
- `frontend/`: ứng dụng React/TypeScript, Zustand quản lý trạng thái, Three.js/React Three Fiber hiển thị địa hình 3D.
- `data/processed/`, `models/`, `reports/`: dữ liệu demo, pipeline mô hình và báo cáo huấn luyện.

### API chính

| Phương thức | Endpoint | Nội dung |
| --- | --- | --- |
| `GET` | `/api/health` | Trạng thái API, tên mô hình, kích thước lưới và thông tin cơ sở dữ liệu |
| `GET` | `/api/base` | Khu vực, sự kiện mô phỏng, metadata và phạm vi tọa độ |
| `GET` | `/api/terrain` | Cao độ, độ dốc và tọa độ lưới cho bản đồ |
| `GET` | `/api/simulation` | Kết quả mô phỏng tại một giờ với các tham số kịch bản |
| `GET` | `/api/series` | Chuỗi kết quả mô phỏng từ giờ 0 đến giờ 24 |
| `GET` | `/api/models` | Báo cáo đánh giá mô hình |
| `GET` | `/api/database/events` | Tối đa 50 sự kiện SQLite nếu cơ sở dữ liệu tồn tại |

## Cài đặt và chạy

Yêu cầu: Python và Node.js/npm. Các lệnh dưới đây dùng PowerShell trên Windows.

### 1. Cài đặt môi trường Python

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Tạo dữ liệu demo và huấn luyện

Nếu chưa có `data/processed/demo_dataset.csv`, tạo dữ liệu trước:

```powershell
.\.venv\Scripts\python.exe scripts/generate_demo_data.py
```

Huấn luyện ba mô hình và tạo báo cáo:

```powershell
.\.venv\Scripts\python.exe app/core/train_models.py
```

### 3. Chạy ứng dụng Streamlit

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

### 4. Chạy giao diện React và API FastAPI

Build giao diện React trước để FastAPI phục vụ nội dung trong `frontend/dist`:

```powershell
cd frontend
npm install
npm run build
cd ..
.\.venv\Scripts\python.exe run_app.py
```

Ứng dụng React và API mặc định chạy tại <http://localhost:8000>. Có thể chạy frontend ở chế độ phát triển riêng bằng `cd frontend` rồi `npm run dev`; khi đó cần đảm bảo cấu hình API trong frontend trỏ tới backend đang chạy.

## Công nghệ sử dụng

- **Backend/ML:** Python, NumPy, pandas, scikit-learn, XGBoost, FastAPI, Uvicorn.
- **Giao diện phân tích:** Streamlit, Plotly.
- **Giao diện web:** React, TypeScript, Vite, Three.js, React Three Fiber, Zustand, Tailwind CSS.
- **Lưu trữ sự kiện tùy chọn:** SQLite.

## Giới hạn và hướng phát triển

Phiên bản hiện tại ưu tiên minh họa quy trình và tương tác giao diện trên dữ liệu tổng hợp. Muốn sử dụng cho nghiên cứu thực địa cần thay thế dữ liệu mô phỏng bằng DEM, mưa, độ ẩm, lớp phủ và hồ sơ sự kiện có nguồn gốc/độ phân giải/thời gian rõ ràng; kiểm tra chất lượng và đồng bộ hệ tọa độ; thiết kế kiểm định theo không gian và thời gian; hiệu chuẩn mô hình với chuyên gia; đồng thời bổ sung quy trình cập nhật, giám sát và đánh giá sai số. Khi chưa hoàn tất các bước đó, mọi kết quả chỉ có ý nghĩa thử nghiệm.
