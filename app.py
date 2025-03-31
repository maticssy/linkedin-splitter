import pandas as pd
import streamlit as st
import io
import os
from collections import defaultdict

st.set_page_config(page_title="LinkedIn Prospect Splitter", layout="centered")
st.title("LinkedIn Daily Prospect Splitter")

st.markdown("""
Upload your daily CSV file with 80-100 prospects. The app will:
1. Categorize by job title into PM, OPEX/CI, and OPS.
2. Distribute each group (PM, OPEX/CI, OPS) as evenly as possible across 5 LinkedIn accounts.
3. Ensure perfectly balanced totals and fair distribution per group.
4. Provide 15 downloadable CSVs.
5. Show a summary of the breakdown.
""")

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

accounts = ["arun", "assaf", "chen", "leigh", "meirav"]

def categorize(title):
    title = str(title).lower()
    if any(keyword in title for keyword in ["plant manager", "factory manager", "site manager"]):
        return "pm"
    elif any(keyword in title for keyword in ["opex", "ci", "operational excellence", "continuous improvement", "excellence"]):
        return "opex ci"
    else:
        return "ops"

def split_group_evenly(group_df):
    group_df = group_df.sample(frac=1).reset_index(drop=True)
    chunks = [[] for _ in range(len(accounts))]
    for i, (_, row) in enumerate(group_df.iterrows()):
        chunks[i % len(accounts)].append(row)
    return chunks

def fair_distribution(df):
    output = {account: [] for account in accounts}
    distribution = defaultdict(lambda: {"pm": 0, "opex ci": 0, "ops": 0, "total": 0})

    for group in ["pm", "opex ci", "ops"]:
        group_df = df[df['group'] == group]
        group_chunks = split_group_evenly(group_df)
        for i, chunk in enumerate(group_chunks):
            account = accounts[i]
            for row in chunk:
                record = row.to_dict()
                output[account].append(record)
                distribution[account][group] += 1
                distribution[account]["total"] += 1

    return output, distribution

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    base_name = os.path.splitext(uploaded_file.name)[0]

    if 'Job Title' not in df.columns:
        st.error("CSV must have a 'Job Title' column.")
    else:
        df['group'] = df['Job Title'].apply(categorize)
        output_map, distribution = fair_distribution(df)

        st.success("Files processed! Download your 15 split files below:")

        st.markdown(f"**Total contacts:** {len(df)}")
        st.markdown("**Group breakdown:**")
        group_counts = df['group'].value_counts()
        for group in ["pm", "opex ci", "ops"]:
            st.markdown(f"- {group.upper()}: {group_counts.get(group, 0)}")

        st.markdown("**Distribution per LinkedIn account:**")
        for account in accounts:
            st.markdown(f"- **{account.capitalize()}**: {distribution[account]['total']} (PM: {distribution[account]['pm']}, OPEX/CI: {distribution[account]['opex ci']}, OPS: {distribution[account]['ops']})")

        for account, rows in output_map.items():
            output_df = pd.DataFrame(rows).drop(columns=['group'])
            for group in ["pm", "opex ci", "ops"]:
                group_df = pd.DataFrame([r for r in rows if r["group"] == group])
                if not group_df.empty:
                    filename = f"{base_name} - {group} - {account}.csv"
                    buffer = io.BytesIO()
                    group_df.drop(columns=['group']).to_csv(buffer, index=False)
                    st.download_button(label=f"Download {filename}", data=buffer.getvalue(), file_name=filename, mime="text/csv")
