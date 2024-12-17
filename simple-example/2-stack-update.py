from typing import Dict, List, Optional
import duckdb
import yaml
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
from abc import ABC, abstractmethod

class DataSource(ABC):
    """Abstract base class for data sources"""
    @abstractmethod
    def get_schema(self) -> Dict:
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        pass

class Transform(ABC):
    """Abstract base class for transformations"""
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        pass

    @abstractmethod
    def validate(self) -> bool:
        pass

class DeclarativeStack:
    """
    Enhanced declarative stack addressing feedback:
    1. Continuous updates vs one-time generation
    2. True declarative interface
    3. Better testing support
    """
    def __init__(self, config_path: str):
        self.conn = duckdb.connect(':memory:')
        self.config = self._load_config(config_path)
        self.state_manager = StateManager()
        self.dependency_graph = DependencyGraph()
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path) as f:
            config = yaml.safe_load(f)
            self._validate_config(config)
            return config
            
    def _validate_config(self, config: dict) -> None:
        """Validate configuration schema and dependencies"""
        required_keys = ['sources', 'transformations', 'dashboard']
        if not all(key in config for key in required_keys):
            raise ValueError(f"Config must contain: {required_keys}")
            
    def watch_for_changes(self):
        """Set up continuous monitoring of config and data changes"""
        self.state_manager.register_callback(self.update_stack)
        
    def update_stack(self, changes: Dict):
        """Handle continuous updates based on changes"""
        if 'config' in changes:
            self._update_config(changes['config'])
        if 'data' in changes:
            self._refresh_data(changes['data'])
            
    def _update_config(self, config_changes: Dict):
        """Update stack configuration without full regeneration"""
        for change in config_changes:
            if change['type'] == 'source':
                self._update_source(change)
            elif change['type'] == 'transform':
                self._update_transform(change)
                
    def _refresh_data(self, data_changes: List[str]):
        """Refresh data for affected tables"""
        affected_tables = self.dependency_graph.get_affected_tables(data_changes)
        for table in affected_tables:
            self._refresh_table(table)

class StateManager:
    """Manages the state of the data stack"""
    def __init__(self):
        self.state = {}
        self.callbacks = []
        
    def register_callback(self, callback):
        self.callbacks.append(callback)
        
    def update_state(self, changes: Dict):
        """Update state and notify callbacks"""
        self.state.update(changes)
        for callback in self.callbacks:
            callback(changes)

class DependencyGraph:
    """Manages dependencies between data objects"""
    def __init__(self):
        self.dependencies = {}
        
    def add_dependency(self, source: str, target: str):
        if source not in self.dependencies:
            self.dependencies[source] = set()
        self.dependencies[source].add(target)
        
    def get_affected_tables(self, changed_tables: List[str]) -> List[str]:
        """Get all tables affected by changes"""
        affected = set(changed_tables)
        for table in changed_tables:
            affected.update(self._get_descendants(table))
        return list(affected)
        
    def _get_descendants(self, node: str) -> set:
        """Get all descendants of a node"""
        descendants = set()
        if node in self.dependencies:
            for child in self.dependencies[node]:
                descendants.add(child)
                descendants.update(self._get_descendants(child))
        return descendants

class TestManager:
    """Manages test cases and validation"""
    def __init__(self, stack: DeclarativeStack):
        self.stack = stack
        self.test_cases = {}
        
    def add_test_case(self, name: str, input_data: Dict, expected_output: Dict):
        """Add a test case"""
        self.test_cases[name] = {
            'input': input_data,
            'expected': expected_output
        }
        
    def run_tests(self) -> Dict:
        """Run all test cases"""
        results = {}
        for name, case in self.test_cases.items():
            results[name] = self._run_test(case)
        return results
        
    def _run_test(self, case: Dict) -> Dict:
        """Run a single test case"""
        # Implementation details for test execution
        pass

def example_usage():
    # Initialize stack with continuous update support
    stack = DeclarativeStack('stack_config.yaml')
    stack.watch_for_changes()
    
    # Set up test cases
    test_manager = TestManager(stack)
    test_manager.add_test_case(
        name="daily_sales_test",
        input_data={
            "raw_sales": [
                {"sale_date": "2024-01-01", "amount": 100},
                {"sale_date": "2024-01-01", "amount": 200}
            ]
        },
        expected_output={
            "sales_daily": [
                {"sale_date": "2024-01-01", "daily_sales": 300, "transaction_count": 2}
            ]
        }
    )
    
    # Run tests
    test_results = test_manager.run_tests()
    print("Test Results:", test_results)

if __name__ == "__main__":
    example_usage()
