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

SELECT 
    bg.name AS building_group,
    b.name AS building_name,
    bu.building_no,
    bu.floor,
    bu.unit_no,
    bu.bedrooms_no,
    bu.rental_year,
    bu.rental_month,
    bu.rental_day,
    bu.listed_price,
    bu.actual_rent,
    bu.rented
FROM building_unit_daily bu
JOIN building b 
    ON bu.building_no = b.building_no
JOIN building_group bg 
    ON b.building_group_no = bg.building_group_no
WHERE bu.rented = 'Y'
LIMIT 200;


