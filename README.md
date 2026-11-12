
# Hệ thống dự đoán nguy cơ sạt lở

Dự án nghiên cứu mô phỏng nguy cơ sạt lở tại khu vực Nam Trung Bộ bằng Streamlit, React Three Fiber và FastAPI.

## Chạy ứng dụng

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Với giao diện React:

```powershell
cd frontend
npm install
npm run build
cd ..
.venv\Scripts\python.exe run_app.py
```

## Mô hình

Huấn luyện lại mô hình:

```powershell
.venv\Scripts\python.exe app/core/train_models.py
```

Các kết quả mô hình được lưu trong `reports/evaluation.json`.

## Lưu ý dữ liệu

DEM, lớp phủ, lượng mưa, độ ẩm đất, các khu vực và sự kiện trong ứng dụng là dữ liệu mô phỏng phục vụ thử nghiệm. Các tên địa danh không đại diện cho kết quả quan trắc hoặc cảnh báo thực tế. Không sử dụng ứng dụng để ra quyết định an toàn mà chưa thay thế bằng dữ liệu GIS và quan trắc địa phương đã kiểm chứng.
