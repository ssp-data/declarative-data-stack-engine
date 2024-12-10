-- Creates an root table with an S3 Location
-- Note: Set aws Region
create table rearc_covid19_world_cases_deaths_testing WITH (
  FORMAT='CSV', 
  skip_header_line_count=1,
  LOCATION='s3://covid19-lake/rearc-covid-19-world-cases-deaths-testing/csv/covid-19-world-cases-deaths-testing.csv'
);
