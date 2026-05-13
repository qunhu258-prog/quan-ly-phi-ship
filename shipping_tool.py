import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def connect_to_sheet():
    try:
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
        
        # PHƯƠNG ÁN 1: Mở bằng ID (Lấy từ URL của Như: 1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg)
        sheet_id = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"
        sh = gc.open_by_key(sheet_id)
        
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

# --- GIAO DIỆN ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.form("form_nhap", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    ngay = col1.date_input("Ngày", datetime.now())
    nd = col2.text_input("Nội dung")
    dv = col3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = col3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        wks, err = connect_to_sheet()
        if wks:
            wks.append_row([ngay.strftime('%d/%m/%Y'), nd, dv, tien])
            st.success("Lưu thành công rồi Như ơi! Đi nghỉ thôi nào! ✅")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Lỗi kết nối chi tiết: {err}")

st.write("---")
# Hiển thị bảng dữ liệu
wks, err = connect_to_sheet()
if wks:
    try:
        data = wks.get_all_records()
        if data:
            st.dataframe(pd.DataFrame(data).iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Bảng đang trống. Như nhớ điền tiêu đề 'Ngày, Nội dung, Đơn vị, Phí' vào hàng 1 của Sheets nhé!")
    except Exception as e:
        st.warning(f"Đã kết nối nhưng chưa đọc được dữ liệu: {e}")
else:
    st.error(f"Kết nối thất bại hoàn toàn: {err}")