-- ============================================================
-- QUERY 4: Product Performance with Running Totals & Rankings
-- Techniques: JOIN, window RANK, SUM OVER (running), ROUND
-- Business Q: Which products drive the most revenue? Pareto analysis?
-- ============================================================

WITH product_revenue AS (
    SELECT
        p.product_id,
        p.name                                                    AS product_name,
        cat.name                                                  AS category,
        COUNT(DISTINCT o.order_id)                               AS orders_count,
        SUM(oi.quantity)                                         AS units_sold,
        ROUND(SUM(oi.unit_price * oi.quantity), 2)              AS total_revenue,
        ROUND(SUM((oi.unit_price - oi.unit_cost) * oi.quantity), 2) AS total_profit,
        ROUND(AVG(oi.unit_price), 2)                            AS avg_selling_price,
        ROUND(SUM((oi.unit_price - oi.unit_cost) * oi.quantity)
              / NULLIF(SUM(oi.unit_price * oi.quantity),0) * 100, 1) AS margin_pct
    FROM order_items oi
    JOIN orders  o   ON oi.order_id  = o.order_id
    JOIN products p  ON oi.product_id = p.product_id
    JOIN categories cat ON p.category_id = cat.category_id
    WHERE o.status = 'completed'
    GROUP BY 1,2,3
),
ranked AS (
    SELECT
        *,
        RANK() OVER (ORDER BY total_revenue DESC)               AS revenue_rank,
        SUM(total_revenue) OVER (ORDER BY total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)   AS running_total,
        SUM(total_revenue) OVER ()                              AS grand_total
    FROM product_revenue
)
SELECT
    revenue_rank,
    product_name,
    category,
    orders_count,
    units_sold,
    total_revenue,
    total_profit,
    margin_pct,
    ROUND(100.0 * running_total / grand_total, 1)              AS cumulative_revenue_pct
FROM ranked
ORDER BY revenue_rank;

-- INSIGHT: First products to reach 80% cumulative_revenue_pct = your Pareto 20%.
--          Low margin_pct on high-revenue products = pricing review needed.
--          High units_sold but low total_revenue = commoditised, check pricing strategy.


-- ============================================================
-- QUERY 5: Sales Channel Performance + Return Rate Analysis
-- Techniques: FILTER aggregation (CASE SUM), multi-metric CTE
-- Business Q: Which channels generate quality revenue (low returns)?
-- ============================================================

WITH channel_stats AS (
    SELECT
        o.channel,
        COUNT(DISTINCT o.order_id)                                    AS total_orders,
        COUNT(DISTINCT CASE WHEN o.status='completed'  THEN o.order_id END) AS completed,
        COUNT(DISTINCT CASE WHEN o.status='returned'   THEN o.order_id END) AS returned,
        COUNT(DISTINCT CASE WHEN o.status='cancelled'  THEN o.order_id END) AS cancelled,
        COUNT(DISTINCT o.customer_id)                                 AS unique_customers,
        ROUND(SUM(CASE WHEN o.status='completed'
                  THEN oi.unit_price * oi.quantity ELSE 0 END), 2)   AS net_revenue,
        ROUND(AVG(CASE WHEN o.status='completed'
                  THEN oi.unit_price * oi.quantity END), 2)           AS avg_order_value,
        ROUND(AVG(CASE WHEN o.status='completed'
                  THEN JULIANDAY(o.shipped_at) - JULIANDAY(o.ordered_at) END),1) AS avg_days_to_ship
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.channel
)
SELECT
    channel,
    total_orders,
    completed,
    returned,
    ROUND(100.0 * returned / NULLIF(total_orders,0), 1)              AS return_rate_pct,
    ROUND(100.0 * cancelled / NULLIF(total_orders,0), 1)             AS cancel_rate_pct,
    unique_customers,
    net_revenue,
    avg_order_value,
    avg_days_to_ship,
    RANK() OVER (ORDER BY net_revenue DESC)                          AS revenue_rank,
    RANK() OVER (ORDER BY avg_order_value DESC)                      AS aov_rank
FROM channel_stats
ORDER BY net_revenue DESC;

-- INSIGHT: High return rate on marketplace = product listing quality issue.
--          Mobile with low AOV but high order count = bundle opportunity.
--          avg_days_to_ship > 3 on web = fulfilment SLA problem.


