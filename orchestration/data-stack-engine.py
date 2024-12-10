from dagster import asset, AssetExecutionContext, Definitions
from dagster_duckdb import DuckDBResource
from dagster_sdf import SdfCliResource, SdfWorkspace, sdf_assets
from pathlib import Path
import json
import requests

# Configuration for workspace paths
workspace_dir = Path(__file__).joinpath("..", "./my_sdf_workspace").resolve()
target_dir = workspace_dir.joinpath("sdf_dagster_out")
environment = "dev"

# Initialize SDF workspace
workspace = SdfWorkspace(
    workspace_dir=workspace_dir,
    target_dir=target_dir,
    environment=environment,
)

@asset
def covid_raw_data(context: AssetExecutionContext, duckdb: DuckDBResource):
    # Ingest data from S3 using DuckDB
    query = 'SELECT * FROM "s3://coviddata/covid_*.parquet"'
    result = duckdb.execute_query(query)
    context.log.info(f"Loaded {len(result)} rows from S3")
    return result

@sdf_assets(workspace=workspace)
def covid_transformed_data(context: AssetExecutionContext, sdf: SdfCliResource, covid_raw_data):
    # Create SDF transformation configuration
    transform_config = {
        'groupby': 'country',
        'aggregate': {
            'cases': 'sum',
            'deaths': 'sum'
        }
    }
    
    # Write config to workspace
    config_path = workspace_dir / "transform_config.json"
    with open(config_path, "w") as f:
        json.dump(transform_config, f)
    
    # Execute SDF transformation
    yield from sdf.cli(
        ["transform", "--config", str(config_path)],
        target_dir=target_dir,
        environment=environment,
        context=context,
    ).stream()

@asset
def covid_dashboard(context: AssetExecutionContext, covid_transformed_data):
    # Configure Rill dashboard
    rill_config = {
        "template": "github://covid/covid_dashboard.md",
        "data": covid_transformed_data
    }
    
    # In practice, you'd use Rill's API here
    # This is a placeholder for the Rill integration
    context.log.info("Publishing dashboard to Rill Developer")
    
    # Simulate dashboard deployment
    # Replace with actual Rill API calls
    dashboard_url = f"https://app.rilldata.com/dashboards/covid-{context.run_id}"
    context.log.info(f"Dashboard published at: {dashboard_url}")
    
    return dashboard_url

# Resource configuration
defs = Definitions(
    assets=[covid_raw_data, covid_transformed_data, covid_dashboard],
    resources={
        "duckdb": DuckDBResource(
            database="covid_data.db"
        ),
        "sdf": SdfCliResource(
            workspace_dir=workspace_dir
        ),
    }
)
