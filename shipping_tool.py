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
        
        # XỬ LÝ KHÓA (PRIVATE KEY) CỰC MẠNH:
        # Loại bỏ khoảng trắng thừa và ép định dạng chuẩn
        raw_key = c["private_key"].strip()
        # Nếu Như lỡ dán có xuống dòng thật, nó sẽ được xử lý lại
        key = raw_key.replace("\\n", "\n")
        
        json_key = {
            "type": c["type"], "project_id": c["project_id"],
            "private_key_id": c["private_key_id"], "private_key": key,
            "client_email": c["client_email"], "client_id": c["client_id"],
            "auth_uri": c["auth_uri"], "token_uri": c["token_uri"],
            "auth_provider_x509_cert_url": c["auth_provider_x509_cert_url"],
            "client_x509_cert_url": c["client_x509_cert_url"]
        }
        
        client = gspread.service_account_from_dict(json_key)
        # Link sheet của Như
        file_sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        return file_sheet.worksheet("Trang tính1")
    except Exception as error:
        return f"Lỗi chìa khóa: {str(error)}"

# --- PHẦN HIỂN THỊ ---
def tai_du_lieu():
    kq = lay_ket_noi()
    if not isinstance(kq, str):
        try:
            return pd.DataFrame(kq.get_all_records())
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

with st.form("form_nhap", clear_on_submit=True):
    col1, col2, col3 = st.columns([1, 2, 1])
    ngay = col1.date_input("Ngày", datetime.now())
    nd = col2.text_input("Nội dung")
    dv = col3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = col3.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        sh = lay_ket_noi()
        if not isinstance(sh, str):
            sh.append_row([ngay.strftime('%d/%m/%Y'), nd, dv, tien])
            st.success("Đã lưu vào Sheets thành công! ✅")
            st.balloons()
            st.rerun()
        else:
            st.error(sh)

df = tai_du_lieu()
if not df.empty:
    st.write("---")
    st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu hoặc lỗi kết nối chìa khóa.")