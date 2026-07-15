# Texture mapping like it's 1995 in python

This code repo is for a talk I gave to PyconIT 2026 in Bologna at end of May 2026.

## txmap-in-numpy.pdf / txmap-in-numpy.with-images.html

Slides used for the presentation. The HTML file can be navigated using arrows (up/down for first/last and left/right for prev/next)

## tx.py

This is the code described in the presentation; starts in numpy-accelerated mode and
pressing `p` switches to pure python or back to accelerated mode.
Requires `numpy` and `pygame` installed.

## txpypy.py

This is a pure python implementation using a slightly different algorithm as it's based on array.array mono-dimensional buffers.

This code use no external dependencies but calls `ffmpeg` at runtime for reading the texture images and calls `ffplay` for doing the rendering. I used this version to show pypy and sPy speed during the presentation.

## Speed statistics

Every second both programs display a time in millisecond for the pure computation part and a frames-per-second that also includes presentation of the result.

## Portability

I only tested on linux 24.04 (old, I know), but other OSs should require little changes.
