import pandas as pd
import mysql.connector
from mysql.connector import Error

# pd.set_option("display.max_columns", None)
# pd.set_option("display.width", None)

def main():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="abc_user",
            password="abc_password",
            database="abc_real_estate"
        )

        if conn.is_connected():
            print("Connected to MySQL successfully.")

            building_group_df = pd.read_sql(
                "SELECT * FROM building_group;",
                conn
            )

            building_df = pd.read_sql(
                "SELECT * FROM building;",
                conn
            )

            building_unit_daily_df = pd.read_sql(
                "SELECT * FROM building_unit_daily;",
                conn
            )

            school_df = pd.read_sql(
                "SELECT * FROM school;",
                conn
            )

            print("\nDataFrames loaded successfully.\n")

            print("building_group_df:")
            print(building_group_df.head())
            print(building_group_df.shape)

            print("\nbuilding_df:")
            print(building_df.head())
            print(building_df.shape)

            print("\nbuilding_unit_daily_df:")
            print(building_unit_daily_df.head())
            print(building_unit_daily_df.shape)

            print("\nschool_df:")
            print(school_df.head())
            print(school_df.shape)

            print("building_group_df columns:")
            print(building_group_df.columns.tolist())

            print("building_df columns:")
            print(building_df.columns.tolist())

            print("building_unit_daily_df columns:")
            print(building_unit_daily_df.columns.tolist())

            print("school_df columns:")
            print(school_df.columns.tolist())

            conn.close()
            print("\nConnection closed.")

    except Error as e:
        print("Error while connecting to MySQL:")
        print(e)


if __name__ == "__main__":
    main()