import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# Hàm kết nối an toàn
def get_gsheet_client():
    try:
        if "connections" not in st.secrets:
            return None, "Chưa cấu hình Secrets trong App Settings"
        
        conf = st.secrets["connections"]["gsheets"]
        # Xử lý ký tự xuống dòng trong private_key
        p_key = conf["private_key"].replace("\\n", "\n")
        
        credentials = {
            "type": conf["type"],
            "project_id": conf["project_id"],
            "private_key_id": conf["private_key_id"],
            "private_key": p_key,
            "client_email": conf["client_email"],
            "client_id": conf["client_id"],
            "auth_uri": conf["auth_uri"],
            "token_uri": conf["token_uri"],
            "auth_provider_x509_cert_url": conf["auth_provider_x509_cert_url"],
            "client_x509_cert_url": conf["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        # Link sheet của Như
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        return sh.worksheet("Trang tính1"), None
    except Exception as e:
        return None, str(e)

# --- GIAO DIỆN ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị mới")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()

# Khối nhập liệu
with st.form("form_nhap", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 2, 1])
    ngay = c1.date_input("Ngày", datetime.now())
    nd = c2.text_input("Nội dung")
    dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    submit = st.form_submit_button("💾 Lưu thông tin")
    if submit:
        wks, err = get_gsheet_client()
        if wks:
            wks.append_row([ngay.strftime('%d/%m/%Y'), nd, dv, tien])
            st.success("Đã lưu thành công! ✅")
            st.balloons()
        else:
            st.error(f"Lỗi kết nối: {err}")

# Hiển thị bảng dữ liệu
st.write("---")
wks, err = get_gsheet_client()
if wks:
    try:
        data = wks.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có dữ liệu trong file Sheets.")
    except:
        st.warning("Không thể hiển thị bảng dữ liệu.")
else:
    st.error(f"Không thể tải dữ liệu: {err}")