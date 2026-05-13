import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

DATA_FILE = "shipping_data.csv"

# --- HÀM LOAD DỮ LIỆU ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
            df['Ngày'] = pd.to_datetime(df['Ngày'], format='%d.%m.%Y', errors='coerce')
            return df.dropna(subset=['Ngày'])
        except:
            return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "ĐVVC", "Phí"])

if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- PHẦN NHẬP LIỆU ---
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns([1.5, 3, 2, 1.5])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị", ["Lalamove 🚛", "Ahamove 🛵", "Grab 🚗", "Viettel Post 📦"])
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
            st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
            st.session_state.df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.rerun()

# --- HIỂN THỊ & XUẤT EXCEL ---
if not st.session_state.df.empty:
    st.write("---")
    # Hiển thị bảng trên web
    df_show = st.session_state.df.copy()
    df_show['Ngày'] = df_show['Ngày'].dt.strftime('%d.%m.%Y')
    st.dataframe(df_show, use_container_width=True)

    # Nút xuất Excel (Đã fix cách 20 dòng và kẻ ô sẵn)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        export_df = st.session_state.df.copy()
        export_df['Ngày'] = export_df['Ngày'].dt.strftime('%d.%m.%Y')
        export_df.to_excel(writer, index=False, sheet_name='Sheet1', startrow=0)
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        
        # Định dạng kẻ ô và đẩy dòng Tổng cộng xuống dòng 32 (như image_729c9e.png)
        border_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0 "đ"'})
        total_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'border': 1})

        # Kẻ sẵn 30 dòng
        for r in range(1, 31):
            for c in range(4):
                worksheet.write(r, c, "", border_fmt)
        
        # Ghi đè dữ liệu thực
        for i, row in enumerate(export_df.values):
            worksheet.write(i+1, 0, row[0], border_fmt)
            worksheet.write(i+1, 1, row[1], border_fmt)
            worksheet.write(i+1, 2, row[2], border_fmt)
            worksheet.write(i+1, 3, row[3], money_fmt)

        # Dòng tổng cộng ở dòng 32
        total_val = st.session_state.df['Phí'].sum()
        worksheet.write(31, 2, "TỔNG CỘNG", total_fmt)
        worksheet.write(31, 3, total_val, total_fmt)

    st.download_button("📥 Tải file Excel Báo cáo", output.getvalue(), "bao_cao_ship.xlsx")