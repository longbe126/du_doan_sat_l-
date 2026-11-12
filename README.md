# Hệ thống giám sát và mô phỏng nguy cơ sạt lở đất

Đồ án xây dựng một ứng dụng Streamlit để minh họa cách kết hợp dữ liệu địa hình, dữ liệu mưa và học máy trong việc phân tích nguy cơ sạt lở. Ứng dụng có các trang tổng quan, lịch sử sự kiện và đánh giá mô hình; phần xử lý dữ liệu và huấn luyện được viết bằng Python, scikit-learn và XGBoost.

**Cách chạy ứng dụng:** dùng Streamlit thông qua `streamlit_app.py`.

> **Cảnh báo về dữ liệu:** Đây là sản phẩm nghiên cứu/mô phỏng, không phải hệ thống cảnh báo thiên tai vận hành thực tế. Địa hình, mưa, độ ẩm, lớp phủ, các điểm khu vực, sự kiện lịch sử và nhãn dùng để huấn luyện hiện được tạo theo quy tắc mô phỏng cố định. Tên địa danh chỉ dùng để minh họa, không xác nhận vị trí hay sự kiện quan trắc. Các điểm số không thể hiện xác suất hoặc kết luận địa chất đã được kiểm chứng. Không dùng kết quả để ra quyết định an toàn, sơ tán hay ứng phó khẩn cấp.

## Mục tiêu đồ án

- Tổ chức một quy trình minh họa từ sinh dữ liệu, huấn luyện và đánh giá mô hình đến hiển thị kết quả trên bản đồ.
- So sánh một mô hình tuyến tính với hai mô hình tổ hợp cây trên cùng bộ đặc trưng.
- Cho phép thay đổi cường độ mưa và mốc phân loại để quan sát cách điểm nguy cơ mô phỏng thay đổi theo thời gian.
- Cung cấp giao diện Streamlit nhiều trang để xem địa hình, phân bố mức nguy cơ, các khu vực minh họa, diễn biến 24 giờ và báo cáo đánh giá mô hình.
- Giữ luồng chạy và thao tác trong một ứng dụng Streamlit duy nhất.

## Luồng hoạt động tổng thể

```text
Sinh dữ liệu demo (hoặc nạp CSV đúng schema)
        ↓
Kiểm tra cột, nhãn và chia train/test
        ↓
Tiền xử lý + huấn luyện 3 mô hình + kiểm định chéo
        ↓
Lưu các pipeline .pkl và báo cáo evaluation.json
        ↓
Khởi động ứng dụng, nạp mô hình được chọn và tạo lưới địa hình mô phỏng
        ↓
Người dùng chọn giờ / cường độ mưa / ngưỡng
        ↓
Tạo đặc trưng cho từng ô → mô hình chấm điểm → tổng hợp thành khu vực và lớp bản đồ
        ↓
Hiển thị bản đồ, chỉ số, biểu đồ và sự kiện suy ra từ kịch bản
```

### Diễn giải từng bước

1. **Tạo dữ liệu:** `scripts/generate_demo_data.py` sinh bảng dữ liệu demo có nhãn nhị phân. Script dùng seed cố định để chạy lại cho kết quả tái lập.
2. **Huấn luyện:** `app/core/train_models.py` kiểm tra schema, tách đặc trưng/nhãn, tiền xử lý trong pipeline và huấn luyện ba bộ phân loại. Mỗi pipeline được đánh giá trên tập test và bằng kiểm định chéo.
3. **Chọn mô hình:** hệ thống chọn mô hình có ROC-AUC trung bình kiểm định chéo cao nhất, lưu báo cáo và pipeline trong `reports/` và `models/`.
4. **Khởi động ứng dụng:** `app/core/model_loader.py` nạp mô hình được chọn. Nếu thiếu báo cáo hoặc file mô hình tương ứng, loader gọi lại bước huấn luyện; vì vậy CSV dữ liệu cần tồn tại trước.
5. **Tạo bản đồ nền:** `app/core/data_engine.py` tạo lưới 72 × 72 gồm cao độ, độ dốc, lượng mưa nền, độ ẩm và lớp phủ. Các giá trị là dữ liệu mô phỏng có seed cố định.
6. **Chạy kịch bản:** mỗi lần người dùng chọn giờ hoặc điều chỉnh tham số, ứng dụng thay đổi lượng mưa đầu vào, chạy mô hình trên các ô lưới, sau đó tổng hợp điểm và phân loại theo ngưỡng.
7. **Trình bày kết quả:** các trang Streamlit gọi trực tiếp những module Python dùng chung để hiển thị bản đồ, chỉ số, biểu đồ và sự kiện của kịch bản.

