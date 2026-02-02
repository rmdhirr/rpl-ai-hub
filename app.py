import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="🤖")

# PASTE YOUR WEB APP URL HERE
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwKxbxD4eQw5cZHx-1_PW1pg67fGYMbTtDawsQwAnv3H9P4_-D9n4Xs6iFwXkdR5Cypvw/exec"

# --- BACKEND WRAPPER ---
# We treat your Sheet like a REST API now.

def api_request(payload):
    try:
        # We must use POST because Apps Script doGet has size limits
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        return response.json()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- UI ---
def main():
    st.title("🤖 RPL Practicum Hub")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    # LOGIN / REGISTER
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            l_user = st.text_input("Username (Name/NIS)", key="l")
            l_pass = st.text_input("Password", type="password", key="lp")
            if st.button("Login"):
                res = api_request({"action": "login", "username": l_user, "password": l_pass})
                if res and res.get('status') == 'success':
                    st.session_state.logged_in = True
                    st.session_state.username = l_user
                    st.success("Welcome!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        with tab2:
            r_user = st.text_input("New Username", key="r")
            r_pass = st.text_input("New Password", type="password", key="rp")
            if st.button("Register"):
                res = api_request({"action": "register", "username": r_user, "password": r_pass})
                if res and res.get('status') == 'success':
                    st.success("Registered! Please Login.")
                elif res and res.get('message') == 'User taken':
                    st.error("Username already taken.")
                else:
                    st.error("Registration failed.")

    # DASHBOARD
    else:
        st.sidebar.write(f"👤 {st.session_state.username}")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # Load existing data on load
        if 'form_data' not in st.session_state:
            res = api_request({"action": "get_submission", "username": st.session_state.username})
            if res and res.get('status') == 'found':
                st.session_state.form_data = res['data']
            else:
                st.session_state.form_data = {}

        data = st.session_state.form_data

        st.subheader("📝 Your Submission")
        
        with st.form("main_form"):
            full_name = st.text_input("Full Name", value=data.get('full_name', ''))
            
            cls_opts = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
            saved_cls = data.get('class_name', "XI RPL 1")
            class_name = st.selectbox("Class", cls_opts, index=cls_opts.index(saved_cls) if saved_cls in cls_opts else 0)

            teammates = st.text_area("Teammates (if any)", value=data.get('teammates', ''))
            colab_link = st.text_input("Colab Link", value=data.get('colab_link', ''))
            
            # Checkbox needs boolean
            is_done_val = data.get('status')
            # Handle string 'TRUE'/'FALSE' from sheets or boolean from JSON
            if isinstance(is_done_val, str):
                is_done_bool = (is_done_val.lower() == 'true')
            else:
                is_done_bool = bool(is_done_val)

            is_done = st.checkbox("Truthful Declaration: 'Sudah Beres'", value=is_done_bool)

            if st.form_submit_button("Save Update"):
                if not colab_link:
                    st.error("Link required.")
                else:
                    payload = {
                        "action": "update_submission",
                        "username": st.session_state.username,
                        "full_name": full_name,
                        "class_name": class_name,
                        "teammates": teammates,
                        "colab_link": colab_link,
                        "status": is_done
                    }
                    with st.spinner("Syncing..."):
                        api_request(payload)
                        # Refresh local state
                        st.session_state.form_data = {
                            "full_name": full_name, "class_name": class_name, 
                            "teammates": teammates, "colab_link": colab_link, "status": is_done
                        }
                    st.success("Saved!")

if __name__ == "__main__":
    main()
