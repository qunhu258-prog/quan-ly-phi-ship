import streamlit as st
import gspread
import pandas as pd
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# FULL WIDTH LAYOUT
# =========================
st.set_page_config(layout="wide")

# =========================
# CONFIG
# =========================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"


# =========================
# CONNECT SHEET
# =========================
@st.cache_resource
def ket_noi_sheet():
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


ws = ket_noi_sheet()


# =========================
# FULL WIDTH CSS
# =========================
st.markdown("""
<style>
.block-container {
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 100%;
}

h1 {
    font-size: 40px !important;
}

.total-box {
    background: #fff3cd;
    padding: 12px;
    border-radius: 12px;
    font-weight: bold;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# TITLE
# =========================
st.title("🚚 Quản Lý Chi Phí Giao Hàng")


# =========================
# SESSION STATE
# =========================
if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Cài đặt")

    moi = st.text_input("Thêm đơn vị")

    if st.button("➕ Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()

    if st.button("🔄 Làm tươi"):
        st.cache_resource.clear()
        st.rerun()


# =========================
# FORM NHẬP
# =========================
with st.form("form_nhap", clear_on_submit=True):

    c1, c2, c3 = st.columns([1, 3, 1])

    ngay = c1.date_input("Ngày", datetime.now())
    nd = c2.text_input("Nội dung")
    dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)

    if st.form_submit_button("💾 Lưu"):
        ws.append_row([ngay.strftime("%d/%m/%Y"), nd, dv, int(tien)])
        st.success("Đã lưu")
        st.cache_resource.clear()
        st.rerun()


# =========================
# LOAD DATA
# =========================
data = ws.get_all_values()

if len(data) <= 1:
    st.info("Chưa có dữ liệu")
    st.stop()

df = pd.DataFrame(data[1:], columns=data[0])


# =========================
# CLEAN MONEY
# =========================
def clean_money(x):
    return int(re.sub(r"[^\d]", "", str(x)) or 0)


df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(clean_money)


# =========================
# FILTER MONTH
# =========================
df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")

months = sorted(df["Ngày"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)

thang = st.selectbox("📅 Chọn tháng", months)

df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]


# =========================
# TABLE CUSTOM (STT = 1)
# =========================
st.subheader("📦 Chi tiết giao dịch")

tong = int(df_f["Phí (VNĐ)"].sum())


for idx, (_, row) in enumerate(df_f.iterrows(), start=1):

    c1, c2, c3, c4, c5 = st.columns([0.5, 3, 2, 2, 1])

    c1.write(idx)  # ⭐ STT bắt đầu từ 1
    c2.write(row["Nội dung"])
    c3.write(row["Đơn vị"])
    c4.write(f"{row['Phí (VNĐ)']:,} VNĐ")

    if c5.button("❌", key=f"del_{idx}"):

        ws.delete_rows(df_f.index[idx-1] + 2)
        st.cache_resource.clear()
        st.rerun()


# =========================
# TOTAL AT BOTTOM
# =========================
st.markdown("---")

st.markdown(
    f"""
    <div class="total-box">
        💰 TỔNG CỘNG THÁNG {thang}: {tong:,.0f} VNĐ
    </div>
    """,
    unsafe_allow_html=True
)