import os
from pathlib import Path

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="Yearly Rent Overview", layout="wide")
st.title("Yearly Average Rent Overview")

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

# -------------------------
# Load filter data
# -------------------------

building_groups_df = pd.read_sql(
    """
    SELECT building_group_no, name
    FROM building_group
    ORDER BY name;
    """,
    conn
)

buildings_df = pd.read_sql(
    """
    SELECT building_no, building_group_no, name, postal_code
    FROM building
    ORDER BY name;
    """,
    conn
)

# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters")

building_group_options = ["All"] + building_groups_df["name"].tolist()

selected_group_name = st.sidebar.selectbox(
    "Building Group",
    building_group_options,
    key="yearly_rent_group_filter"
)

if selected_group_name != "All":
    selected_group_no = int(
        building_groups_df.loc[
            building_groups_df["name"] == selected_group_name,
            "building_group_no"
        ].iloc[0]
    )
else:
    selected_group_no = None

if selected_group_no is not None:
    filtered_buildings_df = buildings_df[
        buildings_df["building_group_no"] == selected_group_no
    ]
else:
    filtered_buildings_df = buildings_df

building_options = ["All"] + filtered_buildings_df["name"].tolist()

selected_building_name = st.sidebar.selectbox(
    "Building",
    building_options,
    key="yearly_rent_building_filter"
)

if selected_building_name != "All":
    selected_building_no = int(
        filtered_buildings_df.loc[
            filtered_buildings_df["name"] == selected_building_name,
            "building_no"
        ].iloc[0]
    )
else:
    selected_building_no = None

bedroom_options = ["All", "Studio/Bachelor", "1", "2", "3"]

selected_bedroom_label = st.sidebar.selectbox(
    "Bedroom No.",
    bedroom_options,
    key="yearly_rent_bedroom_filter"
)

if selected_bedroom_label == "Studio/Bachelor":
    selected_bedroom = 0
elif selected_bedroom_label == "All":
    selected_bedroom = "All"
else:
    selected_bedroom = int(selected_bedroom_label)

selected_postal_code = st.sidebar.text_input(
    "Postal Code",
    key="yearly_rent_postal_code_filter"
)

# -------------------------
# Query yearly average rent
# -------------------------

query = """
SELECT
    bg.name AS building_group_name,
    b.name AS building_name,
    b.postal_code,
    bu.rental_year,
    ROUND(AVG(bu.actual_rent), 2) AS average_rent
FROM building_unit_daily bu
JOIN building b
    ON bu.building_no = b.building_no
JOIN building_group bg
    ON b.building_group_no = bg.building_group_no
WHERE 1 = 1
"""

params = []

if selected_group_no is not None:
    query += " AND bg.building_group_no = %s"
    params.append(selected_group_no)

if selected_building_no is not None:
    query += " AND bu.building_no = %s"
    params.append(selected_building_no)

if selected_bedroom != "All":
    query += " AND bu.bedrooms_no = %s"
    params.append(selected_bedroom)

if selected_postal_code.strip() != "":
    query += " AND b.postal_code LIKE %s"
    params.append(f"%{selected_postal_code.strip()}%")

query += """
GROUP BY
    bg.name,
    b.name,
    b.postal_code,
    bu.rental_year
ORDER BY
    bu.rental_year,
    bg.name,
    b.name;
"""

yearly_rent_df = pd.read_sql(query, conn, params=params)

if yearly_rent_df.empty:
    st.warning("No records found for the selected filters.")
    conn.close()
    st.stop()

# -------------------------
# Chart
# -------------------------

st.subheader("Average Rent by Year")

if selected_building_name != "All":
    chart_title = f"Average Rent by Year for {selected_building_name}"
elif selected_group_name != "All":
    chart_title = f"Average Rent by Year for {selected_group_name}"
else:
    chart_title = "Average Rent by Year"

# If multiple buildings are visible, aggregate again at the year level
chart_df = (
    yearly_rent_df
    .groupby("rental_year", as_index=False)
    .agg(average_rent=("average_rent", "mean"))
)

chart_df["average_rent"] = chart_df["average_rent"].round(2)

fig = px.bar(
    chart_df,
    x="rental_year",
    y="average_rent",
    text="average_rent",
    title=chart_title
)

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Average Rent"
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "Average rent is calculated using the daily unit-level actual rent records "
    "for the selected building group, building, bedroom number, and postal code filters."
)

# -------------------------
# Table
# -------------------------

st.subheader("Yearly Average Rent Table")

display_df = yearly_rent_df.rename(
    columns={
        "building_group_name": "Building Group",
        "building_name": "Building",
        "postal_code": "Postal Code",
        "rental_year": "Year",
        "average_rent": "Average Rent"
    }
)

display_df = display_df[
    [
        "Building Group",
        "Building",
        "Postal Code",
        "Year",
        "Average Rent"
    ]
]

st.dataframe(display_df, width="stretch")

conn.close()