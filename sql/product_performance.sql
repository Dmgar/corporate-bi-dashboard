SELECT 
    p.category,
    p.product_name,
    SUM(s.quantity) as items_sold,
    SUM(s.revenue) as total_revenue,
    SUM(s.profit) as total_profit,
    (SUM(s.profit) / SUM(s.revenue)) * 100 as margin_percentage
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category, p.product_name
ORDER BY total_profit DESC;
