#!/usr/bin/env bash
# Benchmark SPy vs FastAPI Lambda: cold start, warm latency, throughput.
# Results are printed human-readably AND saved to $OUTPUT_JSON.
#
# Run from aws-lambda/ or via:  make benchmark
#
# Dependencies: aws CLI, hey (https://github.com/rakyll/hey)
#   Install hey: go install github.com/rakyll/hey@latest
#               or: brew install hey
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── config ─────────────────────────────────────────────────────────────────────
# Function names and region must match your _config.sh defaults.
# Override via environment variables if you used different names during setup.
SPY_FUNCTION="${SPY_FUNCTION:-spyapi-demo}"
FASTAPI_FUNCTION="${FASTAPI_FUNCTION:-fastapi-demo}"
REGION="${REGION:-us-east-1}"

WARMUP_N=10
THROUGHPUT_N=200
THROUGHPUT_C=20

OUTPUT_JSON="${OUTPUT_JSON:-$SCRIPT_DIR/benchmark_results.json}"

# ── helpers ────────────────────────────────────────────────────────────────────
HEY_TMP=$(mktemp)
trap 'rm -f "$HEY_TMP"' EXIT

hr()   { echo; printf '%.0s─' {1..60}; echo; }
info() { echo "  $*"; }

require() {
    command -v "$1" &>/dev/null || { echo "Error: '$1' not found. $2"; exit 1; }
}
require hey "Install: go install github.com/rakyll/hey@latest  or  brew install hey"

# ── fetch deployed URLs from AWS ───────────────────────────────────────────────
get_url() {
    local fn="$1"
    local url
    url=$(aws lambda get-function-url-config \
        --function-name "$fn" \
        --region "$REGION" \
        --query FunctionUrl --output text 2>/dev/null) || {
        echo "Error: no Function URL found for '$fn'." >&2
        echo "       Run 'make setup' (or 'make setup-spy' / 'make setup-fastapi') first." >&2
        exit 1
    }
    echo "$url"
}

echo
echo "==> Looking up Function URLs..."
SPY_URL=$(get_url "$SPY_FUNCTION")
FASTAPI_URL=$(get_url "$FASTAPI_FUNCTION")
info "SPy     ($SPY_FUNCTION):  $SPY_URL"
info "FastAPI ($FASTAPI_FUNCTION): $FASTAPI_URL"

s_to_ms() {
    # Convert a float-seconds string to milliseconds (2 decimal places).
    # Returns 0 if input is empty (hey omits some percentiles on small samples).
    [[ -z "$1" ]] && { echo "0"; return; }
    awk "BEGIN{printf \"%.2f\", $1 * 1000}"
}

force_cold_start() {
    local fn="$1"
    info "Forcing cold start for $fn..."
    aws lambda update-function-configuration \
        --function-name "$fn" \
        --environment "Variables={BENCH_TS=$(date +%s)}" \
        --region "$REGION" --output text --query 'LastUpdateStatus' > /dev/null
    aws lambda wait function-updated --function-name "$fn" --region "$REGION"
}

# Read $HEY_TMP and store parsed latency/throughput into prefixed global vars.
parse_hey() {
    local pfx="$1"
    local rps avg_s min_s max_s p50_s p95_s p99_s
    rps=$(awk   '/Requests\/sec:/{print $2}' "$HEY_TMP")
    avg_s=$(awk '/Average:/{print $2}'       "$HEY_TMP")
    min_s=$(awk '/Fastest:/{print $2}'       "$HEY_TMP")
    max_s=$(awk '/Slowest:/{print $2}'       "$HEY_TMP")
    # hey outputs "50%% in" (double-%) in its latency distribution section.
    p50_s=$(awk '/50%%/{print $3}'           "$HEY_TMP")
    p95_s=$(awk '/95%%/{print $3}'           "$HEY_TMP")
    p99_s=$(awk '/99%%/{print $3}'           "$HEY_TMP")

    printf -v "${pfx}_rps"    '%s' "$rps"
    printf -v "${pfx}_avg_ms" '%s' "$(s_to_ms "$avg_s")"
    printf -v "${pfx}_min_ms" '%s' "$(s_to_ms "$min_s")"
    printf -v "${pfx}_max_ms" '%s' "$(s_to_ms "$max_s")"
    printf -v "${pfx}_p50_ms" '%s' "$(s_to_ms "$p50_s")"
    printf -v "${pfx}_p95_ms" '%s' "$(s_to_ms "$p95_s")"
    printf -v "${pfx}_p99_ms" '%s' "$(s_to_ms "$p99_s")"
}

