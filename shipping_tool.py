import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def get_conn():
    try:
        # Cách lấy secrets an toàn nhất cho Streamlit Cloud
        s = st.secrets
        creds = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        gc = gspread.service_account_from_dict(creds)
        # Mở trực tiếp bằng ID và lấy sheet đầu tiên
        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

# --- SIDEBAR ---
if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị mới")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()

# --- GIAO DIỆN ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.form("nhap_lieu", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 2, 1])
    ng = c1.date_input("Ngày", datetime.now())
    nd = c2.text_input("Nội dung")
    dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    t = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        ws, err = get_conn()
        if ws:
            ws.append_row([ng.strftime('%d/%m/%Y'), nd, dv, t])
            st.success("Xong rồi Như ơi! ✅")
            st.balloons()
        else:
            st.error(f"Lỗi lưu: {err}")

st.write("---")
# Hiển thị bảng
ws, err = get_conn()
if ws:
    try:
        data = ws.get_all_records()
        if data:
            st.dataframe(pd.DataFrame(data).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Bảng trống. Hàng 1 Sheets cần có: Ngày, Nội dung, Đơn vị, Phí")
    except:
        st.warning("Như kiểm tra lại tiêu đề ở hàng 1 trong Sheets nhé.")
else:
    st.error(f"Kết nối thất bại: {err}")