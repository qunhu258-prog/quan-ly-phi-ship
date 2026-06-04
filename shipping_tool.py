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
# 3. STYLE CSS TỔNG HỢP GIAO DIỆN WEB & CARD KPI
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
    .print-title { display: none; }

    /* CSS CHO KHỐI THÔNG TIN CARD KPI KẾ TOÁN */
    .kpi-container {
        display: flex;
        gap: 20px;
        margin-top: 10px;
        margin-bottom: 25px;
    }
    .kpi-card {
        flex: 1;
        background-color: #ffffff;
        border: 2px solid #5B7E3C;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 3px 8px rgba(0,0,0,0.06);
        text-align: center;
    }
    .kpi-header {
        background-color: #5B7E3C;
        color: #ffffff;
        font-size: 15px;
        font-weight: 700;
        padding: 12px 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-body {
        padding: 20px 10px;
    }
    .kpi-value {
        font-size: 32px;
        color: #222222;
        font-weight: 700;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    .kpi-unit {
        font-size: 13px;
        color: #666666;
        margin-top: 4px;
    }

    @media print {
        @page { size: landscape; margin: 0 !important; }
        body { margin: 0 !important; padding: 0 !important; }
        section[data-testid="stSidebar"], div[data-testid="stForm"], div.stSelectbox,
        header, footer, h1, iframe, [data-testid="stHeader"], div.stButton,
        div[data-testid="stElementContainer"] button { display: none !important; }
        .main, .main .block-container, [data-testid="stMainBlockContainer"] {
            padding-top: 15mm !important; padding-left: 15mm !important; padding-right: 15mm !important;
            margin: 0px !important; top: 0px !important;
        }
        .print-title {
            display: block !important; color: #5B7E3C !important; text-align: center !important;
            margin-top: 10px !important; margin-bottom: 30px !important; font-size: 24px !important; font-weight: bold !important;
        }
        div[data-testid="stHorizontalBlock"] { display: flex !important; flex-direction: row !important; width: 100% !important; gap: 0px !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(8) { display: none !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(1) { width: 5% !important; max-width: 5% !important; flex: 0 0 5% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(2) { width: 11% !important; max-width: 11% !important; flex: 0 0 11% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(3) { width: 34% !important; max-width: 34% !important; flex: 0 0 34% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(4) { width: 12% !important; max-width: 12% !important; flex: 0 0 12% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(5) { width: 13% !important; max-width: 13% !important; flex: 0 0 13% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(6) { width: 13% !important; max-width: 13% !important; flex: 0 0 13% !important; }
        div[data-testid="stHorizontalBlock"] > div:nth-child(7) { width: 12% !important; max-width: 12% !important; flex: 0 0 12% !important; border-right: none !important; }
        div[data-testid="stHorizontalBlock"]:has(.header-col) > div:nth-child(7) .header-col { border-radius: 0 8px 0 0 !important; }
        .row-style, .header-col { font-size: 13px !important; padding: 6px 2px !important; }
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

# Đọc toàn bộ dữ liệu hiện có để xử lý danh sách động
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

# Thiết lập danh sách chọn (Mặc định + Phát sinh thêm từ Sheet)
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
df["開設_DT"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
months = sorted(df["開設_DT"].dt.strftime("%m/%Y").dropna().unique(), reverse=True)

thang = st.selectbox("📅 Chọn tháng xem dữ liệu", months)

df_f = df[df["開設_DT"].dt.strftime("%m/%Y") == thang]
df_f = df_f.sort_values(by="開設_DT", ascending=True)

# --- PHÂN TÍCH SỐ TIỀN THEO ĐỐI TƯỢNG (DÙNG CHO CARD KPI KẾ TOÁN) ---
tien_cty_ck = int(df_f[df_f["Người thanh toán"] == "Công ty CK"]["Phí (VNĐ)"].sum())
tien_quynh_nhu = int(df_f[df_f["Người thanh toán"] == "Quỳnh Như"]["Phí (VNĐ)"].sum())
tong_tien = int(df_f["Phí (VNĐ)"].sum())

# Lấy tiền của những người thanh toán phát sinh khác (nếu có ngoài Công ty CK và Quỳnh Như)
df_phat_sinh = df_f[~df_f["Người thanh toán"].isin(["Công ty CK", "Quỳnh Như"])]
thong_tin_them = ""
if not df_phat_sinh.empty:
    nhom_phat_sinh = df_phat_sinh.groupby("Người thanh toán")["Phí (VNĐ)"].sum()
    for name, money in nhom_phat_sinh.items():
        if name.strip():
            thong_tin_them += f" • Khác ({name}): {int(money):,} VNĐ"

# ==========================================
# 6.2. HIỂN THỊ CÁC CARD TỔNG TIỀN CHO KẾ TOÁN
# ==========================================
st.markdown("### 📊 Số liệu thanh toán cho Kế toán")
st.html(
    f"""
    <div class="kpi-container">
        <!-- Card 1 -->
        <div class="kpi-card">
            <div class="kpi-header">🏢 CÔNG TY THANH TOÁN</div>
            <div class="kpi-body">
                <div class="kpi-value" style="color: #2e7d32;">{tien_cty_ck:,}</div>
                <div class="kpi-unit">VNĐ (Hóa đơn Viettel Post)</div>
            </div>
        </div>
        
        <!-- Card 2 -->
        <div class="kpi-card">
            <div class="kpi-header">👩‍💼 QUỲNH NHƯ THANH TOÁN</div>
            <div class="kpi-body">
                <div class="kpi-value" style="color: #e65100;">{tien_quynh_nhu:,}</div>
                <div class="kpi-unit">VNĐ (Quỳnh Như đã chi hộ)</div>
            </div>
        </div>
    </div>
    """
)

# Nút In & Xuất file
st.write(" ")
btn_c1, btn_c2, btn_c3 = st.columns([1.5, 2, 8])

with btn_c1:
    if st.button("🖨️ In đây nè bé ưi"):
        components.html("<script>window.parent.print();</script>", height=0)

with btn_c2:
    def tao_giao_dien_html_full_width(dataframe, month_txt, total_amount, cty, qnhu):
        rows_html = ""
        for idx, (_, r) in enumerate(dataframe.iterrows(), start=1):
            rows_html += f"""
            <tr>
                <td style='text-align: center; width: 5%;'>{idx}</td>
                <td style='text-align: center; width: 11%;'>{r['Ngày']}</td>
                <td style='text-align: left; padding-left: 8px; width: 34%;'>{r['Nội dung']}</td>
                <td style='text-align: center; width: 12%;'>{r['Đơn vị']}</td>
                <td style='text-align: center; width: 13%;'>{r['Phân loại']}</td>
                <td style='text-align: center; width: 13%;'>{r['Người thanh toán']}</td>
                <td style='text-align: right; padding-right: 12px; font-weight: bold; width: 12%;'>{r['Phí (VNĐ)']:,}</td>
            </tr>
            """
        
        return f"""
        <!DOCTYPE html><html><head><meta charset="utf-8">
        <style>
            @page {{ size: landscape; margin: 0; }}
            body {{ font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; width: 100%; }}
            .title-container {{ text-align: center; padding-top: 30px; margin-bottom: 25px; }}
            .print-title {{ color: #5B7E3C; font-size: 22pt; font-weight: bold; text-transform: uppercase; }}
            table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 20px; }}
            th {{ background-color: #5B7E3C; color: white; font-weight: bold; font-size: 11pt; padding: 10px 4px; border: 1px solid #5B7E3C; }}
            td {{ padding: 10px 4px; font-size: 10pt; border-bottom: 1px solid #eef2ec; vertical-align: middle; }}
            tr:nth-child(even) td {{ background-color: #fcfdfe; }}
            .summary-text {{ font-size: 12pt; margin: 10px 15px; color: #444; font-weight: bold; text-align: left; }}
            .total-box {{ padding: 15px; border-radius: 10px; font-size: 14pt; font-weight: bold; text-align: center; background-color: #5B7E3C; color: white; margin-top: 15px; }}
        </style></head><body>
            <div class="title-container"><h1 class="print-title">CHI PHÍ GIAO HÀNG - THÁNG {month_txt}</h1></div>
            <div class="summary-text">📍 Thống kê nguồn chi: Công ty CK: {cty:,} đ | Quỳnh Như hoàn trả: {qnhu:,} đ</div>
            <table style="padding: 0 10px;">
                <thead><tr>
                    <th style="width: 5%;">STT</th><th style="width: 11%;">Ngày</th><th style="width: 34%;">Nội dung</th>
                    <th style="width: 12%;">ĐVVC</th><th style="width: 13%;">Phân loại</th><th style="width: 13%;">Người TT</th><th style="width: 12%;">Phí (VNĐ)</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div style="padding: 0 10px;"><div class="total-box">💰 TỔNG CỘNG CHI PHÍ: {total_amount:,.0f} VNĐ</div></div>
        </body></html>
        """

    dulieu_html = tao_giao_dien_html_full_width(df_f, thang, tong_tien, tien_cty_ck, tien_quynh_nhu)
    st.download_button(
        label="📥 Xuất file PDF",
        data=dulieu_html,
        file_name=f"Bao_cao_phi_ship_thang_{thang.replace('/', '_')}.html",
        mime="text/html"
    )

# ========================================================
# 7. HIỂN THỊ BẢNG DỮ LIỆU ĐA CỘT MỚI
# ========================================================
st.markdown(f'<div class="print-title">CHI PHÍ GIAO HÀNG - THÁNG {thang}</div>', unsafe_allow_html=True)

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