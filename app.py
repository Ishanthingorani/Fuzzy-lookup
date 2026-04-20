import streamlit as st
import pandas as pd
import re
from rapidfuzz import process, fuzz

# ================= UI =================
st.markdown("<h1 style='color:red;'>KESTONE</h1>", unsafe_allow_html=True)
st.title("Company Fuzzy Matching Tool (Excel-Like Lookup Engine)")


# ================= LOGIN =================
USER_CREDENTIALS = {
    "cep-0068": "0068",
    "kstn-3175": "3175",
    "ki-0536": "0536"
}

def login_check():
    user_id = st.session_state.get("user_id", "").strip().lower()
    password = st.session_state.get("password", "")

    if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == password:
        st.session_state["authenticated"] = True
    else:
        st.session_state["authenticated"] = False


def check_login():

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:

        st.text_input("👤 User ID", key="user_id")
        st.text_input("🔑 Password", type="password", key="password")

        st.markdown("""
        <style>
        div.stButton > button {
            background-color: black;
            color: white;
            border-radius: 6px;
            height: 40px;
            width: 120px;
            font-weight: bold;
        }
        div.stButton > button:hover {
            background-color: #222222;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.button("Login"):
            login_check()
            if not st.session_state["authenticated"]:
                st.error("❌ Invalid ID or Password")
            else:
                st.success("✅ Login Successful")
                st.rerun()

        return False

    return True


if not check_login():
    st.stop()
# ================= CLEANING FUNCTION (LOOKUP KEY BUILDER) =================
def clean_name(name):
    name = str(name).lower()

    # remove legal suffixes
    name = re.sub(r'\b(pvt|private|ltd|limited|llp|inc|co|company|corp|corporation|group)\b', '', name)

    # normalize symbols
    name = name.replace("&", " and ")

    # remove special characters
    name = re.sub(r'[^a-z0-9 ]', ' ', name)

    # remove extra spaces
    name = re.sub(r'\s+', ' ', name)

    return name.strip()


# ================= CONFIDENCE =================
def get_confidence(score):
    if score >= 85:
        return "High"
    elif score >= 70:
        return "Medium"
    else:
        return "Low"


# ================= FILE UPLOAD =================
file1 = st.file_uploader("Upload Client File", type=["csv", "xlsx"])
file2 = st.file_uploader("Upload Lookup File", type=["csv", "xlsx"])


if file1 and file2:

    # read files safely
    df1 = pd.read_excel(file1) if file1.name.lower().endswith("xlsx") else pd.read_csv(file1)
    df2 = pd.read_excel(file2) if file2.name.lower().endswith("xlsx") else pd.read_csv(file2)

    col1 = st.selectbox("Client Column", df1.columns)
    col2 = st.selectbox("Lookup Column", df2.columns)


    if st.button("Run Matching"):

        st.info("Processing fuzzy lookup...")

        results = []

        # ================= PREP LOOKUP TABLE =================
        df2 = df2.drop_duplicates(subset=[col2]).copy()

        df2["clean"] = df2[col2].astype(str).apply(clean_name)

        lookup_clean_list = df2["clean"].tolist()
        lookup_raw_list = df2[col2].astype(str).tolist()

        lookup_map = dict(zip(lookup_clean_list, lookup_raw_list))


        # ================= MATCHING =================
        for name in df1[col1].dropna().astype(str):

            cleaned = clean_name(name)

            match_result = process.extractOne(
                cleaned,
                lookup_clean_list,
                scorer=fuzz.WRatio
            )

            if not match_result:
                continue

            match, score, idx = match_result

            if score < 60:
                continue

            results.append({
                "Client Company": name,
                "Matched Company": lookup_map.get(match, ""),
                "Clean Key": match,
                "Score": score,
                "Confidence": get_confidence(score)
            })


        # ================= OUTPUT =================
        result_df = pd.DataFrame(results)

        st.success("Matching Completed!")

        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "fuzzy_lookup_result.csv")