## Chức năng chính

### Trang tổng quan giám sát

- Hiển thị bản đồ lưới và địa hình mô phỏng trong giao diện Streamlit.
- Tổng hợp điểm nguy cơ, mức thấp/trung bình/cao, lượng mưa, khu vực có điểm cao và thay đổi so với mốc thời gian trước.
- Mô phỏng kịch bản mưa trong 24 giờ. Hệ số mưa tăng theo thời gian; người dùng có thể thay đổi cường độ kịch bản và các ngưỡng phân loại.
- Hiển thị chuỗi thời gian, thông tin khu vực và các mốc sự kiện được suy ra từ thay đổi trong mô phỏng.

### Tra cứu sự kiện

Trang lịch sử trình bày danh sách và thống kê sự kiện, có thể tìm kiếm, lọc theo nguyên nhân và sắp xếp theo thời gian, địa điểm hoặc độ cao. Khi có `data/landslide.db`, trang đọc sự kiện trực tiếp từ SQLite; nếu không có dữ liệu phù hợp, trang dùng bộ sự kiện mô phỏng để minh họa.

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

### Thuật toán tạo nhãn và chấm điểm

**Lưu ý:** công thức dưới đây chỉ tạo nên thế giới dữ liệu mô phỏng của đồ án. Đây không phải mô hình vật lý, công thức địa kỹ thuật hay kết quả nghiên cứu đã được xác nhận.

Trong script sinh dữ liệu demo, một điểm tuyến tính được tính từ các đặc trưng:

```text
z = -4
    + 0.075 × độ_dốc
    + 0.006 × lượng_mưa
    + 1.2 × độ_ẩm_đất
    + 0.0002 × độ_cao
    + 0.8 × I(lớp_phủ = đất_trống)
    + 0.25 × I(lớp_phủ = nông_nghiệp)
    - 0.3 × I(lớp_phủ = rừng)
```

`I(điều kiện)` bằng 1 nếu điều kiện đúng, ngược lại bằng 0. Sau đó generator cộng nhiễu Gaussian với độ lệch chuẩn 0.8, chuyển điểm qua hàm sigmoid để lấy xác suất mô phỏng và rút nhãn 0/1 theo xác suất đó. Cách làm này tạo ra một bài toán có quy luật để kiểm thử pipeline; vì mô hình được huấn luyện trên dữ liệu do chính quy luật giả lập sinh ra, kết quả tốt trên tập demo không chứng minh khả năng dự báo ngoài thực tế.

Khi chạy bản đồ, mô hình được chọn nhận năm đặc trưng của từng ô và trả về đầu ra lớp dương qua `predict_proba`. Các đầu ra này được dùng làm **điểm nguy cơ mô phỏng**:

- Lưới đầu vào có 72 × 72 ô. Để hiển thị lớp lưới gọn hơn, mỗi khối 4 × 4 ô được lấy trung bình, tạo lưới tổng hợp 18 × 18.
- Điểm của một khu vực minh họa là trung bình đầu ra trên cửa sổ 5 × 5 ô quanh tọa độ khu vực.
- Hai ngưỡng do người dùng đặt trên giao diện chia điểm thành mức thấp, trung bình và cao. Đây là nhãn trực quan theo ngưỡng cấu hình, không phải cấp cảnh báo được cơ quan chuyên môn ban hành.
- Trong kịch bản 24 giờ, hệ số nhân mưa tại giờ `h` được tính theo `r(h) = 0.30 + 0.70 × (h / 24)^1.3`, với `h` từ 0 đến 24. Mưa nền tại mỗi ô được nhân với hệ số kịch bản và đầu vào mưa là biến đổi chính trong mô phỏng; các lớp đặc trưng nền khác được giữ nguyên.
- So sánh kết quả hai giờ liên tiếp để tạo chênh lệch điểm, phát hiện đổi mức và ghi nhận các mốc vượt ngưỡng mưa. Đây là sự kiện của kịch bản, không phải cảnh báo thời tiết trực tiếp.

