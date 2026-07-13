#!/bin/bash

python txpypy.py | \
    ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -
