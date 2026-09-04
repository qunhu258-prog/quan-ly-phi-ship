import streamlit as st
import gspread
import pandas as pd
import re
import datetime
from datetime import datetime as dt
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# ==========================================
# 1. CẤU HÌNH TRANG
# ==========================================
st.set_page_config(
    layout="wide",
    page_title="Quản lý phí Ship"
)

# ==========================================
# 2. TIỆN ÍCH SIDEBAR (NGÀY & THỜI TIẾT)
# ==========================================
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

thu_tieng_viet = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật"
]

thu = thu_tieng_viet[now.weekday()]
ngay_hien_tai = f"{thu}, ngày {now.strftime('%d/%m/%Y')}"

gio = now.hour

if 6 <= gio < 17:
    thoi_tiet = "Trời đang nắng đẹp ☀️"
elif 17 <= gio < 19:
    thoi_tiet = "Hoàng hôn lãng mạn 🌇"
else:
    thoi_tiet = "Trời đêm mát mẻ ✨"


# ==========================================
# 3. STYLE CSS TỔNG HỢP
# ==========================================
st.markdown("""
<style>

    /* ==========================================
       GIAO DIỆN CHUNG
       ========================================== */

    .block-container {
        padding: 2rem 3rem;
        max-width: 100%;
    }

    h1 {
        color: #5B7E3C !important;
    }

    .taskbar-box {
        background-color: #f1f4ef;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #5B7E3C;
        margin-bottom: 20px;
    }


    /* ==========================================
       BẢNG DỮ LIỆU
       ========================================== */

    div[data-testid="stHorizontalBlock"]:has(.header-col) {
        gap: 0px !important;
    }

    .header-col {
        background-color: #5B7E3C;
        color: white;
        font-weight: bold;
        font-size: 16px;
        padding: 12px 5px;
        text-align: center;
        border-right: 0.1px solid #ffffff33;
    }

    .header-left {
        border-radius: 8px 0 0 0;
    }

    .header-right {
        border-radius: 0 8px 0 0;
        border-right: none;
    }

    .row-style {
        font-size: 16px;
        padding: 10px 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }


    /* ==========================================
       TỔNG CỘNG
       ========================================== */

    .total-box {
        padding: 18px;
        border-radius: 15px;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        background-color: #5B7E3C;
        color: white;
        box-shadow: 0 4px 15px rgba(91, 126, 60, 0.3);
        margin-top: 20px;
    }


    /* ==========================================
       BUTTON
       ========================================== */

    .stButton > button {
        border-color: #5B7E3C !important;
        color: #5B7E3C !important;
    }

    .stButton > button:hover {
        background-color: #5B7E3C !important;
        color: white !important;
    }


    /* ==========================================
       CARD TỔNG HỢP THEO ĐVVC
       ========================================== */

    .shipping-summary-title {
        font-size: 20px;
        font-weight: bold;
        color: #5B7E3C;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .shipping-card {
        background: #f1f4ef;
        border-radius: 14px;
        padding: 18px 15px;
        text-align: center;
        border: 1px solid #dfe7d9;
        box-shadow: 0 3px 10px rgba(91, 126, 60, 0.10);
        min-height: 105px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        box-sizing: border-box;
    }

    .shipping-card-name {
        font-size: 18px;
        font-weight: bold;
        color: #555;
        margin-bottom: 8px;
    }

    .shipping-card-amount {
        font-size: 24px;
        font-weight: bold;
        color: #5B7E3C;
    }


    /* ==========================================
       TIÊU ĐỀ IN
       ========================================== */

    .print-title {
        display: none;
    }


    /* ==========================================
       CARD ĐVVC DÀNH RIÊNG CHO BẢN IN
       Mặc định ẩn trên màn hình
       ========================================== */

    .print-shipping-summary {
        display: none;
    }


    /* ==========================================
       XỬ LÝ TRIỆT ĐỂ LỖI LÙI TRANG KHI IN
       ========================================== */

    @media print {

        @page {
            size: landscape;
            margin: 8mm 12mm !important;
        }


        /* Ẩn tiêu đề nhập liệu lớn khi in */
        h1,
        [data-testid="stHeader"]+div h1 {
            display: none !important;
        }


        /* Triệt tiêu Header mặc định của Streamlit */
        header,
        [data-testid="stHeader"],
        .stAppHeader {
            display: none !important;
            height: 0 !important;
            opacity: 0 !important;
        }


        /* Ẩn giao diện không cần in */
        section[data-testid="stSidebar"],
        div[data-testid="stForm"],
        div.stSelectbox,
        footer,
        iframe,
        div.stButton,
        div[data-testid="stElementContainer"]:has(button),
        div:has(> .stForm),
        .no-print {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }


        /* Đưa nội dung chính lên đầu trang */
        .stApp,
        .main,
        .main .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-top: 0px !important;
            margin-top: 0px !important;
            padding-left: 0px !important;
            padding-right: 0px !important;
            margin: 0px !important;
            top: 0px !important;
        }


        /* Tiêu đề in */
        .print-title {
            display: block !important;
            color: #5B7E3C !important;
            text-align: center !important;
            margin-top: 0px !important;
            margin-bottom: 20px !important;
            font-size: 26px !important;
            font-weight: bold !important;
        }


        /* ==========================================
           CARD ĐVVC KHI IN
           ========================================== */

        .print-shipping-summary {
            display: block !important;
            margin-bottom: 20px !important;
        }

        .print-shipping-title {
            color: #5B7E3C !important;
            font-size: 16px !important;
            font-weight: bold !important;
            margin-bottom: 10px !important;
        }

        .print-shipping-cards {
            display: flex !important;
            gap: 12px !important;
            width: 100% !important;
        }

        .print-shipping-card {
            flex: 1 !important;
            border: 1px solid #dfe7d9 !important;
            border-radius: 10px !important;
            padding: 12px !important;
            text-align: center !important;
            background-color: #f1f4ef !important;
            box-sizing: border-box !important;
        }

        .print-shipping-name {
            font-size: 13px !important;
            font-weight: bold !important;
            color: #555 !important;
            margin-bottom: 6px !important;
        }

        .print-shipping-amount {
            font-size: 17px !important;
            font-weight: bold !important;
            color: #5B7E3C !important;
        }


        /* ==========================================
           ĐỊNH DẠNG BẢNG KHI IN
           ========================================== */

        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            width: 100% !important;
            gap: 0px !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(8) {
            display: none !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
            width: 5% !important;
            max-width: 5% !important;
            flex: 0 0 5% !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            width: 11% !important;
            max-width: 11% !important;
            flex: 0 0 11% !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(3) {
            width: 33% !important;
            max-width: 33% !important;
            flex: 0 0 33% !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(4) {
            width: 11% !important;
            max-width: 11% !important;
            flex: 0 0 11% !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(5) {
            width: 13% !important;
            max-width: 13% !important;
            flex: 0 0 13% !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(6) {
            width: 13% !important;
            max-width: 13% !important;
            flex: 0 0 13% !important;
        }

        /* Cột Phí */
        div[data-testid="stHorizontalBlock"] > div:nth-child(7) {
            width: 14% !important;
            max-width: 14% !important;
            flex: 0 0 14% !important;
            border-right: none !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.header-col) > div:nth-child(7) .header-col {
            border-radius: 0 8px 0 0 !important;
        }

        .row-style,
        .header-col {
            font-size: 13px !important;
            padding: 6px 2px !important;
        }

        div[data-testid="stHorizontalBlock"] > div:nth-child(7) .row-style {
            white-space: nowrap !important;
            justify-content: center !important;
        }
    }

</style>
""", unsafe_allow_html=True)


