import streamlit as st

import gspread

import pandas as pd

import re

import datetime

from datetime import datetime as dt

from google.oauth2.service_account import Credentials

import streamlit.components.v1 as components



# =========================

# 1. CẤU HÌNH TRANG

# =========================

st.set_page_config(layout="wide", page_title="Quản lý phí Ship")



# =========================

# 2. TIỆN ÍCH SIDEBAR (NGÀY & THỜI TIẾT) - ĐÃ FIX MÚI GIỜ VN

# =========================

now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

thu_tieng_viet = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

thu = thu_tieng_viet[now.weekday()]

ngay_hien_tai = f"{thu}, ngày {now.strftime('%d/%m/%Y')}"



gio = now.hour

if 6 <= gio < 17:

    thoi_tiet = "Trời đang nắng đẹp ☀️"

elif 17 <= gio < 19:

    thoi_tiet = "Hoàng hôn lãng mạn 🌇"

else:

    thoi_tiet = "Trời đêm mát mẻ ✨"



# =========================

# 3. STYLE CSS TỔNG HỢP (SỬA LỖI KHOẢNG TRẮNG TRÊN CÙNG KHI IN)

# =========================

st.markdown("""

<style>

    .block-container { padding: 2rem 3rem; max-width: 100%; }

    

    /* Đổi màu tiêu đề st.title */

    h1 { color: #5B7E3C !important; }



    /* Taskbar sidebar */

    .taskbar-box {

        background-color: #f1f4ef; padding: 15px; border-radius: 10px; 

        border-left: 5px solid #5B7E3C; margin-bottom: 20px;

    }

    

    /* Header bảng */

    div[data-testid="stHorizontalBlock"]:has(.header-col) { gap: 0px !important; }

    .header-col {

        background-color: #5B7E3C; color: white; font-weight: bold;

        font-size: 18px; padding: 12px 5px; text-align: center;

        border-right: 0.1px solid #ffffff33;

    }

    .header-left { border-radius: 8px 0 0 0; }

    .header-right { border-radius: 0 8px 0 0; border-right: none; }

    

    /* Nội dung dòng bảng */

    .row-style {

        font-size: 18px; padding: 10px 0; display: flex;

        align-items: center; justify-content: center;

    }

    

    /* Tổng cộng tháng */

    .total-box {

        padding: 18px; border-radius: 15px; font-size: 22px;

        font-weight: bold; text-align: center;

        background-color: #5B7E3C; color: white;

        box-shadow: 0 4px 15px rgba(91, 126, 60, 0.3);

        margin-top: 20px;

    }



    /* Đổi màu các nút bấm Streamlit mặc định */

    .stButton > button {

        border-color: #5B7E3C !important;

        color: #5B7E3C !important;

    }

    .stButton > button:hover {

        background-color: #5B7E3C !important;

        color: white !important;

    }



    /* Tiêu đề ẩn trên web, chỉ hiện khi in */

    .print-title { display: none; }



    /* =========================================

       CSS ĐỊNH DẠNG RIÊNG KHI BẤM IN (PRINT)

       ========================================= */

    @media print {

        @page {

            size: landscape;

            margin: 5mm 10mm 10mm 10mm; /* Giảm hẳn lề trên xuống còn 5mm */

        }

        

        /* Ẩn các thành phần không liên quan */

        section[data-testid="stSidebar"], 

        div[data-testid="stForm"], 

        div.stSelectbox,

        header, 

        footer,

        h1,

        iframe,

        [data-testid="stHeader"],

        div.stButton { 

            display: none !important; 

        }

        

        /* TRIỆT TIÊU TOÀN BỘ KHOẢNG TRẮNG PHÍA TRÊN CỦA STREAMLIT */

        .main, .main .block-container, [data-testid="stMainBlockContainer"] {

            padding-top: 0px !important;

            margin-top: 0px !important;

            top: 0px !important;

        }



        /* Hiện tiêu đề in chuyên nghiệp */

        .print-title {

            display: block !important;

            color: #5B7E3C !important;

            text-align: center !important;

            margin-top: 0px !important;

            margin-bottom: 25px !important;

            font-size: 24px !important;

            font-weight: bold !important;

        }



        /* Định dạng bảng khi in */

        div[data-testid="stHorizontalBlock"] {

            display: flex !important;

            flex-direction: row !important;

            width: 100% !important;

            gap: 0px !important;

        }



        /* Ẩn cột Xóa (cột số 6) */

        div[data-testid="stHorizontalBlock"] > div:nth-child(6) {

            display: none !important;

        }



        /* Ép layout dòng chia tỉ lệ chuẩn khổ giấy ngang */

        div[data-testid="stHorizontalBlock"] > div:nth-child(1) { width: 6% !important; max-width: 6% !important; flex: 0 0 6% !important; }

        div[data-testid="stHorizontalBlock"] > div:nth-child(2) { width: 14% !important; max-width: 14% !important; flex: 0 0 14% !important; }

        div[data-testid="stHorizontalBlock"] > div:nth-child(3) { width: 50% !important; max-width: 50% !important; flex: 0 0 50% !important; }

        div[data-testid="stHorizontalBlock"] > div:nth-child(4) { width: 15% !important; max-width: 15% !important; flex: 0 0 15% !important; }

        div[data-testid="stHorizontalBlock"] > div:nth-child(5) { 

            width: 15% !important; max-width: 15% !important; flex: 0 0 15% !important;

            border-right: none !important;

        }

        div[data-testid="stHorizontalBlock"]:has(.header-col) > div:nth-child(5) .header-col {

            border-radius: 0 8px 0 0 !important;

        }



        .row-style, .header-col { font-size: 15px !important; padding: 6px 2px !important; }

    }

</style>

""", unsafe_allow_html=True)



