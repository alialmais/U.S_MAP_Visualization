CREATE DATABASE US_MAP_VISUALIZATION;
USE US_MAP_VISUALIZATION;

CREATE TABLE US_Accidents (
    ID VARCHAR(50) PRIMARY KEY,
    Severity INT,                
    Start_Lat FLOAT,
    Start_Lng FLOAT,
    Street VARCHAR(255),
    City VARCHAR(255),
    State VARCHAR(10),
    Year INT  
);

SET GLOBAL max_allowed_packet = 1073741824;
SET GLOBAL net_read_timeout = 600;
SET GLOBAL net_write_timeout = 600;
SET GLOBAL wait_timeout = 600;
SET GLOBAL interactive_timeout = 600;

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/cleaned_US_Accidents_2023.csv'
INTO TABLE US_Accidents
FIELDS TERMINATED BY ','  
ENCLOSED BY '"'  
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;