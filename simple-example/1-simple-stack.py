import duckdb
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

class SimpleDataStack:
    def __init__(self):
        self.conn = duckdb.connect(':memory:')  # Use in-memory database for simplicity
        
    def _create_sample_data(self):
        # Create sample sales data
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='h')
        sales_data = pd.DataFrame({
            'sale_date': dates,
            'amount': np.random.randint(50, 500, size=len(dates)),
            'product_id': np.random.randint(1, 10, size=len(dates))
        })
        return sales_data
        
    def ingest(self):
        # Create sample data and load it directly
        sales_data = self._create_sample_data()
        self.conn.execute("CREATE TABLE raw_sales AS SELECT * FROM sales_data")
        print("Ingested sample sales data")
        
    def transform(self):
        self.conn.execute("""
            CREATE OR REPLACE TABLE sales_daily AS
            SELECT 
                date_trunc('day', sale_date) as sale_date,
                SUM(amount) as daily_sales,
                COUNT(*) as transaction_count
            FROM raw_sales
            GROUP BY 1
            ORDER BY 1
        """)
        print("Transformed data into daily sales aggregates")
        
    def serve(self):
        # Hardcoded dashboard config
        dashboard_config = {
            'title': 'Sales Dashboard',
            'charts': [{
                'name': 'Daily Sales',
                'query': 'SELECT * FROM sales_daily ORDER BY sale_date'
            }]
        }
        
        output_dir = Path('dashboards')
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / 'dashboard.yaml', 'w') as f:
            yaml.dump(dashboard_config, f)
        print("Created dashboard configuration")
        
        # Display sample results
        result = self.conn.execute("SELECT * FROM sales_daily LIMIT 5").fetchdf()
        print("\nSample results:")
        print(result)

class TemplateDataStack:
    def __init__(self, config_path: str):
        self.conn = duckdb.connect(':memory:')  # Use in-memory database
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def _create_sample_data(self):
        # Create sample sales data
        dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='h')
        sales_data = pd.DataFrame({
            'sale_date': dates,
            'amount': np.random.randint(50, 500, size=len(dates)),
            'product_id': np.random.randint(1, 10, size=len(dates))
        })
        return sales_data
    
    def ingest(self):
        sales_data = self._create_sample_data()
        
        for source in self.config['sources']:
            table_name = source['table']
            # Load sample data directly into table
            self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM sales_data")
            print(f"Created and populated table: {table_name}")
    
    def transform(self):
        for transform in self.config['transformations']:
            table_name = transform['output_table']
            group_by = transform.get('group_by', [])
            metrics = transform['metrics']
            source_table = transform['source_table']
            
            # Build dynamic query
            select_parts = []
            for col in group_by:
                select_parts.append(col)
            for metric in metrics:
                select_parts.append(f"{metric['agg']}({metric['column']}) as {metric['name']}")
                
            query = f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT {', '.join(select_parts)}
                FROM {source_table}
                {f"GROUP BY {', '.join(str(i+1) for i in range(len(group_by)))}" if group_by else ''}
                ORDER BY {group_by[0] if group_by else '1'}
            """
            self.conn.execute(query)
            print(f"Created transformed table: {table_name}")
            
            # Display sample results
            result = self.conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchdf()
            print(f"\nSample results from {table_name}:")
            print(result)
    
    def serve(self):
        dashboard_config = {
            'title': self.config['dashboard']['title'],
            'charts': []
        }
        
        for viz in self.config['dashboard']['visualizations']:
            dashboard_config['charts'].append({
                'name': viz['title'],
                'query': viz['query'],
                'type': viz['type']
            })
            
        output_path = Path(self.config['dashboard']['output_path'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(dashboard_config, f)
        print(f"Created dashboard configuration at {output_path}")

# Example config for template-based approach
example_config = """
sources:
  - table: raw_sales
    
transformations:
  - output_table: sales_daily
    source_table: raw_sales
    group_by: 
      - "date_trunc('day', sale_date)"
    metrics:
      - name: daily_sales
        column: amount
        agg: SUM
      - name: transaction_count
        column: '*'
        agg: COUNT

dashboard:
  title: Sales Analytics
  output_path: dashboards/sales_dashboard.yaml
  visualizations:
    - title: Daily Sales Trend
      type: line
      query: SELECT * FROM sales_daily ORDER BY sale_date
    - title: Transaction Volume
      type: bar
      query: SELECT sale_date, transaction_count FROM sales_daily
"""

def run_constant_stack():
    print("\n=== Running Constant Stack ===")
    stack = SimpleDataStack()
    stack.ingest()
    stack.transform()
    stack.serve()

def run_template_stack():
    print("\n=== Running Template Stack ===")
    # Save example config
    config_dir = Path('config')
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / 'stack_config.yaml'
    
    with open(config_path, 'w') as f:
        f.write(example_config)
    print(f"Created config file at {config_path}")
    
    # Run stack with config
    stack = TemplateDataStack(config_path)
    stack.ingest()
    stack.transform()
    stack.serve()

if __name__ == "__main__":
    import numpy as np  # Added import for random data generation
    
    # Create necessary directories
    Path('dashboards').mkdir(exist_ok=True)
    
    # Run both implementations
    run_constant_stack()
    run_template_stack()
