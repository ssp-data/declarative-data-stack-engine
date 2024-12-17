use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

// Core types that represent our DSL
#[derive(Debug, Serialize, Deserialize)]
struct DataStack {
    ingest: IngestConfig,
    transform: TransformConfig,
    serve: ServeConfig,
}

#[derive(Debug, Serialize, Deserialize)]
struct IngestConfig {
    source: String,
    query: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct TransformConfig {
    groupby: Vec<String>,
    aggregate: std::collections::HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ServeConfig {
    template: String,
}

// Tool-specific adapters
trait ToolAdapter {
    fn validate(&self) -> Result<()>;
    fn execute(&self) -> Result<()>;
}

struct SDFAdapter {
    config_path: PathBuf,
}

impl ToolAdapter for SDFAdapter {
    fn validate(&self) -> Result<()> {
        println!("Validating SDF configuration...");
        std::process::Command::new("sdf")
            .args(&["check"])
            .status()
            .context("Failed to validate SDF config")?;
        Ok(())
    }

    fn execute(&self) -> Result<()> {
        println!("Executing SDF transformations...");
        std::process::Command::new("sdf")
            .args(&["run", "-e", "remote", "--show", "all"])
            .status()
            .context("Failed to run SDF")?;
        Ok(())
    }
}

struct RillAdapter {
    config_path: PathBuf,
}

impl ToolAdapter for RillAdapter {
    fn validate(&self) -> Result<()> {
        println!("Validating Rill configuration...");
        // Add Rill-specific validation
        Ok(())
    }

    fn execute(&self) -> Result<()> {
        println!("Starting Rill server...");
        std::process::Command::new("rill")
            .args(&["start"])
            .status()
            .context("Failed to start Rill")?;
        Ok(())
    }
}

// The main engine that coordinates everything
struct DeclarativeEngine {
    transform_adapter: SDFAdapter,
    serve_adapter: RillAdapter,
}

impl DeclarativeEngine {
    fn new() -> Self {
        Self {
            transform_adapter: SDFAdapter {
                config_path: PathBuf::from("transform/workspace.sdf.yml"),
            },
            serve_adapter: RillAdapter {
                config_path: PathBuf::from("serve/rill.yaml"),
            },
        }
    }

    // DSL-like interface
    fn run_stack(&self, stack: DataStack) -> Result<()> {
        self.validate(&stack)?;
        self.execute(&stack)
    }

    fn validate(&self, stack: &DataStack) -> Result<()> {
        self.transform_adapter.validate()?;
        self.serve_adapter.validate()?;
        Ok(())
    }

    fn execute(&self, stack: &DataStack) -> Result<()> {
        self.transform_adapter.execute()?;
        self.serve_adapter.execute()?;
        Ok(())
    }
}

// CLI interface
#[derive(clap::Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(clap::Subcommand)]
enum Commands {
    /// Run the stack with an inline configuration
    Run {
        #[arg(short, long)]
        config: Option<PathBuf>,
    },
    /// Run the stack using DSL syntax
    RunDsl {
        #[arg(short, long)]
        expression: String,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let engine = DeclarativeEngine::new();

    match cli.command {
        Commands::Run { config } => {
            let config_path = config.unwrap_or_else(|| PathBuf::from("data-stack-config.yaml"));
            let stack: DataStack = serde_yaml::from_reader(std::fs::File::open(config_path)?)?;
            engine.run_stack(stack)
        }
        Commands::RunDsl { expression } => {
            // Parse DSL expression and convert to DataStack
            let stack = parse_dsl_expression(&expression)?;
            engine.run_stack(stack)
        }
    }
}

// DSL parser (simplified example)
fn parse_dsl_expression(expression: &str) -> Result<DataStack> {
    // This is a simplified example - you'd want to implement a proper parser
    // Convert DSL syntax into DataStack struct
    Ok(DataStack {
        ingest: IngestConfig {
            source: "duckdb".to_string(),
            query: "SELECT * FROM covid_data".to_string(),
        },
        transform: TransformConfig {
            groupby: vec!["country".to_string()],
            aggregate: [
                ("cases".to_string(), "sum".to_string()),
                ("deaths".to_string(), "sum".to_string()),
            ]
            .into_iter()
            .collect(),
        },
        serve: ServeConfig {
            template: "github://covid/covid_dashboard.md".to_string(),
        },
    })
}
