import streamlit as st
import requests
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="💻", layout="wide")

# ⚠️ UPDATE THIS URL AFTER DEPLOYING THE NEW APPS SCRIPT
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzo5YZZmOfO6mCpl4a6sv4HHYwihLNfRxZ-CsHTH8DXnjESXLlyKHRJdt5WCPWeEyeXOQ/exec"

# --- BACKEND WRAPPER ---
def api_request(payload):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

# --- UI ---
def main():
    # Initialize Session
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # ==========================================
    # 🔐 LOGIN / REGISTER SCREEN
    # ==========================================
    if not st.session_state.logged_in:
        # Centered layout for login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("💻 RPL Practicum Hub")
            st.info("ℹ️ **Perhatian:** Harap ingat Username & Password anda. Admin: Login sebagai 'admin'.")
            
            tab1, tab2 = st.tabs(["Login", "Register"])
            
            with tab1:
                l_user = st.text_input("Username", key="l")
                l_pass = st.text_input("Password", type="password", key="lp")
                if st.button("Login", type="primary", use_container_width=True):
                    with st.spinner("Authenticating..."):
                        res = api_request({"action": "login", "username": l_user, "password": l_pass})
                        if res and res.get('status') == 'success':
                            st.session_state.logged_in = True
                            st.session_state.username = l_user
                            st.toast("Login Berhasil!", icon="✅")
                            st.rerun()
                        else:
                            st.error("Username atau Password salah.")

            with tab2:
                r_user = st.text_input("Buat Username Baru", key="r")
                r_pass = st.text_input("Buat Password Baru", type="password", key="rp")
                if st.button("Register", use_container_width=True):
                    if not r_user or not r_pass:
                        st.error("Field tidak boleh kosong.")
                    else:
                        with st.spinner("Creating account..."):
                            res = api_request({"action": "register", "username": r_user, "password": r_pass})
                            if res and res.get('status') == 'success':
                                st.success("Akun dibuat! Silakan Login.")
                            elif res and res.get('message') == 'User taken':
                                st.error("Username sudah dipakai.")
                            else:
                                st.error("Gagal membuat akun.")

    # ==========================================
    # 🏠 LOGGED IN DASHBOARD
    # ==========================================
    else:
        # --- SIDEBAR MENU ---
        st.sidebar.title("🔧 Menu")
        st.sidebar.write(f"User: **{st.session_state.username}**")
        if st.sidebar.button("Logout", type="primary"):
            st.session_state.logged_in = False
            st.rerun()

        # ==========================================
        # 👑 ADMIN DASHBOARD (IF USER IS 'admin')
        # ==========================================
        if st.session_state.username == "admin": 
            st.title("👑 Admin Dashboard")
            st.markdown("Rekapitulasi Pengumpulan Tugas Siswa")

            col_ref, col_space = st.columns([1, 5])
            with col_ref:
                if st.button("🔄 Refresh Data"):
                    st.rerun()

            # Fetch All Data
            with st.spinner("Mengambil semua data siswa..."):
                res = api_request({"action": "get_all_data"})
            
            if res and res.get('status') == 'success':
                data = res['data']
                if len(data) > 0:
                    df = pd.DataFrame(data)

                    # Quick Metrics
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Total Siswa", len(df))
                    m2.metric("Sudah Mengerjakan", len(df[df['status'] == 'Sudah Mengerjakan']))
                    m3.metric("Belum Mengerjakan", len(df[df['status'] != 'Sudah Mengerjakan']))

                    st.markdown("---")

                    # Class Tabs
                    classes = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
                    tabs = st.tabs(classes)

                    for i, cls in enumerate(classes):
                        with tabs[i]:
                            # Filter dataframe by class
                            df_class = df[df['class_name'] == cls].copy()
                            
                            if df_class.empty:
                                st.info(f"Belum ada data untuk {cls}")
                            else:
                                # Reorder columns for neatness
                                display_cols = ['full_name', 'colab_filename', 'colab_link', 'status', 'teammates', 'last_updated']
                                df_display = df_class[display_cols]
                                
                                # Use Data Editor with Column Config for clickable links
                                st.data_editor(
                                    df_display,
                                    column_config={
                                        "full_name": "Nama Lengkap",
                                        "colab_filename": "Nama File",
                                        "colab_link": st.column_config.LinkColumn(
                                            "Link Colab",
                                            display_text="Buka Colab 🔗"
                                        ),
                                        "status": st.column_config.TextColumn(
                                            "Status",
                                            help="Status pengerjaan siswa"
                                        ),
                                        "teammates": "Tim",
                                        "last_updated": st.column_config.DatetimeColumn(
                                            "Terakhir Update",
                                            format="D MMM YYYY, HH:mm"
                                        ),
                                    },
                                    hide_index=True,
                                    disabled=True, # Read-only
                                    use_container_width=True
                                )
                else:
                    st.warning("Data database kosong.")
            else:
                st.error("Gagal mengambil data dari server. Cek koneksi Apps Script.")

        # ==========================================
        # 🎓 STUDENT DASHBOARD (ALL OTHER USERS)
        # ==========================================
        else:
            # Layout adjustment for student view
            st.title("📝 Dashboard Pengumpulan")
            
            # Load User Data
            if 'form_data' not in st.session_state:
                with st.spinner("Sinkronisasi data..."):
                    res = api_request({"action": "get_submission", "username": st.session_state.username})
                    if res and res.get('status') == 'found':
                        st.session_state.form_data = res['data']
                    else:
                        st.session_state.form_data = {}

            data = st.session_state.form_data

            # 1. Hyperlink Display (If data exists)
            if data.get('colab_link') and data.get('colab_filename'):
                st.success(f"📂 **File Anda Tersimpan:** [{data.get('colab_filename')}]({data.get('colab_link')})")
                st.caption("☝️ *Klik link di atas untuk memastikan file bisa dibuka.*")

            # 2. Submission Form
            with st.form("student_form"):
                st.subheader("Data Siswa")
                col_a, col_b = st.columns(2)
                with col_a:
                    full_name = st.text_input("Nama Lengkap", value=data.get('full_name', ''))
                with col_b:
                    cls_opts = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
                    saved_cls = data.get('class_name', "XI RPL 1")
                    idx = cls_opts.index(saved_cls) if saved_cls in cls_opts else 0
                    class_name = st.selectbox("Kelas", cls_opts, index=idx)

                st.write("👥 **Projectmates (Teman Kelompok)**")
                teammates_text = st.text_area(
                    "List Nama Teman (Satu baris satu nama)", 
                    value=data.get('teammates', '').replace(',', '\n'), 
                    height=100,
                    help="Jika mengerjakan sendiri, kosongkan atau isi '-'. Jika berkelompok, tulis nama teman satu per satu."
                )

                st.markdown("---")
                st.subheader("Link Project")
                
                # Warning Box
                st.warning("""
                ⚠️ **ATURAN WAJIB:**
                1. Ganti nama file Colab anda menjadi format: `Praktikum X_Minggu Y_Nama_Kelas`.
                2. Klik tombol 'Share' di pojok kanan atas Colab.
                3. Ubah akses menjadi **'Anyone with the link'** -> **'Editor'**.
                """)
                
                colab_filename = st.text_input("Nama File Colab (Sesuai format)", 
                                             value=data.get('colab_filename', ''),
                                             placeholder="Contoh: Praktikum 5_Minggu 4_Arid_XIRPL1")
                
                colab_link = st.text_input("Link Colab (URL)", 
                                         value=data.get('colab_link', ''),
                                         placeholder="https://colab.research.google.com/drive/...")

                st.markdown("---")
                
                # Status Dropdown
                status_opts = ["Belum Mengerjakan", "Sudah Mengerjakan"]
                saved_status = data.get('status')
                # Handle legacy boolean or string
                status_idx = 0
                if str(saved_status) == "Sudah Mengerjakan" or str(saved_status).upper() == 'TRUE':
                    status_idx = 1
                
                status_input = st.selectbox("Status Pengerjaan", status_opts, index=status_idx)

                # Submit Button
                submitted = st.form_submit_button("💾 Simpan Data", type="primary")

                if submitted:
                    if not colab_link:
                        st.error("❌ Link Colab wajib diisi!")
                    elif not colab_filename:
                        st.error("❌ Nama File Colab wajib diisi!")
                    elif not full_name:
                        st.error("❌ Nama Lengkap wajib diisi!")
                    else:
                        # Process Data
                        processed_teammates = ", ".join([t.strip() for t in teammates_text.split('\n') if t.strip()])
                        
                        payload = {
                            "action": "update_submission",
                            "username": st.session_state.username,
                            "full_name": full_name,
                            "class_name": class_name,
                            "teammates": processed_teammates,
                            "colab_link": colab_link,
                            "colab_filename": colab_filename,
                            "status": status_input
                        }
                        
                        with st.spinner("Menyimpan ke Database..."):
                            api_request(payload)
                            # Update local session instantly
                            st.session_state.form_data = {
                                "full_name": full_name, 
                                "class_name": class_name, 
                                "teammates": processed_teammates, 
                                "colab_link": colab_link, 
                                "colab_filename": colab_filename,
                                "status": status_input
                            }
                        st.success("✅ Data Berhasil Disimpan!")
                        st.balloons()
                        # Optional: Sleep briefly then rerun to refresh the 'File Tersimpan' link
                        # import time; time.sleep(1); st.rerun()

if __name__ == "__main__":
    main()
