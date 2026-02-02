import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import bcrypt
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="RPL Practicum Hub", page_icon="🤖", layout="centered")

# Scope for Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- BACKEND FUNCTIONS ---

@st.cache_resource
def connect_to_sheets():
    """Connects to Google Sheets using Streamlit Secrets."""
    try:
        # Construct credentials from Streamlit secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Open the Sheet by Key or Name (Put your Sheet Name here)
        sheet = client.open("RPL_Practicum_Data") 
        return sheet
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def get_user_data(sheet, username):
    """Fetches user credentials."""
    users_ws = sheet.worksheet("users")
    records = users_ws.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty and username in df['username'].values:
        return df[df['username'] == username].iloc[0]
    return None

def register_user(sheet, username, password):
    """Registers a new user."""
    users_ws = sheet.worksheet("users")
    # Check if exists
    if get_user_data(sheet, username) is not None:
        return False
    
    hashed = hash_password(password)
    users_ws.append_row([username, hashed])
    return True

def get_submission(sheet, username):
    """Fetches the student's existing submission."""
    sub_ws = sheet.worksheet("submissions")
    records = sub_ws.get_all_records()
    df = pd.DataFrame(records)
    if not df.empty and username in df['username'].values:
        return df[df['username'] == username].iloc[0]
    return None

def save_submission(sheet, data, is_update=False):
    """Saves or updates a submission."""
    sub_ws = sheet.worksheet("submissions")
    
    row_data = [
        data['username'],
        data['full_name'],
        data['class_name'],
        data['teammates'],
        data['colab_link'],
        data['status'], # "Sudah Beres"
        str(pd.Timestamp.now())
    ]

    if is_update:
        # Find the cell to update (A bit manual in gspread, but reliable)
        cell = sub_ws.find(data['username'])
        # Update the entire row (offset based on schema)
        # Note: Ideally we use batch_update for speed, but this is fine for a class
        r = cell.row
        sub_ws.update(f"A{r}:G{r}", [row_data])
    else:
        sub_ws.append_row(row_data)

# --- FRONTEND UI ---

def main():
    st.title("🤖 Intro to AI: Practicum Hub")
    
    # Initialize Session State
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    sheet = connect_to_sheets()

    if not sheet:
        st.warning("Please configure your Google Cloud secrets.")
        return

    # --- LOGIN / REGISTER VIEW ---
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login to access your drive")
            l_user = st.text_input("Username (Name/NIS)", key="l_user")
            l_pass = st.text_input("Password", type="password", key="l_pass")
            
            if st.button("Login", type="primary"):
                user_record = get_user_data(sheet, l_user)
                if user_record is not None and check_password(l_pass, user_record['password']):
                    st.session_state.logged_in = True
                    st.session_state.username = l_user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with tab2:
            st.subheader("Create a Student Account")
            r_user = st.text_input("Choose a Username (Name/NIS)", key="r_user")
            r_pass = st.text_input("Choose a Password", type="password", key="r_pass")
            r_pass_conf = st.text_input("Confirm Password", type="password", key="r_pass_conf")
            
            if st.button("Register"):
                if r_pass != r_pass_conf:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 4:
                    st.error("Password is too short.")
                else:
                    success = register_user(sheet, r_user, r_pass)
                    if success:
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username already taken.")

    # --- DASHBOARD VIEW (LOGGED IN) ---
    else:
        st.sidebar.write(f"Logged in as: **{st.session_state.username}**")
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown("### 📝 Upload Your Practicum Link")
        st.info("You can edit this form anytime. I will only check the latest link.")

        # Check for existing data to pre-fill
        existing_data = get_submission(sheet, st.session_state.username)
        
        with st.form("submission_form"):
            full_name = st.text_input("Full Name", value=existing_data['full_name'] if existing_data is not None else "")
            
            # Class Dropdown
            class_options = ["XI RPL 1", "XI RPL 2", "XI RPL 3"]
            class_idx = class_options.index(existing_data['class_name']) if existing_data is not None and existing_data['class_name'] in class_options else 0
            class_name = st.selectbox("Class", class_options, index=class_idx)

            # Teammates Logic
            # Store as string "Name 1, Name 2" in DB, but showing as text area is easier
            st.caption("Projectmates (Leave blank if solo)")
            teammates = st.text_area("Teammate Names (separate with comma)", value=existing_data['teammates'] if existing_data is not None else "")

            # The Important Bit
            colab_link = st.text_input("Colab Link (Shared as Editor)", value=existing_data['colab_link'] if existing_data is not None else "")
            
            # Status
            status_check = st.checkbox("Truthful Declaration: Sudah Beres?", value=(existing_data['status'] == "TRUE") if existing_data is not None else False)

            submitted = st.form_submit_button("Save / Update Work")
            
            if submitted:
                if "colab" not in colab_link.lower() and "drive" not in colab_link.lower():
                    st.error("That doesn't look like a valid Colab/Drive link.")
                elif not full_name:
                    st.error("Please enter your name.")
                else:
                    data = {
                        "username": st.session_state.username,
                        "full_name": full_name,
                        "class_name": class_name,
                        "teammates": teammates,
                        "colab_link": colab_link,
                        "status": "TRUE" if status_check else "FALSE"
                    }
                    
                    with st.spinner("Syncing to Database..."):
                        save_submission(sheet, data, is_update=(existing_data is not None))
                    
                    st.success("Data Saved! You can close this tab.")

if __name__ == "__main__":
    main()
