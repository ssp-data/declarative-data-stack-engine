from dagster import (
    asset,
    AssetIn,
    AutoMaterializePolicy,
    DailyPartitionsDefinition,
    MetadataValue,
    Output,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)
import duckdb
import pandas as pd
from datetime import datetime, timedelta

# Define time partitions for our data
daily_partitions = DailyPartitionsDefinition(
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Source data asset
@asset(
    auto_materialize_policy=AutoMaterializePolicy.eager(),
    partitions_def=daily_partitions,
    metadata={
        "table": "raw_sales",
        "schema": "public",
        "description": "Raw sales data from source system"
    }
)
def raw_sales(context) -> Output[pd.DataFrame]:
    """Raw sales data ingested from source."""
    # In real implementation, this would read from your actual source
    # For demo, we'll generate sample data for the partition
    partition_date = context.partition_key
    
    # Generate sample data for this partition
    dates = pd.date_range(
        start=partition_date,
        end=pd.Timestamp(partition_date) + timedelta(days=1),
        freq='H'
    )
    
    df = pd.DataFrame({
        'sale_date': dates,
        'amount': np.random.randint(50, 500, size=len(dates)),
        'product_id': np.random.randint(1, 10, size=len(dates))
    })
    
    # Add metadata about the asset
    return Output(
        df,
        metadata={
            "row_count": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
            "schema": MetadataValue.json(df.dtypes.astype(str).to_dict())
        }
    )

# Transformed data asset
@asset(
    ins={"raw_sales": AssetIn()},
    partitions_def=daily_partitions,
    metadata={
        "table": "sales_daily",
        "schema": "analytics",
        "description": "Daily aggregated sales metrics"
    }
)
def sales_daily(context, raw_sales: pd.DataFrame) -> Output[pd.DataFrame]:
    """Daily sales aggregations."""
    # Perform aggregations
    daily_sales = raw_sales.groupby(
        pd.Grouper(key='sale_date', freq='D')
    ).agg({
        'amount': ['sum', 'count']
    }).reset_index()
    
    # Clean up column names
    daily_sales.columns = ['sale_date', 'daily_sales', 'transaction_count']
    
    # Add metadata about the transformation
    return Output(
        daily_sales,
        metadata={
            "row_count": len(daily_sales),
            "total_sales": float(daily_sales['daily_sales'].sum()),
            "total_transactions": int(daily_sales['transaction_count'].sum()),
            "preview": MetadataValue.md(daily_sales.head().to_markdown())
        }
    )

# Dashboard asset (using Rill)
@asset(
    ins={"sales_daily": AssetIn()},
    metadata={
        "dashboard": "sales_overview",
        "refresh_interval": "5m",
        "description": "Sales overview dashboard configuration"
    }
)
def sales_dashboard(context, sales_daily: pd.DataFrame) -> Output[dict]:
    """Generate dashboard configuration for Rill."""
    dashboard_config = {
        'title': 'Sales Overview',
        'metrics': [
            {
                'name': 'Total Sales',
                'query': 'SELECT SUM(daily_sales) FROM sales_daily',
                'format': '$,.2f'
            },
            {
                'name': 'Total Transactions',
                'query': 'SELECT SUM(transaction_count) FROM sales_daily',
                'format': ',d'
            }
        ],
        'charts': [
            {
                'name': 'Daily Sales Trend',
                'type': 'line',
                'query': 'SELECT sale_date, daily_sales FROM sales_daily ORDER BY sale_date'
            },
            {
                'name': 'Transaction Volume',
                'type': 'bar',
                'query': 'SELECT sale_date, transaction_count FROM sales_daily ORDER BY sale_date'
            }
        ]
    }
    
    # Export dashboard configuration
    return Output(
        dashboard_config,
        metadata={
            "preview": MetadataValue.json(dashboard_config),
            "metrics_count": len(dashboard_config['metrics']),
            "charts_count": len(dashboard_config['charts'])
        }
    )

# Define schedule to materialize assets daily
daily_refresh = ScheduleDefinition(
    job=define_asset_job("daily_refresh", selection="*"),
    cron_schedule="0 0 * * *",
    description="Refresh all assets daily"
)

# Define all assets and schedules
defs = Definitions(
    assets=[raw_sales, sales_daily, sales_dashboard],
    schedules=[daily_refresh]
)
