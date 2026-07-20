import os
from pathlib import Path

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="Vacancy Ranking", layout="wide")
st.title("Vacancy Ranking Dashboard")

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

years_df = pd.read_sql(
    """
    SELECT DISTINCT rental_year
    FROM building_unit_daily
    ORDER BY rental_year;
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
    key="vacancy_ranking_group_filter"
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
    key="vacancy_ranking_building_filter"
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
    key="vacancy_ranking_bedroom_filter"
)

if selected_bedroom_label == "Studio/Bachelor":
    selected_bedroom = 0
elif selected_bedroom_label == "All":
    selected_bedroom = "All"
else:
    selected_bedroom = int(selected_bedroom_label)

selected_postal_code = st.sidebar.text_input(
    "Postal Code",
    key="vacancy_ranking_postal_code_filter"
)

selected_year = st.sidebar.selectbox(
    "Rental Year",
    years_df["rental_year"].tolist(),
    key="vacancy_ranking_year_filter"
)

top_n = st.sidebar.slider(
    "Number of Units to Display",
    min_value=5,
    max_value=30,
    value=15,
    step=5,
    key="vacancy_ranking_top_n_filter"
)

# -------------------------
# Query vacancy rate by unit
# -------------------------

query = """
SELECT
    bg.name AS building_group_name,
    b.name AS building_name,
    b.postal_code,
    bu.building_no,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year,
    COUNT(*) AS total_days,
    SUM(CASE WHEN bu.rented = 'N' THEN 1 ELSE 0 END) AS vacant_days,
    ROUND(
        SUM(CASE WHEN bu.rented = 'N' THEN 1 ELSE 0 END) / COUNT(*) * 100,
        2
    ) AS vacancy_rate
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
    bu.building_no,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year
ORDER BY vacancy_rate DESC, vacant_days DESC
LIMIT %s;
"""

params.append(top_n)

vacancy_rank_df = pd.read_sql(query, conn, params=params)

if vacancy_rank_df.empty:
    st.warning("No records found for the selected filters.")
    conn.close()
    st.stop()

# -------------------------
# Chart
# -------------------------

vacancy_rank_df["unit_label"] = (
    vacancy_rank_df["building_name"]
    + " - Unit "
    + vacancy_rank_df["unit_no"].astype(str)
)

st.subheader(f"Top {top_n} Units by Vacancy Rate")

fig = px.bar(
    vacancy_rank_df,
    x="unit_label",
    y="vacancy_rate",
    text="vacancy_rate",
    hover_data={
        "building_group_name": True,
        "building_name": True,
        "postal_code": True,
        "floor": True,
        "unit_no": True,
        "bedrooms_no": True,
        "total_days": True,
        "vacant_days": True,
        "vacancy_rate": True,
        "unit_label": False
    },
    title=f"Top {top_n} Units with Highest Vacancy Rate in {selected_year}"
)

fig.update_layout(
    xaxis_title="Unit",
    yaxis_title="Vacancy Rate (%)"
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "Vacancy Rate is calculated as vacant days divided by total daily records for the selected year. "
    "A unit vacant for the entire year would have a vacancy rate of 100%."
)

# -------------------------
# Ranking table
# -------------------------

st.subheader("Vacancy Ranking Table")

display_df = vacancy_rank_df.copy()
display_df.insert(0, "Rank", range(1, len(display_df) + 1))

display_df = display_df.rename(
    columns={
        "building_group_name": "Building Group",
        "building_name": "Building",
        "postal_code": "Postal Code",
        "floor": "Floor",
        "unit_no": "Unit",
        "bedrooms_no": "Number of Bedrooms",
        "total_days": "Total Days",
        "vacant_days": "Vacant Days",
        "vacancy_rate": "Vacancy Rate (%)"
    }
)

display_df = display_df[
    [
        "Rank",
        "Building Group",
        "Building",
        "Postal Code",
        "Number of Bedrooms",
        "Floor",
        "Unit",
        "Total Days",
        "Vacant Days",
        "Vacancy Rate (%)"
    ]
]

st.dataframe(display_df, width="stretch")

conn.close()