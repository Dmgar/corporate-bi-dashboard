SELECT 
    SUM(revenue) as total_revenue,
    SUM(cost) as total_cost,
    SUM(profit) as total_profit,
    COUNT(transaction_id) as total_transactions
FROM sales;