# ==========================================
# 4. KẾT NỐI GOOGLE SHEETS
# ==========================================

SHEET_ID = "1II4nY7kXYcrfFBzQ86Gm1TLbefI-Ec4GRIB_-APqZpA"


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

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scope
    )

    gc = gspread.authorize(creds)

    return gc.open_by_key(SHEET_ID).sheet1


ws = ket_noi_sheet()


# ==========================================
# 5. ĐỌC DỮ LIỆU GOOGLE SHEETS
# ==========================================

data_all = ws.get_all_values()

if len(data_all) > 1:

    headers = data_all[0]

    while len(headers) < 6:
        headers.append(f"Cột_Trống_{len(headers)+1}")

    df_all = pd.DataFrame(
        data_all[1:],
        columns=headers[:len(data_all[0])]
    )

    df_all.columns = [c.strip() for c in df_all.columns]

    list_dv_sheet = (
        df_all["Đơn vị"].dropna().unique().tolist()
        if "Đơn vị" in df_all.columns
        else []
    )

    list_pl_sheet = (
        df_all["Phân loại"].dropna().unique().tolist()
        if "Phân loại" in df_all.columns
        else []
    )

    list_ntt_sheet = (
        df_all["Người thanh toán"].dropna().unique().tolist()
        if "Người thanh toán" in df_all.columns
        else []
    )

