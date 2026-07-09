import os
from pathlib import Path

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="ABC Real Estate Dashboard", layout="wide")

st.title("ABC Real Estate Rental Dashboard")


conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)


# -------------------------
# Load dropdown values
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

bedrooms_df = pd.read_sql(
    """
    SELECT DISTINCT bedrooms_no
    FROM building_unit_daily
    ORDER BY bedrooms_no;
    """,
    conn
)

years_df = pd.read_sql(
    """
    SELECT DISTINCT rental_year
    FROM building_unit_daily
    ORDER BY rental_year;
    """,
    conn
)


# -------------------------
# Dashboard filters
# -------------------------

st.sidebar.header("Filters")

building_group_options = ["All"] + building_groups_df["name"].tolist()

selected_group_name = st.sidebar.selectbox(
    "Building Group",
    building_group_options
)

if selected_group_name != "All":
    selected_group_no = int(
        building_groups_df.loc[
            building_groups_df["name"] == selected_group_name,
            "building_group_no"
        ].iloc[0]
    )

    filtered_buildings_df = buildings_df[
        buildings_df["building_group_no"] == selected_group_no
    ]
else:
    selected_group_no = None
    filtered_buildings_df = buildings_df


building_options = ["All"] + filtered_buildings_df["name"].tolist()

selected_building_name = st.sidebar.selectbox(
    "Building Name",
    building_options
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
    key="bedroom_filter"
)

if selected_bedroom_label == "Studio/Bachelor":
    selected_bedroom = 0
elif selected_bedroom_label == "All":
    selected_bedroom = "All"
else:
    selected_bedroom = int(selected_bedroom_label)



selected_postal_code = st.sidebar.text_input(
    "Postal Code"
)

selected_year = st.sidebar.selectbox(
    "Rental Year",
    years_df["rental_year"].tolist()
)

month_options = {
    "All": None,
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}

selected_month_label = st.sidebar.selectbox(
    "Rental Month",
    list(month_options.keys()),
    key="rental_month_filter"
)

selected_month = month_options[selected_month_label]

# -------------------------
# Build line chart query dynamically
# -------------------------

query = """
SELECT 
    bu.rental_month,
    ROUND(AVG(bu.actual_rent), 2) AS average_rent
FROM building_unit_daily bu
JOIN building b
    ON bu.building_no = b.building_no
JOIN building_group bg
    ON b.building_group_no = bg.building_group_no
WHERE bu.rental_year = %s
"""

params = [selected_year]

if selected_group_no is not None:
    query += " AND bg.building_group_no = %s"
    params.append(selected_group_no)

if selected_building_no is not None:
    query += " AND b.building_no = %s"
    params.append(selected_building_no)

if selected_bedroom != "All":
    query += " AND bu.bedrooms_no = %s"
    params.append(selected_bedroom)

if selected_postal_code.strip() != "":
    query += " AND b.postal_code LIKE %s"
    params.append(f"%{selected_postal_code.strip()}%")


query += """
GROUP BY bu.rental_month
ORDER BY bu.rental_month;
"""


monthly_rent_df = pd.read_sql(
    query,
    conn,
    params=params
)


# -------------------------
# Display line chart
# -------------------------

st.subheader("Average Rent by Month")

if monthly_rent_df.empty:
    st.warning("No data found for the selected filters.")
else:
    month_names = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sept",
        10: "Oct",
        11: "Nov",
        12: "Dec"
    }

    monthly_rent_df["month_name"] = monthly_rent_df["rental_month"].map(month_names)

    fig = px.line(
        monthly_rent_df,
        x="month_name",
        y="average_rent",
        markers=True,
        title=f"Average Monthly Rent for {selected_year}"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Rent Fee",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(monthly_rent_df, use_container_width=True)
# -------------------------
# Display filtered detail table with postal code
# -------------------------

detail_query = """
SELECT 
    bg.name AS building_group,
    b.name AS building_name,
    b.postal_code,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year,
    bu.rental_month,
    ROUND(AVG(bu.actual_rent), 2) AS average_rent
FROM building_unit_daily bu
JOIN building b
    ON bu.building_no = b.building_no
JOIN building_group bg
    ON b.building_group_no = bg.building_group_no
WHERE bu.rental_year = %s
"""

detail_params = [selected_year]

if selected_group_no is not None:
    detail_query += " AND bg.building_group_no = %s"
    detail_params.append(selected_group_no)

if selected_building_no is not None:
    detail_query += " AND b.building_no = %s"
    detail_params.append(selected_building_no)

if selected_bedroom != "All":
    detail_query += " AND bu.bedrooms_no = %s"
    detail_params.append(selected_bedroom)

if selected_postal_code.strip() != "":
    detail_query += " AND b.postal_code LIKE %s"
    detail_params.append(f"%{selected_postal_code.strip()}%")
if selected_month is not None:
    detail_query += " AND bu.rental_month = %s"
    detail_params.append(selected_month)

detail_query += """
GROUP BY 
    bg.name,
    b.name,
    b.postal_code,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year,
    bu.rental_month
ORDER BY 
    b.name,
    bu.floor,
    bu.unit_no,
    bu.rental_month
LIMIT 100;
"""

detail_df = pd.read_sql(
    detail_query,
    conn,
    params=detail_params
)

st.subheader("Filtered Unit-Level Monthly Rent Preview")
st.dataframe(detail_df, use_container_width=True)

conn.close()