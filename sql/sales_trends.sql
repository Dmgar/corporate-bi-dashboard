WITH monthly_data AS (
    SELECT 
        strftime(date, '%Y-%m') as month,
        SUM(revenue) as total_revenue,
        SUM(profit) as total_profit
    FROM data_table
    GROUP BY 1
)
SELECT 
    month,
    total_revenue,
    total_profit,
    SUM(total_revenue) OVER (ORDER BY month) as cumulative_revenue,
    LAG(total_revenue) OVER (ORDER BY month) as prev_month_revenue,
    ((total_revenue - LAG(total_revenue) OVER (ORDER BY month)) / NULLIF(LAG(total_revenue) OVER (ORDER BY month), 0)) * 100 as growth_pct
FROM monthly_data
ORDER BY month;