else:

    list_dv_sheet = []
    list_pl_sheet = []
    list_ntt_sheet = []


# ==========================================
# 6. DANH MỤC MẶC ĐỊNH
# ==========================================

mac_dinh_dv = [
    "Ahamove",
    "Grab",
    "Lalamove",
    "GHTK",
    "GHN",
    "Viettel Post"
]

mac_dinh_pl = [
    "Đơn hàng bán",
    "Quà Hội viên",
    "Tài liệu"
]

mac_dinh_ntt = [
    "Quỳnh Như",
    "Công ty CK sau"
]


# ==========================================
# 7. SESSION STATE
# ==========================================

if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = list(
        sorted(
            set(
                mac_dinh_dv +
                [x for x in list_dv_sheet if x]
            )
        )
    )

if "ds_phanloai" not in st.session_state:
    st.session_state.ds_phanloai = list(
        sorted(
            set(
                mac_dinh_pl +
                [x for x in list_pl_sheet if x]
            )
        )
    )

if "ds_nguoitt" not in st.session_state:
    st.session_state.ds_nguoitt = list(
        sorted(
            set(
                mac_dinh_ntt +
                [x for x in list_ntt_sheet if x]
            )
        )
    )


# ==========================================
# 8. SIDEBAR GIAO DIỆN
# ==========================================

with st.sidebar:

    st.markdown(
        f'''
        <div class="taskbar-box">

            <p style="margin:0; font-size:14px; color:#555;">
                📅 <b>Hôm nay:</b>
            </p>

            <p style="margin:0; font-size:16px; font-weight:bold;">
                {ngay_hien_tai}
            </p>

            <hr style="margin:10px 0; border:0.5px solid #ddd;">

            <p style="margin:0; font-size:14px; color:#555;">
                🌤️ <b>Thời tiết:</b>
            </p>

            <p style="margin:0; font-size:16px; font-weight:bold;">
                {thoi_tiet}
            </p>

            <p style="margin-top:8px; font-size:16px; font-weight:bold; color:#5B7E3C;">
                Vui vẻ lên nhé ✨🐻
            </p>

        </div>
        ''',
        unsafe_allow_html=True
    )

    st.header("⚙️ Cấu hình danh mục")

    # Thêm ĐVVC
    new_dv = st.text_input("Thêm Đơn vị mới")

    if st.button("➕ Thêm ĐVVC"):

        if new_dv and new_dv not in st.session_state.ds_donvi:

            st.session_state.ds_donvi.append(new_dv)

            st.rerun()


    # Thêm phân loại
    new_pl = st.text_input("Thêm Phân loại mới")

    if st.button("➕ Thêm Phân Loại"):

        if new_pl and new_pl not in st.session_state.ds_phanloai:

            st.session_state.ds_phanloai.append(new_pl)

            st.rerun()


    # Thêm người thanh toán
    new_ntt = st.text_input("Thêm Người thanh toán mới")

    if st.button("➕ Thêm Người TT"):

        if new_ntt and new_ntt not in st.session_state.ds_nguoitt:

            st.session_state.ds_nguoitt.append(new_ntt)

            st.rerun()


    st.write("---")


    # Làm tươi hệ thống
    if st.button("🔄 Làm tươi hệ thống"):

        st.cache_resource.clear()

        st.rerun()


