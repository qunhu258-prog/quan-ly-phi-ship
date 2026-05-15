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
# CONNECT SHEET
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
# UI STYLE
# =========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 18px;
}

h1 {
    font-size: 38px !important;
    color: #ff4b4b;
}

.total-box {
    background: #fff3cd;
    padding: 12px;
    border-radius: 12px;
    font-weight: bold;
    color: #856404;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)


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
# SIDEBAR
# =========================
with st.sidebar:
    st.header("⚙️ Cài đặt")

    moi = st.text_input("Thêm đơn vị mới")

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

    c1, c2, c3 = st.columns([1, 2, 1])

    input_ngay = c1.date_input("Ngày", datetime.now())
    input_nd = c2.text_input("Nội dung")
    input_dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)
    input_tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)

    submit = st.form_submit_button("💾 Lưu")

    if submit:
        wks, err = ket_noi_sheet()

        if wks:
            wks.append_row([
                input_ngay.strftime('%d/%m/%Y'),
                input_nd,
                input_dv,
                input_tien
            ])

            st.success("Đã lưu!")
            st.cache_resource.clear()
            st.rerun()

        else:
            st.error(err)


# =========================
# LOAD DATA
# =========================
st.write("---")

wks, err = ket_noi_sheet()

if not wks:
    st.error(err)
    st.stop()

data = wks.get_all_values()

if len(data) <= 1:
    st.info("Chưa có dữ liệu")
    st.stop()

if data[0] != ['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)']:
    wks.insert_row(['Ngày', 'Nội dung', 'Đơn vị', 'Phí (VNĐ)'], 1)
    data = wks.get_all_values()

df = pd.DataFrame(data[1:], columns=data[0])


# =========================
# FIX TIỀN
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

thang_chon = st.selectbox("📅 Chọn tháng", thang_list)

df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang_chon]


# =========================
# HIỂN THỊ DỮ LIỆU
# =========================
st.subheader("📦 Danh sách giao dịch")

tong = int(df_f["Phí (VNĐ)"].sum())


for i, row in df_f.iterrows():

    c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 1])

    c1.write(i)
    c2.write(row["Nội dung"])
    c3.write(row["Đơn vị"])
    c4.write(f"{row['Phí (VNĐ)']:,} VNĐ")

    if c5.button("❌", key=f"del_{i}"):

        wks.delete_rows(i + 2)
        st.cache_resource.clear()
        st.rerun()


# =========================
# TỔNG CỘNG (CUỐI BẢNG - TÔ MÀU + IN ĐẬM)
# =========================
st.markdown("---")

st.markdown(
    f"""
    <div class="total-box">
        💰 TỔNG CỘNG THÁNG {thang_chon}: {tong:,.0f} VNĐ
    </div>
    """,
    unsafe_allow_html=True
)