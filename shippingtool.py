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
st.set_page_config(layout="wide", page_title="Quản lý phí Ship")

# ==========================================
# 2. TIỆN ÍCH SIDEBAR (NGÀY & THỜI TIẾT)
# ==========================================
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

# ==========================================
# 3. STYLE CSS TỔNG HỢP GIAO DIỆN & TỐI ƯU HÓA IN PDF
# ==========================================
st.markdown("""
<style>
    .block-container { padding: 2rem 3rem; max-width: 100%; }
    h1 { color: #5B7E3C !important; }
    .taskbar-box {
        background-color: #f1f4ef; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #5B7E3C; margin-bottom: 20px;
    }
    div[data-testid="stHorizontalBlock"]:has(.header-col) { gap: 0px !important; }
    .header-col {
        background-color: #5B7E3C; color: white; font-weight: bold;
        font-size: 16px; padding: 12px 5px; text-align: center;
        border-right: 0.1px solid #ffffff33;
    }
    .header-left { border-radius: 8px 0 0 0; }
    .header-right { border-radius: 0 8px 0 0; border-right: none; }
    .row-style {
        font-size: 16px; padding: 10px 0; display: flex;
        align-items: center; justify-content: center;
        text-align: center;
    }
    .total-box {
        padding: 18px; border-radius: 15px; font-size: 22px;
        font-weight: bold; text-align: center;
        background-color: #5B7E3C; color: white;
        box-shadow: 0 4px 15px rgba(91, 126, 60, 0.3);
        margin-top: 20px;
    }
    .stButton > button {
        border-color: #5B7E3C !important;
        color: #5B7E3C !important;
    }
    .stButton > button:hover {
        background-color: #5B7E3C !important;
        color: white !important;
    }
    .print-only-title { display: none; }

    /* CSS KHỐI THÔNG TIN CARD KPI KẾ TOÁN */
    .kpi-wrapper { max-width: 900px; margin: 0 auto; padding: 0 10px; }
    .kpi-container { display: flex; gap: 20px; margin-top: 10px; margin-bottom: 25px; }
    .kpi-card { flex: 1; background-color: #ffffff; border: 2px solid #5B7E3C; border-radius: 8px; overflow: hidden; box-shadow: 0 3px 8px rgba(0,0,0,0.06); text-align: center; }
    .kpi-header { background-color: #5B7E3C; color: #ffffff; font-size: 14px; font-weight: 700; padding: 12px 5px; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-body { padding: 22px 10px; display: flex; align-items: baseline; justify-content: center; gap: 6px; }
    .kpi-value { font-size: 32px; color: #222222; font-weight: 700; font-family: 'Segoe UI', Arial, sans-serif; line-height: 1; }
    .kpi-currency { font-size: 16px; font-weight: bold; color: #666666; }

    /* ========================================================
       🚨 XỬ LÝ TRIỆT ĐỂ ẨN NÚT BẤM VÀ CĂN CHỈNH KHI XUẤT PDF
       ======================================================== */
    @media print {
        @page { size: landscape; margin: 6mm 10mm !important; }
        
        /* Ẩn tiêu đề h1 lớn lúc nhập liệu */
        h1, [data-testid="stHeader"]+div h1 { display: none !important; }

        /* Ẩn thanh công cụ mặc định của Streamlit */
        header, [data-testid="stHeader"], .stAppHeader, footer, [data-testid="stToolbar"] {
            display: none !important; height: 0 !important; opacity: 0 !important;
        }

        /* Ẩn các thành phần nhập liệu không cần thiết trên PDF */
        section[data-testid="stSidebar"], 
        div[data-testid="stForm"], 
        div.stSelectbox,
        .no-print,
        div[data-testid="stElementContainer"]:has(button),
        .stDownloadButton,
        iframe { 
            display: none !important; height: 0 !important; margin: 0 !important; padding: 0 !important; 
        }
        
        /* Đẩy nội dung chính sát lề trên giấy */
        .stApp, .main, .main .block-container, [data-testid="stMainBlockContainer"] {
            padding-top: 0px !important; margin-top: 0px !important;
            padding-left: 0px !important; padding-right: 0px !important;
            margin: 0px !important; top: 0px !important;
        }

        /* Hiển thị tiêu đề in chuyên dụng */
        .print-only-title {
            display: block !important; color: #5B7E3C !important; text-align: center !important;
            margin-top: 0px !important; margin-bottom: 20px !important; 
            font-size: 26px !important; font-weight: bold !important;
        }

        /* Ẩn cột hành động XÓA cuối cùng của bảng khi in */
        div[data-testid="stHorizontalBlock"] > div:nth-last-child(1) { display: none !important; }

        /* Tối ưu lại tỷ lệ các cột để tiền không bị rớt dòng */
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) { width: 6% !important; max-width: 6% !important; flex: 0 0 6% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) { width: 12% !important; max-width: 12% !important; flex: 0 0 12% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) { width: 36% !important; max-width: 36% !important; flex: 0 0 38% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(4) { width: 10% !important; max-width: 10% !important; flex: 0 0 11% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) { width: 11% !important; max-width: 11% !important; flex: 0 0 11% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(6) { width: 11% !important; max-width: 11% !important; flex: 0 0 11% !important; }
        /* Cột số tiền (Cột 7) nới rộng thêm diện tích */
        div[data-testid="stHorizontalBlock"] > div:nth-child(7) { width: 14% !important; max-width: 14% !important; flex: 0 0 14% !important; border-right: none !important; }
        
        div[data-testid="stHorizontalBlock"]:has(.header-col) > div:nth-child(7) .header-col { border-radius: 0 8px 0 0 !important; }
        .row-style, .header-col { font-size: 14px !important; padding: 6px 2px !important; white-space: nowrap !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. KẾT NỐI GOOGLE SHEETS
# ==========================================
SHEET_ID = "1pX1uImwD770upHdJ4OKNzYxwKxd5C_VeI2zQeW0SBLUg"

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

data_all = ws.get_all_values()
if len(data_all) > 1:
    headers = data_all[0]
    while len(headers) < 6:
        headers.append(f"Cột_Trống_{len(headers)+1}")
    
    df_all = pd.DataFrame(data_all[1:], columns=headers[:len(data_all[0])])
    df_all.columns = [c.strip() for c in df_all.columns]
    
    list_dv_sheet = df_all['Đơn vị'].dropna().unique().tolist() if 'Đơn vị' in df_all.columns else []
    list_pl_sheet = df_all['Phân loại'].dropna().unique().tolist() if 'Phân loại' in df_all.columns else []
    list_ntt_sheet = df_all['Người thanh toán'].dropna().unique().tolist() if 'Người thanh toán' in df_all.columns else []
else:
    list_dv_sheet, list_pl_sheet, list_ntt_sheet = [], [], []

mac_dinh_dv = ["Ahamove", "Grab", "Lalamove", "GHTK", "GHN", "Viettel Post"]
mac_dinh_pl = ["Đơn hàng bán", "Quà Hội viên", "Tài liệu"]
mac_dinh_ntt = ["Quỳnh Như", "Công ty CK"]

if "ds_donvi" not in st.session_state:
    st.session_state.ds_donvi = list(sorted(set(mac_dinh_dv + [x for x in list_dv_sheet if x])))
if "ds_phanloai" not in st.session_state:
    st.session_state.ds_phanloai = list(sorted(set(mac_dinh_pl + [x for x in list_pl_sheet if x])))
if "ds_nguoitt" not in st.session_state:
    st.session_state.ds_nguoitt = list(sorted(set(mac_dinh_ntt + [x for x in list_ntt_sheet if x])))

# ==========================================
# 5. SIDEBAR GIAO DIỆN
# ==========================================
with st.sidebar:
    st.markdown(f'''
    <div class="taskbar-box">
        <p style="margin:0; font-size: 14px; color: #555;">📅 <b>Hôm nay:</b></p>
        <p style="margin:0; font-size: 16px; font-weight: bold;">{ngay_hien_tai}</p>
        <hr style="margin: 10px 0; border: 0.5px solid #ddd;">
        <p style="margin:0; font-size: 14px; color: #555;">🌤️ <b>Thời tiết:</b></p>
        <p style="margin:0; font-size: 16px; font-weight: bold;">{thoi_tiet}</p>
        <p style="margin-top:8px; font-size: 16px; font-weight: bold; color: #5B7E3C;">Vui vẻ lên nhé ✨🐻</p>
    </div>
    ''', unsafe_allow_html=True)

    st.header("⚙️ Cấu hình danh mục")
    
    new_dv = st.text_input("Thêm Đơn vị mới")
    if st.button("➕ Thêm ĐVVC"):
        if new_dv and new_dv not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(new_dv)
            st.rerun()
            
    new_pl = st.text_input("Thêm Phân loại mới")
    if st.button("➕ Thêm Phân Loại"):
        if new_pl and new_pl not in st.session_state.ds_phanloai:
            st.session_state.ds_phanloai.append(new_pl)
            st.rerun()

    new_ntt = st.text_input("Thêm Người thanh toán mới")
    if st.button("➕ Thêm Người TT"):
        if new_ntt and new_ntt not in st.session_state.ds_nguoitt:
            st.session_state.ds_nguoitt.append(new_ntt)
            st.rerun()

    st.write("---")
    if st.button("🔄 Làm tươi hệ thống"):
        st.cache_resource.clear()
        st.rerun()

# ==========================================
# 6. NHẬP LIỆU & XỬ LÝ DỮ LIỆU
# ==========================================
st.title("🚚 CHI PHÍ GIAO HÀNG")

with st.form("form_nhap", clear_on_submit=True):
    row1_c1, row1_c2 = st.columns([1, 2])
    ngay = row1_c1.date_input("Ngày", dt.now())
    nd = row1_c2.text_input("Nội dung")
    
    row2_c1, row2_c2, row2_c3, row2_c4 = st.columns([1, 1, 1, 1])
    dv = row2_c1.selectbox("Đơn vị VC", st.session_state.ds_donvi)
    pl = row2_c2.selectbox("Phân loại chi phí", st.session_state.ds_phanloai)
    ntt = row2_c3.selectbox("Người thanh toán", st.session_state.ds_nguoitt)
    tien = row2_c4.number_input("Phí (VNĐ)", min_value=0, step=1000)
    
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

if len(data_all) <= 1:
    st.info("Chưa có dữ liệu chi phí nào được ghi nhận.")
    st.stop()

df = pd.DataFrame(data_all[1:], columns=data_all[0])
df.columns = [c.strip() for c in df.columns]

if 'Phân loại' not in df.columns: df['Phân loại'] = ""
if 'Người thanh toán' not in df.columns: df['Người thanh toán'] = ""

df["Phí (VNĐ)"] = df["Phí (VNĐ)"].apply(lambda x: int(re.sub(r"[^\d]", "", str(x)) or 0))
df["Ngày_DT"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
months = sorted(df["Ngày_DT"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)

thang = st.selectbox("📅 Chọn tháng xem dữ liệu", months)

df_f = df[df["Ngày_DT"].dt.strftime("%m/%Y") == thang]
df_f = df_f.sort_values(by="Ngày_DT", ascending=True)

# --- SỐ TIỀN THEO ĐỐI TƯỢNG CHO CARD KPI ---
tien_cty_ck = int(df_f[df_f["Người thanh toán"] == "Công ty CK"]["Phí (VNĐ)"].sum())
tien_quynh_nhu = int(df_f[df_f["Người thanh toán"] == "Quỳnh Như"]["Phí (VNĐ)"].sum())
tong_tien = int(df_f["Phí (VNĐ)"].sum())

df_phat_sinh = df_f[~df_f["Người thanh toán"].isin(["Công ty CK", "Quỳnh Như"])]
thong_tin_them = ""
if not df_phat_sinh.empty:
    nhom_phat_sinh = df_phat_sinh.groupby("Người thanh toán")["Phí (VNĐ)"].sum()
    for name, money in nhom_phat_sinh.items():
        if name.strip():
            thong_tin_them += f" • Khác ({name}): {int(money):,} VNĐ"

# Tiêu đề in chuyên dụng (Chỉ xuất hiện trên bản in PDF)
st.markdown(f'<div class="print-only-title">CHI PHÍ GIAO HÀNG - THÁNG {thang}</div>', unsafe_allow_html=True)

# ========================================================
# 6.2. HIỂN THỊ CÁC CARD KPI KẾ TOÁN
# ========================================================
st.html(
    f"""
    <div class="kpi-wrapper">
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-header">🏢 SỐ TIỀN CÔNG TY CẦN CHUYỂN KHOẢN</div>
                <div class="kpi-body">
                    <div class="kpi-value" style="color: #2e7d32;">{tien_cty_ck:,}</div>
                    <div class="kpi-currency">VNĐ</div>
                </div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-header">👩‍💼 SỐ TIỀN CẦN TRẢ LẠI CHO QUỲNH NHƯ</div>
                <div class="kpi-body">
                    <div class="kpi-value" style="color: #e65100;">{tien_quynh_nhu:,}</div>
                    <div class="kpi-currency">VNĐ</div>
                </div>
            </div>
        </div>
    </div>
    """
)

# Nút chức năng In ấn / Xuất file PDF hệ thống
st.write(" ")
btn_c1, btn_c2 = st.columns([4, 8])

with btn_c1:
    if st.button("🖨️ XUẤT FILE PDF / IN BÁO CÁO", use_container_width=True):
        components.html("<script>window.parent.print();</script>", height=0)

# ========================================================
# 7. HIỂN THỊ BẢNG DỮ LIỆU ĐA CỘT MỚI
# ========================================================
h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([0.8, 1.8, 4.5, 1.8, 2.0, 2.0, 2.0, 1.2])
h1.markdown('<div class="header-col header-left">STT</div>', unsafe_allow_html=True)
h2.markdown('<div class="header-col">Ngày</div>', unsafe_allow_html=True)
h3.markdown('<div class="header-col">Nội dung</div>', unsafe_allow_html=True)
h4.markdown('<div class="header-col">ĐVVC</div>', unsafe_allow_html=True)
h5.markdown('<div class="header-col">Phân loại</div>', unsafe_allow_html=True)
h6.markdown('<div class="header-col">Người TT</div>', unsafe_allow_html=True)
h7.markdown('<div class="header-col">Phí</div>', unsafe_allow_html=True)
h8.markdown('<div class="header-col header-right">Xóa</div>', unsafe_allow_html=True)

for idx, (i, row) in enumerate(df_f.iterrows(), start=1):
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([0.8, 1.8, 4.5, 1.8, 2.0, 2.0, 2.0, 1.2])
    c1.markdown(f"<div class='row-style'>{idx}</div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='row-style'>{row['Ngày']}</div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='row-style' style='text-align:left; justify-content:flex-start; padding-left:10px;'>{row['Nội dung']}</div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='row-style'>{row['Đơn vị']}</div>", unsafe_allow_html=True)
    c5.markdown(f"<div class='row-style'>{row['Phân loại']}</div>", unsafe_allow_html=True)
    c6.markdown(f"<div class='row-style'>{row['Người thanh toán']}</div>", unsafe_allow_html=True)
    c7.markdown(f"<div class='row-style'><b>{row['Phí (VNĐ)']:,}</b></div>", unsafe_allow_html=True)
    
    with c8:
        if st.button("❌", key=f"del_{i}"):
            ws.delete_rows(i + 2)
            st.cache_resource.clear()
            st.rerun()
            
    st.markdown('<hr style="margin:0; border:0.5px solid #f1f4ef;">', unsafe_allow_html=True)

# ==========================================
# 8. TỔNG CỘNG
# ==========================================
st.markdown(f'<div class="total-box">💰 TỔNG CHI PHÍ THÁNG {thang}: {tong_tien:,.0f} VNĐ {thong_tin_them}</div>', unsafe_allow_html=True)