# =========================

# 4. KẾT NỐI GOOGLE SHEETS

# =========================

SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg"



@st.cache_resource

def ket_noi_sheet():

    s = st.secrets

    creds_dict = {

        "type": s["type"], "project_id": s["project_id"], "private_key_id": s["private_key_id"],

        "private_key": s["private_key"], "client_email": s["client_email"], "client_id": s["client_id"],

        "auth_uri": s["auth_uri"], "token_uri": s["token_uri"],

        "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],

        "client_x509_cert_url": s["client_x509_cert_url"]

    }

    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)

    gc = gspread.authorize(creds)

    return gc.open_by_key(SHEET_ID).sheet1



ws = ket_noi_sheet()



# =========================

# 5. SIDEBAR GIAO DIỆN

# =========================

with st.sidebar:

    st.markdown(f'''

    <div class="taskbar-box">

        <p style="margin:0; font-size: 14px; color: #555;">📅 <b>Hôm nay:</b></p>

        <p style="margin:0; font-size: 16px; font-weight: bold;">{ngay_hien_tai}</p>

        <hr style="margin: 10px 0; border: 0.5px solid #ddd;">

        <p style="margin:0; font-size: 14px; color: #555;">🌤️ <b>Thời tiết:</b></p>

        <p style="margin:0; font-size: 16px; font-weight: bold;">{thoi_tiet}</p>

        <p style="margin-top:8px; font-size: 16px; font-weight: bold; color: #5B7E3C;">

            Vui vẻ lên nhé ✨🐻

        </p>

    </div>

    ''', unsafe_allow_html=True)



    st.header("⚙️ Cài đặt")

    

    data_all = ws.get_all_values()

    if len(data_all) > 1:

        df_all = pd.DataFrame(data_all[1:], columns=data_all[0])

        list_tu_sheet = df_all['Đơn vị'].unique().tolist()

    else:

        list_tu_sheet = []



    mac_dinh = ["Ahamove", "Grab", "Lalamove", "GHTK", "GHN", "Viettel Post"]

    if "ds_donvi" not in st.session_state:

        st.session_state.ds_donvi = list(set(mac_dinh + list_tu_sheet))



    new = st.text_input("Thêm đơn vị mới")

    if st.button("➕ Thêm"):

        if new and new not in st.session_state.ds_donvi:

            st.session_state.ds_donvi.append(new)

            st.rerun()



    if st.session_state.ds_donvi:

        del_unit = st.selectbox("Xóa đơn vị khỏi danh sách chọn", st.session_state.ds_donvi)

        if st.button("🗑 Xóa"):

            st.session_state.ds_donvi.remove(del_unit)

            st.rerun()



    if st.button("🔄 Làm tươi"):

        st.cache_resource.clear()

        st.rerun()



# =========================

