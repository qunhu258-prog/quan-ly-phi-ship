import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"
CARRIER_FILE = "carriers.csv"

# --- HÀM HỖ TRỢ DỮ LIỆU ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d.%m.%Y', errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])

def load_carriers():
    if os.path.exists(CARRIER_FILE):
        try:
            return pd.read_csv(CARRIER_FILE, encoding='utf-8-sig')['Tên'].tolist()
        except:
            return ["Lalamove 🚛", "Ahamove 🛵", "Grab 🚗", "Viettel Post 📦"]
    return ["Lalamove 🚛", "Ahamove 🛵", "Grab 🚗", "Viettel Post 📦"]

def save_carrier(new_name):
    carriers = load_carriers()
    if new_name not in carriers:
        carriers.append(new_name)
        pd.DataFrame(carriers, columns=['Tên']).to_csv(CARRIER_FILE, index=False, encoding='utf-8-sig')
        return True
    return False

# TỰ ĐỘNG CẬP NHẬT MỖI 60 GIÂY
@st.fragment(run_every=60)
def auto_refresh():
    st.session_state.df = load_data()

auto_refresh()

# --- GIAO DIỆN CHÍNH ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# SIDEBAR: THÊM ĐƠN VỊ MỚI
with st.sidebar:
    st.header("⚙️ Cài đặt")
    new_carrier = st.text_input("Thêm đơn vị vận chuyển mới")
    if st.button("Lưu đơn vị"):
        if new_carrier:
            if save_carrier(new_carrier):
                st.success(f"Đã thêm: {new_carrier}")
                st.rerun()

carrier_list = load_carriers()

# NÚT CẬP NHẬT NHANH
if st.button("🔄 Cập nhật dữ liệu ngay lập tức"):
    st.session_state.df = load_data()
    st.rerun()

# --- PHẦN NHẬP LIỆU ---
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([1.5, 3, 2, 1.5])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị", carrier_list)
    with col4:
        price = st.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu chuyến mới"):
        if content and price > 0:
            new_row = pd.DataFrame({
                "Ngày": [pd.to_datetime(date)],
                "Nội dung": [content],
                "ĐVVC": [carrier],
                "Phí": [price]
            })
            # Chống ghi đè: Đọc lại file trước khi ghi tiếp
            current_df = load_data()
            updated_df = pd.concat([current_df, new_row], ignore_index=True)
            updated_df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.session_state.df = updated_df
            st.success("Đã lưu đơn hàng! ✨")
            st.rerun()

# --- HIỂN THỊ & XUẤT EXCEL ---
if not st.session_state.df.empty:
    st.write("---")
    df_show = st.session_state.df.copy()
    df_show['Ngày'] = df_show['Ngày'].dt.strftime('%d.%m.%Y')
    st.dataframe(df_show, use_container_width=True)

    # XUẤT EXCEL (ĐỊNH DẠNG THEO image_72a421.png & image_729c9e.png)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = st.session_state.df.copy()
        export_df['Ngày'] = export_df['Ngày'].dt.strftime('%d.%m.%Y')
        export_df.to_excel(writer, index=False, sheet_name='Báo cáo', startrow=0)
        
        workbook  = writer.book
        worksheet = writer.sheets['Báo cáo']
        
        # Định dạng styles
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'})
        border_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0 "đ"'})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'num_format': '#,##0 "đ"'})
        total_label_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1, 'align': 'center'})

        # Kẻ khung 30 dòng
        for r in range(1, 31):
            for c in range(4):
                worksheet.write(r, c, "", border_fmt)
        
        # Ghi dữ liệu thực
        for i, row in enumerate(export_df.values):
            worksheet.write(i+1, 0, row[0], border_fmt)
            worksheet.write(i+1, 1, row[1], border_fmt)
            worksheet.write(i+1, 2, row[2], border_fmt)
            worksheet.write(i+1, 3, row[3], money_fmt)

        # Dòng tổng cộng cách ra ở dòng 32
        total_val = st.session_state.df['Phí'].sum()
        worksheet.merge_range(31, 0, 31, 2, "TỔNG CỘNG", total_label_fmt)
        worksheet.write(31, 3, total_val, total_fmt)

        # Chỉnh độ rộng cột
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 50)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 18)
        
        # Ghi đè tiêu đề để có màu xanh
        for col_num, value in enumerate(export_df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)

    st.download_button("📥 Tải file Excel Báo cáo", output.getvalue(), f"bao_cao_ship_{datetime.now().strftime('%d_%m')}.xlsx")
else:
    st.info("Chưa có dữ liệu Như ơi! ✨")