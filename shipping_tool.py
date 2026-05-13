import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def lay_ket_noi():
    try:
        if "connections" not in st.secrets:
            return "Thiếu cấu hình Secrets"
        
        c = st.secrets["connections"]["gsheets"]
        
        # XỬ LÝ LỖI PEM: Loại bỏ khoảng trắng và xử lý xuống dòng
        key = c["private_key"].strip().replace("\\n", "\n")
        
        json_key = {
            "type": c["type"], "project_id": c["project_id"],
            "private_key_id": c["private_key_id"], "private_key": key,
            "client_email": c["client_email"], "client_id": c["client_id"],
            "auth_uri": c["auth_uri"], "token_uri": c["token_uri"],
            "auth_provider_x509_cert_url": c["auth_provider_x509_cert_url"],
            "client_x509_cert_url": c["client_x509_cert_url"]
        }
        
        client = gspread.service_account_from_dict(json_key)
        file_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        return file_sheet.worksheet("Trang tính1")
    except Exception as error:
        return f"Lỗi PEM/Kết nối: {str(error)}"

# --- GIỮ NGUYÊN PHẦN GIAO DIỆN PHÍA DƯỚI ---
def tai_du_lieu():
    kq = lay_ket_noi()
    if not isinstance(kq, str):
        try:
            data = kq.get_all_records()
            return pd.DataFrame(data)
        except: pass
    return pd.DataFrame()

if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()
    st.write("---")
    xoa = st.selectbox("Xóa đơn vị", st.session_state.ds_donvi)
    if st.button("Xóa"):
        if len(st.session_state.ds_donvi) > 1:
            st.session_state.ds_donvi.remove(xoa)
            st.rerun()

with st.form("form_nhap", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    ngay = col1.date_input("Ngày", datetime.now())
    nd = col2.text_input("Nội dung")
    dv = col3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = col3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        ket_qua_luu = lay_ket_noi()
        if not isinstance(ket_qua_luu, str):
            # Định dạng ngày về dd/mm/yyyy để Sheets dễ hiểu
            ket_qua_luu.append_row([ngay.strftime('%d/%m/%Y'), nd, dv, tien])
            st.success("Lưu thành công!")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Không thể lưu. {ket_qua_luu}")

df = tai_du_lieu()
if not df.empty:
    st.write("---")
    st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu hoặc lỗi kết nối.")