# 6. NHẬP LIỆU & XỬ LÝ DỮ LIỆU

# =========================

st.title("🚚 CHI PHÍ GIAO HÀNG")

with st.form("form_nhap", clear_on_submit=True):

    c1, c2, c3 = st.columns([1, 3, 1])

    ngay = c1.date_input("Ngày", dt.now())

    nd = c2.text_input("Nội dung")

    dv = c3.selectbox("Đơn vị", st.session_state.ds_donvi)

    tien = c3.number_input("Phí (VNĐ)", min_value=0, step=1000)

    if st.form_submit_button("💾 Lưu dữ liệu"):

        ws.append_row([ngay.strftime("%d/%m/%Y"), nd, dv, int(tien)])

        st.cache_resource.clear()

        st.rerun()



data = ws.get_all_values()

if len(data) <= 1:

    st.info("Chưa có dữ liệu")

    st.stop()



df = pd.DataFrame(data[1:], columns=data[0])

df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(lambda x: int(re.sub(r"[^\d]", "", str(x)) or 0))

df["Ngày"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")

months = sorted(df["Ngày"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)



thang = st.selectbox("📅 Chọn tháng hiển thị", months)



df_f = df[df["Ngày"].dt.strftime("%m/%Y") == thang]

df_f = df_f.sort_values(by="Ngày", ascending=True)



# --- SỬA LỖI BẤM ĐƯỢC NHIỀU LẦN VỚI PHƯƠNG PHÁP CHUYỂN ĐỔI STATE ---

st.write(" ")

if st.button("🖨️ In ở đây bé ưi"):

    components.html("""

        <script>

            window.parent.print();

        </script>

    """, height=0)

    # Tự động reload nhẹ chạy ngầm để xóa trạng thái cũ, giúp nút bấm sẵn sàng cho lần tiếp theo

    st.session_state["print_triggered"] = True



# ========================================================

# 7. HIỂN THỊ BẢNG DỮ LIỆU

# ========================================================

st.markdown(f'<div class="print-title">CHI PHÍ GIAO HÀNG - THÁNG {thang}</div>', unsafe_allow_html=True)



h1, h2, h3, h4, h5, h6 = st.columns([1, 2.5, 7, 3, 3, 1.5])

h1.markdown('<div class="header-col header-left">STT</div>', unsafe_allow_html=True)

h2.markdown('<div class="header-col">Ngày</div>', unsafe_allow_html=True)

h3.markdown('<div class="header-col">Nội dung</div>', unsafe_allow_html=True)

h4.markdown('<div class="header-col">ĐVVC</div>', unsafe_allow_html=True)

h5.markdown('<div class="header-col">Phí</div>', unsafe_allow_html=True)

h6.markdown('<div class="header-col header-right">Xóa</div>', unsafe_allow_html=True)



for idx, (i, row) in enumerate(df_f.iterrows(), start=1):

    ngay_txt = row["Ngày"].strftime("%d/%m/%Y") if not pd.isna(row["Ngày"]) else ""

    c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 7, 3, 3, 1.5])

    c1.markdown(f"<div class='row-style'>{idx}</div>", unsafe_allow_html=True)

    c2.markdown(f"<div class='row-style'>{ngay_txt}</div>", unsafe_allow_html=True)

    c3.markdown(f"<div class='row-style' style='text-align:left; justify-content:flex-start; padding-left:10px;'>{row['Nội dung']}</div>", unsafe_allow_html=True)

    c4.markdown(f"<div class='row-style'>{row['Đơn vị']}</div>", unsafe_allow_html=True)

    c5.markdown(f"<div class='row-style'><b>{row['Phí (VNĐ)']:,}</b></div>", unsafe_allow_html=True)

    with c6:

        if st.button("❌", key=f"del_{i}"):

            ws.delete_rows(i + 2)

            st.cache_resource.clear()

            st.rerun()

    st.markdown('<hr style="margin:0; border:0.5px solid #f1f4ef;">', unsafe_allow_html=True)



# =========================

# 8. TỔNG CỘNG

# =========================

tong = int(df_f["Phí (VNĐ)"].sum())

st.markdown(f'<div class="total-box">💰 TỔNG CHI PHÍ THÁNG {thang}: {tong:,.0f} VNĐ</div>', unsafe_allow_html=True)