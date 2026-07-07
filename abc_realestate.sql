DROP DATABASE IF EXISTS abc_real_estate;
CREATE DATABASE abc_real_estate;
USE abc_real_estate;

DROP TABLE IF EXISTS building_unit_daily;

CREATE TABLE building_unit_daily (
    building_no INT,
    floor INT,
    unit_no VARCHAR(20),
    bedrooms_no INT,
    listed_price DECIMAL(10,2),
    actual_rent DECIMAL(10,2),
    rental_year INT,
    rental_month INT,
    rental_day INT,
    rented CHAR(1),
    FOREIGN KEY (building_no) REFERENCES building(building_no)
);

CREATE TABLE building_group (
    building_group_no INT PRIMARY KEY,
    name VARCHAR(100),
    country VARCHAR(50),
    city_region VARCHAR(100),
    postal_code VARCHAR(20)
);


CREATE TABLE building (
    building_no INT PRIMARY KEY,
    building_group_no INT,
    name VARCHAR(100),
    country VARCHAR(50),
    city_region VARCHAR(100),
    street_line_1 VARCHAR(150),
    unit_no VARCHAR(20),
    postal_code VARCHAR(20),
    FOREIGN KEY (building_group_no) REFERENCES building_group(building_group_no)
);
ALTER TABLE building
DROP COLUMN unit_no;

CREATE TABLE school (
    school_no INT PRIMARY KEY,
    school_type VARCHAR(50),
    name VARCHAR(150),
    country VARCHAR(50),
    city_region VARCHAR(100),
    street_line_1 VARCHAR(150),
    street_line_2 VARCHAR(150),
    score DECIMAL(3,1),
    ranking_across_ontario INT,
    building_group_no INT,
    FOREIGN KEY (building_group_no) REFERENCES building_group(building_group_no)
);



DESCRIBE building_group;
DESCRIBE building;
DESCRIBE school;
DESCRIBE building_unit_daily;

SELECT *
FROM building_unit_daily
LIMIT 50;

SELECT *
FROM building_unit_daily
WHERE rented = 'N'

LIMIT 200;


SELECT building_no, building_group_no, name, postal_code
FROM building
ORDER BY name;
USE abc_real_estate;

DROP TABLE IF EXISTS building_unit_monthly_aggr;

CREATE TABLE building_unit_monthly_aggr AS
SELECT
    building_no,
    floor,
    unit_no,
    bedrooms_no,
    rental_year,
    rental_month,
    ROUND(AVG(listed_price), 2) AS avg_listed_price,
    ROUND(AVG(actual_rent), 2) AS avg_actual_rent,
    COUNT(*) AS daily_record_count,
    SUM(CASE WHEN rented = 'Y' THEN 1 ELSE 0 END) AS rented_days,
    SUM(CASE WHEN rented = 'N' THEN 1 ELSE 0 END) AS unrented_days
FROM building_unit_daily
GROUP BY
    building_no,
    floor,
    unit_no,
    bedrooms_no,
    rental_year,
    rental_month
ORDER BY
    building_no,
    unit_no,
    rental_year,
    rental_month;
    
SELECT
    rental_year,
    rental_month,
    COUNT(*) AS monthly_unit_rows
FROM building_unit_monthly_aggr
GROUP BY rental_year, rental_month
ORDER BY rental_year, rental_month;

SELECT *
FROM building_unit_monthly_aggr
LIMIT 50;

