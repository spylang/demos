#!/usr/bin/env bash
# Package and deploy updated code to Lambda.
# Flags (used internally by aws_setup.sh):
#   --package-only   build function.zip but don't push
#   --deploy-only    push existing function.zip without rebuilding
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_config.sh"

PACKAGE_ONLY=false
DEPLOY_ONLY=false
for arg in "$@"; do
    case $arg in
        --package-only) PACKAGE_ONLY=true ;;
        --deploy-only)  DEPLOY_ONLY=true ;;
    esac
done

# ── package ───────────────────────────────────────────────────────────────────
if ! $DEPLOY_ONLY; then
    echo "==> Packaging"

    PACKAGE_DIR="$SCRIPT_DIR/.package"
    rm -rf "$PACKAGE_DIR"
    mkdir -p "$PACKAGE_DIR"

    echo "  Installing dependencies..."
    pip install -q -r "$SCRIPT_DIR/requirements.txt" -t "$PACKAGE_DIR"

    cp "$SCRIPT_DIR/main.py" "$PACKAGE_DIR/"

    echo "  Zipping..."
    (cd "$PACKAGE_DIR" && zip -q -r "$SCRIPT_DIR/function.zip" .)

    SIZE=$(du -sh "$SCRIPT_DIR/function.zip" | cut -f1)
    echo "✓ function.zip ready ($SIZE)"
fi

$PACKAGE_ONLY && exit 0

# ── deploy ────────────────────────────────────────────────────────────────────
echo
echo "==> Deploying"

if ! aws lambda get-function --function-name "$FUNCTION_NAME" \
        --region "$REGION" &>/dev/null; then
    echo "Error: function '$FUNCTION_NAME' does not exist." >&2
    echo "Run aws_setup.sh first." >&2
    exit 1
fi

echo "  Uploading function.zip..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://"$SCRIPT_DIR/function.zip" \
    --region "$REGION" \
    --output text --query 'CodeSize' > /dev/null

echo "  Waiting for update to complete..."
aws lambda wait function-updated \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION"

URL=$(aws lambda get-function-url-config \
    --function-name "$FUNCTION_NAME" \
    --region "$REGION" \
    --query FunctionUrl --output text 2>/dev/null || echo "(no Function URL configured)")

echo
echo "✓ Deploy complete!"
echo
echo "  URL: $URL"
echo
