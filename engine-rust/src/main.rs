use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fs;
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
struct StackConfig {
    version: String,
    stack: Stack,
    ingestion: Ingestion,
    transformations: Vec<Transformation>,
    serving: Vec<Serving>,
    orchestration: Orchestration,
}

#[derive(Debug, Serialize, Deserialize)]
struct Stack {
    name: String,
    description: String,
    environment: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct Ingestion {
    sources: Vec<Source>,
}

#[derive(Debug, Serialize, Deserialize)]
struct Source {
    name: String,
    #[serde(rename = "type")]
    source_type: String,
    config: serde_yaml::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct Transformation {
    name: String,
    depends_on: Vec<String>,
    #[serde(rename = "type")]
    transform_type: String,
    config: serde_yaml::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct Serving {
    name: String,
    #[serde(rename = "type")]
    serving_type: String,
    template: String,
    data_sources: Vec<String>,
    config: serde_yaml::Value,
}

#[derive(Debug, Serialize, Deserialize)]
struct Orchestration {
    schedule: String,
    retries: i32,
    timeout: String,
    notifications: serde_yaml::Value,
}

// Tool-specific configuration generators
trait ConfigGenerator {
    fn generate_config(&self, config: &StackConfig) -> Result<String, Box<dyn Error>>;
}

struct SDFConfigGenerator;
struct RillConfigGenerator;

impl ConfigGenerator for SDFConfigGenerator {
    fn generate_config(&self, config: &StackConfig) -> Result<String, Box<dyn Error>> {
        // Convert ingestion and transformation configs to SDF format
        let sdf_config = serde_yaml::to_string(&json!({
            "version": "1.0",
            "sources": config.ingestion.sources,
            "transformations": config.transformations,
        }))?;
        Ok(sdf_config)
    }
}

impl ConfigGenerator for RillConfigGenerator {
    fn generate_config(&self, config: &StackConfig) -> Result<String, Box<dyn Error>> {
        // Convert serving configs to Rill format
        let rill_config = serde_yaml::to_string(&json!({
            "dashboards": config.serving,
        }))?;
        Ok(rill_config)
    }
}

// Main engine implementation
struct DeclarativeStackEngine {
    config: StackConfig,
    sdf_generator: SDFConfigGenerator,
    rill_generator: RillConfigGenerator,
}

impl DeclarativeStackEngine {
    fn new(config_path: &str) -> Result<Self, Box<dyn Error>> {
        let config_str = fs::read_to_string(config_path)?;
        let config: StackConfig = serde_yaml::from_str(&config_str)?;
        
        Ok(Self {
            config,
            sdf_generator: SDFConfigGenerator,
            rill_generator: RillConfigGenerator,
        })
    }

    fn update_downstream_configs(&self) -> Result<(), Box<dyn Error>> {
        // Generate and save SDF config
        let sdf_config = self.sdf_generator.generate_config(&self.config)?;
        fs::write("sdf/config.yml", sdf_config)?;

        // Generate and save Rill config
        let rill_config = self.rill_generator.generate_config(&self.config)?;
        fs::write("rill/config.yml", rill_config)?;

        Ok(())
    }

    fn run_pipeline(&self) -> Result<(), Box<dyn Error>> {
        // Execute SDF commands
        Command::new("sdf")
            .args(&["compile"])
            .status()?;

        Command::new("sdf")
            .args(&["run"])
            .status()?;

        // Start Rill server
        Command::new("rill")
            .args(&["start"])
            .status()?;

        Ok(())
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let engine = DeclarativeStackEngine::new("data-stack-config.yaml")?;
    
    // Parse command line arguments
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("update-configs") => engine.update_downstream_configs()?,
        Some("run") => engine.run_pipeline()?,
        _ => println!("Usage: {} <update-configs|run>", args[0]),
    }

    Ok(())
}
