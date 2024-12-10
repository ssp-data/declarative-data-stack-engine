.DEFAULT_GOAL := run

.PHONY: all build test update-dds run clean

auth: #use name in ~/.aws/credentials (default is the default :)
	sdf auth login aws --profile default
	sdf auth login aws --profile default --default-region us-east-2

clean:
	sdf clean

compile:
	sdf compile -e remote --show all

run:
	sdf run -e remote --show all


clean-run: clean compile run
