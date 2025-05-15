# NOTE: set_page_config must be the very first Streamlit command
import streamlit as st
st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image

# Theme toggle
theme = st.sidebar.radio("Theme", ["Light", "Dark"])

# Apply theme styles
if theme == "Dark":
    bg_color = "#DA362C"
    text_color = "white"
    chart_colors = ["#FFFFFF", "#FFD700", "#1E90FF"]
else:
    bg_color = "white"
    text_color = "black"
    chart_colors = px.colors.qualitative.Set1

# Styling injection
st.markdown(f"""
    <style>
        .stApp, .block-container, header, footer, .css-18ni7ap, .css-1d391kg, .css-1v0mbdj, .css-6qob1r, .st-emotion-cache-1v0mbdj {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}
        .css-1v0mbdj .css-1cpxqw2 {{
            background-color: {bg_color} !important;
        }}
        h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown, .stTextInput > div > div > input {{
            color: {text_color} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# Display logo
logo = Image.open("The Roc.png")
st.image(logo, width=200)

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

    # Sidebar filters
    st.sidebar.header("Filters")
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].dropna().unique(), default=df['Username'].dropna().unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].dropna().unique(), default=df['Workstations'].dropna().unique())
    min_date, max_date = df['Date'].min(), df['Date'].max()
    months = pd.date_range(start=min_date, end=max_date, freq='MS').strftime('%B %Y').tolist()
    selected_month = st.sidebar.selectbox("Select Month", months)

    month_start = pd.to_datetime(selected_month)
    month_end = (month_start + pd.offsets.MonthEnd(0)).date()
    date_range = st.sidebar.date_input("Select Date Range", [month_start, month_end], min_value=month_start, max_value=month_end, format="DD/MM/YYYY")

    metrics_to_show = st.sidebar.multiselect(
        "Select Metrics to Display in Charts",
        options=["SourceTotes", "DestinationTotes", "TotalRefills"],
        default=["SourceTotes", "DestinationTotes", "TotalRefills"]
    )

    filtered_df = df[
        (df['Username'].isin(users)) &
        (df['Workstations'].isin(workstations)) &
        (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
    ]

    st.markdown("### 📊 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Source Totes", int(filtered_df['SourceTotes'].sum()))
    col2.metric("Total Destination Totes", int(filtered_df['DestinationTotes'].sum()))
    col3.metric("Total Refills", int(filtered_df['TotalRefills'].sum()))

    # Best average performer
    best_user = filtered_df.copy()
    best_user['Efficiency'] = best_user['TotalRefills'] / (best_user['SourceTotes'] + best_user['DestinationTotes'])
    best_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=False).iloc[0]
    col4.markdown(f"<h6>🏆 Top Efficiency</h6><p style='font-size:14px'>{best_avg['Username']}<br>{best_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)
    worst_avg = best_user.groupby('Username')['Efficiency'].mean().reset_index().sort_values(by='Efficiency', ascending=True).iloc[0]
    col5.markdown(f"<h6>🔻 Lowest Efficiency</h6><p style='font-size:14px'>{worst_avg['Username']}<br>{worst_avg['Efficiency']:.2f}</p>", unsafe_allow_html=True)

    st.markdown("### 📈 Performance Over Time")
    time_df = filtered_df.groupby('Date').sum(numeric_only=True).reset_index()
    if metrics_to_show:
        fig_time = px.line(
            time_df, x='Date', y=metrics_to_show, title='Operational Totals Over Time',
            color_discrete_sequence=chart_colors
        )
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("### 👤 Performance by User")
    user_df = filtered_df.groupby('Username').sum(numeric_only=True).reset_index()
    user_df = user_df[user_df[metrics_to_show[0]] > 0]
    user_df = user_df.sort_values(by=metrics_to_show[0], ascending=False)
    fig_user = px.bar(
        user_df,
        x='Username', y=metrics_to_show[0], color='Username',
        title='Total Operations per User',
        color_discrete_sequence=chart_colors, text=metrics_to_show[0]
    )
    fig_user.update_traces(textposition='outside')
    st.plotly_chart(fig_user, use_container_width=True)  # fixed indentation

    st.markdown("### 🛠️ Performance by Workstation")
    ws_df = filtered_df.groupby('Workstations').sum(numeric_only=True).reset_index()
    ws_df = ws_df[ws_df[metrics_to_show[0]] > 0]
    if metrics_to_show:
        ws_df = ws_df.sort_values(by=metrics_to_show[0], ascending=False)
        fig_ws = px.bar(ws_df, x='Workstations', y=metrics_to_show, barmode='group', title='Operations per Workstation', color_discrete_sequence=chart_colors)
        st.plotly_chart(fig_ws, use_container_width=True)

    st.markdown("### ⚙️ Efficiency Score")
    st.caption("Efficiency = Total Refills / (Source Totes + Destination Totes). This gives a rough measure of how many refills are completed per tote moved.")
    filtered_df['Efficiency'] = filtered_df['TotalRefills'] / (filtered_df['SourceTotes'] + filtered_df['DestinationTotes'])
    eff_df = filtered_df.groupby('Username')['Efficiency'].mean().reset_index()
    eff_df = eff_df[eff_df['Efficiency'] > 0]
    eff_df = eff_df.sort_values(by='Efficiency', ascending=False)
    fig_eff = px.bar(eff_df, x='Username', y='Efficiency', title='Average Efficiency per User', color_discrete_sequence=chart_colors)
    st.plotly_chart(fig_eff, use_container_width=True)

    # Best average performer
    best_user = eff_df.iloc[0]
    st.success(f"🏆 Best Average Efficiency: {best_user['Username']} with score {best_user['Efficiency']:.2f}")

    output = BytesIO()
    filtered_df.to_csv(output, index=False)
    st.download_button("Download Filtered CSV", data=output.getvalue(), file_name="filtered_picking_data.csv", mime="text/csv")

else:
    st.info("Please upload a CSV file to begin.")


