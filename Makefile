.DEFAULT_GOAL := dagster-run


.PHONY: all build test update-dds run clean


sdf-auth:
	sdf auth login aws --profile default
	sdf auth login aws --profile default --default-region us-east-2

sdf-run:
	sdf run -e remote --show all


# Build the Rust engine
build:
	cargo build --release

# Update downstream configurations
update-dds: build
	./target/release/declarative-stack-engine update-configs

# Run tests
test: build
	sdf test

# Run the complete pipeline
run: update-dds
	./target/release/declarative-stack-engine run

# Clean build artifacts
clean:
	cargo clean
	rm -f sdf/config.yml
	rm -f rill/config.yml

###############################################3333
dagster-run:
	DAGSTER_SDF_COMPILE_ON_LOAD=1 dagster dev

install-sdf:
	curl -LSfs https://cdn.sdf.com/releases/download/install.sh | bash -s --

update-sdf:
	curl -LSfs https://cdn.sdf.com/releases/download/install.sh | bash -s -- --update

check-lineage:
	sdf dbt refresh
	sdf compile
	sdf lineage
