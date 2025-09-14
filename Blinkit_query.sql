-- DATA CLEANING AND ER SETTINGS
-- creating new tables without constraints for importing CSVs
CREATE TABLE warehouses (
    warehouse_id INT PRIMARY KEY,
    warehouse_location VARCHAR(100),
    capacity_utilization DECIMAL
);
CREATE TABLE customers2(
    customer_id INT,
    customer_name VARCHAR(100),
    email VARCHAR(100),
    signup_date DATE,
    city VARCHAR(100),
    is_prime_user VARCHAR(10)
);
CREATE TABLE orders2(
    order_id BIGINT,
    customer_id INT,
    order_date TIMESTAMP,
    warehouse_id INT,
    order_status VARCHAR(20),
    total_value DECIMAL,
    delivery_time_minutes INT
);

CREATE TABLE order_items2(
    order_item_id BIGINT,
    order_id BIGINT,
    product_id INT,
    quantity INT,
    price_per_unit DECIMAL
);
CREATE TABLE payments2 (
    payment_id BIGINT,
    order_id BIGINT,
    payment_date TIMESTAMP,
    payment_method VARCHAR(50),
    amount DECIMAL
);

update payments
set payment_method='UPI'
where lower(payment_method) like 'upi';


select* from payments2 limit 5;
select* from order_items2 limit 5;
select* from orders2 limit 5;
select* from warehouses limit 5;
select* from customers2 limit 100;
select* from campaigns limit 5;


-- checking for duplicates
SELECT EXISTS (
    SELECT 1
    FROM customers2
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) AS has_duplicates;


-- creating a clean table without duplicates
CREATE TABLE customers as
	 Select distinct on (customer_id) *
	 from customers2
	 order by customer_id;

	 
-- adding primary key
alter table customers add primary key (customer_id);
select* from customers limit 10;

-- adding foreign key on order_items, orders, payments
alter table orders2 add primary key(order_id);

ALTER TABLE order_items2
ADD CONSTRAINT fk_order_id
FOREIGN KEY (order_id)
REFERENCES orders2(order_id);

-- checking which order_id is not present in orders table
select* from order_items2 oi
where not exists (
select 1
from orders2 o
where oi.order_id=o.order_id
) limit 100;
--deleting
delete from order_items2 oi
where not exists (
select 1
from orders2 o
where oi.order_id=o.order_id
);

-- checking which customer_id is not present in customers table but is in orders

create index ids_orders2_customer on orders2(customer_id);
create index ids_customer_order on customers(customer_id);

select *
from orders2 o WHERE NOT EXISTS (
    SELECT 1
    FROM customers c
    WHERE c.customer_id = o.customer_id
) limit 100;

delete from orders2 o WHERE NOT EXISTS (
    SELECT 1
    FROM customers c
    WHERE c.customer_id = o.customer_id
);

ALTER TABLE orders2
ADD CONSTRAINT fk_customer
FOREIGN KEY (customer_id)
REFERENCES customers(customer_id);


--identifying invalid warehouse ids in orders table
CREATE INDEX idx_orders_warehouse_id ON orders2(warehouse_id);
delete from orders2 where warehouse_id>50;

ALTER TABLE orders2
ADD CONSTRAINT fk_warehouse
FOREIGN KEY (warehouse_id)
REFERENCES warehouses(warehouse_id);


create index idx_payments on payments2(order_id);
create index idx_orders on orders2(order_id);

select*
from payments2 p1
where not exists (
select 1
from orders2 o2
where p1.order_id=o2.order_id
);

delete
from payments2 p1
where not exists (
select 1
from orders2 o2
where p1.order_id=o2.order_id
);

alter table payments2 add constraint fk_order foreign key (order_id) references orders2(order_id)
--select* from orders2 limit 100;

--Finally renaming the tables
alter table order_items2 rename to order_items;
alter table orders2 rename to orders;
alter table payments2 rename to payments;

select "location" from warehouses; 


-- QUERYING 
-- Case study: Consider the problem statement,
-- Blinkit is an instant grocery delivery platform. They want to improve customer retention, optimize warehouse efficiency, and measure marketing campaigns. 

-- finding the customer retention of prime vs non-prime users by identifying the % of users who had more than 1 order.
select * from customers c
join orders o using(customer_id)
join payments p using(order_id)
where order_status ='delivered' and is_prime_user='Yes'
limit 50;
select count(customer_id)
from orders 
group by customer_id limit 10;

-- comparing the recurring customers% for prime vs non-prime users.
select
is_prime_user,
Round(100.00*count(*) filter (where order_count>2)/count(*),2) as retention
from (
select c.customer_id, count(o.order_id) as order_count, c.is_prime_user from customers c
join orders o
using(customer_id)
where order_status='delivered'
group by customer_id
) t
group by is_prime_user;

