import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def lay_ket_noi():
    try:
        # Lấy thông tin từ Secrets
        c = st.secrets["connections"]["gsheets"]
        p_key = c["private_key"].replace("\\n", "\n")
        
        credentials = {
            "type": c["type"], "project_id": c["project_id"],
            "private_key_id": c["private_key_id"], "private_key": p_key,
            "client_email": c["client_email"], "client_id": c["client_id"],
            "auth_uri": c["auth_uri"], "token_uri": c["token_uri"],
            "auth_provider_x509_cert_url": c["auth_provider_x509_cert_url"],
            "client_x509_cert_url": c["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        # Mở file bằng URL
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        # Tự động lấy trang đầu tiên (không cần quan tâm tên là gì)
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

# --- GIAO DIỆN CHÍNH ---
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

with st.form("nhap_lieu", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    n = col1.date_input("Ngày", datetime.now())
    nd = col2.text_input("Nội dung")
    dv = col3.selectbox("Đơn vị", st.session_state.ds_donvi)
    t = col3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        ws, err = lay_ket_noi()
        if ws:
            ws.append_row([n.strftime('%d/%m/%Y'), nd, dv, t])
            st.success("Lưu thành công rồi Như ơi! ✅")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Lỗi kết nối: {err}")

st.write("---")
# Hiển thị bảng
ws, err = lay_ket_noi()
if ws:
    try:
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Bảng đang trống, Như hãy nhập đơn đầu tiên nhé!")
    except:
        st.warning("Gợi ý: Dòng đầu tiên trong Sheets phải là: Ngày, Nội dung, Đơn vị, Phí")
else:
    st.error(f"Kết nối thất bại: {err}")