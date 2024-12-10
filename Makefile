.PHONY: all init update run clean

# Default environment
ENV ?= local

# Initialize project
init:
	ddse init covid-analysis

# Update configs
update:
	ddse update

# Run the stack
run:
	ddse run -e $(ENV)

# Clean generated files
clean:
	rm -rf transform/generated
	rm -rf serve/generated

# Install DDSE CLI (for development)
install-dev:
	cd engine-rust && cargo install --path .
