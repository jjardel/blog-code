-- third-party implementation of MEDIAN in PGSQL
-- https://wiki.postgresql.org/wiki/Aggregate_Median

CREATE OR REPLACE FUNCTION _final_median(NUMERIC[])
   RETURNS NUMERIC AS
$$
   SELECT AVG(val)
   FROM (
     SELECT val
     FROM unnest($1) val
     ORDER BY 1
     LIMIT  2 - MOD(array_upper($1, 1), 2)
     OFFSET CEIL(array_upper($1, 1) / 2.0) - 1
   ) sub;
$$
LANGUAGE 'sql' IMMUTABLE;

CREATE AGGREGATE median(NUMERIC) (
  SFUNC=array_append,
  STYPE=NUMERIC[],
  FINALFUNC=_final_median,
  INITCOND='{}'
);


-- build this out if necessary

WITH stats_data AS(
    SELECT
        *,
        MEDIAN(x6::NUMERIC) OVER () AS x6_median,
        STDDEV(x6) OVER () AS x6_std,
        MEDIAN(x7::NUMERIC) OVER () AS x7_median,
        STDDEV(x7) OVER () AS x7_std,
        MEDIAN(x8::NUMERIC) OVER () AS x8_median,
        STDDEV(x8) OVER () AS x8_median

    FROM clean.customer_attributes

)
SELECT * FROM stats_data;


SELECT * FROM clean.customer_attributes
ORDER BY x6 DESC NULLS LAST