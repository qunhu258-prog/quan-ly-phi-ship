import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

# 1. Cấu hình trang luôn nằm trên cùng
st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# 2. Hàm kết nối (Không để lỗi này làm sập cả app)
def connect_to_sheet():
    try:
        if "connections" not in st.secrets:
            return None, "Thiếu cấu hình Secrets trong App Settings"
        
        c = st.secrets["connections"]["gsheets"]
        p_key = c["private_key"].replace("\\n", "\n")
        
        creds = {
            "type": c["type"], "project_id": c["project_id"],
            "private_key_id": c["private_key_id"], "private_key": p_key,
            "client_email": c["client_email"], "client_id": c["client_id"],
            "auth_uri": c["auth_uri"], "token_uri": c["token_uri"],
            "auth_provider_x509_cert_url": c["auth_provider_x509_cert_url"],
            "client_x509_cert_url": c["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(creds)
        sheet_id = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"
        sh = gc.open_by_key(sheet_id)
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

# --- 3. PHẦN SIDEBAR (Luôn luôn hiện diện) ---
if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị mới")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()
    
    st.write("---")
    xoa = st.selectbox("Xóa đơn vị", st.session_state.ds_donvi)
    if st.button("Xóa"):
        st.session_state.ds_donvi.remove(xoa)
        st.rerun()

# --- 4. GIAO DIỆN CHÍNH ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.form("form_nhap", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    ngay = col1.date_input("Ngày", datetime.now())
    nd = col2.text_input("Nội dung")
    dv = col3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = col3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    submit = st.form_submit_button("💾 Lưu thông tin")
    if submit:
        wks, err = connect_to_sheet()
        if wks:
            wks.append_row([ngay.strftime('%d/%m/%Y'), nd, dv, tien])
            st.success("Lưu thành công rồi Như ơi! ✅")
            st.balloons()
        else:
            st.error(f"Lỗi không lưu được: {err}")

st.write("---")

# 5. HIỂN THỊ BẢNG DỮ LIỆU
wks, err = connect_to_sheet()
if wks:
    try:
        data = wks.get_all_records()
        if data:
            st.dataframe(pd.DataFrame(data).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Bảng đang trống. Như nhớ điền tiêu đề vào hàng 1 của Sheets nhé!")
    except Exception as e:
        st.warning(f"Kết nối OK nhưng chưa có dữ liệu: {e}")
else:
    st.error(f"⚠️ App chưa kết nối được với Google Sheets. Lỗi: {err}")
    st.info("Như nhớ: 1. Share file Sheets cho email trong Service Account. 2. Kiểm tra lại Secrets.")