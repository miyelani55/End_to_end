"""
Creates a local SQLite database mirroring a PostgreSQL/BigQuery schema.
Same SQL syntax works on Postgres — just swap the connection string.
"""
import sqlite3, pandas as pd, numpy as np, os
from datetime import datetime, timedelta
import random, json

random.seed(42); np.random.seed(42)
DB = "/home/claude/sql_analytics/ecommerce.db"
conn = sqlite3.connect(DB)
cur  = conn.cursor()

# ── DDL ──────────────────────────────────────────────────────────────────────
cur.executescript("""
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS marketing_spend;

CREATE TABLE categories (
    category_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    parent_id     INTEGER REFERENCES categories(category_id)
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    category_id   INTEGER REFERENCES categories(category_id),
    unit_cost     REAL NOT NULL,
    unit_price    REAL NOT NULL,
    launched_at   DATE NOT NULL,
    is_active     INTEGER DEFAULT 1
);

CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    full_name     TEXT NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    city          TEXT,
    country       TEXT DEFAULT 'ZA',
    segment       TEXT CHECK(segment IN ('B2C','B2B','VIP')),
    acquired_at   DATE NOT NULL,
    referral_src  TEXT
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(customer_id),
    status        TEXT CHECK(status IN ('completed','returned','cancelled','pending')),
    channel       TEXT CHECK(channel IN ('web','mobile','store','marketplace')),
    ordered_at    DATETIME NOT NULL,
    shipped_at    DATETIME,
    discount_pct  REAL DEFAULT 0
);

CREATE TABLE order_items (
    item_id       INTEGER PRIMARY KEY,
    order_id      INTEGER REFERENCES orders(order_id),
    product_id    INTEGER REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    REAL NOT NULL,
    unit_cost     REAL NOT NULL
);

CREATE TABLE marketing_spend (
    spend_id      INTEGER PRIMARY KEY,
    month         TEXT NOT NULL,
    channel       TEXT NOT NULL,
    spend_zar     REAL NOT NULL
);
""")

# ── SEED DATA ─────────────────────────────────────────────────────────────────
cats = [
  (1,'Electronics',None),(2,'Clothing',None),(3,'Home & Kitchen',None),
  (4,'Sports',None),(5,'Beauty',None),
  (6,'Laptops',1),(7,'Phones',1),(8,'Audio',1),
  (9,'Tops',2),(10,'Footwear',2),(11,'Outerwear',2)
]
cur.executemany("INSERT INTO categories VALUES(?,?,?)", cats)

products_data = [
  (1,'MacBook Pro 14"',6,8500,14999,'2022-01-15',1),
  (2,'iPhone 15',7,6200,11999,'2023-09-20',1),
  (3,'Sony WH-1000XM5',8,1800,3499,'2022-06-10',1),
  (4,'Samsung Galaxy S24',7,5800,10999,'2024-01-17',1),
  (5,'Dell XPS 15',6,7200,13499,'2021-08-01',1),
  (6,'AirPods Pro',8,1200,2799,'2022-11-01',1),
  (7,'Nike Air Max',10,450,1199,'2023-03-12',1),
  (8,'Levi 501 Jeans',9,280,699,'2021-05-20',1),
  (9,'North Face Jacket',11,1100,2499,'2022-09-01',1),
  (10,'Dyson V15',3,3200,6999,'2023-01-10',1),
  (11,'Air Fryer XL',3,650,1299,'2022-07-14',1),
  (12,'Yoga Mat Pro',4,180,449,'2023-04-01',1),
  (13,'Protein Powder 2kg',4,320,699,'2022-10-01',1),
  (14,'Neutrogena Set',5,180,399,'2023-02-01',1),
  (15,'Fenty Beauty Kit',5,620,1199,'2023-08-15',1),
]
cur.executemany("INSERT INTO products VALUES(?,?,?,?,?,?,?)", products_data)

first = ['Sipho','Thandi','Bongani','Lerato','Naledi','Kagiso','Ayanda','Mpho','Zanele','Lebo',
         'Tshepo','Nomsa','Sifiso','Palesa','Nhlanhlayethu','Thandeka','Sibusiso','Mamello','Rethabile','Katlego',
         'James','Sarah','Michael','Emma','David','Lisa','John','Anna','Chris','Maria']