-- ============================================================
-- QUERY 6: Marketing ROI — Revenue per Acquisition Channel
-- Techniques: CTE join between fact & spend tables, ratio metrics
-- Business Q: Which marketing channels give the best return on spend?
-- ============================================================

WITH channel_revenue AS (
    SELECT
        c.referral_src                                AS acq_channel,
        COUNT(DISTINCT c.customer_id)                AS customers_acquired,
        COUNT(DISTINCT o.order_id)                   AS total_orders,
        ROUND(SUM(oi.unit_price * oi.quantity), 2)   AS total_revenue
    FROM customers c
    JOIN orders     o  ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id   = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY c.referral_src
),
channel_spend AS (
    SELECT channel, ROUND(SUM(spend_zar), 2) AS total_spend
    FROM marketing_spend
    GROUP BY channel
),
combined AS (
    SELECT
        cr.acq_channel,
        cr.customers_acquired,
        cr.total_orders,
        cr.total_revenue,
        COALESCE(cs.total_spend, 0)                  AS marketing_spend,
        ROUND(cr.total_revenue
              / NULLIF(cs.total_spend,0), 2)          AS revenue_per_rand_spent,
        ROUND(cs.total_spend
              / NULLIF(cr.customers_acquired,0), 2)   AS cost_per_customer,
        ROUND(cr.total_revenue
              / NULLIF(cr.customers_acquired,0), 2)   AS revenue_per_customer
    FROM channel_revenue cr
    LEFT JOIN channel_spend cs ON cr.acq_channel = cs.channel
)
SELECT
    *,
    RANK() OVER (ORDER BY revenue_per_rand_spent DESC NULLS LAST) AS roi_rank
FROM combined
ORDER BY revenue_per_rand_spent DESC;

-- INSIGHT: revenue_per_rand_spent < 1.0 = channel is underwater (spending more than generating).
--          Organic / referral with 0 spend = high-value, invest in referral programs.
--          Email: low cost_per_customer = scale email list aggressively.


-- ============================================================
-- QUERY 7: Customer Lifetime Value (CLV) by Segment
-- Techniques: Window AVG, multi-level CTE, conditional aggregation
-- Business Q: What is the true value of each customer segment over time?
-- ============================================================

WITH customer_spend AS (
    SELECT
        o.customer_id,
        c.segment,
        c.city,
        c.referral_src,
        c.acquired_at,
        COUNT(DISTINCT o.order_id)                                   AS order_count,
        ROUND(SUM(oi.unit_price * oi.quantity), 2)                  AS total_spend,
        MIN(DATE(o.ordered_at))                                      AS first_order,
        MAX(DATE(o.ordered_at))                                      AS last_order,
        CAST(JULIANDAY(MAX(DATE(o.ordered_at)))
           - JULIANDAY(MIN(DATE(o.ordered_at))) AS INTEGER)         AS customer_lifespan_days
    FROM orders o
    JOIN order_items oi ON o.order_id    = oi.order_id
    JOIN customers c    ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY 1,2,3,4,5
),
segment_clv AS (
    SELECT
        segment,
        COUNT(DISTINCT customer_id)                                  AS customers,
        ROUND(AVG(total_spend), 2)                                  AS avg_clv,
        ROUND(AVG(order_count), 1)                                  AS avg_orders,
        ROUND(AVG(total_spend / NULLIF(order_count,0)), 2)         AS avg_order_value,
        ROUND(AVG(customer_lifespan_days), 0)                       AS avg_lifespan_days,
        ROUND(MAX(total_spend), 2)                                  AS max_clv,
        ROUND(MIN(total_spend), 2)                                  AS min_clv,
        -- Predicted annual CLV (simple: avg_order_value * purchase_frequency_per_year)
        ROUND(AVG(total_spend / NULLIF(order_count,0))
              * (AVG(order_count)
                 / NULLIF(AVG(customer_lifespan_days)/365.0, 0)), 2) AS predicted_annual_clv
    FROM customer_spend
    GROUP BY segment
)
SELECT
    *,
    ROUND(100.0 * avg_clv / SUM(avg_clv) OVER (), 1)              AS clv_index
FROM segment_clv
ORDER BY avg_clv DESC;

-- INSIGHT: VIP avg_clv / B2C avg_clv ratio > 5x = different product/service tier needed.
--          Low lifespan_days + high avg_order_value = one-time big buyers; push subscriptions.
--          predicted_annual_clv drives how much you should spend to acquire each segment.
