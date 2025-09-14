#pip install streamlit psycopg2-binary pandas plotly
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import altair as alt

# --------------------------
# DB Connection
# --------------------------
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="postgres",
        user="postgres",
        password="nupur"
    )

@st.cache_data(ttl=600)  # cache for 10 minutes
def run_query(query: str):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    return df


# --------------------------
# Streamlit Layout
# --------------------------
st.set_page_config(page_title="Blinkit Dashboard", layout="wide")
st.title("Blinkit Analytics Dashboard")

# Tabs
tabs = st.tabs(["👥 Customers", "📦 Orders", "🏘 Warehouses", "💹 Campaigns"])

# --------------------------
# Customers Tab
# --------------------------
with tabs[0]:
    st.header("Customer Analytics")

    retention_query = """
    SELECT
        is_prime_user,
        ROUND(100.00*count(*) FILTER (WHERE order_count>2)/count(*),2) AS retention
    FROM (
        SELECT c.customer_id, COUNT(o.order_id) AS order_count, c.is_prime_user
        FROM customers c
        JOIN orders o USING(customer_id)
        WHERE order_status='delivered'
        GROUP BY customer_id
    ) t
    GROUP BY is_prime_user;
    """
    retention_df = run_query(retention_query)
    st.subheader("Retention: Prime vs Non-Prime")
    st.dataframe(retention_df)

    # Chart
    fig = px.bar(retention_df, x="is_prime_user", y="retention", title="Retention % by Prime Status", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)


#average activation time
    st.subheader("Average Activation Time (Days) by Prime Status")
    activation_query = """
    SELECT 
    is_prime_user,AVG(EXTRACT(DAY FROM (first_order_date - signup_date))) AS avg_days_to_first_order
    FROM 
    (select min(o.order_date) as first_order_date, c.signup_date, is_prime_user
    from customers c
    JOIN orders o USING (customer_id)
    GROUP BY c.customer_id) t
    group by is_prime_user;
    """
    activation_df = run_query(activation_query)
    st.dataframe(activation_df)
    fig3 = px.bar(activation_df, x="is_prime_user", y="avg_days_to_first_order", title="Average activation time by Prime Status", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)

#customer lifetime value
    st.subheader("Customer Lifetime Value by prime user")
    clv_query = """
    SELECT c.is_prime_user, AVG(total_spent) AS avg_lifetime_value
FROM (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM payments p
    JOIN orders o USING(order_id)
    WHERE o.order_status='delivered'
    GROUP BY customer_id
) t
JOIN customers c USING(customer_id)
GROUP BY c.is_prime_user;
    """
    clv_df = run_query(clv_query)
    st.dataframe(clv_df)
    fig3 = px.bar(clv_df, x="is_prime_user", y="avg_lifetime_value", title="Average Customer Lifetime Value by Prime Status", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True) 

