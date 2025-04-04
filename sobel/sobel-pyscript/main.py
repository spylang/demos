import numpy as np
import js
from pyodide.code import run_js
from pyodide.ffi import to_js, create_proxy
from js import document, window, requestAnimationFrame, cancelAnimationFrame
from js import Uint8ClampedArray, ImageData
import time
from pyscript import when
from sobel_np import sobel_np

# Global variables
video = document.getElementById('video')
original_canvas = document.getElementById('original')
processed_canvas = document.getElementById('processed')
start_btn = document.getElementById('startBtn')
stop_btn = document.getElementById('stopBtn')
status_element = document.getElementById('status')
high_contrast_checkbox = document.getElementById('highContrast')

# Canvas contexts
original_ctx = original_canvas.getContext('2d')
processed_ctx = processed_canvas.getContext('2d')

stream = None
animation_id = None
high_contrast = False
frame_count = 0
last_time = 0
fps = 0


def update_status():
    if not stream:
        status_message = 'Camera inactive'
    else:
        status_message = f'Processing: {fps} FPS'
        if high_contrast:
            status_message += ' (High contrast mode)'
        status_message += ' - Using PyScript'

    status_element.textContent = status_message

def calculate_fps(timestamp):
    global last_time, frame_count, fps
    if not last_time:
        last_time = timestamp
        return

    frame_count += 1
    if timestamp - last_time >= 1000:
        fps = round((frame_count * 1000) / (timestamp - last_time))
        frame_count = 0
        last_time = timestamp
        update_status()


W, H = 400, 300
W, H = 160, 120

# preallocate input and output buffers
in_buf = np.zeros(H*W*4, dtype=np.uint8)
out_buf = np.zeros(H*W*4, dtype=np.uint8)
js_out_buf = Uint8ClampedArray.new(W*H*4)

def process_frame(timestamp):
    global animation_id
    calculate_fps(timestamp)

    # Draw the current video frame to canvas and get image data
    original_ctx.drawImage(video, 0, 0, W, H)
    in_img_data = original_ctx.getImageData(0, 0, W, H)

    # copy img_data into the input buffer
    np.copyto(in_buf, in_img_data.data, casting='unsafe')

    #sobel_np(in_buf, H, W, out_buf)  # do sobel filter
    js_out_buf.set(to_js(in_buf))    # fake filter, just copy bytes

    # copy the pixels into the canvas
    out_img_data = ImageData.new(js_out_buf, W, H)
    processed_ctx.putImageData(out_img_data, 0, 0)

    # Continue the processing loop
    frame_proxy = create_proxy(process_frame)
    animation_id = requestAnimationFrame(frame_proxy)

# Start camera and processing
@when("click", "#startBtn")
async def start_camera(ev):
    print("start")
    global stream

    def on_stream(media_stream):
        global stream
        stream = media_stream
        video.srcObject = stream

        start_btn.disabled = True
        stop_btn.disabled = False
        status_element.textContent = "Starting camera..."

        # Start processing when video is ready
        def on_load(ev):
            video.play()
            frame_proxy = create_proxy(process_frame)
            animation_id = requestAnimationFrame(frame_proxy)
            update_status()

        video.onloadedmetadata = on_load

    def on_error(error):
        print(f"Error accessing webcam: {error}")
        status_element.textContent = "Error: Could not access camera"

    # Get user media with constraints
    constraints = {
        "video": {
            ## "width": {"ideal": 640},
            ## "height": {"ideal": 480},
            "width": {"ideal": 160},
            "height": {"ideal": 120},
            "facingMode": "user"
        }
    }

    promise = window.navigator.mediaDevices.getUserMedia(to_js(constraints))
    promise.then(create_proxy(on_stream)).catch(create_proxy(on_error))

# Stop camera and processing
@when("click", "#stopBtn")
def stop_camera():
    global stream, animation_id, frame_count, last_time, fps

    if stream:
        for track in stream.getTracks():
            track.stop()
        stream = None

    if animation_id:
        cancelAnimationFrame(animation_id)
        animation_id = None

    start_btn.disabled = False
    stop_btn.disabled = True

    # Reset fps counters
    frame_count = 0
    last_time = 0
    fps = 0

    update_status()

# Toggle high contrast mode
def toggle_contrast():
    global high_contrast
    high_contrast = high_contrast_checkbox.checked
    update_status()

# Initialize
def init():
    stop_btn.disabled = True
    update_status()
    print("ready")

# Initialize the app
init()
