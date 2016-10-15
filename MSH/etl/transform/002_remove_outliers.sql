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


DROP TABLE IF EXISTS clean.customer_attributes_clipped;

CREATE TABLE clean.customer_attributes_clipped AS
WITH stats_data AS(
    SELECT
        *,
        MEDIAN(x6::NUMERIC) OVER () AS x6_median,
        STDDEV(x6) OVER () AS x6_std,
        MEDIAN(x7::NUMERIC) OVER () AS x7_median,
        STDDEV(x7) OVER () AS x7_std,
        MEDIAN(x8::NUMERIC) OVER () AS x8_median,
        STDDEV(x8) OVER () AS x8_std,
        MEDIAN(days_since_signup::NUMERIC) OVER () AS days_median,
        STDDEV(days_since_signup) OVER () AS days_std

    FROM clean.customer_attributes

)
SELECT
    customer_id,
    signup_date,
    status,
    cancel_date,
    days_since_signup,
    x1,
    x2,
    x3,
    x4,
    x5,
    x6,
    x7,
    x8
FROM stats_data
WHERE days_since_signup > 0
      AND COALESCE(days_since_signup, 0) < days_median + days_std * 5
      AND COALESCE(x6, 0) < x6_median + x6_std * 5
      AND COALESCE(x7, 0) < x7_median + x7_std * 5
      AND COALESCE(x8, 0) < x8_median + x8_std * 5
;
