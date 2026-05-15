import streamlit as st
import pandas as pd
from datetime import datetime
import gspread

st.set_page_config(page_title="Quản lý Phí Giao Hàng", layout="wide")

def get_conn():
    try:
        # Lấy thông tin bảo mật từ Streamlit Secrets
        s = st.secrets
        creds = {
            "type": s["type"],
            "project_id": s["project_id"],
            "private_key_id": s["private_key_id"],
            "private_key": s["private_key"].replace("\\n", "\n"),
            "client_email": s["client_email"],
            "client_id": s["client_id"],
            "auth_uri": s["auth_uri"],
            "token_uri": s["token_uri"],
            "auth_provider_x509_cert_url": s["auth_provider_x509_cert_url"],
            "client_x509_cert_url": s["client_x509_cert_url"]
        }
        gc = gspread.service_account_from_dict(creds)
        # Mở bằng ID file Sheets của bạn
        sh = gc.open_by_key("1pX1uImwD770upHdJ4OKNzYxwKxd5qVeI2zQeW0SBLUg")
        return sh.get_worksheet(0), None
    except Exception as e:
        return None, str(e)

# --- QUẢN LÝ DANH SÁCH ĐƠN VỊ ---
if 'ds_donvi' not in st.session_state:
    st.session_state.ds_donvi = ["Ahamove 🛵", "Grab 🚗", "Lalamove 🚛", "GHTK 📦"]

with st.sidebar:
    st.header("⚙️ Cài đặt")
    moi = st.text_input("Thêm đơn vị vận chuyển mới")
    if st.button("Thêm"):
        if moi and moi not in st.session_state.ds_donvi:
            st.session_state.ds_donvi.append(moi)
            st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.title("🚚 Quản Lý Chi Phí Giao Hàng")

with st.form("nhap_lieu", clear_on_submit=True):
    c1, c2, c3 = st.columns([1, 2, 1])
    ng = c1.date_input("Ngày tháng năm", datetime.now())
    nd = c2.text_input("Nội dung (Giao hàng cho ai/cái gì...)")
    dv = c3.selectbox("Đơn vị vận chuyển", st.session_state.ds_donvi)
    t = c3.number_input("Phí vận chuyển (VNĐ)", min_value=0, step=1000)
    
    submit = st.form_submit_button("💾 Lưu thông tin")
    
    if submit:
        if not nd:
            st.warning("Như ơi, nhập thêm nội dung nhé!")
        else:
            ws, err = get_conn()
            if ws:
                # Lưu dữ liệu xuống Sheets
                ws.append_row([ng.strftime('%d/%m/%Y'), nd, dv, t])
                st.success("Đã lưu thành công! ✅")
                st.balloons()
            else:
                st.error(f"Lỗi kết nối: {err}")

st.write("---")

# --- HIỂN THỊ DỮ LIỆU & BỘ LỌC ---
ws, err = get_conn()
if ws:
    try:
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data)
            
            # Tính tổng cộng
            tong_phi = df['Phí'].sum()
            
            col_t1, col_t2 = st.columns([3, 1])
            with col_t1:
                st.subheader("📋 Danh sách đã book")
            with col_t2:
                st.metric("Tổng cộng", f"{tong_phi:,} VNĐ")
            
            # Hiển thị bảng (đưa đơn hàng mới nhất lên đầu)
            st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
            
            # Nút xuất file để Như in báo cáo
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Xuất file Excel (CSV) để in",
                data=csv,
                file_name=f'phi_vanchuyen_{datetime.now().strftime("%m_%Y")}.csv',
                mime='text/csv',
            )
        else:
            st.info("Chưa có dữ liệu. Như hãy nhập đơn hàng đầu tiên nhé!")
    except Exception as e:
        st.warning("Không đọc được dữ liệu. Như hãy kiểm tra hàng 1 của file Sheets có đúng 4 cột: Ngày, Nội dung, Đơn vị, Phí không nhé.")
else:
    st.error("Không thể kết nối với dữ liệu. Hãy kiểm tra lại phần Secrets hoặc quyền chia sẻ file Sheets.")