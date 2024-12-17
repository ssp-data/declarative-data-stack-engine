# Declarative Data Stack Engine

This is the implementation from the article of [The Rise of the Declarative Data Stack](https://www.rilldata.com/blog/the-rise-of-the-declarative-data-stack) and the code for [Part 3]().

> **Info**: Most of this code is work in progress, and is to illustrate how a declarative data stack and its engine could be build.

## Structure and folders of this project

This project is work in progress. In `simple-example` we have different levels of declarative data stack, from super simple to one that uses dagster as the engine.

`ddse` is a start of declarative data stack "engine" with rust. 

The root folders with `serve`, `transform` is a example data stack with SDF and Rill. `data-stack-config.yaml` is an example declarative file that defines a full data stack, where I built ddse against.