# ==========================================
# 9. NHẬP LIỆU
# ==========================================

st.title("🚚 CHI PHÍ GIAO HÀNG")


with st.form("form_nhap", clear_on_submit=True):

    row1_c1, row1_c2 = st.columns([1, 2])

    ngay = row1_c1.date_input(
        "Ngày",
        dt.now()
    )

    nd = row1_c2.text_input(
        "Nội dung"
    )


    row2_c1, row2_c2, row2_c3, row2_c4 = st.columns(
        [1, 1, 1, 1]
    )

    dv = row2_c1.selectbox(
        "Đơn vị VC",
        st.session_state.ds_donvi
    )

    pl = row2_c2.selectbox(
        "Phân loại chi phí",
        st.session_state.ds_phanloai
    )

    ntt = row2_c3.selectbox(
        "Người thanh toán",
        st.session_state.ds_nguoitt
    )

    tien = row2_c4.number_input(
        "Phí (VNĐ)",
        min_value=0,
        step=1000
    )


    if st.form_submit_button("💾 Lưu dữ liệu"):

        ws.append_row([
            ngay.strftime("%d/%m/%Y"),
            nd,
            dv,
            int(tien),
            pl,
            ntt
        ])

        st.cache_resource.clear()

        st.rerun()


# ==========================================
# 10. KIỂM TRA DỮ LIỆU
# ==========================================

if len(data_all) <= 1:

    st.info(
        "Chưa có dữ liệu chi phí nào được ghi nhận."
    )

    st.stop()


# ==========================================
# 11. XỬ LÝ DATAFRAME
# ==========================================

df = pd.DataFrame(
    data_all[1:],
    columns=data_all[0]
)

df.columns = [
    c.strip()
    for c in df.columns
]


if "Phân loại" not in df.columns:
    df["Phân loại"] = ""


if "Người thanh toán" not in df.columns:
    df["Người thanh toán"] = ""


# Chuyển phí về dạng số
df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(
    lambda x: int(
        re.sub(
            r"[^\d]",
            "",
            str(x)
        ) or 0
    )
)


# Chuyển ngày
df["Ngày_DT"] = pd.to_datetime(
    df["Ngày"],
    format="%d/%m/%Y",
    errors="coerce"
)


# Danh sách tháng
months = sorted(
    df["Ngày_DT"]
    .dt.strftime("%m/%Y")
    .dropna()
    .unique(),
    reverse=True
)


# ==========================================
# 12. CHỌN THÁNG
# ==========================================

thang = st.selectbox(
    "📅 Chọn tháng xem dữ liệu",
    months
)


# Lọc dữ liệu theo tháng
df_f = df[
    df["Ngày_DT"]
    .dt.strftime("%m/%Y") == thang
].copy()


df_f = df_f.sort_values(
    by="Ngày_DT",
    ascending=True
)


# ==========================================
# 13. TÍNH TỔNG TIỀN
# ==========================================

tong_tien = int(
    df_f["Phí (VNĐ)"].sum()
)


# ==========================================
# 14. TỔNG HỢP CHI PHÍ THEO ĐVVC
# ==========================================

tong_theo_dvvc = (
    df_f
    .groupby("Đơn vị")["Phí (VNĐ)"]
    .sum()
    .sort_values(
        ascending=False
    )
)


# Chỉ lấy các ĐVVC có phát sinh chi phí
tong_theo_dvvc = tong_theo_dvvc[
    tong_theo_dvvc > 0
]


# ==========================================
# 15. CARD TỔNG HỢP THEO ĐVVC
# ==========================================

