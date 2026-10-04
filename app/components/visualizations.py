import plotly.graph_objects as go
import numpy as np

def create_3d_terrain():
    """Tạo mô hình 3D địa hình và cảnh báo nguy cơ sạt lở."""
    # Giả lập dữ liệu địa hình (DEM)
    x = np.linspace(-5, 5, 80)
    y = np.linspace(-5, 5, 80)
    X, Y = np.meshgrid(x, y)
    
    # Tạo các đỉnh núi và thung lũng
    Z = np.sin(X) * np.cos(Y) * 2 + np.exp(-(X**2 + Y**2)/10) * 5
    
    # Tính độ dốc (Slope) để làm dữ liệu nền cho nguy cơ
    dzdx = np.gradient(Z, axis=1)
    dzdy = np.gradient(Z, axis=0)
    slope = np.sqrt(dzdx**2 + dzdy**2)
    
    # Thang màu cảnh báo (Xanh -> Vàng -> Cam -> Đỏ)
    colorscale = [
        [0.0, '#2e8b57'],  # No/Low Susceptibility (Green)
        [0.3, '#ffd700'],  # Moderate Susceptibility (Yellow)
        [0.6, '#ff8c00'],  # High Susceptibility (Orange)
        [1.0, '#ff0000']   # Very High Susceptibility (Red)
    ]
    
    fig = go.Figure(data=[go.Surface(
        z=Z, 
        surfacecolor=slope, 
        colorscale=colorscale,
        colorbar=dict(title="Nguy cơ<br>sạt lở")
    )])
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, title='Độ cao')
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        template="plotly_dark",
        height=500,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def create_gauge_chart(value, title):
    """Tạo biểu đồ Gauge hiển thị lượng mưa/tốc độ dòng chảy."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = value,
        title = {'text': title, 'font': {'size': 14, 'color': '#00ffcc'}},
        gauge = {
            'axis': {'range': [None, 150], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#00ffcc"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': "rgba(46, 139, 87, 0.6)"}, # Xanh
                {'range': [50, 100], 'color': "rgba(255, 140, 0, 0.6)"}, # Cam
                {'range': [100, 150], 'color': "rgba(255, 0, 0, 0.6)"} # Đỏ
            ]
        }
    ))
    fig.update_layout(
        height=200, 
        margin=dict(l=20, r=20, t=40, b=20), 
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig
    
def create_line_chart(x_data, y_data, title, color='#00ffcc'):
    """Tạo biểu đồ Line Chart thể hiện xu hướng."""
    fig = go.Figure(data=go.Scatter(
        x=x_data, 
        y=y_data, 
        mode='lines+markers', 
        line=dict(color=color, width=3),
        fill='tozeroy',
        fillcolor=f'rgba{tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (0.2,)}'
    ))
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 14, 'color': color}},
        height=200, 
        margin=dict(l=20, r=20, t=40, b=20), 
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    # Tắt gridlines để giống giao diện Sci-fi
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    return fig