# --------------------------
# Orders Tab
# --------------------------
with tabs[1]:
    st.header("Orders Analysis")

    monthly_orders = """
    SELECT 
        month_year,
        count_orders,
        round(100*(count_orders-LAG(count_orders) OVER (ORDER BY month_year))/
              NULLIF(LAG(count_orders) OVER (ORDER BY month_year), 0),2) AS mom_growth
    FROM (
        SELECT TO_CHAR(order_date, 'YYYY-MM') AS month_year,
               COUNT(*) AS count_orders
        FROM orders
        WHERE order_status='delivered'
        GROUP BY TO_CHAR(order_date, 'YYYY-MM')
    ) t
    ORDER BY month_year;
    """
    monthly_df = run_query(monthly_orders)
    st.subheader("Monthly Orders & MoM Growth")
    st.dataframe(monthly_df)

    fig = px.line(monthly_df, x="month_year", y="count_orders", markers=True, title="Monthly Delivered Orders")
    st.plotly_chart(fig, use_container_width=True)
    #order_funnel
    order_fquery="""SELECT 
    order_status,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM orders), 2) AS pct_of_orders
FROM orders
GROUP BY order_status;"""
    order_funnel_df=run_query(order_fquery)
    st.subheader("Order Status Distribution")
    st.dataframe(order_funnel_df)
    fig1 = px.pie(order_funnel_df, names='order_status', values='pct_of_orders', title='Order Status Distribution', hole=0.4)
    st.plotly_chart(fig1, use_container_width=True)

    #number of orders per city
    city_query="""
    SELECT 
    city,
    COUNT(distinct o.customer_id) FILTER (WHERE is_prime_user = 'Yes') AS prime_users,
    COUNT(distinct o.customer_id) FILTER (WHERE is_prime_user = 'No')  AS non_prime_users, 
	count(*) as order_count
    FROM customers c
    join orders o using(customer_id)
    where order_status='delivered'
    GROUP BY city
    ORDER BY order_count desc;
    """

    city_df=run_query(city_query)
    st.subheader("Orders by City with Prime vs Non-Prime Users")
    st.dataframe(city_df)
    city_df_melted = city_df.melt(id_vars=['city', 'order_count'], value_vars=['prime_users', 'non_prime_users'], var_name='user_type', value_name='user_count')
    fig=px.bar(city_df_melted, x='city', y='user_count', color='user_type', title='Prime vs Non-Prime Users by City', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    #median order value by city
    st.subheader("Median Order Value by City")
    mov_query="""
    SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_order_amount, c.city
    FROM payments p
    join orders o
    using(order_id)
    join customers c using(customer_id)
    group by c.city
    order by median_order_amount desc;

    """
    mov_df=run_query(mov_query)
    st.dataframe(mov_df)
    fig=px.bar(mov_df, x='city', y='median_order_amount',
                title='Median Order Value by City', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    #peak order hours
    st.subheader("Peak Order Hours")
    peak_query="""
    SELECT 
    DATE_PART('hour', order_date) AS order_hour,
    COUNT(*) AS total_orders
FROM orders
WHERE order_status = 'delivered'
GROUP BY order_hour
ORDER BY total_orders DESC;
    """
    peak_df=run_query(peak_query)
    st.dataframe(peak_df)
    fig=px.bar(peak_df, x='order_hour', y='total_orders',
                title='Total Orders by Hour of Day', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# Warehouses Tab
# --------------------------
with tabs[2]:
    st.header("Warehouse Performance")

    wh_orders = """
    SELECT warehouse_id, COUNT(order_id) AS total_orders
    FROM orders
    GROUP BY warehouse_id
    ORDER BY total_orders DESC;
    """
    wh_df = run_query(wh_orders)
    st.subheader("Orders by Warehouse")
    st.dataframe(wh_df)
    wh_df["warehouse_id"] = wh_df["warehouse_id"].astype(str)
    fig = px.bar(wh_df, x="warehouse_id", y="total_orders", title="Total Orders by Warehouse")
    st.plotly_chart(fig, use_container_width=True)

    #average delivery time by warehouse
    st.subheader("Average Delivery Time by Warehouse")
    delivery_query = """
    select PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_time_minutes) AS median_time, warehouse_id
from orders 
group by warehouse_id
order by median_time desc;
    """
    delivery_df = run_query(delivery_query)
    st.dataframe(delivery_df)
    delivery_df["warehouse_id"] = delivery_df["warehouse_id"].astype(str)
    fig2 = px.bar(delivery_df, x="warehouse_id", y="median_time", title="Median Delivery Time (Minutes) by Warehouse", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

    #warehouses with the most cancellations
    st.subheader("Warehouses with Most Cancellations")
    cancel_query = """
    select count(*) as cancel_warehouse, o.warehouse_id
from orders o
join warehouses w using(warehouse_id)
where order_status='delivered'
group by o.warehouse_id
order by cancel_warehouse desc;
    """
    cancel_df = run_query(cancel_query)
    st.dataframe(cancel_df)
    cancel_df["warehouse_id"] = cancel_df["warehouse_id"].astype(str)
    fig3 = px.bar(cancel_df, x="warehouse_id", y="cancel_warehouse", title="Cancellations by Warehouse", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)

    #best performing warehouse during peak hours
    st.subheader("Best Performing Warehouse During Peak Hours (2 PM - 6 PM)")
    peak_wh_query = """
    with peak_hours as (
select date_part('hour',order_date) as order_hour
from orders
group by order_hour
order by count(*) desc
limit 3
)
select 
	o.warehouse_id,
	w.location,
	date_part('hour',o.order_date) as order_hour,
	count(*) as total_order
from orders o
join warehouses w using(warehouse_id)
where date_part('hour',o.order_date) in (select order_hour from peak_hours) and o.order_status='delivered'
group by order_hour,o.warehouse_id,w.location
order by total_order desc,order_hour;
"""
    peak_wh_df = run_query(peak_wh_query)
    st.dataframe(peak_wh_df)
    peak_wh_df["warehouse_id"] = peak_wh_df["warehouse_id"].astype(str)
    fig4 = px.bar(peak_wh_df, x="warehouse_id", y="total_order", color="order_hour", title="Total Orders by Warehouse During Peak Hours", text_auto=True)
    st.plotly_chart(fig4, use_container_width=True)

# --------------------------
# Campaigns Tab
# --------------------------
with tabs[3]:
    st.header("Campaign Performance")

    ctr_query = """
    SELECT channel,
           ROUND(AVG((clicks::numeric / NULLIF(impressions, 0)) * 100), 2) AS ctr
    FROM campaigns
    GROUP BY channel
    ORDER BY ctr DESC;
    """
    ctr_df = run_query(ctr_query)
    st.subheader("CTR by Channel")
    st.dataframe(ctr_df)

    fig = px.bar(ctr_df, x="channel", y="ctr", title="CTR % by Channel", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    roas_query = """
    select round((avg(conversions::numeric/spend)*100),2) as ROAS,
    channel
    from campaigns
    group by channel;
    """
    roas_df = run_query(roas_query)
    st.subheader("ROAS by Channel")
    st.dataframe(roas_df)

    fig2 = px.bar(roas_df, x="channel", y="roas", title="ROAS by Channel", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

    #CPC(cost per click) by channel
    cpc_query = """
    SELECT channel, ROUND(avg((spend::numeric / NULLIF(clicks, 0))*100), 2) AS cpc
    FROM campaigns
    group by channel
    order by cpc desc;
    """
    cpc_df = run_query(cpc_query)
    st.subheader("Cost Per Click by Channel")
    st.dataframe(cpc_df)
    fig3 = px.bar(cpc_df, x="channel", y="cpc", title="Cost Per Click by Channel", text_auto=True)
    st.plotly_chart(fig3, use_container_width=True)

    #CTR(click through rate) by campaign type
    ctr_type_query = """
    SELECT 
    channel,
    ROUND(AVG((clicks::numeric / NULLIF(impressions, 0)) * 100), 2) AS ctr
    FROM campaigns
    GROUP BY channel
    ORDER BY ctr DESC;
    """
    ctr_type_df = run_query(ctr_type_query)
    st.subheader("CTR by Campaign Type")
    st.dataframe(ctr_type_df)
    fig4 = px.bar(ctr_type_df, x="channel", y="ctr", title="CTR % by Campaign Type", text_auto=True)
    st.plotly_chart(fig4, use_container_width=True)

    #conversion rate
    conv_query = """
    SELECT 
    channel,
    ROUND(AVG((conversions::numeric / NULLIF(clicks, 0)) * 100), 2) AS cr
    FROM campaigns
    GROUP BY channel
    ORDER BY cr DESC;
    """
    conv_df = run_query(conv_query)
    st.subheader("Conversion Rate by Channel")
    st.dataframe(conv_df)
    fig5 = px.bar(conv_df, x="channel", y="cr", title="Conversion Rate % by Channel", text_auto=True)
    st.plotly_chart(fig5, use_container_width=True)