st.markdown(
    '<div class="shipping-summary-title">'
    '📦 TỔNG HỢP PHÍ THEO ĐVVC'
    '</div>',
    unsafe_allow_html=True
)


if len(tong_theo_dvvc) > 0:

    so_dvvc = len(tong_theo_dvvc)

    cols = st.columns(
        so_dvvc
    )


    for col, (dvvc, tong_phi) in zip(
        cols,
        tong_theo_dvvc.items()
    ):

        with col:

            st.markdown(
                f"""
                <div class="shipping-card">

                    <div class="shipping-card-name">
                        🚚 {dvvc}
                    </div>

                    <div class="shipping-card-amount">
                        {tong_phi:,.0f} VNĐ
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

else:

    st.info(
        "Chưa có chi phí phát sinh theo ĐVVC trong tháng này."
    )


# ==========================================
# 16. CARD ĐVVC DÀNH RIÊNG CHO BẢN IN
# ==========================================

cards_print_html = ""


for dvvc, tong_phi in tong_theo_dvvc.items():

    cards_print_html += f"""
    <div class="print-shipping-card">

        <div class="print-shipping-name">
            🚚 {dvvc}
        </div>

        <div class="print-shipping-amount">
            {tong_phi:,.0f} VNĐ
        </div>

    </div>
    """


# Chỉ tạo khu vực này để dùng khi IN
st.markdown(
    f"""
    <div class="print-shipping-summary">

        <div class="print-shipping-title">
            📦 TỔNG HỢP PHÍ THEO ĐVVC
        </div>

        <div class="print-shipping-cards">
            {cards_print_html}
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================
# 17. TIÊU ĐỀ IN
# ==========================================

st.markdown(
    f'''
    <div class="print-title">
        CHI PHÍ GIAO HÀNG - THÁNG {thang}
    </div>
    ''',
    unsafe_allow_html=True
)


# ==========================================
# 18. HÀM TẠO HTML XUẤT FILE
# ==========================================

def tao_giao_dien_html_full_width(
    dataframe,
    month_txt,
    total_amount,
    summary_dvvc
):

    rows_html = ""


    # ------------------------------------------
    # Tạo các dòng dữ liệu
    # ------------------------------------------

    for idx, (_, r) in enumerate(
        dataframe.iterrows(),
        start=1
    ):

        rows_html += f"""
        <tr>

            <td style="
                text-align:center;
                width:5%;
            ">
                {idx}
            </td>

            <td style="
                text-align:center;
                width:11%;
            ">
                {r['Ngày']}
            </td>

            <td style="
                text-align:left;
                padding-left:8px;
                width:34%;
            ">
                {r['Nội dung']}
            </td>

            <td style="
                text-align:center;
                width:12%;
            ">
                {r['Đơn vị']}
            </td>

            <td style="
                text-align:center;
                width:13%;
            ">
                {r['Phân loại']}
            </td>

            <td style="
                text-align:center;
                width:13%;
            ">
                {r['Người thanh toán']}
            </td>

            <td style="
                text-align:center;
                font-weight:bold;
                width:12%;
                white-space:nowrap;
            ">
                {r['Phí (VNĐ)']:,}
            </td>

        </tr>
        """


    # ------------------------------------------
    # HTML hoàn chỉnh
    # ------------------------------------------

    return f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="utf-8">

        <style>

            @page {{
                size: landscape;
                margin: 10mm;
            }}


            body {{
                font-family: Arial, sans-serif;
                color: #333;
                margin: 0;
                padding: 0;
                width: 100%;
                background-color: #fff;
            }}


            /* ----------------------------------
               TIÊU ĐỀ
               ---------------------------------- */

            .title-container {{
                text-align: center;
                padding-top: 10px;
                margin-bottom: 20px;
            }}


            .print-title {{
                color: #5B7E3C;
                font-size: 22pt;
                font-weight: bold;
                text-transform: uppercase;
                margin: 0;
            }}


            /* ----------------------------------
               TỔNG HỢP ĐVVC
               ---------------------------------- */

            .shipping-summary {{
                margin: 0 10px 20px 10px;
            }}


            .shipping-summary-title {{
                color: #5B7E3C;
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 10px;
            }}


            .shipping-cards {{
                display: flex;
                gap: 12px;
                width: 100%;
            }}


            .shipping-card {{
                flex: 1;
                border: 1px solid #dfe7d9;
                border-radius: 10px;
                padding: 12px;
                text-align: center;
                background-color: #f1f4ef;
                box-sizing: border-box;
            }}


            .shipping-card-name {{
                font-size: 11pt;
                font-weight: bold;
                color: #555;
                margin-bottom: 6px;
            }}


            .shipping-card-amount {{
                font-size: 15pt;
                font-weight: bold;
                color: #5B7E3C;
            }}


            /* ----------------------------------
               BẢNG
               ---------------------------------- */

            table {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
                margin-bottom: 20px;
            }}


            th {{
                background-color: #5B7E3C;
                color: white;
                font-weight: bold;
                font-size: 11pt;
                padding: 10px 4px;
                border: 1px solid #5B7E3C;
                text-align: center;
            }}


            td {{
                padding: 10px 4px;
                font-size: 10pt;
                border-bottom: 1px solid #eef2ec;
                vertical-align: middle;
            }}


            tr:nth-child(even) td {{
                background-color: #fcfdfe;
            }}


            /* ----------------------------------
               TỔNG CỘNG
               ---------------------------------- */

            .total-box {{
                padding: 15px;
                border-radius: 10px;
                font-size: 14pt;
                font-weight: bold;
                text-align: center;
                background-color: #5B7E3C;
                color: white;
                margin-top: 15px;
            }}

        </style>

    </head>


    <body>


        <!-- =================================
             TIÊU ĐỀ
             ================================= -->

        <div class="title-container">

            <h1 class="print-title">
                CHI PHÍ GIAO HÀNG - THÁNG {month_txt}
            </h1>

        </div>


        <!-- =================================
             TỔNG HỢP THEO ĐVVC
             ================================= -->

        <div class="shipping-summary">

            <div class="shipping-summary-title">
                📦 TỔNG HỢP PHÍ THEO ĐVVC
            </div>

            <div class="shipping-cards">

                {summary_dvvc}

            </div>

        </div>


        <!-- =================================
             BẢNG CHI TIẾT
             ================================= -->

        <table style="padding:0 10px;">

            <thead>

                <tr>

                    <th style="width:5%;">
                        STT
                    </th>

                    <th style="width:11%;">
                        Ngày
                    </th>

                    <th style="width:34%;">
                        Nội dung
                    </th>

                    <th style="width:12%;">
                        ĐVVC
                    </th>

                    <th style="width:13%;">
                        Phân loại
                    </th>

                    <th style="width:13%;">
                        Người TT
                    </th>

                    <th style="width:12%; text-align:center;">
                        Phí (VNĐ)
                    </th>

                </tr>

            </thead>


            <tbody>

                {rows_html}

            </tbody>

        </table>


        <!-- =================================
             TỔNG CỘNG
             ================================= -->

        <div style="padding:0 10px;">

            <div class="total-box">

                💰 TỔNG CỘNG CHI PHÍ:
                {total_amount:,.0f} VNĐ

            </div>

        </div>


    </body>

    </html>
    """


# ==========================================
# 19. TẠO HTML CARD CHO FILE XUẤT
# ==========================================

summary_dvvc_html = ""


for dvvc, tong_phi in tong_theo_dvvc.items():

    summary_dvvc_html += f"""
    <div class="shipping-card">

        <div class="shipping-card-name">
            🚚 {dvvc}
        </div>

        <div class="shipping-card-amount">
            {tong_phi:,.0f} VNĐ
        </div>

    </div>
    """


# ==========================================
# 20. NÚT IN & XUẤT FILE
# ==========================================

st.write(" ")


btn_c1, btn_c2, btn_c3 = st.columns(
    [1.5, 2, 8]
)


# ------------------------------------------
# NÚT IN
# ------------------------------------------

with btn_c1:

    if st.button("🖨️ In đây nè bé ưi"):

        components.html(
            """
            <script>
                window.parent.print();
            </script>
            """,
            height=0
        )


# ------------------------------------------
# NÚT XUẤT HTML/PDF
# ------------------------------------------

with btn_c2:

    dulieu_html = tao_giao_dien_html_full_width(
        df_f,
        thang,
        tong_tien,
        summary_dvvc_html
    )


    st.download_button(
        label="📥 Xuất file HTML/PDF",

        data=dulieu_html,

        file_name=(
            f"Bao_cao_phi_ship_thang_"
            f"{thang.replace('/', '_')}.html"
        ),

        mime="text/html"
    )


# ==========================================
# 21. HIỂN THỊ BẢNG DỮ LIỆU
# ==========================================

h1, h2, h3, h4, h5, h6, h7, h8 = st.columns(
    [
        0.8,
        1.8,
        4.5,
        1.8,
        2.0,
        2.0,
        2.0,
        1.2
    ]
)


# Header
h1.markdown(
    '<div class="header-col header-left">STT</div>',
    unsafe_allow_html=True
)

h2.markdown(
    '<div class="header-col">Ngày</div>',
    unsafe_allow_html=True
)

h3.markdown(
    '<div class="header-col">Nội dung</div>',
    unsafe_allow_html=True
)

h4.markdown(
    '<div class="header-col">ĐVVC</div>',
    unsafe_allow_html=True
)

h5.markdown(
    '<div class="header-col">Phân loại</div>',
    unsafe_allow_html=True
)

h6.markdown(
    '<div class="header-col">Người TT</div>',
    unsafe_allow_html=True
)

h7.markdown(
    '<div class="header-col">Phí</div>',
    unsafe_allow_html=True
)

h8.markdown(
    '<div class="header-col header-right">Xóa</div>',
    unsafe_allow_html=True
)


# ==========================================
# 22. CÁC DÒNG DỮ LIỆU
# ==========================================

for idx, (i, row) in enumerate(
    df_f.iterrows(),
    start=1
):

    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(
        [
            0.8,
            1.8,
            4.5,
            1.8,
            2.0,
            2.0,
            2.0,
            1.2
        ]
    )


    c1.markdown(
        f"<div class='row-style'>{idx}</div>",
        unsafe_allow_html=True
    )


    c2.markdown(
        f"<div class='row-style'>{row['Ngày']}</div>",
        unsafe_allow_html=True
    )


    c3.markdown(
        f"""
        <div class='row-style'
             style='
                text-align:left;
                justify-content:flex-start;
                padding-left:10px;
             '>
            {row['Nội dung']}
        </div>
        """,
        unsafe_allow_html=True
    )


    c4.markdown(
        f"<div class='row-style'>{row['Đơn vị']}</div>",
        unsafe_allow_html=True
    )


    c5.markdown(
        f"<div class='row-style'>{row['Phân loại']}</div>",
        unsafe_allow_html=True
    )


    c6.markdown(
        f"<div class='row-style'>{row['Người thanh toán']}</div>",
        unsafe_allow_html=True
    )


    c7.markdown(
        f"""
        <div class='row-style'>
            <b>{row['Phí (VNĐ)']:,}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


    # Nút xóa
    with c8:

        if st.button(
            "❌",
            key=f"del_{i}"
        ):

            ws.delete_rows(
                i + 2
            )

            st.cache_resource.clear()

            st.rerun()


    st.markdown(
        '<hr style="margin:0; border:0.5px solid #f1f4ef;">',
        unsafe_allow_html=True
    )


# ==========================================
# 23. TỔNG CỘNG
# ==========================================

st.markdown(
    f"""
    <div class="total-box">

        💰 TỔNG CHI PHÍ THÁNG {thang}:
        {tong_tien:,.0f} VNĐ

    </div>
    """,
    unsafe_allow_html=True
)
