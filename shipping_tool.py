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
# UI STYLE (TO + ĐẸP)
# =========================
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-size: 18px;
}

h1 {
    font-size: 38px !important;
    color: #ff4b4b;
}

.stButton button {
    border-radius: 12px;
    font-size: 16px;
    padding: 8px 14px;
}

div[data-testid="metric-container"] {
    background-color: #f5f7ff;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# CONNECT GOOGLE SHEETS
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

st.title("🚚 Quản Lý Chi Phí Giao Hàng")


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


# =========================
# SIDEBAR - QUẢN LÝ ĐƠN VỊ
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
        st.success("Đã xoá")
        st.rerun()


# =========================
# NÚT LÀM TƯƠI
# =========================
if st.button("🔄 Làm tươi dữ liệu"):
    st.cache_resource.clear()
    st.rerun()


# =========================
# FORM NHẬP LIỆU
# =========================
with st.form("nhap_lieu", clear_on_submit=True):

    c1, c2, c3, c4 = st.columns([1, 2, 2, 1])

    ngay = c1.date_input("Ngày", datetime.now())

    noidung = c2.text_input("Nội dung giao hàng")

    donvi = c3.selectbox("Đơn vị", st.session_state.ds_donvi)

    phi = c4.number_input(
        "Phí (VNĐ)",
        min_value=0,
        step=1000,
        format="%d"
    )

    submit = st.form_submit_button("💾 Lưu")

    if submit:
        if not noidung:
            st.warning("Vui lòng nhập nội dung")
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
# LẤY DỮ LIỆU
# =========================
st.divider()

data = ws.get_all_values()

if len(data) <= 1:
    st.info("Chưa có dữ liệu")
    st.stop()

# tạo header nếu chưa có
if data[0] != ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)']:
    ws.insert_row(['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)'], 1)
    data = ws.get_all_values()

df = pd.DataFrame(data[1:], columns=data[0])


# =========================
# FIX TIỀN = 0 LỖI
# =========================
def clean_money(x):
    x = str(x)
    x = re.sub(r"[^\d]", "", x)
    return int(x) if x else 0


df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(clean_money)

df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")


# =========================
# FILTER THÁNG
# =========================
thang_list = sorted(
    df["Ngày"].dt.strftime("%m/%Y").dropna().unique(),
    reverse=True
)

if not thang_list:
    st.info("Chưa có dữ liệu tháng")
    st.stop()

thang = st.selectbox("📅 Chọn tháng", thang_list)

df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]


# =========================
# TỔNG TIỀN
# =========================
tong = int(df_f["Phí (VNĐ)"].sum())


c1, c2 = st.columns([3, 1])
c1.subheader(f"📋 Dữ liệu tháng {thang}")
c2.metric("💰 Tổng chi phí", f"{tong:,.0f} VNĐ")


# =========================
# HIỂN THỊ + XOÁ DÒNG
# =========================
st.subheader("🧾 Danh sách chi phí")

for i, row in df_f.iterrows():

    c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 1])

    c1.write(i)
    c2.write(row["Nội dung"])
    c3.write(row["Đơn vị"])
    c4.write(f"{row['Phí (VNĐ)']:,} VNĐ")

    if c5.button("🗑️", key=f"del_{i}"):

        ws.delete_rows(i + 2)  # +2 vì header + index sheet
        st.success("Đã xoá dòng")
        st.cache_resource.clear()
        st.rerun()


# =========================
# TABLE FULL
# =========================
st.divider()
st.dataframe(df_f, use_container_width=True, hide_index=True)


# =========================
# EXPORT CSV
# =========================
csv = df_f.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "📥 Tải báo cáo CSV",
    csv,
    f"bao_cao_{thang}.csv",
    "text/csv"
)