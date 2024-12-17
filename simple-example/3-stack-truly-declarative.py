from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import yaml
import duckdb
import pandas as pd
from datetime import datetime
import numpy as np
from pathlib import Path

# Existing types from previous implementation...
class DataType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    TIMESTAMP = "timestamp"

# New visualization-specific types
class ChartType(Enum):
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    TABLE = "table"
    METRIC = "metric"

@dataclass
class Column:
    name: str
    type: DataType
    nullable: bool = True

@dataclass
class Schema:
    columns: List[Column]

@dataclass
class DataSource:
    name: str
    schema: Schema
    refresh_interval: str
    retention_period: str

@dataclass
class Transformation:
    name: str
    inputs: List[str]
    output: str
    schema: Schema
    aggregations: Optional[Dict[str, List[str]]] = None
    filters: Optional[Dict[str, Any]] = None
    joins: Optional[List[Dict[str, Any]]] = None

# New serving-related classes
@dataclass
class Metric:
    name: str
    query: str
    format: str = ",.0f"  # Python format string
    description: Optional[str] = None

@dataclass
class Chart:
    name: str
    type: ChartType
    query: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color_by: Optional[str] = None
    filters: Optional[List[Dict[str, Any]]] = None

@dataclass
class Dashboard:
    name: str
    metrics: List[Metric]
    charts: List[Chart]
    refresh_interval: str = "5m"
    access_roles: List[str] = None

@dataclass
class ServingLayer:
    dashboards: List[Dashboard]