# Parse a "n=X min=X p50=X p95=X max=X avg=X" line into prefixed global vars.
parse_cw_line() {
    local pfx="$1" line="$2"
    printf -v "${pfx}_n"      '%s' "$(echo "$line" | grep -oP '^n=\K\d+'         || true)"
    printf -v "${pfx}_min_ms" '%s' "$(echo "$line" | grep -oP '(?<=min=)[\d.]+' || true)"
    printf -v "${pfx}_p50_ms" '%s' "$(echo "$line" | grep -oP '(?<=p50=)[\d.]+' || true)"
    printf -v "${pfx}_p95_ms" '%s' "$(echo "$line" | grep -oP '(?<=p95=)[\d.]+' || true)"
    printf -v "${pfx}_max_ms" '%s' "$(echo "$line" | grep -oP '(?<=max=)[\d.]+' || true)"
    printf -v "${pfx}_avg_ms" '%s' "$(echo "$line" | grep -oP '(?<=avg=)[\d.]+' || true)"
}

measure_cold_start() {
    local pfx="$1" fn="$2" url="$3"
    force_cold_start "$fn"

    info "Invoking (cold)..."
    local t0
    t0=$(date +%s%3N)
    curl -s -o /dev/null "$url"
    local wall=$(( $(date +%s%3N) - t0 ))

    sleep 5

    local report
    report=$(aws logs filter-log-events \
        --log-group-name "/aws/lambda/$fn" \
        --start-time $(( ($(date +%s) - 30) * 1000 )) \
        --filter-pattern "Init Duration" \
        --region "$REGION" \
        --query 'events[0].message' \
        --output text 2>/dev/null || echo "")

    local duration init_dur
    duration=$(echo "$report" | grep -oP '(?<=Duration: )\S+' | head -1 || true)
    init_dur=$(echo "$report" | grep -oP '(?<=Init Duration: )\S+' || true)

    echo "  Wall clock (client):  ${wall} ms"
    echo "  Init Duration (cold): ${init_dur:-n/a} ms   ← runtime + code init"
    echo "  Handler Duration:     ${duration:-n/a} ms   ← actual handler"

    printf -v "${pfx}_cold_wall_ms"    '%s' "${wall}"
    printf -v "${pfx}_cold_init_ms"    '%s' "${init_dur:-0}"
    printf -v "${pfx}_cold_handler_ms" '%s' "${duration:-0}"
}

