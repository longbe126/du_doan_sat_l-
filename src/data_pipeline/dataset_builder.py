import pandas as pd
import numpy as np

def create_mock_dataset(n_samples=1000):
    """
    Tạo dữ liệu giả lập để kiểm thử ML pipeline theo cấu trúc bảng trong Đề cương (Mục 10.3).
    Bao gồm: Elevation, Slope, Aspect, Rainfall, Land Cover, Flow Accumulation, Label.
    """
    np.random.seed(42)
    
    elevation = np.random.uniform(10, 1500, n_samples)
    slope = np.random.uniform(0, 60, n_samples)
    aspect = np.random.uniform(0, 360, n_samples)
    rainfall = np.random.uniform(50, 400, n_samples)
    land_cover = np.random.choice(['Forest', 'Cropland', 'Urban', 'Bare'], n_samples)
    flow_acc = np.random.uniform(10, 5000, n_samples)
    
    # Tạo logic giả lập: Độ dốc cao + Mưa nhiều + Rừng thưa/đất trống -> Nguy cơ sạt lở cao
    risk_score = (slope / 60) * 0.4 + (rainfall / 400) * 0.4 + (elevation / 1500) * 0.2
    
    # Điều chỉnh mạo hiểm cho các loại bề mặt
    lc_risk = {'Forest': -0.1, 'Cropland': 0.1, 'Urban': 0.2, 'Bare': 0.3}
    risk_score += np.array([lc_risk[lc] for lc in land_cover])
    
    # Gán nhãn sạt lở (1) nếu rủi ro vượt ngưỡng 0.6, (0) nếu an toàn
    labels = (risk_score > 0.6).astype(int)
    
    df = pd.DataFrame({
        'Elevation': elevation,
        'Slope': slope,
        'Aspect': aspect,
        'Rainfall': rainfall,
        'Land_Cover': land_cover,
        'Flow_Accumulation': flow_acc,
        'Label': labels
    })
    return df

def preprocess_features(df):
    """Mã hóa các biến phân loại (One-hot encoding) và tách feature/label."""
    # Mã hóa cột Land_Cover thành các cột boolean
    df_encoded = pd.get_dummies(df, columns=['Land_Cover'], drop_first=True)
    X = df_encoded.drop(columns=['Label'])
    y = df_encoded['Label']
    return X, y

if __name__ == "__main__":
    print("--- Test Dataset Builder ---")
    df = create_mock_dataset(10)
    print("Mẫu dữ liệu:")
    print(df.head())
    print(f"\nPhân bố nhãn trên 10 mẫu: \n{df['Label'].value_counts()}")
