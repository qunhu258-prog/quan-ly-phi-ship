import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# Kết nối với Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Link file Sheets của Như (đã bật quyền Editor cho Client Email)
SHEET_URL = "https://docs.google.com/spreadsheets/d/ID_CUA_NHU/edit"

# 1. Hàm đọc dữ liệu
def load_data():
    return conn.read(spreadsheet=SHEET_URL, usecols=[0, 1, 2, 3])

st.title("🚚 Quản Lý Phí Ship - Tự Động Lưu Sheets")

# Nút cập nhật (Đúng ý Như: Đọc lại từ Sheets ngay lập tức)
if st.button("🔄 Cập nhật dữ liệu"):
    st.cache_data.clear()
    st.rerun()

# --- SIDEBAR & FORM NHẬP LIỆU (Giữ nguyên giao diện của Như) ---
# ... (Phần Sidebar thêm/xóa ĐVVC Như giữ nguyên nhé) ...

with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị vận chuyển", ["Grab", "Ahamove", "Lalamove"]) # Hoặc list từ sidebar
        price = st.number_input("Phí (VNĐ)", min_value=0, step=1000)

    if st.form_submit_button("💾 Lưu thông tin"):
        if content and price > 0:
            # Đọc dữ liệu cũ
            existing_data = load_data()
            
            # Tạo dòng mới
            new_row = pd.DataFrame([{
                "Ngày": date.strftime('%d/%m/%Y'),
                "Nội dung": content,
                "Đơn vị vận chuyển": carrier,
                "Phí": price
            }])
            
            # Gộp lại và GHI THẲNG LÊN SHEETS
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            
            st.success("Đã ghi vào Google Sheets thành công! ✅")
            st.cache_data.clear() # Xóa cache để bảng bên dưới hiện dòng mới ngay
            st.rerun()

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
data = load_data()
if not data.empty:
    st.dataframe(data.iloc[::-1], use_container_width=True) # Hiện chuyến mới nhất lên đầu