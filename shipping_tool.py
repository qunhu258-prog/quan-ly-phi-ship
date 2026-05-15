import streamlit as st
import gspread
import pandas as pd
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# CONFIG
# =========================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"

# =========================
# KẾT NỐI SHEET
# =========================
@st.cache_resource
def ket_noi_sheet():
    try:
        s = st.secrets

        creds_dict = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"],
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        gc = gspread.authorize(creds)

        sh = gc.open_by_key(SHEET_ID)
        return sh.sheet1, None

    except Exception as e:
        return None, str(e)


# =========================
# UI
# =========================
st.title("🚚 Quản Lý Chi Phí Giao Hàng")


# =========================
# SESSION STATE
# =========================
if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = [
        "Ahamove 🛵",
        "Grab 🚗",
        "Lalamove 🚛",
        "GHTK 📦"
    ]


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Cài đặt")

    moi = st.text_input("Thêm đơn vị mới")

    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()

    if st.button("🔄 Làm tươi dữ liệu"):
        st.cache_resource.clear()
        st.rerun()


# =========================
# FORM NHẬP LIỆU
# =========================
with st.form("form_nhap", clear_on_submit=True):

    c1, c2, c3 = st.columns([1, 2, 1])

    input_ngay = c1.date_input("Ngày", datetime.now())
    input_nd = c2.text_input("Nội dung")
    input_dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    input_tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)

    submit = st.form_submit_button("💾 Lưu thông tin")

    if submit:
        wks, err = ket_noi_sheet()

        if wks:
            wks.append_row([
                input_ngay.strftime('%d/%m/%Y'),
                input_nd,
                input_dv,
                input_tien
            ])

            st.success("Đã lưu thành công! ✅")
            st.balloons()
            st.cache_resource.clear()
            st.rerun()

        else:
            st.error(f"Lỗi: {err}")


# =========================
# HIỂN THỊ + XOÁ DÒNG
# =========================
st.write("---")

wks, err = ket_noi_sheet()

if wks:

    data = wks.get_all_values()

    if len(data) <= 1:
        st.info("Chưa có dữ liệu.")
        st.stop()

    # đảm bảo header
    if data[0] != ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)']:
        wks.insert_row(['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)'], 1)
        data = wks.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    # =========================
    # FIX TIỀN = 0
    # =========================
    def clean_money(x):
        x = str(x)
        x = re.sub(r"[^\d]", "", x)
        return int(x) if x else 0

    df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(clean_money)

    # =========================
    # HIỂN THỊ NGƯỢC MỚI NHẤT
    # =========================
    st.subheader("📋 Danh sách chi phí")

    for i, row in df[::-1].iterrows():

        c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 1])

        c1.write(i)
        c2.write(row["Nội dung"])
        c3.write(row["Đơn vị"])
        c4.write(f"{row['Phí (VNĐ)']:,} VNĐ")

        if c5.button("🗑️", key=f"del_{i}"):

            wks.delete_rows(i + 2)
            st.success("Đã xoá")
            st.cache_resource.clear()
            st.rerun()

else:
    st.error(f"Kết nối thất bại: {err}")