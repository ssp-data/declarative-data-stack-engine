-- 3. Vaccination Progress Dashboard
SELECT 
    date,
    country_code,
    total_vaccinations,
    people_fully_vaccinated,
    vaccination_rate_pct,
    ROUND(
        (people_fully_vaccinated - LAG(people_fully_vaccinated, 7) OVER (PARTITION BY country_code ORDER BY date)) * 100.0 / population,
        2
    ) as weekly_vaccination_rate_change
FROM covid_metrics_enriched
WHERE people_fully_vaccinated > 0
ORDER BY date;
