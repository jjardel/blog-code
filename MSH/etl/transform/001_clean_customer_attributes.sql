DROP TABLE IF EXISTS clean.customer_attributes;

CREATE TABLE clean.customer_attributes AS
WITH c1 AS(
    SELECT
        signup_date::DATE,
        status,
        cancel_date::DATE,
        x1,
        x2,
        x3,
        x4,
        x5,
        x6,
        x7,
        x8
    FROM raw.customer_attributes
)
SELECT
    uuid_generate_v4() AS customer_id,
    signup_date::DATE,
    status,
    cancel_date::DATE,
    COALESCE(cancel_date, '2016-01-16'::DATE) - signup_date AS days_since_signup,
    x1,
    x2,
    x3,
    x4,
    x5,
    x6,
    x7,
    x8

FROM c1;
