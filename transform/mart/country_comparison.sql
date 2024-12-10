-- 4. Country Comparison by Population Density Impact
SELECT 
    country_code,
    population_density,
    MAX(cases_per_million) as max_cases_per_million,
    MAX(deaths_per_million) as max_deaths_per_million,
    MAX(vaccination_rate_pct) as max_vaccination_rate,
    ROUND(MAX(total_deaths) * 100.0 / NULLIF(MAX(total_cases), 0), 2) as case_fatality_rate
FROM covid_metrics_enriched
GROUP BY 1, 2
ORDER BY population_density DESC;
