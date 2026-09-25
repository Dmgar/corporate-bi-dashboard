SELECT 
    strftime('%Y-%m', date) as month,
    SUM(revenue) as total_revenue,
    SUM(profit) as total_profit
FROM sales
GROUP BY month
ORDER BY month;
