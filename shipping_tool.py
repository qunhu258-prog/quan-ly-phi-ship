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
        
        # Tự động sửa lỗi định dạng private_key
        p_key = s["private_key"]
        if "\\n" in p_key:
            p_key = p_key.replace("\\n", "\n")
        
        # Tạo cấu hình chuẩn
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
        
        # SỬA LỖI TẠI ĐÂY: Dùng worksheet("Tên_Trang_Tính") cho chính xác
        return sh.worksheet("Trang tính1")
    except Exception as e:
        st.error(f"⚠️ Lỗi kết nối: {str(e)}")
        return None

# 2. Hàm đọc dữ liệu
def load_data():
    sheet = connect_gsheet() # Định nghĩa sheet ngay trong hàm để tránh lỗi NameError
    if sheet:
        try:
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                # Ép kiểu dữ liệu cột Ngày và Phí cho chuẩn
                df['Ngày giao'] = pd.to_datetime(df['Ngày giao'], dayfirst=True, errors='coerce')
                df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
                return df.dropna(subset=['Ngày giao'])
        except:
            pass
    return pd.DataFrame(columns=["Ngày giao", "Nội dung đơn hàng", "Đơn vị vận chuyển", "Phí (VNĐ)"])

# Khởi tạo danh sách đơn vị vận chuyển
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

# Khởi tạo dataframe trong bộ nhớ
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
        date_input = st.date_input("Ngày giao", datetime.now())
    with col2:
        content_input = st.text_input("Nội dung đơn hàng")
    with col3:
        carrier_input = st.selectbox("Đơn vị vận chuyển", st.session_state.carriers)
        price_input = st.number_input("Phí (VNĐ)", min_value=0, step=1000, format="%d")
    
    if st.form_submit_button("💾 Lưu thông tin"):
        if content_input and price_input > 0:
            sheet_to_save = connect_gsheet()
            if sheet_to_save:
                # Ghi đúng thứ tự cột trong Google Sheets của Như
                new_row = [date_input.strftime('%d/%m/%Y'), content_input, carrier_input, price_input]
                sheet_to_save.append_row(new_row)
                
                # Cập nhật lại bảng hiển thị
                st.session_state.df = load_data()
                st.balloons()
                st.success("Đã lưu vào Google Sheets thành công! ✅")
                st.rerun()
            else:
                st.error("Không thể kết nối để lưu dữ liệu!")
        else:
            st.warning("Vui lòng điền đầy đủ Nội dung và Phí!")

# --- HIỂN THỊ DANH SÁCH ---
st.write("---")
if not st.session_state.df.empty:
    df_display = st.session_state.df.copy()
    df_display['Tháng_Năm'] = df_display['Ngày giao'].dt.strftime('%m/%Y')
    
    all_months = sorted(df_display['Tháng_Năm'].unique(), reverse=True)
    sel_month = st.selectbox("📅 Chọn tháng:", all_months)
    
    month_data = df_display[df_display['Tháng_Năm'] == sel_month].copy()
    
    # Hiển thị tổng tiền
    st.info(f"💰 **Tổng cộng tháng {sel_month}: {month_data['Phí (VNĐ)'].sum():,.0f} VNĐ**")
    
    # Định dạng lại ngày để hiển thị cho đẹp (dd/mm/yyyy)
    month_data['Ngày giao'] = month_data['Ngày giao'].dt.strftime('%d/%m/%Y')
    
    # Hiển thị bảng (đảo ngược để đơn mới nhất lên đầu)
    st.dataframe(month_data.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu nào trong Google Sheets.")