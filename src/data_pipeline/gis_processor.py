import os
import warnings
import numpy as np

try:
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.crs import CRS
except ImportError:  # Cho phép import module ngay cả khi môi trường chưa cài rasterio
    rasterio = None
    CRS = None

# Bỏ qua một số cảnh báo không quan trọng của rasterio/pyproj
warnings.filterwarnings("ignore", category=UserWarning)


class GISProcessor:
    def __init__(self, target_crs: str = "EPSG:32648"):
        """
        Khởi tạo GIS Processor.
        Mặc định sử dụng WGS 84 / UTM zone 48N (EPSG:32648) cho khu vực Quảng Nam.
        """
        self.target_crs_str = target_crs
        self.target_crs = CRS.from_string(target_crs) if CRS is not None else target_crs
        print(f"GISProcessor initialized with Target CRS: {self.target_crs}")

    def _require_rasterio(self):
        if rasterio is None:
            raise RuntimeError("Thư viện 'rasterio' chưa được cài đặt. Hãy chạy: pip install rasterio")

    def reproject_raster(self, input_path: str, output_path: str, resampling_method: str = "bilinear"):
        """Chuyển đổi hệ tọa độ của file Raster về target CRS."""
        self._require_rasterio()
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Không tìm thấy file: {input_path}")

        resampling_map = {
            "nearest": Resampling.nearest,
            "bilinear": Resampling.bilinear,
            "cubic": Resampling.cubic,
        }
        resample_alg = resampling_map.get(resampling_method, Resampling.bilinear)

        with rasterio.open(input_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, self.target_crs, src.width, src.height, *src.bounds
            )
            kwargs = src.meta.copy()
            kwargs.update({
                "crs": self.target_crs,
                "transform": transform,
                "width": width,
                "height": height,
            })

            with rasterio.open(output_path, "w", **kwargs) as dst:
                for i in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, i),
                        destination=rasterio.band(dst, i),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=transform,
                        dst_crs=self.target_crs,
                        resampling=resample_alg,
                    )
        print(f"[XONG] Đã chuyển đổi hệ tọa độ (Reproject) raster lưu tại: {output_path}")

    @staticmethod
    def compute_slope_from_array(dem: np.ndarray, dx: float, dy: float) -> np.ndarray:
        """
        Tính độ dốc (Slope) chuẩn địa kỹ thuật từ mảng DEM 2D, đơn vị: độ (0° - 90°).
        Lưu ý: Trong mảng 2D (rows, cols), trục 0 là phương Bắc-Nam (dy), trục 1 là phương Đông-Tây (dx).
        Công thức chuẩn: slope = arctan(sqrt((dz/dx)^2 + (dz/dy)^2)).
        """
        dem_f = np.asarray(dem, dtype=np.float64)
        dz_dy, dz_dx = np.gradient(dem_f, float(dy), float(dx))
        slope_rad = np.arctan(np.hypot(dz_dx, dz_dy))
        return np.degrees(slope_rad).astype(np.float32)

    @staticmethod
    def compute_aspect_from_array(dem: np.ndarray, dx: float, dy: float) -> np.ndarray:
        """
        Tính hướng dốc (Aspect) chuẩn GIS từ mảng DEM 2D, đơn vị: độ (0° - 360° theo chiều kim đồng hồ từ hướng Bắc).
        Vùng bằng phẳng (độ dốc ~ 0) được gán giá trị -1.0.
        """
        dem_f = np.asarray(dem, dtype=np.float64)
        dz_dy, dz_dx = np.gradient(dem_f, float(dy), float(dx))
        # Trong hệ tọa độ ảnh raster: chỉ số hàng tăng từ Bắc xuống Nam nên vector hướng Bắc là -dz_dy
        aspect_rad = np.arctan2(dz_dx, -dz_dy)
        aspect_deg = np.mod(np.degrees(aspect_rad), 360.0)
        flat_mask = np.hypot(dz_dx, dz_dy) < 1e-6
        aspect_deg = np.where(flat_mask, -1.0, aspect_deg)
        return aspect_deg.astype(np.float32)

    def calculate_slope(self, dem_path: str, output_path: str):
        """Tính toán độ dốc (Slope) từ file DEM GeoTIFF, đơn vị: độ."""
        self._require_rasterio()
        with rasterio.open(dem_path) as src:
            dem = src.read(1, masked=True).filled(np.nan)
            dx = abs(float(src.transform[0]))
            dy = abs(float(src.transform[4]))

            slope_deg = self.compute_slope_from_array(dem, dx=dx, dy=dy)

            kwargs = src.meta.copy()
            kwargs.update(dtype=rasterio.float32, nodata=np.nan)

            with rasterio.open(output_path, "w", **kwargs) as dst:
                dst.write(slope_deg, 1)
        print(f"[XONG] Đã tính toán Slope và lưu tại: {output_path}")

    def calculate_aspect(self, dem_path: str, output_path: str):
        """Tính toán hướng dốc (Aspect) từ file DEM GeoTIFF, đơn vị: độ (0-360, -1 cho vùng phẳng)."""
        self._require_rasterio()
        with rasterio.open(dem_path) as src:
            dem = src.read(1, masked=True).filled(np.nan)
            dx = abs(float(src.transform[0]))
            dy = abs(float(src.transform[4]))

            aspect_deg = self.compute_aspect_from_array(dem, dx=dx, dy=dy)

            kwargs = src.meta.copy()
            kwargs.update(dtype=rasterio.float32, nodata=-9999.0)

            with rasterio.open(output_path, "w", **kwargs) as dst:
                dst.write(np.nan_to_num(aspect_deg, nan=-9999.0), 1)
        print(f"[XONG] Đã tính toán Aspect và lưu tại: {output_path}")


if __name__ == "__main__":
    print("Kiểm tra GISProcessor...")
    processor = GISProcessor()
    sample_dem = np.zeros((10, 10), dtype=np.float32)
    flat_slope = processor.compute_slope_from_array(sample_dem, dx=30.0, dy=30.0)
    print(f"Độ dốc địa hình phẳng (kỳ vọng 0.0°): {float(flat_slope.max()):.2f}°")
