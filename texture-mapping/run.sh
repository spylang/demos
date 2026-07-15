#!/bin/bash
set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <variant> [extra args...]" >&2
    echo "Variants: py315, py315-jit, numpy, numba, pypy, spy" >&2
    exit 1
fi

variant="$1"
shift

FFPLAY=(ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -)

case "$variant" in
    py315)
        uv run --python 3.15 tx.py "$@" | "${FFPLAY[@]}"
        ;;
    py315-jit)
        PYTHON_JIT=1 uv run --python 3.15 tx.py "$@" | "${FFPLAY[@]}"
        ;;
    numpy)
        uv run --python 3.13 tx_numpy.py "$@" | "${FFPLAY[@]}"
        ;;
    numba)
        uv run --python 3.13 tx_numba.py "$@" | "${FFPLAY[@]}"
        ;;
    pypy)
        pypy tx.py "$@" | "${FFPLAY[@]}"
        ;;
    spy)
        spy build --release txspy.spy
        ./build/txspy "$@" | "${FFPLAY[@]}"
        ;;
    *)
        echo "Unknown variant: $variant" >&2
        echo "Variants: py315, py315-jit, numpy, numba, pypy, spy" >&2
        exit 1
        ;;
esac