### Đọc các chỉ số đánh giá

- **Precision:** trong các trường hợp mô hình gán nhãn sạt lở, tỷ lệ được gán đúng.
- **Recall:** trong các trường hợp sạt lở của tập đánh giá, tỷ lệ mô hình phát hiện được.
- **F1:** trung bình điều hòa giữa precision và recall.
- **ROC-AUC:** khả năng xếp hạng lớp dương cao hơn lớp âm trên các ngưỡng phân loại.
- **PR-AUC / Average Precision:** chất lượng precision-recall, hữu ích khi hai lớp mất cân bằng.
- **Brier score:** sai số bình phương giữa đầu ra xác suất và nhãn; thấp hơn thường tốt hơn, nhưng chỉ có ý nghĩa khi dữ liệu và xác suất được hiệu chuẩn phù hợp.

Các chỉ số hiện phản ánh hiệu năng trên tập demo và cách chia tập được ghi trong báo cáo. Có một giới hạn cần lưu ý khi đọc kết quả hiện tại: code tạo holdout 80/20 nhưng gọi `cross_validate` trên toàn bộ `X, y`, tức các dòng thuộc holdout cũng tham gia các vòng kiểm định chéo dùng để chọn mô hình. Chúng không được dùng để fit pipeline cuối trên train, nhưng holdout không còn hoàn toàn độc lập với bước chọn mô hình; vì vậy nên xem các chỉ số này là kết quả tham khảo, không phải ước lượng cuối cùng không thiên lệch. Để đánh giá nghiêm ngặt hơn, cần tách riêng tập test cuối cùng khỏi mọi bước lựa chọn mô hình/siêu tham số hoặc dùng quy trình nested cross-validation. Bộ dữ liệu demo hiện không có nhóm không gian, nên mặc định dùng chia phân tầng ngẫu nhiên; các điểm có liên hệ không gian không được giữ tách biệt giữa train và test. Code hỗ trợ chia theo `block_id`, `spatial_block` hoặc `group` khi các cột đó có trong dữ liệu, nhưng khả năng này chưa đồng nghĩa với việc đã có kiểm định không gian trên dữ liệu thực.

## Kiến trúc ứng dụng Streamlit

```text
scripts/generate_demo_data.py
          │
          ▼
data/processed/demo_dataset.csv ──► app/core/train_models.py
                                          │
                            models/*.pkl + reports/evaluation.json
                                          │
                                          ▼
                              streamlit_app.py
                               ┌──────┼──────┐
                               ▼      ▼      ▼
                           Tổng quan Lịch sử Đánh giá AI
                               │
                               ▼
                  app/core/data_engine.py
                  tính toán và tạo dữ liệu bản đồ
```

### Các thành phần chính

- `streamlit_app.py`: entry point duy nhất cần dùng để chạy ứng dụng Streamlit; điều hướng các trang tổng quan, lịch sử sạt lở và đánh giá AI.
- `app/main.py`, `app/pages/`: nội dung trang tổng quan và các trang chức năng Streamlit.
- `app/core/data_engine.py`: tạo lưới địa hình/lớp phủ/mưa mô phỏng và tính điểm bằng mô hình đã huấn luyện.
- `app/core/train_models.py`: tiền xử lý, huấn luyện, kiểm định và xuất báo cáo.
- `app/core/model_loader.py`: nạp mô hình được chọn; tự gọi pipeline huấn luyện khi chưa có mô hình hoặc báo cáo phù hợp.
- `app/components/`: các thành phần giao diện và trực quan hóa dùng trong ứng dụng Streamlit.
- `data/processed/`, `models/`, `reports/`: dữ liệu demo, pipeline mô hình và báo cáo huấn luyện.

## Cài đặt và chạy

Yêu cầu: Python. Các lệnh dưới đây dùng PowerShell trên Windows.

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

## Công nghệ sử dụng

- **Ứng dụng:** Streamlit, Python.
- **Xử lý dữ liệu và học máy:** NumPy, pandas, scikit-learn, XGBoost.
- **Biểu đồ:** Plotly.
- **Lưu trữ sự kiện tùy chọn:** SQLite.

## Mức độ hoàn thiện hiện tại

**Đánh giá tổng quát: nguyên mẫu chức năng / proof of concept (PoC), phù hợp trình diễn và kiểm thử quy trình; chưa phải sản phẩm thử nghiệm hiện trường hoặc hệ thống cảnh báo vận hành.**

| Hạng mục | Trạng thái hiện tại |
| --- | --- |
| Luồng sinh dữ liệu, huấn luyện, so sánh và lưu mô hình | Có thể chạy end-to-end trên bộ dữ liệu tổng hợp |
| Giao diện theo dõi và kịch bản mưa | Ứng dụng Streamlit nhiều trang; thể hiện kết quả mô hình trên dữ liệu mô phỏng |
| Đánh giá mô hình | Có tập holdout, kiểm định chéo và nhiều chỉ số; cấu hình chia theo không gian chỉ được kích hoạt khi dữ liệu có cột nhóm |
| Dữ liệu thực địa đã xác minh | Chưa có trong luồng demo hiện tại |
| Dự báo thời tiết / cảm biến thời gian thực | Chưa tích hợp; kịch bản mưa là tham số do người dùng đặt |
| Kiểm định hiệu quả cảnh báo ngoài thực tế | Chưa thể kết luận từ dữ liệu tổng hợp |
| Sẵn sàng cho quyết định an toàn hoặc ứng phó | Chưa; không sử dụng cho mục đích này |

### Những việc cần làm để tiến tới thử nghiệm thực địa

1. Thu thập dữ liệu sạt lở có nguồn, thời gian, tọa độ và định nghĩa nhãn được chuyên gia xác nhận; ghi rõ sai số và dữ liệu thiếu.
2. Thay thế các lớp nền mô phỏng bằng DEM, độ dốc, lớp phủ, mưa và độ ẩm có nguồn gốc/độ phân giải phù hợp; đồng bộ hệ tọa độ và đơn vị đo.
3. Thiết kế tập kiểm tra theo khu vực và theo thời gian, bảo đảm không để dữ liệu gần nhau hoặc cùng một sự kiện lọt đồng thời vào train và test.
4. So sánh với baseline đơn giản, hiệu chuẩn xác suất, phân tích sai số theo địa bàn/điều kiện và nhờ chuyên gia địa chất đánh giá ngưỡng.
5. Thử nghiệm thận trọng ở phạm vi nhỏ, có đối chiếu dữ liệu độc lập và quy trình con người xác nhận trước mọi thông báo.
6. Trước khi vận hành cần bổ sung bảo mật, kiểm soát truy cập, logging/monitoring, quản lý phiên bản dữ liệu/mô hình, sao lưu và quy trình xử lý khi dịch vụ hoặc dữ liệu đầu vào lỗi.

## Giới hạn và hướng phát triển

Phiên bản hiện tại ưu tiên minh họa quy trình và tương tác giao diện trên dữ liệu tổng hợp. Muốn sử dụng cho nghiên cứu thực địa cần thay thế dữ liệu mô phỏng bằng DEM, mưa, độ ẩm, lớp phủ và hồ sơ sự kiện có nguồn gốc/độ phân giải/thời gian rõ ràng; kiểm tra chất lượng và đồng bộ hệ tọa độ; thiết kế kiểm định theo không gian và thời gian; hiệu chuẩn mô hình với chuyên gia; đồng thời bổ sung quy trình cập nhật, giám sát và đánh giá sai số. Khi chưa hoàn tất các bước đó, mọi kết quả chỉ có ý nghĩa thử nghiệm.
