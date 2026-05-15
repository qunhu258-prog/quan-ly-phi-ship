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

.block-container {
    padding: 2rem 3rem;
    max-width: 100%;
}

/* HEADER */
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
    padding: 10px 8px;
    border-bottom: 1px solid #eee;
    transition: 0.2s;
}

/* HOVER */
.row:hover {
    background: #f3f6ff;
}

/* COL */
.c1 { width: 6%; }
.c2 { width: 14%; }
.c3 { width: 40%; }
.c4 { width: 18%; }
.c5 { width: 15%; }
.c6 { width: 7%; }

.total-box {
    padding: 18px;
    border-radius: 15px;
    font-size: 22px;
    font-weight: bold;
    text-align: center;
    background: linear-gradient(90deg,#ffeaa7,#fab1a0);
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
# SESSION STATE
# =========================
if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]


# =========================
# SIDEBAR (RESTORED)
# =========================
with st.sidebar:
    st.header("⚙️ Đơn vị vận chuyển")

    new = st.text_input("Thêm đơn vị")

    if st.button("➕ Thêm"):
        if new and new not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(new)
            st.rerun()

    if st.session_state.ds_donvi:
        del_unit = st.selectbox("Xóa đơn vị", st.session_state.ds_donvi)

        if st.button("🗑 Xóa"):
            st.session_state.ds_donvi.remove(del_unit)
            st.rerun()

    st.divider()

    if st.button("🔄 Làm tươi"):
        st.cache_resource.clear()
        st.rerun()


# =========================
# TITLE
# =========================
st.title("🚚 DASHBOARD CHI PHÍ GIAO HÀNG")


# =========================
# FORM NHẬP LIỆU (RESTORED)
# =========================
with st.form("form_nhap", clear_on_submit=True):

    c1, c2, c3 = st.columns([1, 3, 1])

    ngay = c1.date_input("Ngày", datetime.now())
    nd = c2.text_input("Nội dung")
    dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)

    if st.form_submit_button("💾 Lưu"):
        ws.append_row([ngay.strftime("%d/%m/%Y"), nd, dv, int(tien)])
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
# CLEAN
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
# KPI
# =========================
tong = int(df_f["Phí (VNĐ)"].sum())

c1, c2, c3 = st.columns(3)
c1.metric("📦 Số đơn", len(df_f))
c2.metric("💰 Tổng chi", f"{tong:,.0f} VNĐ")
c3.metric("🚚 TB / đơn", f"{tong/max(len(df_f),1):,.0f}")


st.write("---")


# =========================
# HEADER TABLE
# =========================
st.markdown("""
<div class="header-row">
    <div class="c1">STT</div>
    <div class="c2">Ngày</div>
    <div class="c3">Nội dung</div>
    <div class="c4">ĐVVC</div>
    <div class="c5">Phí</div>
    <div class="c6">Xoá</div>
</div>
""", unsafe_allow_html=True)


# =========================
# ROWS
# =========================
for idx, (i, row) in enumerate(df_f.iterrows(), start=1):

    ngay = row["Ngày"].strftime("%d/%m/%Y") if not pd.isna(row["Ngày"]) else ""

    c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.4, 4, 2, 1.5, 0.8])

    c1.markdown(f"<div class='row c1'>{idx}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='row c2'>{ngay}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='row c3'>{row['Nội dung']}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='row c4'>{row['Đơn vị']}</div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='row c5'><b>{row['Phí (VNĐ)']:,} VNĐ</b></div>", unsafe_allow_html=True)

    if c6.button("❌", key=f"del_{i}"):
        ws.delete_rows(i + 2)
        st.cache_resource.clear()
        st.rerun()


# =========================
# TOTAL
# =========================
st.markdown("---")

st.markdown(f"""
<div class="total-box">
💰 TỔNG CỘNG THÁNG {thang}: {tong:,.0f} VNĐ
</div>
""", unsafe_allow_html=True)