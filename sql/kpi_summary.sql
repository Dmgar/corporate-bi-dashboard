SELECT 
    SUM(revenue) as total_revenue,
    SUM(cost) as total_cost,
    SUM(profit) as total_profit,
    COUNT(*) as total_transactions,
    AVG(profit) as avg_profit_per_txn,
    COALESCE((SUM(profit) / NULLIF(SUM(revenue), 0)) * 100, 0) as overall_margin
FROM data_table;
