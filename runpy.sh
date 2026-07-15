#!/bin/bash

python tx.py | \
    ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -
