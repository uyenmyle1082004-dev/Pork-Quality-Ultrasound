import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.formula.api as smf
import os
import re

def extract_day_num(sheet_name):
    """Trích xuất số từ tên sheet (Ví dụ: 'Ngày 1 (1903)' -> 1)"""
    nums = re.findall(r'\d+', str(sheet_name))
    return int(nums[0]) if nums else 0

def format_p_value(p):
    """
    Định dạng p-value sang dạng toán học lũy thừa nếu số quá nhỏ.
    Tránh ghi số 0 tuyệt đối sai bản chất toán thống kê.
    """
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

def run_comprehensive_statistical_pipeline(file_path, category_label):
    if not os.path.exists(file_path):
        print(f"❌ Không tìm thấy file: {file_path}")
        return

    # 1. Đọc dữ liệu và sắp xếp thứ tự các Ngày (Tab Excel)
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
    
    table_1_results = []
    table_2_results = []

    for col in ratio_cols:
        clean_data = df[[col, 'Ngay_Bao_Quan', 'Mẫu số']].dropna()
        if clean_data.empty:
            continue
            
        groups = [clean_data[clean_data['Ngay_Bao_Quan'] == g][col].values for g in clean_data['Ngay_Bao_Quan'].unique()]
        
        # --- BẢNG 1: KIỂM ĐỊNH GIẢ ĐỊNH & KRUSKAL-WALLIS ---
        try:
            _, p_shapiro = stats.shapiro(clean_data[col].values)
        except:
            p_shapiro = np.nan
            
        try:
            _, p_levene = stats.levene(*groups) if len(groups) > 1 else (np.nan, np.nan)
        except:
            p_levene = np.nan
            
        try:
            stat_k, p_k = stats.kruskal(*groups)
            p_k_str = format_p_value(p_k)
        except:
            p_k_str = "Lỗi tính"

        table_1_results.append({
            'Đặc trưng': col,
            'P_Shapiro': format_p_value(p_shapiro),
            'P_Levene': format_p_value(p_levene),
            'Phương pháp': 'Kruskal-Wallis',
            'P_Kruskal': p_k_str
        })
        
        # --- BẢNG 2: THAM SỐ MÔ HÌNH LMM ---
        try:
            df_lmm = clean_data.rename(columns={col: 'target', 'Ngay_Bao_Quan': 'time', 'Mẫu số': 'id'})
            model = smf.mixedlm("target ~ C(time)", df_lmm, groups=df_lmm["id"])
            mdf = model.fit(method=["lbfgs"])
            
            fixed_effect_est = mdf.fe_params[0]  # Hệ số tự do cố định làm đại diện
            p_lmm_fixed = mdf.pvalues[0]
            
            # Trích xuất độ lệch chuẩn (SD) của hiệu ứng ngẫu nhiên
            random_effect_var = list(mdf.vcomp.values())[0] if mdf.vcomp else 0
            random_effect_sd = np.sqrt(random_effect_var)
            
            table_2_results.append({
                'Đặc trưng': col,
                'Fixed_Est': round(fixed_effect_est, 4),
                'P_Fixed': format_p_value(p_lmm_fixed),
                'Random_SD': round(random_effect_sd, 4)
            })
        except:
            table_2_results.append({
                'Đặc trưng': col,
                'Fixed_Est': "Lỗi hội tụ",
                'P_Fixed': "Lỗi hội tụ",
                'Random_SD': "Lỗi hội tụ"
            })

    # --- ĐẦU RA TERMINAL ĐƯỢC ĐỊNH DẠNG ĐẸP ---
    print("\n" + "="*115)
    print(f"📊 [BẢNG 1 - ĐIỀN HÌNH image_263590] KIỂM ĐỊNH GIẢ ĐỊNH & KRUSKAL-WALLIS - NHÓM: {category_label.upper()}")
    print("="*115)
    print(f"{'Đặc trưng thực nghiệm':<32} | {'P_Shapiro':<15} | {'P_Levene':<15} | {'Phương pháp áp dụng':<20} | {'P_Kruskal':<15}")
    print("-"*115)
    for r in table_1_results:
        print(f"{r['Đặc trưng']:<32} | {r['P_Shapiro']:<15} | {r['P_Levene']:<15} | {r['Phương pháp']:<20} | {r['P_Kruskal']:<15}")
    print("="*115)

    print("\n" + "="*100) # Đã sửa lỗi thiếu dấu nhân (*) ở đây
    print(f"📊 [BẢNG 2 - ĐIỀN HÌNH image_269dd0] THAM SỐ MÔ HÌNH HỖN HỢP TUYẾN TÍNH LMM - NHÓM: {category_label.upper()}")
    print("="*100)
    print(f"{'Đặc trưng thực nghiệm':<32} | {'Fixed Effect (Est)':<20} | {'p-value (Fixed)':<15} | {'Random Effect (SD)':<15}")
    print("-"*100)
    for r in table_2_results:
        print(f"{r['Đặc trưng']:<32} | {r['Fixed_Est']:<20} | {r['P_Fixed']:<15} | {r['Random_SD']:<15}")
    print("="*100 + "\n")

if __name__ == "__main__":
    # Thực thi tuần tự cho cả 3 nhóm mô cơ thực nghiệm thịt heo
    run_comprehensive_statistical_pipeline('Tỉ lệ so sánh Ba rọi.xlsx', 'Ba Rọi')
    run_comprehensive_statistical_pipeline('Tỉ lệ so sánh Nạc thăn.xlsx', 'Nạc Thăn')
    run_comprehensive_statistical_pipeline('Tỉ lệ so sánh sườn.xlsx', 'Sườn')