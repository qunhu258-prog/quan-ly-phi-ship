import streamlit as st
import gspread
import pandas as pd
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# =========================
# FULL WIDTH
# =========================
st.set_page_config(layout="wide")

# =========================
# STYLE PRO TABLE
# =========================
st.markdown("""
<style>

/* FULL WIDTH */
.block-container {
    padding: 2rem 3rem;
    max-width: 100%;
}

/* HEADER STICKY */
.header-row {
    display: flex;
    font-weight: bold;
    background: #111827;
    color: white;
    padding: 12px 8px;
    border-radius: 10px;
    position: sticky;
    top: 0;
    z-index: 100;
}

/* ROW */
.row {
    display: flex;
    padding: 12px 8px;
    border-bottom: 1px solid #eee;
    transition: 0.2s;
}

/* HOVER EFFECT */
.row:hover {
    background: #f3f6ff;
    transform: scale(1.002);
}

/* COL WIDTH */
.col-stt { width: 6%; }
.col-date { width: 14%; }
.col-content { width: 40%; }
.col-unit { width: 18%; }
.col-money { width: 15%; }
.col-action { width: 7%; }

/* DELETE BUTTON */
.delete-btn button {
    background: #ff4b4b;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 4px 8px;
}
</style>
""", unsafe_allow_html=True)


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
# TITLE
# =========================
st.title("🚚 CHI PHÍ GIAO HÀNG")


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
# TOTAL
# =========================
tong = int(df_f["Phí (VNĐ)"].sum())

col1, col2, col3 = st.columns(3)
col1.metric("📦 Số đơn", len(df_f))
col2.metric("💰 Tổng chi", f"{tong:,.0f} VNĐ")
col3.metric("🚚 TB / đơn", f"{tong/max(len(df_f),1):,.0f} VNĐ")


st.write("---")


# =========================
# HEADER TABLE
# =========================
st.markdown("""
<div class="header-row">
    <div class="col-stt">STT</div>
    <div class="col-date">Ngày</div>
    <div class="col-content">Nội dung</div>
    <div class="col-unit">ĐVVC</div>
    <div class="col-money">Phí</div>
    <div class="col-action">Xoá</div>
</div>
""", unsafe_allow_html=True)


# =========================
# ROWS
# =========================
for idx, (i, row) in enumerate(df_f.iterrows(), start=1):

    ngay = row["Ngày"].strftime("%d/%m/%Y") if not pd.isna(row["Ngày"]) else ""

    c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.4, 4, 2, 1.5, 0.8])

    c1.markdown(f"<div class='row'>{idx}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='row'>{ngay}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='row'>{row['Nội dung']}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='row'>{row['Đơn vị']}</div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='row'><b>{row['Phí (VNĐ)']:,} VNĐ</b></div>", unsafe_allow_html=True)

    if c6.button("❌", key=f"del_{i}"):
        ws.delete_rows(i + 2)
        st.cache_resource.clear()
        st.rerun()


# =========================
# TOTAL BOTTOM
# =========================
st.markdown("---")

st.markdown(f"""
<div style="
    padding:18px;
    border-radius:14px;
    font-size:22px;
    font-weight:bold;
    text-align:center;
    background: linear-gradient(90deg,#ffeaa7,#fab1a0);
">
💰 TỔNG CỘNG THÁNG {thang}: {tong:,.0f} VNĐ
</div>
""", unsafe_allow_html=True)