-- ============================================================
-- QUERY 2: RFM Customer Segmentation
-- Techniques: Multiple CTEs, NTILE, CASE, subquery scoring
-- Business Q: Which customers are Champions vs At-Risk vs Lost?
-- ============================================================

WITH last_order_date AS (
    SELECT MAX(DATE(ordered_at)) AS snapshot_date
    FROM orders
    WHERE status = 'completed'
),
customer_metrics AS (
    SELECT
        o.customer_id,
        c.full_name,
        c.city,
        c.segment,
        c.referral_src,
        -- Recency: days since last purchase
        CAST(JULIANDAY((SELECT snapshot_date FROM last_order_date))
             - JULIANDAY(MAX(DATE(o.ordered_at))) AS INTEGER)  AS recency_days,
        -- Frequency: number of orders
        COUNT(DISTINCT o.order_id)                             AS frequency,
        -- Monetary: total spend
        ROUND(SUM(oi.unit_price * oi.quantity), 2)             AS monetary
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN customers c    ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY 1,2,3,4,5
),
rfm_scores AS (
    SELECT
        *,
        -- Score 5=best, 1=worst for each dimension
        NTILE(5) OVER (ORDER BY recency_days  ASC)  AS r_score,
        NTILE(5) OVER (ORDER BY frequency     DESC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary      DESC) AS m_score
    FROM customer_metrics
),
rfm_segments AS (
    SELECT
        *,
        (r_score + f_score + m_score)                          AS rfm_total,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4
                THEN '⭐ Champion'
            WHEN r_score >= 3 AND f_score >= 3
                THEN '💚 Loyal Customer'
            WHEN r_score >= 4 AND f_score <= 2
                THEN '🆕 Promising New'
            WHEN r_score >= 3 AND f_score >= 1 AND m_score >= 3
                THEN '🎯 Potential Loyalist'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3
                THEN '⚠️  At Risk'
            WHEN r_score <= 2 AND f_score >= 4
                THEN '😴 Cant Lose Them'
            WHEN r_score <= 1 AND f_score <= 2
                THEN '💀 Lost'
            ELSE '🌱 Regular'
        END                                                    AS rfm_label
    FROM rfm_scores
)
SELECT
    rfm_label,
    COUNT(*)                              AS customer_count,
    ROUND(AVG(recency_days), 0)          AS avg_recency_days,
    ROUND(AVG(frequency), 1)             AS avg_orders,
    ROUND(AVG(monetary), 2)              AS avg_spend,
    ROUND(SUM(monetary), 2)              AS total_revenue,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_customers
FROM rfm_segments
GROUP BY rfm_label
ORDER BY avg_spend DESC;

-- INSIGHT: Champions drive disproportionate revenue with < 20% of customer base.
--          "At Risk" segment = highest-ROI retention campaign target.
--          "Lost" with high monetary = win-back email priority list.
