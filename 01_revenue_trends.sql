-- ============================================================
-- QUERY 1: Monthly Revenue Trend with MoM Growth
-- Techniques: CTE, LAG window function, ROUND, strftime
-- Business Q: How is revenue trending month-over-month?
-- ============================================================

WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.ordered_at)          AS month,
        COUNT(DISTINCT o.order_id)               AS total_orders,
        COUNT(DISTINCT o.customer_id)            AS unique_customers,
        ROUND(SUM(oi.unit_price * oi.quantity), 2) AS gross_revenue,
        ROUND(SUM(oi.unit_price * oi.quantity * (1 - o.discount_pct)), 2) AS net_revenue,
        ROUND(SUM((oi.unit_price - oi.unit_cost) * oi.quantity), 2) AS gross_profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY 1
),
with_growth AS (
    SELECT
        month,
        total_orders,
        unique_customers,
        gross_revenue,
        net_revenue,
        gross_profit,
        LAG(net_revenue) OVER (ORDER BY month)  AS prev_month_revenue,
        ROUND(
            100.0 * (net_revenue - LAG(net_revenue) OVER (ORDER BY month))
            / NULLIF(LAG(net_revenue) OVER (ORDER BY month), 0), 1
        )                                        AS mom_growth_pct,
        ROUND(gross_profit / NULLIF(net_revenue,0) * 100, 1) AS profit_margin_pct
    FROM monthly_revenue
)
SELECT
    month,
    total_orders,
    unique_customers,
    net_revenue,
    gross_profit,
    profit_margin_pct,
    COALESCE(CAST(mom_growth_pct AS TEXT) || '%', 'N/A') AS mom_growth
FROM with_growth
ORDER BY month;

-- INSIGHT: Look for seasonal acceleration (Nov/Dec) and post-holiday dips (Jan/Feb).
--          Declining profit_margin_pct with rising revenue signals discount abuse.
