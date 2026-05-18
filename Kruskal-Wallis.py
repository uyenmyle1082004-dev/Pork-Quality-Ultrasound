import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
import os
import re

def extract_day_num(sheet_name):
    nums = re.findall(r'\d+', str(sheet_name))
    return int(nums[0]) if nums else 0

def format_p_value(p):
    """Định dạng p-value sang dạng khoa học nếu số quá nhỏ"""
    try:
        p_float = float(p)
        if p_float == 0.0:
            return "< 1.00x10(-300)"
        if p_float < 0.0001:
            s = "{:.2e}".format(p_float)
            base, exponent = s.split('e')
            return f"{float(base):.2f}x10({int(exponent)})"
        return str(round(p_float, 4))
    except:
        return str(p)

def run_kruskal_and_lmm_pipeline(file_path, output_name):
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return

    # Đọc dữ liệu và sắp xếp thứ tự các Ngày từ các sheet
    xls = pd.ExcelFile(file_path)
    day_sheets = [s for s in xls.sheet_names if "Ngày" in s]
    day_sheets.sort(key=extract_day_num)
    
    df_list = []
    for i, sheet in enumerate(day_sheets):
        temp_df = pd.read_excel(xls, sheet_name=sheet)
        temp_df['Ngay_Bao_Quan'] = i + 1
        df_list.append(temp_df)
    
    df = pd.concat(df_list, ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    ratio_cols = [col for col in df.columns if 'Ratio' in col]
    
    kruskal_results = []
    lmm_results = []

    for col in ratio_cols:
        clean_data = df[[col, 'Ngay_Bao_Quan', 'Mẫu số']].dropna()
        if clean_data.empty:
            continue
            
        groups = [clean_data[clean_data['Ngay_Bao_Quan'] == g][col].values for g in clean_data['Ngay_Bao_Quan'].unique()]
        
        # 1. Tính toán Kruskal-Wallis
        stat_k, p_k = stats.kruskal(*groups)
        kruskal_results.append({
            'Đặc trưng': col,
            'H-statistic': round(stat_k, 4),
            'p-value': format_p_value(p_k)
        })
        
        # 2. Tính toán mô hình LMM (Điền bảng 2 - image_269dd0)
        try:
            df_lmm = clean_data.rename(columns={col: 'target', 'Ngay_Bao_Quan': 'time', 'Mẫu số': 'id'})
            model = smf.mixedlm("target ~ C(time)", df_lmm, groups=df_lmm["id"])
            mdf = model.fit(method=["lbfgs"])
            
            # Trích xuất các tham số cần thiết cho bảng 2
            fixed_effect_intercept = mdf.fe_params[0] # Hệ số tự do làm đại diện
            p_lmm_fixed = mdf.pvalues[0]
            
            # Lấy độ lệch chuẩn (SD) của Hiệu ứng ngẫu nhiên (Random Effect SD)
            random_effect_var = list(mdf.vcomp.values())[0] if mdf.vcomp else 0
            random_effect_sd = np.sqrt(random_effect_var)
            
            lmm_results.append({
                'Đặc trưng': col,
                'Fixed Effect (Est)': round(fixed_effect_intercept, 4),
                'LMM p-value': format_p_value(p_lmm_fixed),
                'Random Effect (SD)': round(random_effect_sd, 4)
            })
        except:
            lmm_results.append({
                'Đặc trưng': col,
                'Fixed Effect (Est)': "Lỗi hội tụ",
                'LMM p-value': "Lỗi hội tụ",
                'Random Effect (SD)': "Lỗi hội tụ"
            })

    # --- IN KẾT QUẢ RA TERMINAL ---
    print("\n" + "="*85)
    print(f"📊 [BẢNG 1] KẾT QUẢ KIỂM ĐỊNH PHI THAM SỐ KRUSKAL-WALLIS: {output_name.upper()}")
    print("="*85)
    print(f"{'Đặc trưng thực nghiệm':<32} | {'Hệ số H (Statistic)':<20} | {'p-value':<15}")
    print("-"*85)
    for res in kruskal_results:
        print(f"{res['Đặc trưng']:<32} | {res['H-statistic']:<20} | {res['p-value']:<15}")
    print("="*85)

    print("\n" + "="*95)
    print(f"📊 [BẢNG 2] THAM SỐ MÔ HÌNH HỖN HỢP TUYẾN TÍNH (LMM) ĐỂ ĐIỀN HÌNH 2: {output_name.upper()}")
    print("="*95)
    print(f"{'Đặc trưng thực nghiệm':<32} | {'Fixed Effect (Est)':<20} | {'p-value (Fixed)':<15} | {'Random Effect (SD)':<15}")
    print("-"*95)
    for res in lmm_results:
        print(f"{res['Đặc trưng']:<32} | {res['Fixed Effect (Est)']:<20} | {res['LMM p-value']:<15} | {res['Random Effect (SD)']:<15}")
    print("="*95 + "\n")

if __name__ == "__main__":
    # Chạy đồng thời cho cả 3 file Excel
    run_kruskal_and_lmm_pipeline('Tỉ lệ so sánh Ba rọi.xlsx', 'Ba Rọi')
    run_kruskal_and_lmm_pipeline('Tỉ lệ so sánh Nạc thăn.xlsx', 'Nạc Thăn')
    run_kruskal_and_lmm_pipeline('Tỉ lệ so sánh sườn.xlsx', 'Sườn')