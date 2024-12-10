-- 2. Monthly Testing and Positivity Trends
SELECT 
    DATE_TRUNC('month', date) as month,
    country_code,
    SUM(new_tests) as monthly_tests,
    SUM(new_cases) as monthly_cases,
    ROUND(SUM(new_cases) * 100.0 / NULLIF(SUM(new_tests), 0), 2) as monthly_positivity_rate
FROM covid_metrics_enriched
GROUP BY 1, 2
ORDER BY 1;