measure_warm() {
    local pfx="$1" fn="$2" url="$3"

    info "Warming up ($WARMUP_N requests)..."
    for i in $(seq 1 $WARMUP_N); do curl -s -o /dev/null "$url"; done

    info "Measuring warm latency (sequential, 50 requests)..."
    hey -n 50 -c 1 "$url" > "$HEY_TMP" 2>/dev/null
    grep -E 'Average|Fastest|Slowest|Requests/sec' "$HEY_TMP" | sed 's/^/  /'
    parse_hey "${pfx}_warm"

    sleep 3
    info "Server-side Duration from CloudWatch (last 50 invocations):"
    local cw_line
    cw_line=$(aws logs filter-log-events \
        --log-group-name "/aws/lambda/$fn" \
        --start-time $(( ($(date +%s) - 120) * 1000 )) \
        --filter-pattern "REPORT RequestId" \
        --region "$REGION" \
        --query 'events[*].message' --output text 2>/dev/null \
    | grep -oP '(?<=\tDuration: )\S+' \
    | sort -n \
    | awk '
        BEGIN { sum=0; n=0 }
        { v[n++]=$1; sum+=$1 }
        END {
            if (n==0) { print "n=0 min=0 p50=0 p95=0 max=0 avg=0"; exit }
            printf "n=%d min=%.2f p50=%.2f p95=%.2f max=%.2f avg=%.2f\n",
                n, v[0], v[int(n*0.50)], v[int(n*0.95)], v[n-1], sum/n
        }')
    echo "  $cw_line"
    parse_cw_line "${pfx}_warm_cw" "$cw_line"
}

measure_throughput() {
    local pfx="$1" url="$2"
    info "Throughput: $THROUGHPUT_N requests, concurrency $THROUGHPUT_C..."
    hey -n "$THROUGHPUT_N" -c "$THROUGHPUT_C" "$url" > "$HEY_TMP" 2>/dev/null
    grep -E 'Requests/sec|Average|Fastest|Slowest|99%|95%|50%' "$HEY_TMP" | sed 's/^/  /'
    parse_hey "${pfx}_tput"
}

# ── main ───────────────────────────────────────────────────────────────────────
echo
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         SPy Native Binary  vs  FastAPI + CPython         ║"
echo "╚══════════════════════════════════════════════════════════╝"

hr
echo "COLD START"
hr
echo "[ SPy ($SPY_FUNCTION) ]"
measure_cold_start spy "$SPY_FUNCTION" "$SPY_URL"
echo
echo "[ FastAPI ($FASTAPI_FUNCTION) ]"
measure_cold_start fastapi "$FASTAPI_FUNCTION" "$FASTAPI_URL"

hr
echo "WARM LATENCY"
hr
echo "[ SPy ($SPY_FUNCTION) ]"
measure_warm spy "$SPY_FUNCTION" "$SPY_URL"
echo
echo "[ FastAPI ($FASTAPI_FUNCTION) ]"
measure_warm fastapi "$FASTAPI_FUNCTION" "$FASTAPI_URL"

hr
echo "THROUGHPUT (concurrency=$THROUGHPUT_C)"
hr
echo "[ SPy ($SPY_FUNCTION) ]"
measure_throughput spy "$SPY_URL"
echo
echo "[ FastAPI ($FASTAPI_FUNCTION) ]"
measure_throughput fastapi "$FASTAPI_URL"

hr

# ── write JSON ─────────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
python3 - <<EOF
import json

data = {
    "timestamp": "$TIMESTAMP",
    "config": {
        "throughput_n": $THROUGHPUT_N,
        "throughput_c": $THROUGHPUT_C,
        "warmup_n": $WARMUP_N,
    },
    "spy": {
        "function_name": "$SPY_FUNCTION",
        "cold_start": {
            "wall_ms":    $spy_cold_wall_ms,
            "init_ms":    $spy_cold_init_ms,
            "handler_ms": $spy_cold_handler_ms,
        },
        "warm_latency": {
            "client": {
                "avg_ms": $spy_warm_avg_ms,
                "min_ms": $spy_warm_min_ms,
                "max_ms": $spy_warm_max_ms,
                "p50_ms": $spy_warm_p50_ms,
                "p95_ms": $spy_warm_p95_ms,
                "p99_ms": $spy_warm_p99_ms,
            },
            "server": {
                "n":      $spy_warm_cw_n,
                "min_ms": $spy_warm_cw_min_ms,
                "p50_ms": $spy_warm_cw_p50_ms,
                "p95_ms": $spy_warm_cw_p95_ms,
                "max_ms": $spy_warm_cw_max_ms,
                "avg_ms": $spy_warm_cw_avg_ms,
            },
        },
        "throughput": {
            "requests_per_sec": $spy_tput_rps,
            "avg_ms": $spy_tput_avg_ms,
            "min_ms": $spy_tput_min_ms,
            "max_ms": $spy_tput_max_ms,
            "p50_ms": $spy_tput_p50_ms,
            "p95_ms": $spy_tput_p95_ms,
            "p99_ms": $spy_tput_p99_ms,
        },
    },
    "fastapi": {
        "function_name": "$FASTAPI_FUNCTION",
        "cold_start": {
            "wall_ms":    $fastapi_cold_wall_ms,
            "init_ms":    $fastapi_cold_init_ms,
            "handler_ms": $fastapi_cold_handler_ms,
        },
        "warm_latency": {
            "client": {
                "avg_ms": $fastapi_warm_avg_ms,
                "min_ms": $fastapi_warm_min_ms,
                "max_ms": $fastapi_warm_max_ms,
                "p50_ms": $fastapi_warm_p50_ms,
                "p95_ms": $fastapi_warm_p95_ms,
                "p99_ms": $fastapi_warm_p99_ms,
            },
            "server": {
                "n":      $fastapi_warm_cw_n,
                "min_ms": $fastapi_warm_cw_min_ms,
                "p50_ms": $fastapi_warm_cw_p50_ms,
                "p95_ms": $fastapi_warm_cw_p95_ms,
                "max_ms": $fastapi_warm_cw_max_ms,
                "avg_ms": $fastapi_warm_cw_avg_ms,
            },
        },
        "throughput": {
            "requests_per_sec": $fastapi_tput_rps,
            "avg_ms": $fastapi_tput_avg_ms,
            "min_ms": $fastapi_tput_min_ms,
            "max_ms": $fastapi_tput_max_ms,
            "p50_ms": $fastapi_tput_p50_ms,
            "p95_ms": $fastapi_tput_p95_ms,
            "p99_ms": $fastapi_tput_p99_ms,
        },
    },
}

with open("$OUTPUT_JSON", "w") as f:
    json.dump(data, f, indent=2)
print(f"Results saved to $OUTPUT_JSON")
EOF

echo "Done."
echo
