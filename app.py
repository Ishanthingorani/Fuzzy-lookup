import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz

# 🎨 Title
st.markdown("<h1 style='color:red;'>KESTONE</h1>", unsafe_allow_html=True)
st.title("Company Fuzzy Matching Tool")

# 🔐 LOGIN
USER_CREDENTIALS = {
    "cep-0068": "0068",
    "kstn-3175": "3175",
    "ki-0536": "0536"
}

def check_login():
    def login():
        user_id = st.session_state["user_id"].strip().lower()
        password = st.session_state["password"].strip()

        if user_id in USER_CREDENTIALS and USER_CREDENTIALS[user_id] == password:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("👤 User ID", key="user_id")
        st.text_input("🔑 Password", type="password", key="password", on_change=login)
        return False

    elif not st.session_state["authenticated"]:
        st.text_input("👤 User ID", key="user_id")
        st.text_input("🔑 Password", type="password", key="password", on_change=login)
        st.error("❌ Invalid ID or Password")
        return False

    return True

if not check_login():
    st.stop()

# 📊 Confidence Logic
def get_confidence(score):
    if score >= 85:
        return "High"
    elif score >= 60:
        return "Acceptable"
    else:
        return "Low"

# 🧠 Token Overlap
def token_overlap_score(a, b):
    set1 = set(a.lower().split())
    set2 = set(b.lower().split())

    if not set1 or not set2:
        return 0

    overlap = len(set1 & set2)
    total = max(len(set1), len(set2))

    return int((overlap / total) * 100)

# 📂 SAFE FILE READER (FIXED ERROR)
def read_file(file):
    try:
        if file.name.endswith("xlsx"):
            return pd.read_excel(file)
        else:
            return pd.read_csv(file, encoding="utf-8")
    except:
        try:
            return pd.read_csv(file, encoding="latin1")
        except:
            return pd.read_csv(file, encoding="ISO-8859-1")

# 📂 Upload
file1 = st.file_uploader("Upload Client File", type=["csv", "xlsx"])
file2 = st.file_uploader("Upload File For Fuzzy Matching", type=["csv", "xlsx"])

if file1 and file2:
    df1 = read_file(file1)
    df2 = read_file(file2)

    col1 = st.selectbox("Client Column", df1.columns)
    col2 = st.selectbox("Fuzzy Match Column", df2.columns)

    if st.button("Run Matching"):
        results = []

        lusha_raw = df2[col2].dropna().astype(str).tolist()

        for name in df1[col1].dropna().astype(str):

            matches = process.extract(
                name,
                lusha_raw,
                scorer=fuzz.WRatio,
                limit=3
            )

            best = matches[0]
            match_name = best[0]

            # Scores
            fuzzy_score = best[1]
            overlap_score = token_overlap_score(name, match_name)

            score = max(fuzzy_score, overlap_score)

            # Substring Boost
            if name.lower() in match_name.lower():
                score = max(score, 90)

            results.append({
                "Client Company": name,
                "Matched Company": match_name,
                "Score": score,
                "Confidence": get_confidence(score),
                "Alt Match 1": matches[1][0] if len(matches) > 1 else "",
                "Alt Match 2": matches[2][0] if len(matches) > 2 else ""
            })

        result_df = pd.DataFrame(results)

        st.dataframe(result_df)

        # Download
        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "result.csv")
