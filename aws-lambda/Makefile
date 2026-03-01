SHELL := bash

.PHONY: help setup setup-fastapi setup-spy push-fastapi push-spy \
        benchmark plot teardown teardown-fastapi teardown-spy

help: ## Show this help
	@printf "Usage: make <target>\n\nTargets:\n"
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile \
	    | awk -F':.*## ' '{printf "  %-20s %s\n", $$1, $$2}'

# ── setup ──────────────────────────────────────────────────────────────────────

setup: setup-fastapi setup-spy ## Create IAM roles + Lambda functions for both demos

setup-fastapi: ## Set up the FastAPI demo (IAM role + Lambda function + Function URL)
	bash fastapi-demo/aws_setup.sh

setup-spy: ## Set up the SPy demo (IAM role + Lambda function + Function URL)
	bash spyapi-demo/aws_setup.sh

# ── deploy ─────────────────────────────────────────────────────────────────────

push-fastapi: ## Build and deploy the FastAPI demo (re-run after editing main.py)
	bash fastapi-demo/aws_push.sh

push-spy: ## Build and deploy the SPy demo (re-run after editing demo.spy)
	bash spyapi-demo/aws_push.sh

# ── benchmark ──────────────────────────────────────────────────────────────────

benchmark: ## Run cold-start + warm-latency + throughput benchmark; saves benchmark_results.json
	bash benchmark.sh

plot: ## Plot benchmark_results.json → benchmark_results.png
	uv run plot_benchmark.py benchmark_results.json

# ── teardown ───────────────────────────────────────────────────────────────────

teardown: teardown-fastapi teardown-spy ## Delete both Lambda functions and their URLs

teardown-fastapi: ## Tear down the FastAPI demo
	bash fastapi-demo/aws_teardown.sh

teardown-spy: ## Tear down the SPy demo
	bash spyapi-demo/aws_teardown.sh
