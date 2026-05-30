# 🔍 End-to-End SQL Analytics Project
### E-Commerce Business Intelligence — PostgreSQL / BigQuery Compatible

> **7 production-grade SQL queries** covering revenue trends, RFM segmentation, cohort retention, product Pareto, channel performance, marketing ROI, and CLV — built against a normalised 6-table e-commerce schema with 6,600+ transactions.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL%20%7C%20BigQuery%20%7C%20SQLite-336791?logo=postgresql)
![Dash](https://img.shields.io/badge/Plotly_Dash-2.17-purple?logo=plotly)
![Pandas](https://img.shields.io/badge/Pandas-2.2-green?logo=pandas)

---

## 📐 Database Schema

```
┌─────────────────────┐     ┌──────────────────────┐
│     customers        │     │       orders          │
│─────────────────────│     │──────────────────────│
│ customer_id   PK    │────▶│ order_id    PK        │
│ full_name           │     │ customer_id FK        │
│ email               │     │ status  (completed /  │
│ city                │     │          returned /   │
│ segment (B2C/B2B/VIP│     │          cancelled /  │
│ acquired_at         │     │          pending)     │
│ referral_src        │     │ channel (web/mobile/  │
└─────────────────────┘     │          store/mktpl) │
                             │ ordered_at            │
         ┌───────────────────│ discount_pct          │
         │                   └──────────────────────┘
         ▼                              │
┌─────────────────────┐                ▼
│    order_items       │     ┌──────────────────────┐
│─────────────────────│     │      products         │
│ item_id     PK      │────▶│──────────────────────│
│ order_id    FK      │     │ product_id   PK       │
│ product_id  FK      │     │ name                  │
│ quantity            │     │ category_id  FK       │
│ unit_price          │     │ unit_cost             │
│ unit_cost           │     │ unit_price            │
└─────────────────────┘     │ launched_at           │
                             └──────────────────────┘
                                        │
                             ┌──────────────────────┐
                             │     categories        │
                             │──────────────────────│
                             │ category_id  PK       │
                             │ name                  │
                             │ parent_id   (self FK) │
                             └──────────────────────┘

┌──────────────────────────┐
│    marketing_spend        │
│──────────────────────────│
│ spend_id    PK            │
│ month (YYYY-MM)           │
│ channel                   │
│ spend_zar                 │
└──────────────────────────┘
```

**Dataset:** 1,500 customers · 4,403 orders · 6,622 line items · 15 products · Jan 2022–Dec 2023

---

## 🗂️ Project Structure

```
sql_analytics/
│
├── sql/
│   ├── 01_revenue_trends.sql        # MoM growth with LAG()
│   ├── 02_rfm_segmentation.sql      # RFM with NTILE(5) windows
│   ├── 03_cohort_retention.sql      # Cohort heatmap query
│   └── 04_07_advanced_queries.sql   # Product, Channel, Mktg, CLV
│
├── setup_db.py                      # Seeds SQLite DB (mirrors PostgreSQL DDL)
├── run_queries.py                   # Runs all queries → exports CSV
├── dashboard.py                     # Plotly Dash analytics dashboard
│
├── outputs/                         # Auto-generated query results (CSV + JSON)
│   ├── revenue_trend.csv
│   ├── rfm_segments.csv
│   ├── cohort_retention.csv
│   ├── product_performance.csv
│   ├── channel_performance.csv
│   ├── marketing_roi.csv
│   ├── segment_clv.csv
│   └── summary.json
│
├── requirements.txt
├── Procfile
└── README.md
```

---

## 📊 The 7 Queries — Skills Demonstrated

### Query 1 — Monthly Revenue Trend + MoM Growth
**Techniques:** CTE, `LAG()` window, `NULLIF`, date truncation

```sql
WITH monthly_revenue AS (
    SELECT strftime('%Y-%m', ordered_at) AS month,
           SUM(unit_price * quantity * (1 - discount_pct)) AS net_revenue
    FROM orders JOIN order_items USING (order_id)
    WHERE status = 'completed'
    GROUP BY 1
)
SELECT month, net_revenue,
       LAG(net_revenue) OVER (ORDER BY month) AS prev_month,
       ROUND(100.0 * (net_revenue - LAG(net_revenue) OVER (ORDER BY month))
             / NULLIF(LAG(net_revenue) OVER (ORDER BY month), 0), 1) AS mom_growth_pct
FROM monthly_revenue;
```
**Insight:** Nov–Dec 2023 holiday spike = 60% above monthly average. Margin held steady, no discount abuse.

---

### Query 2 — RFM Customer Segmentation
**Techniques:** `NTILE(5)` window, chained CTEs, `CASE` scoring matrix

| Segment | Customers | Avg Spend | Avg Recency |
|---|---|---|---|
| Champion | ~15% | Highest | < 30 days |
| Loyal Customer | ~22% | High | < 60 days |
| At Risk | ~12% | High | 90–150 days |
| Lost | ~18% | Low | > 200 days |

**Insight:** Champions are 15% of the base but drive 38% of revenue. "At Risk" = top retention priority.

---

### Query 3 — Monthly Cohort Retention
**Techniques:** `MIN() OVER` partition, date arithmetic for month index, conditional self-join

**Insight:** Month-1 retention ~25% (industry avg). Brighter rows in later cohorts = improving product-market fit. Push to 30%+ with post-purchase email automation.

---

### Query 4 — Product Pareto Analysis
**Techniques:** `RANK()`, `SUM() OVER` running total, margin calculation

**Insight:** Top 3 products = 52% of total revenue. Beauty products carry 55% margin vs 42% for Electronics — prioritise Beauty in paid campaigns.

---

### Query 5 — Sales Channel Quality Analysis
**Techniques:** Conditional aggregation with `CASE`, return rate ratio, `RANK()` window

| Channel | AOV | Return Rate | Revenue Rank |
|---|---|---|---|
| Web | Highest | Low | 1 |
| Mobile | Medium | Medium | 2 |
| Store | Medium | Low | 3 |
| Marketplace | Low | **Highest** | 4 |

**Insight:** Marketplace has highest return rate — product listing quality issue. Fix descriptions and images.

---

### Query 6 — Marketing ROI (ROAS + CAC)
**Techniques:** CTE join across fact + spend tables, division ratio, `LEFT JOIN` for missing spend

| Channel | ROAS | Verdict |
|---|---|---|
| Email | 15× | Scale aggressively |
| TikTok | 7× | Monitor creative |
| Instagram | 4.5× | Solid |
| Google | 2.6× | Above breakeven |
| Organic/Referral | ∞ | Invest in referral program |

**Insight:** Email delivers 15× ROAS — lowest CAC at scale. Build the list.

---

### Query 7 — Customer Lifetime Value by Segment
**Techniques:** Multi-level CTE, `AVG() OVER`, predicted annual CLV formula

**Insight:** VIP and B2B segments have similar CLV — B2B should be a growth priority as CAC is justified.

---

## 🚀 Run Locally

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/sql-analytics.git
cd sql-analytics

# Install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Build database & run queries
python setup_db.py
python run_queries.py

# Launch dashboard
python dashboard.py
# → http://localhost:8051
```

---

## ☁️ Deploy on PostgreSQL (Production)

The `setup_db.py` schema and all SQL queries are **PostgreSQL-compatible**. To switch:

```python
# In setup_db.py / run_queries.py, replace:
import sqlite3
conn = sqlite3.connect("ecommerce.db")

# With:
import psycopg2
conn = psycopg2.connect(
    host="localhost", database="ecommerce",
    user="postgres", password="yourpassword"
)
```

Change SQLite-specific functions:
| SQLite | PostgreSQL |
|---|---|
| `strftime('%Y-%m', col)` | `TO_CHAR(col, 'YYYY-MM')` |
| `JULIANDAY(date2) - JULIANDAY(date1)` | `date2 - date1` (returns interval) |
| `INTEGER` | `SERIAL` for PKs |

---

## ☁️ Deploy on BigQuery (Cloud)

```python
from google.cloud import bigquery

client = bigquery.Client(project="your-project-id")

# Load CSV to BigQuery
job = client.load_table_from_dataframe(
    df, "your-project.ecommerce.orders",
    job_config=bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
)
job.result()

# Run query
result = client.query("""
    SELECT ... FROM `your-project.ecommerce.orders`
    JOIN `your-project.ecommerce.order_items` USING (order_id)
""").to_dataframe()
```

BigQuery SQL changes:
- Use backtick table names: `` `project.dataset.table` ``
- Replace `strftime` with `FORMAT_DATE('%Y-%m', ordered_at)`
- Replace `JULIANDAY` with `DATE_DIFF(date2, date1, DAY)`

---

## 📤 GitHub Upload — Step by Step

### Step 1: Create the repo
1. Go to [github.com/new](https://github.com/new)
2. Name: `sql-analytics-ecommerce`
3. Description: `End-to-end SQL analytics project — RFM, cohort retention, CLV, marketing ROI`
4. Set to **Public** (recruiters need to see it)
5. ✅ Check "Add README" → click **Create repository**

### Step 2: Initialise git locally
```bash
cd sql_analytics
git init
git add .
git commit -m "feat: initial SQL analytics project with 7 queries and Dash dashboard"
```

### Step 3: Connect and push
```bash
git remote add origin https://github.com/YOUR_USERNAME/sql-analytics-ecommerce.git
git branch -M main
git push -u origin main
```

### Step 4: Add a .gitignore
```bash
cat > .gitignore << EOF
__pycache__/
*.pyc
.env
venv/
ecommerce.db
EOF
git add .gitignore
git commit -m "chore: add gitignore"
git push
```

### Step 5: Deploy dashboard to Render (free hosting)
1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Settings:
   - **Build:** `pip install -r requirements.txt && python setup_db.py && python run_queries.py`
   - **Start:** `gunicorn dashboard:server`
4. Click **Deploy** — live URL in ~3 minutes
5. Add the live URL to your GitHub repo description

### Step 6: Make your repo recruiter-ready
- ✅ Pin the repo on your GitHub profile
- ✅ Add topics: `sql`, `data-analytics`, `python`, `plotly`, `postgresql`, `rfm`, `cohort-analysis`
- ✅ Add a screenshot of the dashboard to the README
- ✅ Link to it in your LinkedIn Featured section

---

## 🧠 SQL Concepts Covered (Recruiter Checklist)

| Concept | Query | Status |
|---|---|---|
| Common Table Expressions (CTEs) | All queries | ✅ |
| LAG / LEAD window functions | Q1 | ✅ |
| NTILE window function | Q2 | ✅ |
| RANK / DENSE_RANK | Q4 | ✅ |
| Running totals with SUM() OVER | Q4 | ✅ |
| Conditional aggregation (CASE SUM) | Q5 | ✅ |
| Multi-table JOINs (3–5 tables) | All queries | ✅ |
| Self-referencing / cohort joins | Q3 | ✅ |
| Date arithmetic | Q2, Q3 | ✅ |
| NULLIF / COALESCE | Q1, Q5, Q6 | ✅ |
| Subqueries in FROM / WHERE | Q2 | ✅ |
| Schema design (star schema) | DDL | ✅ |

---

## 📬 Contact

**Miyelani Teddy Mashele** — Honours Computer Science, University of Limpopo
- 📧 teddymatimu@gmail.com · 📱 +27 76 996 0929
- 🔗 [linkedin.com/in/miyelani-teddy-mashele](https://linkedin.com/in/miyelani-teddy-mashele)
- 💻 [github.com/miyelani55](https://github.com/miyelani55) · 🌐 [miyelani.streamlit.app](https://miyelani.streamlit.app)
