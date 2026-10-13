SELECT 
    region,
    channel,
    SUM(revenue) as total_revenue,
    SUM(profit) as total_profit,
    COUNT(*) as num_transactions,
    COALESCE((SUM(profit) / NULLIF(SUM(revenue), 0)) * 100, 0) as margin_percentage
FROM data_table
GROUP BY region, channel
ORDER BY total_revenue DESC;
