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
2. Distribute all contacts as evenly as possible across 5 LinkedIn accounts: Arun, Assaf, Chen, Leigh, Meirav.
3. Ensure balanced totals across accounts, even if group sizes vary.
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

def balanced_distribution(df):
    df = df.sample(frac=1).reset_index(drop=True)  # shuffle for fairness
    distribution = defaultdict(lambda: {"pm": 0, "opex ci": 0, "ops": 0, "total": 0})
    output = {account: [] for account in accounts}

    # Sort by group for tracking group counts later
    grouped = df.groupby("group")
    rows = df.to_dict(orient="records")

    for i, row in enumerate(rows):
        account = accounts[i % len(accounts)]
        output[account].append(row)
        distribution[account][row["group"]] += 1
        distribution[account]["total"] += 1

    return output, distribution

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    base_name = os.path.splitext(uploaded_file.name)[0]

    if 'Job Title' not in df.columns:
        st.error("CSV must have a 'Job Title' column.")
    else:
        df['group'] = df['Job Title'].apply(categorize)
        output_map, distribution = balanced_distribution(df)

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
