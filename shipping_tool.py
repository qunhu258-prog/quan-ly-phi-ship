import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# 1. Cấu hình trang
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def connect_gsheet():
    try:
        # Kiểm tra xem secrets có tồn tại không
        if "connections" not in st.secrets:
            st.error("❌ Chưa cấu hình Secrets trên Streamlit Cloud!")
            return None
            
        s = st.secrets["connections"]["gsheets"]
        p_key = s["private_key"].replace("\\n", "\n")
        
        credentials = {
            "type": s["type"], "project_id": s["project_id"],
            "private_key_id": s["private_key_id"], "private_key": p_key,
            "client_email": s["client_email"], "client_id": s["client_id"],
            "auth_uri": s["auth_uri"], "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        # Link file của Như
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        return sh.worksheet("Trang tính1")
    except Exception as e:
        st.error(f"❌ Lỗi kết nối chi tiết: {str(e)}")
        return None

# 2. Hàm đọc dữ liệu an toàn
def load_data():
    local_sheet = connect_gsheet() 
    if local_sheet is not None:
        try:
            data = local_sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df['Ngày giao'] = pd.to_datetime(df['Ngày giao'], dayfirst=True, errors='coerce')
                df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
                return df.dropna(subset=['Ngày giao'])
        except Exception as e:
            st.warning(f"Đã kết nối nhưng chưa có dữ liệu chuẩn: {e}")
    return pd.DataFrame(columns=["Ngày giao", "Nội dung đơn hàng", "Đơn vị vận chuyển", "Phí (VNĐ)"])

# Khởi tạo dữ liệu ban đầu
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

if 'df' not in st.session_state:
    st.session_state.df = load_data()

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# --- NÚT CẬP NHẬT ---
if st.button("🔄 Cập nhật dữ liệu từ Sheets"):
    st.session_state.df = load_data()
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
    
    submit = st.form_submit_button("💾 Lưu thông tin")
    
    if submit:
        if content_val and price_val > 0:
            write_sheet = connect_gsheet()
            if write_sheet is not None:
                new_row = [date_val.strftime('%d/%m/%Y'), content_val, carrier_val, price_val]
                write_sheet.append_row(new_row)
                st.session_state.df = load_data()
                st.balloons()
                st.success("Đã lưu thành công! ✅")
                st.rerun()
            else:
                st.error("Không thể kết nối để ghi dữ liệu!")
        else:
            st.warning("Vui lòng nhập đủ Nội dung và Phí!")

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Tháng_Năm'] = df_display['Ngày giao'].dt.strftime('%m/%Y')
    months = sorted(df_display['Tháng_Năm'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Chọn tháng:", months)
    
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    st.info(f"💰 **Tổng cộng tháng {sel_month}: {month_data['Phí (VNĐ)'].sum():,.0f} VNĐ**")
    
    month_data['Ngày giao'] = month_data['Ngày giao'].dt.strftime('%d/%m/%Y')
    st.dataframe(month_data.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu hiển thị.")