@dataclass
class Pipeline:
    sources: List[DataSource]
    transformations: List[Transformation]
    serving: ServingLayer

    def validate(self) -> bool:
        """Validate the entire pipeline declaratively"""
        # Build and validate dependency graph
        dependency_graph = self._build_dependency_graph()
        if self._has_cycles(dependency_graph):
            raise ValueError("Pipeline contains cyclic dependencies")

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build a graph of dependencies between transformations"""
        graph = {}
        # Add all transformation outputs as nodes
        for transform in self.transformations:
            graph[transform.output] = []
        
        # Add edges for each input dependency
        for transform in self.transformations:
            for input_table in transform.inputs:
                if input_table not in graph:
                    graph[input_table] = []
                graph[input_table].append(transform.output)
        
        return graph

    def _has_cycles(self, graph: Dict[str, List[str]]) -> bool:
        """Check if the dependency graph has cycles using DFS"""
        visited = set()
        rec_stack = set()

        def is_cyclic_util(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if is_cyclic_util(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if is_cyclic_util(node):
                    return True
        return False
            
        for transform in self.transformations:
            self._validate_schema_compatibility(transform)
            
        # Validate serving layer
        self._validate_serving_layer()
        
        return True
    
    def _validate_serving_layer(self) -> None:
        """Validate that all queries in serving layer reference valid tables"""
        available_tables = {source.name for source in self.sources}
        available_tables.update(transform.output for transform in self.transformations)
        
        for dashboard in self.serving.dashboards:
            # Validate metrics
            for metric in dashboard.metrics:
                if not self._validate_query(metric.query, available_tables):
                    raise ValueError(f"Invalid query in metric {metric.name}")
            
            # Validate charts
            for chart in dashboard.charts:
                if not self._validate_query(chart.query, available_tables):
                    raise ValueError(f"Invalid query in chart {chart.name}")
    
    def _validate_query(self, query: str, available_tables: set) -> bool:
        """Simple validation that query only references available tables"""
        # This is a simplified validation - in practice you'd want to parse the SQL
        query_lower = query.lower()
        for table in available_tables:
            query_lower = query_lower.replace(table.lower(), '')
        
        # Check if any table-like words remain in FROM or JOIN clauses
        # This is a very simple check - in practice you'd want proper SQL parsing
        remaining_query = query_lower.split('from')[-1]
        suspicious_words = ['select', 'from', 'join']
        return not any(word in remaining_query for word in suspicious_words)

class DeclarativeEngine:
    """Engine that interprets and executes declarative specifications"""
    
    def __init__(self):
        self.conn = duckdb.connect(':memory:')
        
    def execute_pipeline(self, pipeline: Pipeline) -> None:
        """Execute complete pipeline including serving layer"""
        # Validate entire pipeline
        pipeline.validate()
        
        # Execute data pipeline
        self._execute_data_pipeline(pipeline)
        
        # Generate serving layer
        self._generate_serving_layer(pipeline.serving)
    
    def _execute_data_pipeline(self, pipeline: Pipeline) -> None:
        """Execute data ingestion and transformation"""
        # Create sources
        for source in pipeline.sources:
            self._create_source(source)
            
        # Execute transformations in dependency order
        ordered_transforms = self._topological_sort(pipeline)
        for transform in ordered_transforms:
            self._execute_transformation(transform)
    
    def _generate_serving_layer(self, serving: ServingLayer) -> None:
        """Generate dashboard configurations and assets"""
        output_dir = Path('dashboards')
        output_dir.mkdir(exist_ok=True)
        
        for dashboard in serving.dashboards:
            dashboard_config = self._generate_dashboard_config(dashboard)
            
            # Save dashboard configuration
            dashboard_path = output_dir / f"{dashboard.name.lower().replace(' ', '_')}.yaml"
            with open(dashboard_path, 'w') as f:
                yaml.dump(dashboard_config, f)
            
            # Execute and save metric values
            metric_values = self._compute_metrics(dashboard.metrics)
            metric_path = output_dir / f"{dashboard.name.lower().replace(' ', '_')}_metrics.yaml"
            with open(metric_path, 'w') as f:
                yaml.dump(metric_values, f)
    
    def _generate_dashboard_config(self, dashboard: Dashboard) -> dict:
        """Generate dashboard configuration"""
        return {
            'name': dashboard.name,
            'refresh_interval': dashboard.refresh_interval,
            'access_roles': dashboard.access_roles,
            'metrics': [
                {
                    'name': metric.name,
                    'description': metric.description,
                    'format': metric.format
                }
                for metric in dashboard.metrics
            ],
            'charts': [
                {
                    'name': chart.name,
                    'type': chart.type.value,
                    'x_axis': chart.x_axis,
                    'y_axis': chart.y_axis,
                    'color_by': chart.color_by,
                    'filters': chart.filters
                }
                for chart in dashboard.charts
            ]
        }
    
    def _compute_metrics(self, metrics: List[Metric]) -> dict:
        """Compute current values for all metrics"""
        values = {}
        for metric in metrics:
            try:
                result = self.conn.execute(metric.query).fetchone()[0]
                values[metric.name] = result
            except Exception as e:
                print(f"Error computing metric {metric.name}: {e}")
                values[metric.name] = None
        return values

# Example usage
def create_example_pipeline() -> Pipeline:
    """Create example pipeline with serving layer"""
    # Previous source and transformation definitions...
    sales_schema = Schema([
        Column("sale_date", DataType.TIMESTAMP),
        Column("amount", DataType.FLOAT),
        Column("product_id", DataType.INTEGER)
    ])
    
    sales_source = DataSource(
        name="raw_sales",
        schema=sales_schema,
        refresh_interval="1h",
        retention_period="1y"
    )
    
    daily_sales_schema = Schema([
        Column("sale_date", DataType.TIMESTAMP),
        Column("daily_sales", DataType.FLOAT),
        Column("transaction_count", DataType.INTEGER)
    ])
    
    daily_sales_transform = Transformation(
        name="daily_sales_transform",
        inputs=["raw_sales"],
        output="sales_daily",
        schema=daily_sales_schema,
        aggregations={
            "sum": ["amount"],
            "count": ["*"]
        }
    )
    
    # Define serving layer
    sales_dashboard = Dashboard(
        name="Sales Overview",
        metrics=[
            Metric(
                name="Total Sales",
                query="SELECT SUM(daily_sales) FROM sales_daily",
                format="$,.2f",
                description="Total sales across all time"
            ),
            Metric(
                name="Total Transactions",
                query="SELECT SUM(transaction_count) FROM sales_daily",
                format=",d",
                description="Total number of transactions"
            )
        ],
        charts=[
            Chart(
                name="Daily Sales Trend",
                type=ChartType.LINE,
                query="SELECT sale_date, daily_sales FROM sales_daily ORDER BY sale_date",
                x_axis="sale_date",
                y_axis="daily_sales"
            ),
            Chart(
                name="Transaction Volume",
                type=ChartType.BAR,
                query="SELECT sale_date, transaction_count FROM sales_daily ORDER BY sale_date",
                x_axis="sale_date",
                y_axis="transaction_count"
            )
        ],
        refresh_interval="5m",
        access_roles=["analyst", "manager"]
    )
    
    serving_layer = ServingLayer(dashboards=[sales_dashboard])
    
    return Pipeline(
        sources=[sales_source],
        transformations=[daily_sales_transform],
        serving=serving_layer
    )

if __name__ == "__main__":
    # Create and execute pipeline
    pipeline = create_example_pipeline()
    
    engine = DeclarativeEngine()
    engine.execute_pipeline(pipeline)
    
    # Show results
    print("\nTransformed Data Sample:")
    print(engine.conn.execute("SELECT * FROM sales_daily LIMIT 5").fetchdf())
    
    print("\nDashboard files generated in ./dashboards/")
