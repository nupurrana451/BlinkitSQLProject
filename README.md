# Blinkit Database Simulation & Analytics (PostgreSQL)

## 📌 Problem Statement
Blinkit (a quick-commerce company) relies heavily on customer behavior insights, warehouse efficiency, and campaign performance to optimize its operations.  
The goal of this project was to **simulate a realistic Blinkit-like database** and perform **SQL-based analytics** to derive business insights around customer retention, order funnels, warehouse performance, and marketing effectiveness.

---

## ⚙️ Tech Stack
- **Database:** PostgreSQL  
- **Data Generation:** [Faker](https://faker.readthedocs.io/) (Python) for creating synthetic data (100k+ rows)  
- **Data Analysis & Queries:** SQL (CTEs, Aggregations, Joins, Window Functions)  
- **Visualization:** pgAdmin / Plotly / Streamlit (optional if you visualized)  
- **Version Control:** Git + GitHub  

---

## 📂 Database Schema
The project simulates the following tables:
[Database](https://github.com/nupurrana451/BlinkitSQLProject/blob/main/BlinkiDatabaseSchema.png)

1. **customers** – customer info (prime vs non-prime, city, signup date, etc.)  
2. **orders** – order-level data with timestamps and order status (delivered, cancelled, returned, etc.)  
3. **order_items** – items linked to orders, including product details and quantities  
4. **payments** – payment method, amount, status  
5. **warehouses** – warehouse locations and capacity  
6. **campaigns** – marketing campaigns with spend, clicks, impressions, conversions, etc.  

---

## 🛠️ Project Workflow

1. **Data Generation**  
   - Created synthetic data (100k+ rows) using Faker.  
   - Designed tables to mirror real-world Blinkit operations.  
   - Inserted data into PostgreSQL.  

2. **Data Cleaning & Constraints**  
   - Applied **primary keys, foreign keys, unique constraints**.  
   - Enforced **not null, check constraints, and data consistency rules**.  

3. **SQL Queries & Insights**  
   - **Customer Retention:** Identified customers who ordered **2+ times**, grouped by **Prime vs Non-Prime**.  
   - **City-Level Analysis:** Avg orders per city.  
   - **Order Funnel Analysis:** % of users in delivered, cancelled, returned stages.  
   - **Monthly Growth:** Orders per month, **MoM% growth graph**.  
   - **Warehouse Efficiency:** Identified warehouses handling excess load and those delivering during **peak hours**.  
   - **Peak Hours Analysis:** Determined busiest hours of the day.  
   - **Campaign KPIs:** Calculated CPC, CTR, Conversion Rate, customer lifetime value, AOV etc.  

---

## 📊 Key Insights
* Customer Retention Rate: **23% of prime customers** and **22.82% of non-prime user** placed repeat orders within 30 days, indicating effective retention strategies are needed.
* Average Orders per Customer: On average, each customer placed **1.1 orders per month**.
* Customer Lifetime Value (CLV): High-value customers contributed 35% of total revenue despite being only 15% of the customer base.
* Churn rate after 30 days: **82% of customers** churn after 30 days of inactivity.
* October had the highest number returning customers, with further analysis we can identify the underlying reason/campaign.
* Warehouses with id 20,37,33 show the best performance during peak hours (3 PM, 4 PM, 6PM).
* Identifying bottlenecks: 32, 49, 5 warehouse IDs have the most cancelled orders.
* CPA: Cost Per Aquisition for Emails is the least, hence it's most cost-efficient campaign, with 51% conversion rate(second highest) and highest CTR(click through rate).

