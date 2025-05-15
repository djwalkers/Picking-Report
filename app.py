# NOTE: set_page_config must be the very first Streamlit command
import streamlit as st
st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from io import BytesIO

st.title("📦 Picking Performance Dashboard")
st.markdown("Upload your Picking Performance CSV file to begin analysis.")

# File upload
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Clean column names and convert data types
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['SourceTotes'] = pd.to_numeric(df['SourceTotes'], errors='coerce')
    df['DestinationTotes'] = pd.to_numeric(df['DestinationTotes'], errors='coerce')
    df['TotalRefills'] = pd.to_numeric(df['TotalRefills'], errors='coerce')

    # Debug output
    with st.expander("🔍 Show Debug Info"):
        st.write("Column names:", df.columns.tolist())
        st.write("Data types:", df.dtypes)
        st.write("Sample data:", df.head())

    # Sidebar filters
    st.sidebar.header("Filters")
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].dropna().unique(), default=df['Username'].dropna().unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].dropna().unique(), default=df['Workstations'].dropna().unique())
    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input("Filter by Date Range (DD/MM/YYYY)", [min_date, max_date], min_value=min_date, max_value=max_date, format="DD/MM/YYYY")

    # Data field selection for charts
    metrics_to_show = st.sidebar.multiselect(
        "Select Metrics to Display in Charts",
        options=["SourceTotes", "DestinationTotes", "TotalRefills"],
        default=["SourceTotes", "DestinationTotes", "TotalRefills"]
    )

    # Filter DataFrame
    filtered_df = df[
        (df['Username'].isin(users)) &
        (df['Workstations'].isin(workstations)) &
        (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
    ]

    st.markdown("### 📊 Summary Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Source Totes", int(filtered_df['SourceTotes'].sum()))
    col2.metric("Total Destination Totes", int(filtered_df['DestinationTotes'].sum()))
    col3.metric("Total Refills", int(filtered_df['TotalRefills'].sum()))

    st.markdown("### 📈 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_time = px.line(time_df, x='Date', y=metrics_to_show, title='Operational Totals Over Time')
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("### 👤 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_user = px.bar(user_df, x='Username', y=metrics_to_show, barmode='group', title='Operations per User')
        st.plotly_chart(fig_user, use_container_width=True)

    st.markdown("### 🛠️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_ws = px.bar(ws_df, x='Workstations', y=metrics_to_show, barmode='group', title='Operations per Workstation')
        st.plotly_chart(fig_ws, use_container_width=True)

    st.markdown("### ⚙️ Efficiency Score")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    fig_eff = px.bar(eff_df, x='Username', y='Efficiency', title='Average Efficiency per User')
    st.plotly_chart(fig_eff, use_container_width=True)

    # Download filtered data
    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button("Download Filtered CSV", data=output.getvalue(), file_name="filtered_picking_data.csv", mime="text/csv")

else:
    st.info("Please upload a CSV file to begin.")