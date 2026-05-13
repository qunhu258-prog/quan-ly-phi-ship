import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

# Hàm kết nối an toàn
def connect_gsheet():
    try:
        # Kiểm tra xem có mục [connections.gsheets] không
        if "connections" not in st.secrets:
            return "Chưa cấu hình Secrets [connections.gsheets] trên Streamlit Cloud."
            
        s = st.secrets["connections"]["gsheets"]
        p_key = s["private_key"].replace("\\n", "\n")
        
        credentials = {
            "type": s["type"], "project_id": s["project_id"],
            "private_key_id": s["private_key_id"], "private_key": p_key,
            "client_email": s["client_email"], "client_id": s["client_id"],
            "auth_uri": s["auth_uri"], "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        
        gc = gspread.service_account_from_dict(credentials)
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg/edit")
        return sh.worksheet("Trang tính1")
    except Exception as e:
        return str(e)

# Hàm đọc dữ liệu không bao giờ chết
def load_data():
    res = connect_gsheet()
    if isinstance(res, gspread.Worksheet):
        try:
            data = res.get_all_records()
            df = pd.DataFrame(data)
            if not df.empty:
                df['Ngày giao'] = pd.to_datetime(df['Ngày giao'], dayfirst=True, errors='coerce')
                df['Phí (VNĐ)'] = pd.to_numeric(df['Phí (VNĐ)'], errors='coerce').fillna(0)
                return df.dropna(subset=['Ngày giao'])
        except:
            pass
    return pd.DataFrame(columns=["Ngày giao", "Nội dung đơn hàng", "Đơn vị vận chuyển", "Phí (VNĐ)"])

# Khởi tạo Session
if 'carriers' not in st.session_state:
    st.session_state.carriers = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

# Giao diện
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.sidebar:
    st.header("⚙️ Quản lý Đơn vị")
    new_c = st.text_input("Thêm đơn vị mới")
    if st.button("➕ Thêm"):
        if new_c and new_c not in st.session_state.carriers:
            st.session_state.carriers.append(new_c)
            st.rerun()
    
    del_c = st.selectbox("Xóa đơn vị", st.session_state.carriers)
    if st.button("❌ Xóa"):
        if len(st.session_state.carriers) > 1:
            st.session_state.carriers.remove(del_c)
            st.rerun()

# Form nhập liệu
with st.form("input_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 2, 1])
    d = c1.date_input("Ngày", datetime.now())
    n = c2.text_input("Nội dung")
    dv = c3.selectbox("Đơn vị", st.session_state.carriers)
    p = c3.number_input("Phí", min_value=0, step=1000)
    
    if st.form_submit_button("💾 Lưu thông tin"):
        res = connect_gsheet()
        if isinstance(res, gspread.Worksheet):
            res.append_row([d.strftime('%d/%m/%Y'), n, dv, p])
            st.success("Đã lưu thành công! ✅")
            st.balloons()
        else:
            st.error(f"Không thể lưu. Lỗi: {res}")

# Hiển thị bảng
df = load_data()
if not df.empty:
    st.write("---")
    df['Tháng'] = df['Ngày giao'].dt.strftime('%m/%Y')
    sel = st.selectbox("📅 Tháng:", sorted(df['Tháng'].unique(), reverse=True))
    sub = df[df['Tháng'] == sel].copy()
    st.info(f"💰 Tổng: {sub['Phí (VNĐ)'].sum():,.0f} VNĐ")
    sub['Ngày giao'] = sub['Ngày giao'].dt.strftime('%d/%m/%Y')
    st.dataframe(sub.iloc[::-1], use_container_width=True, hide_index=True)
else:
    st.write("Chưa có dữ liệu hoặc lỗi kết nối Sheets.")