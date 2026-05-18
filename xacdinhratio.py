import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re
import numpy as np

# Cấu hình thẩm mỹ cao
plt.rcParams['figure.dpi'] = 150
sns.set_theme(style="whitegrid")

def extract_day_num(sheet_name):
    nums = re.findall(r'\d+', sheet_name)
    return int(nums[0]) if nums else 0

def process_and_save_trend(file_name, category_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)
    
    if not os.path.exists(file_path):
        print(f"X Không tìm thấy: {file_name}")
        return

    xl = pd.ExcelFile(file_path)
    day_sheets = [s for s in xl.sheet_names if "Ngày" in s]
    day_sheets.sort(key=extract_day_num)

    all_data = []
    for i, sheet in enumerate(day_sheets):
        df = pd.read_excel(xl, sheet_name=sheet)
        df['Day'] = i + 1 
        all_data.append(df)
    full_df = pd.concat(all_data, ignore_index=True)

    # --- 1. VẼ LINEPLOT TỐI ƯU XU HƯỚNG ---
    plt.figure(figsize=(10, 6))
    
    if "Ba rọi" in category_name:
        metrics = ['Ratio_1_Marbling(Mean)', 'Ratio_2_System(Mean)', 
                   'Ratio_3_Texture_Res(Contrast)', 'Ratio_Homogeneity_Thit/Da']
        df_line = full_df.groupby('Day')[metrics].mean().reset_index()
        for m in metrics:
            plt.plot(df_line['Day'], df_line[m], marker='o', linewidth=2, markersize=6, label=m)
        plt.yscale('log')
        plt.title(f'Lineplot của {category_name} (Thang Log)', fontsize=14, fontweight='bold')
        plt.ylabel('Giá trị (Log scale)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
    else: # Sườn và Nạc thăn
        # Tính Mean và Standard Error (SE = Std / sqrt(n))
        stats = full_df.groupby('Day')['Ratio_Mean'].agg(['mean', 'std', 'count']).reset_index()
        stats['se'] = stats['std'] / np.sqrt(stats['count'])
        
        # Vẽ vùng sai số dựa trên SE để đường line rõ hơn
        plt.fill_between(stats['Day'], 
                         stats['mean'] - stats['se'], 
                         stats['mean'] + stats['se'], 
                         color='blue', alpha=0.15, label='Vùng sai số chuẩn (SE)')
        
        # Vẽ đường line chính với màu tương phản
        plt.plot(stats['Day'], stats['mean'], color='#d62728', # Màu đỏ đậm
                 marker='D', linewidth=3, markersize=7, label='Xu hướng trung bình')
        
        plt.title(f'Lineplot của {category_name} (Cận cảnh xu hướng)', fontsize=14, fontweight='bold')
        plt.ylabel('Tỉ lệ trung bình (Ratio_Mean)')
        
        # TỐI ƯU TRỤC Y: Tập trung vào khoảng biến động của dữ liệu
        y_min, y_max = stats['mean'].min(), stats['mean'].max()
        margin = (y_max - y_min) * 0.5 if y_max != y_min else 0.1
        plt.ylim(y_min - margin, y_max + margin) 
        plt.legend(loc='best')

    plt.xlabel('Thời gian (Ngày)')
    plt.xticks(range(1, len(day_sheets) + 1))
    plt.tight_layout()
    plt.savefig(os.path.join(current_dir, f"Lineplot của {category_name}.png"))
    plt.close()

    # --- 2. VẼ BOXPLOT ---
    plt.figure(figsize=(10, 6))
    if "Ba rọi" in category_name:
        df_melted = full_df.melt(id_vars=['Day'], value_vars=metrics, var_name='Chỉ số', value_name='Giá trị')
        sns.boxplot(x='Day', y='Giá trị', hue='Chỉ số', data=df_melted, palette="Set2")
        plt.yscale('log')
    else:
        sns.boxplot(x='Day', y='Ratio_Mean', data=full_df, color='#aec7e8', width=0.5)
        # Giới hạn trục Y của Boxplot để không bị quá loãng
        plt.ylim(full_df['Ratio_Mean'].min()*0.8, full_df['Ratio_Mean'].max()*1.2)
        
    plt.title(f'Boxplot của {category_name}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(current_dir, f"Boxplot của {category_name}.png"))
    plt.close()
    print(f"V Đã cập nhật file cho: {category_name}")

if __name__ == "__main__":
    tasks = [
        ("Tỉ lệ so sánh Ba rọi.xlsx", "Ba rọi"),
        ("Tỉ lệ so sánh sườn.xlsx", "Sườn"),
        ("Tỉ lệ so sánh Nạc thăn.xlsx", "Nạc thăn")
    ]
    for file, cat in tasks:
        process_and_save_trend(file, cat)