-- finding the percentage of customers at every stage of order funnel(delivered, cancelled, returned)
--cancelled
SELECT 
    COUNT(DISTINCT customer_id) * 100.0 / 
    (SELECT COUNT(DISTINCT customer_id) FROM orders) AS cancelled_orders_pct
FROM orders
WHERE order_status = 'cancelled';
--delivered
select 
	count(distinct customer_id)*100.0/
	(select count(distinct customer_id) from orders) as delivered_orders
from orders
where order_status='delivered';
--returned
select 
	count(distinct customer_id)*100.0/
	(select count(distinct customer_id) from orders) as returned_orders
from orders
where order_status='returned';


--finding average activation time for prime vs non-prime users
select* from orders limit 50;
select* from payments limit 50;

SELECT 
    is_prime_user,AVG(EXTRACT(DAY FROM (first_order_date - signup_date))) AS avg_days_to_first_order
FROM 
(select min(o.order_date) as first_order_date, c.signup_date, is_prime_user
from customers c
JOIN orders o USING (customer_id)
GROUP BY c.customer_id) t
group by is_prime_user;

--Number of orders per month
select max(order_date), min(order_date) from orders;

SELECT 
    month_year,
    count_orders,
	round(100*(count_orders-LAG(count_orders) over (order by month_year))/nullif(LAG(count_orders) OVER (ORDER BY month_year), 0),2) as MoM_growth
FROM 
(select
	TO_CHAR(order_date, 'YYYY-MM') AS month_year,
    COUNT(*) AS count_orders
from orders
where order_status='delivered'
GROUP BY TO_CHAR(order_date, 'YYYY-MM')) t
ORDER BY month_year;

-- Number of orders per city
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

--signups from each city
select count(*) as count_signup, city
from customers
where signup_date is not null
group by city
order by count_signup desc;


--median order value from each city
create index idx_customers on orders(customer_id);
create index idx_payments2 on payments(order_id);
SELECT 
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) AS median_order_amount, c.city
FROM payments p
join orders o
using(order_id)
join customers c using(customer_id)
group by c.city
order by median_order_amount desc;

--AOV of cancelled orders
select avg(p.amount) as AOV, c.city
from payments p
join orders o
using(order_id)
join customers c using(customer_id)
where o.order_status='cancelled'
group by c.city
order by AOV desc;

-- warehouse optimization
SELECT warehouse_id, COUNT(order_id) AS total_orders
FROM orders
GROUP BY warehouse_id
order by total_orders desc;

--average delivery time for each warehouse
select PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY delivery_time_minutes) AS median_time, warehouse_id
from orders 
group by warehouse_id
order by median_time desc;

--average order value per payment method
select avg(amount) as AOV,payment_method
from payments
group by payment_method
order by AOV desc;

select* from campaigns;

select avg(spend) as campaign_spend, channel
from campaigns
group by channel
order by campaign_spend desc;

select avg(impressions) as avg_imp, channel
from campaigns
group by channel
order by avg_imp desc;

select avg(clicks) as avg_clicks, channel
from campaigns
group by channel
order by avg_clicks desc;

select avg(conversions) as avg_conversions, channel
from campaigns
group by channel
order by avg_conversions desc;

--ROAS
select round((avg(conversions/spend)*100),2) as ROAS,
channel
from campaigns
group by channel;

--CPC
SELECT channel, ROUND(avg((spend::numeric / NULLIF(clicks, 0))*100), 2) AS cpc
FROM campaigns
group by channel
order by cpc desc;


--CTR
SELECT 
    channel,
    ROUND(AVG((clicks::numeric / NULLIF(impressions, 0)) * 100), 5) AS ctr
FROM campaigns
GROUP BY channel
ORDER BY ctr DESC;

--CPS
SELECT 
    channel,
    ROUND(AVG((spend::numeric / NULLIF(conversions, 0)) * 100), 5) AS cpc
FROM campaigns
GROUP BY channel
ORDER BY cpc DESC;

--Conversion rate
SELECT 
    channel,
    ROUND(AVG((conversions::numeric / NULLIF(clicks, 0)) * 100), 5) AS cr
FROM campaigns
GROUP BY channel
ORDER BY cr DESC;

--customer lifetime value
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

--failing warehouses
select count(*) as cancel_warehouse, o.warehouse_id
from orders o
join warehouses w using(warehouse_id)
where order_status='delivered'
group by o.warehouse_id
order by cancel_warehouse desc;

--peak hours
SELECT 
    DATE_PART('hour', order_date) AS order_hour,
    COUNT(*) AS total_orders
FROM orders
WHERE order_status = 'delivered'
GROUP BY order_hour
ORDER BY total_orders DESC;

--peak hours best performing warehouses
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
order by total_order desc,order_hour

select* from order_items limit 50;