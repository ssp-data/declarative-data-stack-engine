SELECT 
    date,
    iso_code as country_code,
    location,
    COALESCE(new_cases, 0) as new_cases,
    COALESCE(new_deaths, 0) as new_deaths,
    COALESCE(total_cases, 0) as total_cases,
    COALESCE(total_deaths, 0) as total_deaths,
    COALESCE(new_tests, 0) as new_tests,
    COALESCE(total_tests, 0) as total_tests,
    COALESCE(positive_rate, 0) as positive_rate,
    COALESCE(total_vaccinations, 0) as total_vaccinations,
    COALESCE(people_fully_vaccinated, 0) as people_fully_vaccinated
FROM rearc_covid19_world_cases_deaths_testing
WHERE date >= '2020-01-01'
--AND iso_code = 'CHE'
;
