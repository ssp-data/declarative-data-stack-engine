SELECT 
    c.*,
    p.population,
    p.population_density,
    p.median_age,
    ROUND(c.total_cases * 1000000.0 / p.population, 2) as cases_per_million,
    ROUND(c.total_deaths * 1000000.0 / p.population, 2) as deaths_per_million,
    ROUND(c.people_fully_vaccinated * 100.0 / p.population, 2) as vaccination_rate_pct
FROM covid_daily_metrics c
LEFT JOIN population_base p 
    ON c.country_code = p.country_code 
    AND EXTRACT(YEAR FROM c.date) = p.year;
