import os
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
import warnings

# Bỏ qua một số cảnh báo không quan trọng của rasterio/pyproj
warnings.filterwarnings("ignore", category=UserWarning)

class GISProcessor:
    def __init__(self, target_crs="EPSG:32648"):
        """
        Khởi tạo GIS Processor.
        Mặc định sử dụng WGS 84 / UTM zone 48N (EPSG:32648) cho khu vực Quảng Nam.
        """
        self.target_crs = CRS.from_string(target_crs)
        print(f"GISProcessor initialized with Target CRS: {self.target_crs}")

    def reproject_raster(self, input_path, output_path):
        """Chuyển đổi hệ tọa độ của file Raster về target CRS."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Không tìm thấy file: {input_path}")
            
        with rasterio.open(input_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, self.target_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': self.target_crs,
                'transform': transform,
                'width': width,
                'height': height
            })

            with rasterio.open(output_path, 'w', **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=self.target_crs,
                        resampling=Resampling.nearest)
        print(f"[XONG] Đã chuyển đổi hệ tọa độ (Reproject) raster lưu tại: {output_path}")

    def calculate_slope(self, dem_path, output_path):
        """Tính toán độ dốc (Slope) từ DEM, đơn vị: độ."""
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            # Kích thước pixel (độ phân giải)
            dx, dy = src.transform[0], -src.transform[4]
            
            # Tính gradient theo x và y
            x, y = np.gradient(dem, dx, dy)
            
            # Tính slope
            slope = np.pi/2. - np.arctan(np.sqrt(x*x + y*y))
            slope_deg = np.degrees(slope)

            kwargs = src.meta.copy()
            kwargs.update(dtype=rasterio.float32)
            
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                dst.write(slope_deg.astype(rasterio.float32), 1)
        print(f"[XONG] Đã tính toán Slope và lưu tại: {output_path}")

    def calculate_aspect(self, dem_path, output_path):
        """Tính toán hướng dốc (Aspect) từ DEM, đơn vị: độ (0-360)."""
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            dx, dy = src.transform[0], -src.transform[4]
            
            x, y = np.gradient(dem, dx, dy)
            aspect = np.arctan2(-x, y)
            aspect_deg = np.degrees(aspect)
            
            # Chuyển về hệ quy chiếu 0-360 độ
            aspect_deg = np.where(aspect_deg < 0, 360 + aspect_deg, aspect_deg)

            kwargs = src.meta.copy()
            kwargs.update(dtype=rasterio.float32)
            
            with rasterio.open(output_path, 'w', **kwargs) as dst:
                dst.write(aspect_deg.astype(rasterio.float32), 1)
        print(f"[XONG] Đã tính toán Aspect và lưu tại: {output_path}")

if __name__ == "__main__":
    print("Test GISProcessor init...")
    processor = GISProcessor()
    # Các hàm này sẽ được gọi ở bước tiếp theo khi có dữ liệu thật hoặc giả lập
    # processor.reproject_raster('data/raw/dem.tif', 'data/processed/dem_epsg32648.tif')
    # processor.calculate_slope('data/processed/dem_epsg32648.tif', 'data/processed/slope.tif')
    # processor.calculate_aspect('data/processed/dem_epsg32648.tif', 'data/processed/aspect.tif')
