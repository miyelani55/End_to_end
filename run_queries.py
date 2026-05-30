"""Run all SQL analytics queries, export results to CSV and JSON for the dashboard."""
import sqlite3, pandas as pd, json, os

DB = "/home/claude/sql_analytics/ecommerce.db"
OUT = "/home/claude/sql_analytics/outputs"
os.makedirs(OUT, exist_ok=True)

conn = sqlite3.connect(DB)

# ── Q1: Revenue Trend ────────────────────────────────────────────────────────
q1 = """
WITH monthly_revenue AS (
    SELECT
        strftime('%Y-%m', o.ordered_at)           AS month,
        COUNT(DISTINCT o.order_id)                AS total_orders,
        COUNT(DISTINCT o.customer_id)             AS unique_customers,
        ROUND(SUM(oi.unit_price * oi.quantity * (1 - o.discount_pct)), 2) AS net_revenue,
        ROUND(SUM((oi.unit_price - oi.unit_cost) * oi.quantity), 2)       AS gross_profit
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY 1
)
SELECT *, ROUND(gross_profit/NULLIF(net_revenue,0)*100,1) AS margin_pct
FROM monthly_revenue ORDER BY month
"""
df1 = pd.read_sql(q1, conn)
df1.to_csv(f"{OUT}/revenue_trend.csv", index=False)
print(f"Q1 Revenue Trend: {len(df1)} months | Total Rev: R{df1['net_revenue'].sum():,.0f}")

# ── Q2: RFM Segmentation ─────────────────────────────────────────────────────
q2 = """
WITH last_order_date AS (SELECT MAX(DATE(ordered_at)) AS snap FROM orders WHERE status='completed'),
customer_metrics AS (
    SELECT o.customer_id, c.full_name, c.city, c.segment,
        CAST(JULIANDAY((SELECT snap FROM last_order_date)) - JULIANDAY(MAX(DATE(o.ordered_at))) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.unit_price * oi.quantity), 2) AS monetary
    FROM orders o JOIN order_items oi ON o.order_id=oi.order_id JOIN customers c ON o.customer_id=c.customer_id
    WHERE o.status='completed' GROUP BY 1,2,3,4
),
rfm_scores AS (
    SELECT *, NTILE(5) OVER (ORDER BY recency_days ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency DESC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary DESC) AS m_score
    FROM customer_metrics
),
rfm_segments AS (
    SELECT *, (r_score+f_score+m_score) AS rfm_total,
        CASE WHEN r_score>=4 AND f_score>=4 AND m_score>=4 THEN 'Champion'
             WHEN r_score>=3 AND f_score>=3 THEN 'Loyal Customer'
             WHEN r_score>=4 AND f_score<=2 THEN 'Promising New'
             WHEN r_score>=3 AND m_score>=3 THEN 'Potential Loyalist'
             WHEN r_score<=2 AND f_score>=3 AND m_score>=3 THEN 'At Risk'
             WHEN r_score<=2 AND f_score>=4 THEN 'Cant Lose Them'
             WHEN r_score<=1 AND f_score<=2 THEN 'Lost'
             ELSE 'Regular' END AS rfm_label
    FROM rfm_scores
)
SELECT rfm_label, COUNT(*) AS customers, ROUND(AVG(recency_days),0) AS avg_recency,
    ROUND(AVG(frequency),1) AS avg_orders, ROUND(AVG(monetary),2) AS avg_spend,
    ROUND(SUM(monetary),2) AS total_revenue
FROM rfm_segments GROUP BY rfm_label ORDER BY avg_spend DESC
"""
df2 = pd.read_sql(q2, conn)
df2.to_csv(f"{OUT}/rfm_segments.csv", index=False)
print(f"Q2 RFM: {len(df2)} segments | {df2['customers'].sum()} customers")

# ── Q3: Cohort Retention ─────────────────────────────────────────────────────
q3 = """
WITH first_purchase AS (
    SELECT customer_id, MIN(strftime('%Y-%m', ordered_at)) AS cohort_month
    FROM orders WHERE status='completed' GROUP BY customer_id
),
customer_orders AS (
    SELECT o.customer_id, fp.cohort_month,
        CAST(
            (CAST(strftime('%Y',o.ordered_at) AS INT) - CAST(strftime('%Y',fp.cohort_month||'-01') AS INT))*12
          + (CAST(strftime('%m',o.ordered_at) AS INT) - CAST(strftime('%m',fp.cohort_month||'-01') AS INT))
        AS INTEGER) AS month_number
    FROM orders o JOIN first_purchase fp ON o.customer_id=fp.customer_id WHERE o.status='completed'
),
cohort_size AS (SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_customers FROM first_purchase GROUP BY 1),
retention_raw AS (
    SELECT cohort_month, month_number, COUNT(DISTINCT customer_id) AS retained
    FROM customer_orders WHERE month_number BETWEEN 0 AND 5 GROUP BY 1,2
)
SELECT r.cohort_month, cs.cohort_customers, r.month_number, r.retained,
    ROUND(100.0*r.retained/cs.cohort_customers,1) AS retention_pct
FROM retention_raw r JOIN cohort_size cs ON r.cohort_month=cs.cohort_month
ORDER BY r.cohort_month, r.month_number
"""
df3 = pd.read_sql(q3, conn)
df3.to_csv(f"{OUT}/cohort_retention.csv", index=False)
print(f"Q3 Cohort: {df3['cohort_month'].nunique()} cohorts")

