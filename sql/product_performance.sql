SELECT 
    category,
    product_name,
    SUM(quantity) as items_sold,
    SUM(revenue) as total_revenue,
    SUM(profit) as total_profit,
    COALESCE((SUM(profit) / NULLIF(SUM(revenue), 0)) * 100, 0) as margin_percentage,
    RANK() OVER (PARTITION BY category ORDER BY SUM(profit) DESC) as category_rank
FROM data_table
GROUP BY category, product_name
ORDER BY total_profit DESC;
