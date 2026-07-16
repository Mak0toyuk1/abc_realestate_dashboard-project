import os
from pathlib import Path

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="Vacancy Intervals", layout="wide")
st.title("Vacancy / Rent Interval Dashboard")

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
    key="vacancy_building_group_filter"
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
    key="vacancy_building_filter"
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
    key="vacancy_bedroom_filter"
)

if selected_bedroom_label == "Studio/Bachelor":
    selected_bedroom = 0
elif selected_bedroom_label == "All":
    selected_bedroom = "All"
else:
    selected_bedroom = int(selected_bedroom_label)

selected_postal_code = st.sidebar.text_input(
    "Postal Code",
    key="vacancy_postal_code_filter"
)

selected_year = st.sidebar.selectbox(
    "Rental Year",
    years_df["rental_year"].tolist(),
    key="vacancy_year_filter"
)

# -------------------------
# Query daily vacancy data
# -------------------------

query = """
SELECT
    bu.building_no,
    b.name AS building_name,
    bg.name AS building_group_name,
    b.postal_code,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year,
    bu.rental_month,
    bu.rental_day,
    bu.rented,
    STR_TO_DATE(
        CONCAT(bu.rental_year, '-', bu.rental_month, '-', bu.rental_day),
        '%Y-%m-%d'
    ) AS rental_date
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
ORDER BY
    bu.building_no,
    bu.unit_no,
    rental_date;
"""

daily_df = pd.read_sql(query, conn, params=params)

if daily_df.empty:
    st.warning("No records found for the selected filters.")
    conn.close()
    st.stop()

daily_df["rental_date"] = pd.to_datetime(daily_df["rental_date"])

# -------------------------
# Chart: unrented days by month
# -------------------------

vacancy_by_month_df = (
    daily_df[daily_df["rented"] == "N"]
    .groupby("rental_month", as_index=False)
    .agg(unrented_days=("rented", "count"))
)

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

all_months_df = pd.DataFrame({"rental_month": list(range(1, 13))})

vacancy_by_month_df = all_months_df.merge(
    vacancy_by_month_df,
    on="rental_month",
    how="left"
)

vacancy_by_month_df["unrented_days"] = vacancy_by_month_df["unrented_days"].fillna(0)
vacancy_by_month_df["month_name"] = vacancy_by_month_df["rental_month"].map(month_names)

st.subheader("Unrented Days by Month")

fig = px.bar(
    vacancy_by_month_df,
    x="month_name",
    y="unrented_days",
    text="unrented_days",
    title=f"Unrented Days by Month in {selected_year}"
)

fig.update_layout(
    xaxis_title="Month",
    yaxis_title="Unrented Days"
)

st.plotly_chart(fig, width="stretch")

st.caption(
    "This chart counts the number of daily records where rented = 'N'. "
    "Higher values indicate more unrented days under the selected filters."
)

# -------------------------
# Table: continuous vacancy intervals
# -------------------------

st.subheader("Vacancy Intervals")

vacant_df = daily_df[daily_df["rented"] == "N"].copy()

if vacant_df.empty:
    st.info("There are no vacancy intervals for the selected filters.")
    conn.close()
    st.stop()

vacant_df = vacant_df.sort_values(
    ["building_no", "unit_no", "rental_date"]
)

vacant_df["previous_date"] = (
    vacant_df
    .groupby(["building_no", "unit_no"])["rental_date"]
    .shift()
)

vacant_df["new_interval"] = (
    vacant_df["previous_date"].isna()
    | ((vacant_df["rental_date"] - vacant_df["previous_date"]).dt.days > 1)
)

vacant_df["interval_id"] = (
    vacant_df
    .groupby(["building_no", "unit_no"])["new_interval"]
    .cumsum()
)

intervals_df = (
    vacant_df
    .groupby(
        [
            "building_no",
            "building_name",
            "building_group_name",
            "postal_code",
            "unit_no",
            "floor",
            "bedrooms_no",
            "interval_id"
        ],
        as_index=False
    )
    .agg(
        start_date=("rental_date", "min"),
        end_date=("rental_date", "max"),
        interval_days=("rental_date", "count")
    )
)

intervals_df = intervals_df.sort_values(
    ["start_date", "building_name", "unit_no"]
).reset_index(drop=True)

intervals_df["Rent Interval"] = intervals_df.index + 1

display_df = intervals_df.rename(
    columns={
        "building_group_name": "Building Group",
        "building_name": "Building",
        "postal_code": "Postal Code",
        "unit_no": "Unit No",
        "floor": "Floor",
        "bedrooms_no": "Bedrooms No",
        "start_date": "Start Date",
        "end_date": "End Date",
        "interval_days": "Interval Days"
    }
)

display_df["Start Date"] = display_df["Start Date"].dt.date
display_df["End Date"] = display_df["End Date"].dt.date

display_df = display_df[
    [
        "Rent Interval",
        "Building Group",
        "Building",
        "Postal Code",
        "Unit No",
        "Floor",
        "Bedrooms No",
        "Start Date",
        "End Date",
        "Interval Days"
    ]
]

st.dataframe(display_df, width="stretch")

conn.close()