last  = ['Dlamini','Nkosi','Molefe','Sithole','Mthembu','Khumalo','Mokoena','Mahlangu','Cele','Ndlovu',
         'Shabalala','Mhlongo','Zulu','Buthelezi','Ntuli','Mabaso','Gumede','Radebe','Mthethwa','Bhengu',
         'Smith','Johnson','Williams','Brown','Jones','Davis','Wilson','Taylor','Anderson','Thomas']
cities= ['Johannesburg','Cape Town','Durban','Pretoria','Port Elizabeth','Bloemfontein','Polokwane','Nelspruit','Kimberley','East London']
srcs  = ['google','facebook','instagram','referral','organic','tiktok','email']
segs  = ['B2C','B2C','B2C','B2B','VIP']

customers, orders, items, mktg = [], [], [], []
start = datetime(2022,1,1)

for cid in range(1, 1501):
    fn = random.choice(first); ln = random.choice(last)
    acq = start + timedelta(days=random.randint(0,700))
    customers.append((cid,f"{fn} {ln}",f"{fn.lower()}.{ln.lower()}{cid}@mail.com",
                      random.choice(cities),'ZA',random.choice(segs),
                      acq.strftime('%Y-%m-%d'),random.choice(srcs)))

cur.executemany("INSERT INTO customers VALUES(?,?,?,?,?,?,?,?)", customers)

order_id = 1; item_id = 1
channels = ['web','mobile','store','marketplace']
statuses = ['completed','completed','completed','completed','returned','cancelled','pending']
ch_weights = [40,30,20,10]

for oid_offset, (cid,*_) in enumerate(customers):
    n_orders = random.choices([1,2,3,4,5,6],[20,25,20,15,12,8])[0]
    acq_date = datetime.strptime(customers[oid_offset][6],'%Y-%m-%d')
    for _ in range(n_orders):
        o_date = acq_date + timedelta(days=random.randint(1,min(700,(datetime(2023,12,31)-acq_date).days+1)))
        if o_date > datetime(2023,12,31): continue
        status = random.choice(statuses)
        channel= random.choices(channels,weights=ch_weights)[0]
        disc   = random.choices([0,0.05,0.10,0.15,0.20],[55,20,12,8,5])[0]
        shipped= (o_date+timedelta(days=random.randint(1,5))).strftime('%Y-%m-%d %H:%M:%S') if status=='completed' else None
        orders.append((order_id,cid,status,channel,o_date.strftime('%Y-%m-%d %H:%M:%S'),shipped,disc))
        n_items = random.choices([1,2,3],[60,30,10])[0]
        prods_chosen = random.sample(products_data, min(n_items,len(products_data)))
        for p in prods_chosen:
            pid,_,_,ucost,uprice,*__ = p
            qty = random.choices([1,2,3],[70,20,10])[0]
            items.append((item_id,order_id,pid,qty,uprice*(1-disc),ucost))
            item_id+=1
        order_id+=1

cur.executemany("INSERT INTO orders VALUES(?,?,?,?,?,?,?)", orders)
cur.executemany("INSERT INTO order_items VALUES(?,?,?,?,?,?)", items)

# marketing spend per month/channel
months = pd.date_range('2022-01-01','2023-12-01',freq='MS')
mktg_channels = ['google','facebook','instagram','tiktok','email']
spend_id=1
for m in months:
    for ch in mktg_channels:
        base={'google':45000,'facebook':32000,'instagram':28000,'tiktok':18000,'email':8000}[ch]
        spend = base * random.uniform(0.7,1.4)
        mktg.append((spend_id,m.strftime('%Y-%m'),ch,round(spend,2)))
        spend_id+=1
cur.executemany("INSERT INTO marketing_spend VALUES(?,?,?,?)", mktg)

conn.commit()

# verify
for tbl in ['categories','products','customers','orders','order_items','marketing_spend']:
    n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"  {tbl}: {n:,} rows")
conn.close()
print("\n✓ Database ready:", DB)
