#!/bin/bash

spy build --release -x txspy.spy | \
    ffplay -loglevel error -autoexit -f image2pipe -vcodec ppm -i -
