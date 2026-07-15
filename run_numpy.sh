#!/bin/bash

python tx_numpy.py | \
    ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -
