import streamlit as st
import pandas as pd
import re
from rapidfuzz import process, fuzz

st.title("Company Fuzzy Matching Tool")

def clean_name(name):
    name = str(name).lower()
    name = re.sub(r'\b(pvt|private|ltd|limited|llp|inc)\b', '', name)
    name = re.sub(r'[^a-z0-9 ]', '', name)
    return name.strip()

def get_confidence(score):
    if score >= 85:
        return "High"
    elif score >= 70:
        return "Medium"
    else:
        return "Low"

file1 = st.file_uploader("Upload Client File", type=["csv", "xlsx"])
file2 = st.file_uploader("Upload FIle For Fuzzy", type=["csv", "xlsx"])

if file1 and file2:
    df1 = pd.read_excel(file1) if file1.name.endswith("xlsx") else pd.read_csv(file1)
    df2 = pd.read_excel(file2) if file2.name.endswith("xlsx") else pd.read_csv(file2)

    col1 = st.selectbox("Client Column", df1.columns)
    col2 = st.selectbox("For Fuzzy lookup File Column", df2.columns)

    if st.button("Run Matching"):
        results = []

        lusha_raw = df2[col2].dropna().astype(str).tolist()
        lusha_clean = [clean_name(x) for x in lusha_raw]

        for name in df1[col1].dropna().astype(str):
            cleaned = clean_name(name)

            match, score, idx = process.extractOne(
                cleaned,
                lusha_clean,
                scorer=fuzz.token_sort_ratio
            )

            results.append({
                "Client Company": name,
                "Matched Company": lusha_raw[idx],
                "Score": score,
                "Confidence": get_confidence(score)
            })

        result_df = pd.DataFrame(results)
        st.dataframe(result_df)

        csv = result_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "result.csv")
