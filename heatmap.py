import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Thiết lập phong cách biểu đồ chuyên nghiệp
sns.set_theme(style="whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_and_merge_sheets(file_path):
    """Đọc tất cả các tab trong file Excel và gộp thành một DataFrame duy nhất"""
    xls = pd.ExcelFile(file_path)
    all_sheets = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        # Thêm cột Ngày để dễ phân loại nếu cần
        df['Tab_Source'] = sheet_name
        all_sheets.append(df)
    return pd.concat(all_sheets, ignore_index=True)

def export_visualizations(df, group_name, is_ratio=False):
    """Tạo và lưu các biểu đồ Boxplot, Violin và Heatmap"""
    
    # Danh sách các đặc trưng cần vẽ
    if is_ratio:
        features = [col for col in df.columns if 'Ratio' in col]
        folder_prefix = "Ratios"
    else:
        features = ['Mean', 'Std', 'Contrast', 'Homogeneity', 'Energy', 'Correlation']
        folder_prefix = "Raw"

    # 1. Heatmap Ma trận tương quan (Pearson) 
    plt.figure(figsize=(10, 8))
    correlation_matrix = df[features].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title(f'Heatmap Tương quan Pearson - {group_name} ({folder_prefix})')
    plt.savefig(f'{group_name}_{folder_prefix}_Heatmap.png')
    plt.close()

    # 2. Boxplot & Violin Plot cho từng đặc trưng
    for feat in features:
        # Tạo đồ thị kết hợp Violin và Boxplot
        plt.figure(figsize=(12, 6))
        
        # Nhóm theo 'Lớp' (Da, Mỡ, Thịt...) để so sánh
        sns.violinplot(x='Lớp' if not is_ratio else 'Nhóm', y=feat, data=df, inner=None, color=".8")
        sns.boxplot(x='Lớp' if not is_ratio else 'Nhóm', y=feat, data=df, whis=[0, 100], width=.15, palette="vlag")
        
        plt.title(f'Phân phối đặc trưng {feat} - {group_name}')
        plt.xlabel('Cấu trúc mô')
        plt.ylabel('Giá trị')
        plt.savefig(f'{group_name}_{folder_prefix}_{feat}_Distribution.png')
        plt.close()

# --- THỰC THI CHO CÁC BỘ DỮ LIỆU ---

# Danh sách file Raw và Ratio
raw_files = {
    'BaRoi': 'HÓA ĐIÊN CÙNG BA RỌI.xlsx',
    'NacThan': 'HÓA ĐIÊN CÙNG NẠC THĂN.xlsx',
    'Suon': 'HÓA ĐIÊN CÙNG SUON.xlsx'
}

ratio_files = {
    'BaRoi': 'Tỉ lệ so sánh Ba rọi.xlsx',
    'NacThan': 'Tỉ lệ so sánh Nạc thăn.xlsx',
    'Suon': 'Tỉ lệ so sánh sườn.xlsx'
}

# Xử lý dữ liệu Raw
for name, path in raw_files.items():
    try:
        print(f"🔄 Đang xử lý dữ liệu Raw: {name}...")
        df_raw = load_and_merge_sheets(path)
        export_visualizations(df_raw, name, is_ratio=False)
    except Exception as e:
        print(f"❌ Lỗi khi xử lý {name}: {e}")

# Xử lý dữ liệu Ratio
for name, path in ratio_files.items():
    try:
        print(f"🔄 Đang xử lý dữ liệu Ratio: {name}...")
        df_ratio = load_and_merge_sheets(path)
        # Giả định cột phân loại cho Ratio là 'Nhóm' hoặc 'So sánh'
        export_visualizations(df_ratio, name, is_ratio=True)
    except Exception as e:
        print(f"❌ Lỗi khi xử lý Ratio {name}: {e}")

print("✨ Hoàn tất! Tất cả biểu đồ 300 DPI đã được lưu trong thư mục làm việc.")