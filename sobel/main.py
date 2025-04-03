# /// script
# dependencies = [
#   "numpy",
#   "opencv-python",
# ]
# ///

import cv2
import numpy as np
import array
import argparse
import sys
import time
from collections import deque

#from _sobel_cython import sobel
#from _sobel_python import sobel
import _sobel_spy

def sobel(frame, output):
    # temporary hack: the spy version expects a 2d grayscale, not a 3d RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = frame.shape
    ptr_frame = _sobel_spy.ffi.from_buffer(frame)
    ptr_output = _sobel_spy.ffi.from_buffer(output)
    _sobel_spy.lib.sobel(ptr_frame, w, h, ptr_output)


def read_frames(source):
    """Read frames from webcam or video file."""
    if source.isdigit():
        cap = cv2.VideoCapture(int(source))
    else:
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        sys.exit(f"Error: Could not open {source}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ## width = 80
    ## height = 60

    output = np.empty((height, width, 3), dtype=np.uint8)

    # create the output window and initialize the videosource outside the
    # loop, to avoid polluting FPS computation
    cv2.imshow('Original | Processed', output)
    ret, frame = cap.read()
    assert ret

    try:
        # Setup for FPS calculation
        fps_counter = deque(maxlen=30)  # for moving average
        start_time = time.time()
        frame_count = 0

        last_time = time.time()
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            #frame = cv2.resize(frame, (width, height))
            sobel(frame, output)
            display = np.hstack((frame, output))

            # Calculate and display FPS
            frame_time = time.time() - last_time
            last_time = time.time()
            fps = 1.0 / frame_time if frame_time > 0 else 0
            fps_counter.append(fps)
            avg_fps = sum(fps_counter) / len(fps_counter)

            # Put FPS text on image
            cv2.putText(display, f"FPS: {avg_fps:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow('Original | Processed', display)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            frame_count += 1

    finally:
        # Calculate and print total average FPS
        total_time = time.time() - start_time
        average_fps = frame_count / total_time if total_time > 0 else 0
        print(f"Average FPS: {average_fps:.2f}")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process and display video frames."
    )
    parser.add_argument(
        "source",
        help="Video source (0 for webcam, or path to video file)"
    )
    args = parser.parse_args()
    read_frames(args.source)
