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
# STYLE
# =========================
st.markdown("""
<style>

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
    padding: 10px 8px;
    border-bottom: 1px solid #eee;
    align-items: center;
}

/* HOVER */
.row:hover {
    background: #f3f6ff;
}

/* KHÔNG XUỐNG DÒNG */
.c1,.c2,.c3,.c4,.c5,.c6 {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* COL WIDTH */
.c1 { width: 6%; }
.c2 { width: 14%; }
.c3 { width: 42%; }
.c4 { width: 18%; }
.c5 { width: 15%; }
.c6 { width: 5%; }

/* BUTTON XOÁ (KHÔNG ĐỎ) */
button {
    background: #f3f4f6 !important;
    color: black !important;
    border: 1px solid #ddd !important;
    border-radius: 6px !important;
}

/* TOTAL */
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
# TITLE
# =========================
st.title("🚚 CHI PHÍ GIAO HÀNG")


# =========================
# SESSION STATE
# =========================
if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]


# =========================
# SIDEBAR
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
df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")


# =========================
# FILTER MONTH
# =========================
months = sorted(df["Ngày"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)
thang = st.selectbox("📅 Chọn tháng", months)

df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]


# =========================
# HEADER
# =========================
st.markdown("""
<style>
    /* Triệt tiêu khoảng trắng giữa các cột trong Header */
    div[data-testid="stHorizontalBlock"]:has(.header-col) {
        gap: 0px !important;
    }

    /* Style cho Header: Chữ trắng, in đậm, size to */
    .header-col {
        background-color: #1f77b4;
        color: white;
        font-weight: bold;
        font-size: 18px;
        padding: 12px 5px;
        text-align: center;
        border-right: 0.1px solid #ffffff33;
    }

    /* Bo góc cho 2 đầu thanh header */
    .header-left { border-radius: 8px 0 0 0; }
    .header-right { border-radius: 0 8px 0 0; border-right: none; }

    /* Style cho dòng dữ liệu: Chữ to (18px), căn giữa dọc */
    .row-style {
        font-size: 18px; 
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 10px 0;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Căn giữa tuyệt đối cho cột chứa nút Xóa */
    [data-testid="column"]:last-child {
        display: flex;
        justify-content: center;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# 2. PHẦN HIỂN THỊ HEADER
with st.container():
    # Tỷ lệ cột khớp hoàn toàn với phần dữ liệu
    h1, h2, h3, h4, h5, h6 = st.columns([1, 2.5, 7, 3, 3, 1.5])
    h1.markdown('<div class="header-col header-left">STT</div>', unsafe_allow_html=True)
    h2.markdown('<div class="header-col">Ngày</div>', unsafe_allow_html=True)
    h3.markdown('<div class="header-col">Nội dung</div>', unsafe_allow_html=True)
    h4.markdown('<div class="header-col">ĐVVC</div>', unsafe_allow_html=True)
    h5.markdown('<div class="header-col">Phí</div>', unsafe_allow_html=True)
    h6.markdown('<div class="header-col header-right">Xóa</div>', unsafe_allow_html=True)

# 3. PHẦN HIỂN THỊ DỮ LIỆU
for idx, (i, row) in enumerate(df_f.iterrows(), start=1):
    ngay_txt = row["Ngày"].strftime("%d/%m/%Y") if not pd.isna(row["Ngày"]) else ""
    
    with st.container():
        c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 7, 3, 3, 1.5])
        
        c1.markdown(f"<div class='row-style'>{idx}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='row-style'>{ngay_txt}</div>", unsafe_allow_html=True)
        
        # Cột nội dung căn lề trái (left) để dễ đọc, có tooltip
        c3.markdown(f"<div class='row-style' style='text-align: left; justify-content: flex-start; padding-left: 10px;' title='{row['Nội dung']}'>{row['Nội dung']}</div>", unsafe_allow_html=True)
        
        c4.markdown(f"<div class='row-style'>{row['Đơn vị']}</div>", unsafe_allow_html=True)
        c5.markdown(f"<div class='row-style'><b>{row['Phí (VNĐ)']:,}</b></div>", unsafe_allow_html=True)
        
        # Cột nút Xóa: Nằm chính giữa
        with c6:
            if st.button("❌", key=f"del_{i}"):
                ws.delete_rows(i + 2)
                st.cache_resource.clear()
                st.rerun()
        
        # Đường kẻ ngang mờ phân cách các dòng
        st.markdown('<hr style="margin: 0; border: 0.5px solid #f0f2f6;">', unsafe_allow_html=True)
    
# =========================
# TOTAL
# =========================
tong = int(df_f["Phí (VNĐ)"].sum())

st.markdown("---")

st.markdown(f"""
<div class="total-box">
💰 TỔNG CỘNG THÁNG {thang}: {tong:,.0f} VNĐ
</div>
""", unsafe_allow_html=True)