SELECT 
    ISO3_Alpha_code as country_code,
    Year as year,
    CAST(REPLACE(Population_Thousands, ' ', '') AS INTEGER) as population,
    Population_Density_Per_Square_KM as population_density,
    Median_Age as median_age
FROM un_pop_data
where Year >= 2020
--AND ISO3_Alpha_code = 'CHE'
;
