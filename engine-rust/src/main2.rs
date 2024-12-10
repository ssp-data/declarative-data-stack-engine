use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};
use std::fs;
use anyhow::Result;

#[derive(Parser)]
#[command(name = "ddse")]
#[command(about = "Declarative Data Stack Engine CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize a new data stack project
    Init {
        /// Project name
        name: String,
    },
    /// Update downstream configs from data-stack-config.yaml
    Update {
        /// Path to config file
        #[arg(default_value = "data-stack-config.yaml")]
        config: PathBuf,
    },
    /// Run the entire stack
    Run {
        /// Environment to run in
        #[arg(short, long, default_value = "local")]
        environment: String,
    },
    /// Generate boilerplate for a new component
    Generate {
        #[command(subcommand)]
        component: GenerateCommands,
    },
}

#[derive(Subcommand)]
enum GenerateCommands {
    Transform { name: String },
    Serve { name: String },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Init { name } => init_project(&name),
        Commands::Update { config } => update_configs(&config),
        Commands::Run { environment } => run_stack(&environment),
        Commands::Generate { component } => match component {
            GenerateCommands::Transform { name } => generate_transform(&name),
            GenerateCommands::Serve { name } => generate_serve(&name),
        },
    }
}

fn init_project(name: &str) -> Result<()> {
    // Create project structure
    let dirs = [
        "transform/core",
        "transform/mart",
        "transform/stage",
        "serve/dashboards",
        "serve/metrics",
        "serve/models",
        "orchestration",
    ];

    for dir in dirs {
        fs::create_dir_all(format!("{}/{}", name, dir))?;
    }

    // Create default config
    let default_config = include_str!("../templates/default-config.yaml");
    fs::write(
        format!("{}/data-stack-config.yaml", name),
        default_config,
    )?;

    // Create Makefile
    let makefile = include_str!("../templates/Makefile");
    fs::write(format!("{}/Makefile", name), makefile)?;

    println!("✨ Created new data stack project: {}", name);
    Ok(())
}

fn update_configs(config_path: &Path) -> Result<()> {
    // Read main config
    let config: StackConfig = serde_yaml::from_str(&fs::read_to_string(config_path)?)?;

    // Update transform configs
    update_transform_configs(&config)?;

    // Update serve configs
    update_serve_configs(&config)?;

    println!("📦 Updated all downstream configs");
    Ok(())
}

fn run_stack(environment: &str) -> Result<()> {
    // Run transform
    println!("🔄 Running transformations...");
    std::process::Command::new("sdf")
        .args(&["run", "-e", environment, "--show", "all"])
        .status()?;

    // Run serve
    println!("🚀 Starting Rill...");
    std::process::Command::new("rill")
        .args(&["start"])
        .status()?;

    Ok(())
}

// Helper functions for config management omitted for brevity...
