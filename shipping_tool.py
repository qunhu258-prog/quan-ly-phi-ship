import streamlit as st
import gspread
import pandas as pd
import re
import altair as alt
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# FULL WIDTH UI
# =========================
st.set_page_config(layout="wide")

st.markdown("""
<style>
.block-container {
    padding: 2rem 3rem;
    max-width: 100%;
}

h1 {
    font-size: 42px !important;
    color: #ff4b4b;
}

/* CARD giao dịch */
.card {
    padding: 12px 14px;
    border-radius: 12px;
    background: #f7f9ff;
    margin-bottom: 10px;
    border: 1px solid #e6e9ff;
}

.total-box {
    padding: 18px;
    border-radius: 15px;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg, #ffeaa7, #fab1a0);
}
</style>
""", unsafe_allow_html=True)


# =========================
# CONFIG SHEET
# =========================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"


# =========================
# CONNECT GOOGLE SHEET
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
# TITLE
# =========================
st.title("🚚 Dashboard Quản Lý Chi Phí Giao Hàng")


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
df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")


# =========================
# FILTER MONTH
# =========================
months = sorted(df["Ngày"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)
thang = st.selectbox("📅 Chọn tháng", months)

df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]


# =========================
# KPI DASHBOARD
# =========================
tong = int(df_f["Phí (VNĐ)"].sum())

col1, col2, col3 = st.columns(3)

col1.metric("📦 Số đơn", len(df_f))
col2.metric("💰 Tổng chi", f"{tong:,.0f} VNĐ")
col3.metric("🚚 Trung bình / đơn", f"{tong/max(len(df_f),1):,.0f} VNĐ")


st.write("---")


# =========================
# CHART THEO ĐƠN VỊ
# =========================
chart_data = df_f.groupby("Đơn vị")["Phí (VNĐ)"].sum().reset_index()

bar = alt.Chart(chart_data).mark_bar().encode(
    x="Đơn vị",
    y="Phí (VNĐ)",
    color="Đơn vị"
)

st.altair_chart(bar, use_container_width=True)


st.write("---")


# =========================
# LIST GIAO DỊCH (CARD UI)
# =========================
st.subheader("📦 Chi tiết giao dịch")

for idx, (_, row) in enumerate(df_f.iterrows(), start=1):

    st.markdown(f"""
    <div class="card">
        <b>#{idx}</b> — {row['Nội dung']} <br>
        🚚 {row['Đơn vị']} <br>
        💰 <b>{row['Phí (VNĐ)']:,} VNĐ</b> <br>
        📅 {row['Ngày'].strftime('%d/%m/%Y') if not pd.isna(row['Ngày']) else ''}
    </div>
    """, unsafe_allow_html=True)


# =========================
# TOTAL BANNER
# =========================
st.markdown(f"""
<div class="total-box">
💰 TỔNG CỘNG THÁNG {thang}: {tong:,.0f} VNĐ
</div>
""", unsafe_allow_html=True)