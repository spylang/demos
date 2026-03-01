# Deployment instructions

**WARNING**: this document has been entirely written by AI.

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
  installed and configured (`aws configure` or `aws sso login`)
- An AWS account with permission to create Lambda functions and IAM roles
- [hey](https://github.com/rakyll/hey) for the benchmark
  (`go install github.com/rakyll/hey@latest` or `brew install hey`)
- Python 3 with `matplotlib` and `numpy` for plotting

## Quickstart

```bash
# 1. Deploy both demos
make setup

# 2. Run the benchmark
make benchmark

# 3. Plot the results
make plot
```

## All commands

```
make setup           Create IAM roles + Lambda functions for both demos
make setup-fastapi   Set up the FastAPI demo only
make setup-spy       Set up the SPy demo only

make push-fastapi    Build and deploy the FastAPI demo (after editing main.py)
make push-spy        Build and deploy the SPy demo (after editing demo.spy)

make benchmark       Run cold-start + warm-latency + throughput benchmark
make plot            Plot benchmark_results.json → benchmark_results.png

make teardown        Delete both Lambda functions and their URLs
make teardown-fastapi
make teardown-spy
```

Run `make help` to see the same list at any time.

## Configuration

Function names and region default to the values in each demo's `_config.sh`.
Override via environment variables:

```bash
# Use a different region
REGION=eu-west-1 make setup

# Use different function names for the benchmark
SPY_FUNCTION=my-spy FASTAPI_FUNCTION=my-fastapi make benchmark
```

## Project layout

```
aws-lambda/
├── Makefile                  top-level entry point
├── benchmark.sh              benchmarks both deployed functions
├── plot_benchmark.py         plots benchmark_results.json → .png
├── fastapi-demo/             CPython + FastAPI + Mangum
│   ├── _config.sh            function name, region, memory, timeout
│   ├── aws_setup.sh          one-shot deploy (IAM + Lambda + Function URL)
│   ├── aws_push.sh           incremental redeploy
│   ├── aws_teardown.sh       delete function + URL
│   └── main.py               FastAPI app
└── spyapi-demo/              SPy compiled to a native binary
    ├── _config.sh
    ├── aws_setup.sh
    ├── aws_push.sh
    ├── aws_teardown.sh
    └── demo.spy              SPy source
```
