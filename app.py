import streamlit as st
st.set_page_config(page_title="Picking Performance Dashboard", layout="wide")

import pandas as pd
import plotly.express as px
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta

bg_color = "#DA362C"
text_color = "white"
chart_colors = ["#FFFFFF", "#FFD700", "#1E90FF"]

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
        .outlier {{
            color: #FFD700 !important;
            background-color: #750000 !important;
            border-radius: 6px;
            padding: 2px 8px;
            font-weight: bold;
            display: inline-block;
        }}
    </style>
""", unsafe_allow_html=True)

def style_chart(fig):
    fig.update_layout(
        font=dict(family="Segoe UI, Arial", size=16, color="#FFF"),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color="#FFF"),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=14, color="#FFF"),
            title=dict(font=dict(size=16, color="#FFF")),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=14, color="#FFF"),
            title=dict(font=dict(size=16, color="#FFF")),
            zeroline=False,
        ),
        margin=dict(t=60, b=50, l=50, r=30),
    )
    return fig

logo = Image.open("The Roc.png")
st.image(logo, width=200)

st.title("📦 Picking Performance Dashboard")
st.markdown("Upload your Picking Performance CSV file to begin analysis.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

def assign_shift(dt):
    if pd.isnull(dt):
        return "UNKNOWN"
    hour = dt.hour
    if 6 <= hour < 14:
        return "AM"
    elif 14 <= hour < 22:
        return "PM"
    else:
        return "NIGHT"

def get_date_slicer(min_date, max_date):
    today = pd.Timestamp.today().normalize()
    week_ago = today - pd.Timedelta(days=6)
    month_ago = today - pd.Timedelta(days=29)
    slicer = st.sidebar.radio(
        "Quick Date Slicers",
        options=["Today", "This Week", "This Month", "Custom"],
        index=2 if max_date - min_date > pd.Timedelta(days=7) else 0,
        horizontal=True,
    )
    if slicer == "Today":
        return [today, today]
    elif slicer == "This Week":
        return [week_ago, today]
    elif slicer == "This Month":
        return [month_ago, today]
    else:
        return st.sidebar.date_input(
            "Select Date Range (DD/MM/YYYY)",
            [min_date.date(), max_date.date()],
            min_value=min_date.date(),
            max_value=max_date.date(),
            format="DD/MM/YYYY"
        )

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()
    df['DateTime'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    df['Date'] = df['DateTime'].dt.date
    df['Time'] = df['DateTime'].dt.time
    df['Shift'] = df['DateTime'].apply(assign_shift)
    df['SourceTotes'] = pd.to_numeric(df['SourceTotes'], errors='coerce')
    df['DestinationTotes'] = pd.to_numeric(df['DestinationTotes'], errors='coerce')
    df['TotalRefills'] = pd.to_numeric(df['TotalRefills'], errors='coerce')

    st.sidebar.header("Filters")
    users = st.sidebar.multiselect("Filter by User", options=df['Username'].dropna().unique(), default=df['Username'].dropna().unique())
    workstations = st.sidebar.multiselect("Filter by Workstation", options=df['Workstations'].dropna().unique(), default=df['Workstations'].dropna().unique())
    min_dt, max_dt =

