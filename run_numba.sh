#!/bin/bash

python tx_numba.py | \
    ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -
