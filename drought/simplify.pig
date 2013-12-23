-- I crawled data from USGS hydrometers located in rivers and streams throughout 
-- the entire Southwest.  This script selects only those sites in the Colorado
-- River Basin, and gets a daily average flow from the data which is in 
-- 15 minute intervals


raw = LOAD 's3://jardel-blog/LCRA/usgs-flowrates--chunk*' USING PigStorage() AS (agency:chararray, stationID:int, date:chararray, time:chararray, timezone:chararray, flow:float, status:chararray);

stations = LOAD 's3://jardel-blog/LCRA/stations.list' USING PigStorage() AS (stationID:int);

-- select only stations in stations.list
selected = JOIN raw BY stationID, stations BY stationID PARALLEL 10;

-- group by site and date
grouped = GROUP selected BY (raw::stationID,raw::date) PARALLEL 10;

-- get average flow for each date
averaged = FOREACH grouped GENERATE group, AVG($1.raw::flow);

STORE averaged INTO 's3://jardel-blog/LCRA/usgs.dailyaverages';
