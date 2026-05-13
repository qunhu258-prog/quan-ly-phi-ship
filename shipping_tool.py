import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# 2. Kết nối Google Sheets
# Chú ý: SHEET_URL này Như thay bằng link file Sheets của Như nhé
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_URL = "https://docs.google.com/spreadsheets/d/THAY_ID_CUA_NHU_TAI_DAY/edit#gid=0"

def load_data():
    return conn.read(spreadsheet=SHEET_URL, ttl="0")

# Khởi tạo danh sách đơn vị vận chuyển (Sidebar)
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

st.title("🚚 Quản Lý Phí Ship (Ghi thẳng vào Sheets)")

# --- SIDEBAR: QUẢN LÝ ĐƠN VỊ ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    new_c = st.text_input("Thêm đơn vị mới")
    if st.button("Lưu đơn vị"):
        if new_c and new_c not in st.session_state.carriers:
            st.session_state.carriers.append(new_c)
            st.rerun()
    
    st.write("---")
    carrier_to_del = st.selectbox("Xóa đơn vị", st.session_state.carriers)
    if st.button("🗑️ Xóa đơn vị"):
        st.session_state.carriers.remove(carrier_to_del)
        st.rerun()

# --- NÚT CẬP NHẬT ---
if st.button("🔄 Cập nhật dữ liệu từ Sheets"):
    st.cache_data.clear()
    st.rerun()

# --- FORM NHẬP LIỆU ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date = st.date_input("Ngày giao", datetime.now())
    with col2:
        content = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier = st.selectbox("Đơn vị vận chuyển", st.session_state.carriers)
        price = st.number_input("Phí (VNĐ)", min_value=0, step=1000, format="%d")
    
    if st.form_submit_button("💾 Lưu thông tin"):
        if content and price > 0:
            existing_data = load_data()
            new_row = pd.DataFrame([{
                "Ngày": date.strftime('%d/%m/%Y'),
                "Nội dung": content,
                "Đơn vị vận chuyển": carrier,
                "Phí": price
            }])
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            
            # Ghi dữ liệu lên Sheets
            conn.update(spreadsheet=SHEET_URL, data=updated_df)
            st.success("Đã ghi vào Google Sheets! ✅")
            st.cache_data.clear()
            st.rerun()

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
data = load_data()
if not data.empty:
    # Đảo ngược bảng để chuyến mới nhất lên đầu
    st.dataframe(data.iloc[::-1], use_container_width=True)