# ── Q4: Product Performance ──────────────────────────────────────────────────
q4 = """
WITH pr AS (
    SELECT p.name AS product, cat.name AS category,
        COUNT(DISTINCT o.order_id) AS orders,
        SUM(oi.quantity) AS units,
        ROUND(SUM(oi.unit_price*oi.quantity),2) AS revenue,
        ROUND(SUM((oi.unit_price-oi.unit_cost)*oi.quantity),2) AS profit,
        ROUND(SUM((oi.unit_price-oi.unit_cost)*oi.quantity)/NULLIF(SUM(oi.unit_price*oi.quantity),0)*100,1) AS margin_pct
    FROM order_items oi JOIN orders o ON oi.order_id=o.order_id
    JOIN products p ON oi.product_id=p.product_id JOIN categories cat ON p.category_id=cat.category_id
    WHERE o.status='completed' GROUP BY 1,2
)
SELECT *, RANK() OVER (ORDER BY revenue DESC) AS rank FROM pr ORDER BY revenue DESC
"""
df4 = pd.read_sql(q4, conn)
df4.to_csv(f"{OUT}/product_performance.csv", index=False)
print(f"Q4 Products: {len(df4)} products | Top: {df4.iloc[0]['product']} R{df4.iloc[0]['revenue']:,.0f}")

# ── Q5: Channel Analysis ─────────────────────────────────────────────────────
q5 = """
SELECT o.channel,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status='completed' THEN o.order_id END) AS completed,
    COUNT(DISTINCT CASE WHEN o.status='returned'  THEN o.order_id END) AS returned,
    ROUND(100.0*COUNT(DISTINCT CASE WHEN o.status='returned' THEN o.order_id END)/COUNT(DISTINCT o.order_id),1) AS return_rate_pct,
    ROUND(SUM(CASE WHEN o.status='completed' THEN oi.unit_price*oi.quantity ELSE 0 END),2) AS net_revenue,
    ROUND(AVG(CASE WHEN o.status='completed' THEN oi.unit_price*oi.quantity END),2) AS avg_order_value
FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
GROUP BY o.channel ORDER BY net_revenue DESC
"""
df5 = pd.read_sql(q5, conn)
df5.to_csv(f"{OUT}/channel_performance.csv", index=False)
print(f"Q5 Channels: {len(df5)} channels")

# ── Q6: Marketing ROI ─────────────────────────────────────────────────────────
q6 = """
WITH cr AS (
    SELECT c.referral_src AS channel, COUNT(DISTINCT c.customer_id) AS customers,
        ROUND(SUM(oi.unit_price*oi.quantity),2) AS revenue
    FROM customers c JOIN orders o ON c.customer_id=o.customer_id
    JOIN order_items oi ON o.order_id=oi.order_id WHERE o.status='completed' GROUP BY 1
),
cs AS (SELECT channel, ROUND(SUM(spend_zar),2) AS spend FROM marketing_spend GROUP BY 1)
SELECT cr.channel, cr.customers, cr.revenue, COALESCE(cs.spend,0) AS spend,
    ROUND(cr.revenue/NULLIF(cs.spend,0),2) AS roas,
    ROUND(cs.spend/NULLIF(cr.customers,0),2) AS cac
FROM cr LEFT JOIN cs ON cr.channel=cs.channel ORDER BY roas DESC NULLS LAST
"""
df6 = pd.read_sql(q6, conn)
df6.to_csv(f"{OUT}/marketing_roi.csv", index=False)
print(f"Q6 Marketing ROI: {len(df6)} channels")

# ── Q7: Customer Segment CLV ──────────────────────────────────────────────────
q7 = """
WITH cs AS (
    SELECT o.customer_id, c.segment, COUNT(DISTINCT o.order_id) AS orders,
        ROUND(SUM(oi.unit_price*oi.quantity),2) AS spend
    FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
    JOIN customers c ON o.customer_id=c.customer_id WHERE o.status='completed' GROUP BY 1,2
)
SELECT segment, COUNT(*) AS customers, ROUND(AVG(spend),2) AS avg_clv,
    ROUND(AVG(orders),1) AS avg_orders, ROUND(SUM(spend),2) AS total_revenue
FROM cs GROUP BY segment ORDER BY avg_clv DESC
"""
df7 = pd.read_sql(q7, conn)
df7.to_csv(f"{OUT}/segment_clv.csv", index=False)
print(f"Q7 CLV by segment: {len(df7)} segments")

conn.close()
print("\n✓ All queries exported to", OUT)

# Save summary for dashboard
summary = {
    "total_revenue": float(df1['net_revenue'].sum()),
    "total_orders":  int(df1['total_orders'].sum()),
    "avg_margin":    float(df1['margin_pct'].mean()),
    "top_product":   df4.iloc[0]['product'],
    "top_channel":   df5.iloc[0]['channel'],
}
with open(f"{OUT}/summary.json","w") as f:
    json.dump(summary, f, indent=2)
print("Summary:", summary)
