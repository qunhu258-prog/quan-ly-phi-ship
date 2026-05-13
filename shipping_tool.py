import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def connect_gsheet():
    try:
        # Lấy cấu hình từ Streamlit Secrets
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            st.error("❌ Lỗi: Bạn chưa dán nội dung JSON vào mục Secrets trên Streamlit Cloud.")
            return None
            
        s = st.secrets["connections"]["gsheets"]
        
        # Xử lý ký tự xuống dòng trong Private Key
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
        # Link Google Sheets của Như
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        
        # Thử mở trang tính (Đảm bảo tên đúng là 'Trang tính1')
        return sh.worksheet("Trang tính1")
    except Exception as e:
        st.error(f"❌ Lỗi kết nối chi tiết: {str(e)}")
        return None

# 2. Hàm đọc dữ liệu
def load_data():
    sheet = connect_gsheet()
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df['Ngày giao'] = pd.to_datetime(df['Ngày giao'], dayfirst=True, errors='coerce')
                df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
                return df.dropna(subset=['Ngày giao'])
        except Exception as e:
            st.warning(f"Sheets trống hoặc sai cấu trúc: {e}")
    return pd.DataFrame(columns=["Ngày giao", "Nội dung đơn hàng", "Đơn vị vận chuyển", "Phí (VNĐ)"])

# 3. Khởi tạo dữ liệu (Session State)
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

if 'df' not in st.session_state:
    st.session_state.df = load_data()

# --- GIAO DIỆN CHÍNH ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- SIDEBAR (Phần Như bảo bị mất) ---
with st.sidebar:
    st.header("⚙️ Quản lý Đơn vị")
    
    # Thêm đơn vị mới
    new_c = st.text_input("Nhập tên đơn vị mới")
    if st.button("➕ Thêm đơn vị"):
        if new_c and new_c not in st.session_state.carriers:
            st.session_state.carriers.append(new_c)
            st.success(f"Đã thêm {new_c}")
            st.rerun()
            
    st.write("---")
    # Xóa đơn vị (Như muốn thêm phần này)
    st.subheader("🗑️ Xóa đơn vị")
    del_c = st.selectbox("Chọn đơn vị muốn xóa", st.session_state.carriers)
    if st.button("❌ Xác nhận xóa"):
        if len(st.session_state.carriers) > 1:
            st.session_state.carriers.remove(del_c)
            st.warning(f"Đã xóa {del_c}")
            st.rerun()
        else:
            st.error("Phải để lại ít nhất 1 đơn vị!")

# --- PHẦN NHẬP LIỆU ---
st.subheader("➕ Thêm chuyến mới")
with st.form("input_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        date_input = st.date_input("Ngày giao", datetime.now())
    with col2:
        content_input = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier_input = st.selectbox("Đơn vị vận chuyển", st.session_state.carriers)
        price_input = st.number_input("Phí (VNĐ)", min_value=0, step=1000, format="%d")
    
    if st.form_submit_button("💾 Lưu thông tin"):
        if content_input and price_input > 0:
            s_target = connect_gsheet()
            if s_target:
                new_row = [date_input.strftime('%d/%m/%Y'), content_input, carrier_input, price_input]
                s_target.append_row(new_row)
                st.session_state.df = load_data() # Cập nhật lại bảng
                st.balloons()
                st.success("Đã lưu vào Google Sheets! ✅")
                st.rerun()
        else:
            st.warning("Vui lòng điền đủ Nội dung và Phí!")

# --- HIỂN THỊ DỮ LIỆU ---
if st.button("🔄 Làm mới dữ liệu"):
    st.session_state.df = load_data()
    st.rerun()

st.write("---")
if not st.session_state.df.empty:
    df_view = st.session_state.df.copy()
    df_view['Tháng'] = df_view['Ngày giao'].dt.strftime('%m/%Y')
    
    month_list = sorted(df_view['Tháng'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Xem theo tháng:", month_list)
    
    filtered_df = df_view[df_view['Tháng'] == sel_month].copy()
    st.info(f"💰 **Tổng chi phí tháng {sel_month}: {filtered_df['Phí (VNĐ)'].sum():,.0f} VNĐ**")
    
    filtered_df['Ngày giao'] = filtered_df['Ngày giao'].dt.strftime('%d/%m/%Y')
    st.dataframe(filtered_df.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu nào được ghi nhận.")