# FastAPI Lambda Demo

The same three-page demo as `examples/aws_lambda/demo.spy`, but built with
CPython + FastAPI + Mangum and deployed on AWS Lambda.

[Mangum](https://mangum.fastapiexpert.com/) is a thin adapter that translates
Lambda's `(event, context)` invocation into ASGI, so any FastAPI (or Starlette)
app works without modification.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt uvicorn

uvicorn main:app --reload
# Open http://localhost:8000
```

## Deploy to AWS Lambda

### Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) installed and configured (`aws configure` or `aws sso login`)
- An AWS account with permission to create Lambda functions and IAM roles

### First deploy

Run the one-shot setup script. It creates the IAM role, packages the app,
creates the Lambda function, and attaches a public Function URL:

```bash
./aws_setup.sh
```

It prints the public URL when done.

### Subsequent deploys

After editing `main.py`, push the updated code with:

```bash
./aws_push.sh
```

### Configuration

Edit `_config.sh` to change the function name, region, memory, or timeout
before running either script. You can also override via environment variables:

```bash
FUNCTION_NAME=my-demo REGION=eu-west-1 ./aws_setup.sh
```

### Teardown

```bash
aws lambda delete-function --function-name fastapi-demo
aws lambda delete-function-url-config --function-name fastapi-demo
aws iam detach-role-policy \
  --role-name fastapi-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name fastapi-lambda-role
```

## Comparison with the SPy version

| | SPy (`demo.spy`) | FastAPI (`main.py`) |
|---|---|---|
| Runtime | Native binary (no interpreter) | CPython 3.12 |
| Cold-start overhead | ~0 ms | ~200–400 ms |
| Package size | ~2 MB | ~15 MB |
| Language | SPy (statically-typed Python dialect) | Standard Python |
| Framework | Custom `spyapi` | FastAPI + Mangum |
| Type safety | Compile-time | Runtime (Pydantic) |
