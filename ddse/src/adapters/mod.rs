use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use anyhow::Result;

// Generic transformation config that tools will implement
#[derive(Debug, Serialize, Deserialize)]
pub struct TransformationConfig {
    name: String,
    depends_on: Vec<String>,
    columns: Vec<Column>,
    aggregations: Vec<Aggregation>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Column {
    name: String,
    data_type: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Aggregation {
    column: String,
    function: String,
}

// Tool adapter trait
#[async_trait]
pub trait TransformationTool {
    async fn generate_config(&self, config: &TransformationConfig) -> Result<String>;
    async fn validate(&self) -> Result<()>;
    async fn execute(&self) -> Result<()>;
}

// SDF Implementation
pub struct SdfAdapter {
    workspace_path: String,
}

#[async_trait]
impl TransformationTool for SdfAdapter {
    async fn generate_config(&self, config: &TransformationConfig) -> Result<String> {
        // Convert generic config to SDF workspace.sdf.yml format
        let sdf_config = serde_yaml::to_string(&json!({
            "workspace": {
                "name": config.name,
                "dependencies": config.depends_on,
                "transformations": {
                    config.name: {
                        "columns": config.columns,
                        "aggregations": config.aggregations,
                    }
                }
            }
        }))?;
        Ok(sdf_config)
    }

    async fn validate(&self) -> Result<()> {
        std::process::Command::new("sdf")
            .args(&["check"])
            .status()?;
        Ok(())
    }

    async fn execute(&self) -> Result<()> {
        std::process::Command::new("sdf")
            .args(&["run", "-e", "remote", "--show", "all"])
            .status()?;
        Ok(())
    }
}

// dbt Implementation
pub struct DbtAdapter {
    project_path: String,
}

#[async_trait]
impl TransformationTool for DbtAdapter {
    async fn generate_config(&self, config: &TransformationConfig) -> Result<String> {
        // Convert generic config to dbt model format
        let dbt_model = format!(
            r#"
            {{{{ config(
                materialized='table',
                depends_on=[{}]
            ) }}}}

            SELECT 
                {}
            FROM source_table
            GROUP BY {}
            "#,
            config.depends_on.join(", "),
            config.aggregations.iter()
                .map(|agg| format!("{}({}) as {}", agg.function, agg.column, agg.column))
                .collect::<Vec<_>>()
                .join(",\n    "),
            config.columns.iter()
                .map(|col| col.name.clone())
                .collect::<Vec<_>>()
                .join(", ")
        );
        Ok(dbt_model)
    }

    async fn validate(&self) -> Result<()> {
        std::process::Command::new("dbt")
            .args(&["compile"])
            .status()?;
        Ok(())
    }

    async fn execute(&self) -> Result<()> {
        std::process::Command::new("dbt")
            .args(&["run"])
            .status()?;
        Ok(())
    }
}

// Factory to create the right adapter based on config
pub fn create_transformation_tool(tool_type: &str, config: &ToolConfig) -> Box<dyn TransformationTool> {
    match tool_type {
        "sdf" => Box::new(SdfAdapter {
            workspace_path: config.path.clone(),
        }),
        "dbt" => Box::new(DbtAdapter {
            project_path: config.path.clone(),
        }),
        _ => panic!("Unsupported transformation tool"),
    }
}
