-- ============================================================
-- QUERY 3: Monthly Cohort Retention Analysis
-- Techniques: CTE chain, DENSE_RANK window, MIN OVER partition,
--             self-join, conditional aggregation
-- Business Q: What % of customers return in months 1, 2, 3... after first purchase?
-- ============================================================

WITH first_purchase AS (
    -- Assign each customer their acquisition cohort (month of first order)
    SELECT
        customer_id,
        MIN(strftime('%Y-%m', ordered_at)) AS cohort_month
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
customer_orders AS (
    -- For each order, calculate how many months after cohort it occurred
    SELECT
        o.customer_id,
        fp.cohort_month,
        -- Month index: 0 = acquisition month, 1 = one month later, etc.
        CAST(
            (strftime('%Y', o.ordered_at) - strftime('%Y', fp.cohort_month || '-01')) * 12
          + (strftime('%m', o.ordered_at) - strftime('%m', fp.cohort_month || '-01'))
        AS INTEGER) AS month_number
    FROM orders o
    JOIN first_purchase fp ON o.customer_id = fp.customer_id
    WHERE o.status = 'completed'
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers
    FROM first_purchase
    GROUP BY cohort_month
),
retention_raw AS (
    SELECT
        cohort_month,
        month_number,
        COUNT(DISTINCT customer_id) AS retained_customers
    FROM customer_orders
    WHERE month_number BETWEEN 0 AND 6
    GROUP BY 1, 2
)
SELECT
    r.cohort_month,
    cs.cohort_customers,
    r.month_number,
    r.retained_customers,
    ROUND(100.0 * r.retained_customers / cs.cohort_customers, 1) AS retention_rate_pct
FROM retention_raw r
JOIN cohort_size cs ON r.cohort_month = cs.cohort_month
ORDER BY r.cohort_month, r.month_number;

-- INSIGHT: Month-1 retention < 20% = acquisition quality problem.
--          If month-3 retention > month-1, indicates reactivation campaigns working.
--          Compare cohorts — improving retention in newer cohorts shows product improvement.
