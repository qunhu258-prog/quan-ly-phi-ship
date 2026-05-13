import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def connect_gsheet():
    try:
        # Lấy thông tin từ Secrets
        s = st.secrets["connections"]["gsheets"]
        
        # Sửa lỗi định dạng private_key
        p_key = s["private_key"]
        if "\\n" in p_key:
            p_key = p_key.replace("\\n", "\n")
        
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
        # Link file Sheets của Như
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        
        # Dùng worksheet("Trang tính1") để khớp với file của Như
        return sh.worksheet("Trang tính1")
    except Exception as e:
        # Chỉ hiện lỗi khi thực sự không kết nối được
        return None

# 2. Hàm đọc dữ liệu
def load_data():
    # Gọi kết nối ngay bên trong hàm để chắc chắn có biến 'sheet'
    sheet = connect_gsheet() 
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                # Ép kiểu dữ liệu đúng tên cột Như đã sửa
                df['Ngày giao'] = pd.to_datetime(df['Ngày giao'], dayfirst=True, errors='coerce')
                df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
                return df.dropna(subset=['Ngày giao'])
        except:
            pass
    return pd.DataFrame(columns=["Ngày giao", "Nội dung đơn hàng", "Đơn vị vận chuyển", "Phí (VNĐ)"])

# Khởi tạo dữ liệu
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

# --- FORM NHẬP LIỆU ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date_val = st.date_input("Ngày giao", datetime.now())
    with col2:
        content_val = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier_val = st.selectbox("Đơn vị vận chuyển", st.session_state.carriers)
        price_val = st.number_input("Phí (VNĐ)", min_value=0, step=1000, format="%d")
    
    if st.form_submit_button("💾 Lưu thông tin"):
        if content_val and price_val > 0:
            # Kết nối để lưu
            target_sheet = connect_gsheet()
            if target_sheet:
                new_row = [date_val.strftime('%d/%m/%Y'), content_val, carrier_val, price_val]
                target_sheet.append_row(new_row)
                
                # Cập nhật lại giao diện
                st.session_state.df = load_data()
                st.balloons()
                st.success("Đã lưu thành công! ✅")
                st.rerun()
            else:
                st.error("Không thể kết nối với Sheets để lưu!")
        else:
            st.warning("Vui lòng điền đủ thông tin!")

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Tháng_Năm'] = df_display['Ngày giao'].dt.strftime('%m/%Y')
    
    months = sorted(df_display['Tháng_Năm'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Chọn tháng:", months)
    
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    
    st.info(f"💰 **Tổng cộng tháng {sel_month}: {month_data['Phí (VNĐ)'].sum():,.0f} VNĐ**")
    
    # Định dạng hiển thị ngày
    month_data['Ngày giao'] = month_data['Ngày giao'].dt.strftime('%d/%m/%Y')
    st.dataframe(month_data.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu. Hãy thêm chuyến mới hoặc bấm Cập nhật.")