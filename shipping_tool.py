import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"

# =========================
# CONNECT SHEET
# =========================
@st.cache_resource
def get_conn():

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
    return sh.sheet1


ws = get_conn()

# =========================
# SESSION STATE
# =========================
if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = [
        "Ahamove 🛵",
        "Grab 🚗",
        "Lalamove 🚛",
        "GHTK 📦"
    ]

if "refresh" not in st.session_state:
    st.session_state.refresh = False


# =========================
# SIDEBAR - THÊM / XOÁ ĐƠN VỊ
# =========================
with st.sidebar:
    st.header("⚙️ Đơn vị vận chuyển")

    moi = st.text_input("Thêm đơn vị mới")

    if st.button("➕ Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.success("Đã thêm")
            st.rerun()

    st.divider()

    xoa = st.selectbox("Chọn đơn vị để xoá", st.session_state.ds_donvi)

    if st.button("🗑️ Xoá đơn vị"):
        st.session_state.ds_donvi.remove(xoa)
        st.success(f"Đã xoá {xoa}")
        st.rerun()


# =========================
# TITLE
# =========================
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

# =========================
# NÚT LÀM TƯƠI
# =========================
col_refresh, _ = st.columns([1, 5])

with col_refresh:
    if st.button("🔄 Làm tươi dữ liệu"):
        st.cache_resource.clear()
        st.rerun()


# =========================
# FORM NHẬP LIỆU
# =========================
with st.form("nhap_lieu", clear_on_submit=True):

    c1, c2, c3, c4 = st.columns([1, 2, 2, 1])

    ngay = c1.date_input("Ngày", datetime.now())

    noidung = c2.text_input("Nội dung")

    donvi = c3.selectbox(
        "Đơn vị",
        st.session_state.ds_donvi
    )

    phi = c4.number_input("Phí (VNĐ)", min_value=0, step=1000)

    submit = st.form_submit_button("💾 Lưu")

    if submit:
        if not noidung:
            st.warning("Nhập nội dung")
        else:
            ws.append_row([
                ngay.strftime("%d/%m/%Y"),
                noidung,
                donvi,
                phi
            ])

            st.success("Đã lưu!")
            st.cache_resource.clear()
            st.rerun()


# =========================
# HIỂN THỊ DỮ LIỆU
# =========================
st.divider()

try:
    data = ws.get_all_values()

    if len(data) <= 1:
        st.info("Chưa có dữ liệu")
        st.stop()

    # header
    if data[0] != ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)']:
        ws.insert_row(['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)'], 1)
        data = ws.get_all_values()

    df = pd.DataFrame(data[1:], columns=data[0])

    df["Phí (VNĐ)"] = pd.to_numeric(df["Phí (VNĐ)"], errors="coerce").fillna(0)
    df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")

    # filter tháng
    thang_list = sorted(df["Ngày"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)

    if thang_list:

        thang = st.selectbox("📅 Chọn tháng", thang_list)

        df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]

        col1, col2 = st.columns([3, 1])

        col1.subheader(f"Dữ liệu tháng {thang}")
        col2.metric("Tổng chi phí", f"{df_f['Phí (VNĐ)'].sum():,.0f} VNĐ")

        st.dataframe(df_f, use_container_width=True, hide_index=True)

    else:
        st.info("Chưa có dữ liệu tháng")

except Exception as e:
    st.error("Lỗi hiển thị dữ liệu")
    st.exception(e)