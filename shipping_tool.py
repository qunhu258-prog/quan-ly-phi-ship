import streamlit as st
import pandas as pd
from datetime import datetime
import io
import gspread

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def connect_gsheet():
    try:
        # Lấy thông tin từ Secrets
        s = st.secrets["connections"]["gsheets"]
        
        # CHỖ NÀY QUAN TRỌNG: Tự động sửa lỗi định dạng private_key
        p_key = s["private_key"]
        if "\\n" in p_key:
            p_key = p_key.replace("\\n", "\n")
        
        # Tạo cấu hình chuẩn để gửi cho Google
        credentials = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": p_key,
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        # Link file Sheets của Như từ hình image_56089a.png
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit?gid=0#gid=0")
        return sh.get_worksheet(0)
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {str(e)}")
        return None

sheet = connect_gsheet()

# 2. Hàm đọc dữ liệu
def load_data():
    if sheet:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df['Ngày'] = pd.to_datetime(df['Ngày'], dayfirst=True, errors='coerce')
            return df.dropna(subset=['Ngày'])
    return pd.DataFrame(columns=["Ngày", "Nội dung", "Đơn vị vận chuyển", "Phí"])

# Khởi tạo danh sách đơn vị vận chuyển
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    new_c = st.text_input("Thêm đơn vị mới")
    if st.button("Lưu đơn vị"):
        if new_c and new_c not in st.session_state.carriers:
            st.session_state.carriers.append(new_c)
            st.rerun()

# --- NÚT CẬP NHẬT ---
if st.button("🔄 Cập nhật dữ liệu (Đọc từ Google Sheets)"):
    st.session_state.df = load_data()
    st.success("Đã đồng bộ dữ liệu mới nhất! ✅")
    st.rerun()

# --- FORM NHẬP LIỆU (Ghi thẳng lên Sheets) ---
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
            new_row = [date.strftime('%d/%m/%Y'), content, carrier, price]
            if sheet:
                sheet.append_row(new_row) # Ghi trực tiếp lên Sheets
                st.session_state.df = load_data() # Nạp lại dữ liệu hiển thị
                st.balloons()
                st.rerun()

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Tháng_Năm'] = df_display['Ngày'].dt.strftime('%m/%Y')
    
    sel_month = st.selectbox("📅 Chọn tháng:", sorted(df_display['Tháng_Năm'].unique(), reverse=True))
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    
    # Hiển thị bảng đơn giản cho nhân viên dễ xem
    st.dataframe(month_data.iloc[::-1], use_container_width=True)
    st.info(f"💰 **Tổng cộng: {month_data['Phí'].sum():,.0f} VNĐ**")