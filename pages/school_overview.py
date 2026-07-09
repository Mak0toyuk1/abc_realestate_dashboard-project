import os
from pathlib import Path

import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
from dotenv import load_dotenv


# -------------------------
# Page setup and database connection
# -------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

st.set_page_config(page_title="School Overview", layout="wide")

st.title("School Overview")

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


# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters")

building_group_options = ["All"] + building_groups_df["name"].tolist()

selected_group_name = st.sidebar.selectbox(
    "Building Group",
    building_group_options,
    key="school_building_group_filter"
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


# -------------------------
# Query school data
# -------------------------

school_query = """
SELECT
    school_no,
    school_type,
    name,
    country,
    city_region,
    street_line_1,
    street_line_2,
    score,
    ranking_across_ontario,
    building_group_no
FROM school
WHERE 1 = 1
"""

school_params = []

if selected_group_no is not None:
    school_query += " AND building_group_no = %s"
    school_params.append(selected_group_no)

school_query += """
ORDER BY school_type, ranking_across_ontario;
"""

school_df = pd.read_sql(
    school_query,
    conn,
    params=school_params
)


# -------------------------
# Display school overview
# -------------------------

if school_df.empty:
    st.warning("No school data found for the selected building group.")
else:
    total_schools = len(school_df)
    avg_score = school_df["score"].mean()
    best_rank = school_df["ranking_across_ontario"].min()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Schools", total_schools)

    with col2:
        st.metric("Average Score", round(avg_score, 2))

    with col3:
        st.metric("Best Ranking", int(best_rank))

    st.divider()


    # -------------------------
    # Aggregate chart data
    # -------------------------

    school_chart_df = (
        school_df
        .groupby("school_type", as_index=False)
        .agg(
            school_count=("school_no", "count"),
            average_score=("score", "mean"),
            best_ranking=("ranking_across_ontario", "min")
        )
    )

    school_chart_df["average_score"] = school_chart_df["average_score"].round(2)


    # -------------------------
    # Charts
    # -------------------------

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig_score = px.bar(
            school_chart_df,
            x="school_type",
            y="average_score",
            text="average_score",
            title="Average Score by School Type"
        )

        fig_score.update_layout(
            xaxis_title="School Type",
            yaxis_title="Average Score"
        )

        st.plotly_chart(fig_score, width="stretch")

    with chart_col2:
        fig_rank = px.bar(
            school_chart_df,
            x="school_type",
            y="best_ranking",
            text="best_ranking",
            title="Best Ranking by School Type"
        )

        fig_rank.update_layout(
            xaxis_title="School Type",
            yaxis_title="Ranking Across Ontario"
        )

        st.plotly_chart(fig_rank, width="stretch")

    st.caption("Note: for rankings, a lower number represents a better ranking.")

    st.divider()


    # -------------------------
    # School count chart
    # -------------------------

    # fig_count = px.bar(
    #     school_chart_df,
    #     x="school_type",
    #     y="school_count",
    #     text="school_count",
    #     title="Number of Schools by School Type"
    # )

    # fig_count.update_layout(
    #     xaxis_title="School Type",
    #     yaxis_title="Number of Schools"
    # )

    # st.plotly_chart(fig_count, width="stretch")


    # -------------------------
    # School detail table
    # -------------------------

    school_display_df = school_df.rename(
        columns={
            "school_no": "School No",
            "school_type": "School Type",
            "name": "Name",
            "country": "Country",
            "city_region": "City Region",
            "street_line_1": "Street Line 1",
            "street_line_2": "Street Line 2",
            "score": "Score",
            "ranking_across_ontario": "Ranking Across Ontario",
            "building_group_no": "Building Group No"
        }
    )

    school_display_df["Address"] = (
        school_display_df["Street Line 1"].fillna("")
        + " "
        + school_display_df["Street Line 2"].fillna("")
    ).str.strip()

    school_display_df = school_display_df[
        [
            "School No",
            "School Type",
            "Name",
            "City Region",
            "Address",
            "Score",
            "Ranking Across Ontario",
            "Building Group No"
        ]
    ]

    st.subheader("School Details")
    st.dataframe(school_display_df, width="stretch")


conn.close()