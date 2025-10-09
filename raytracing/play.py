#!/usr/bin/env python3
"""Output raw RGB frames to stdout for piping to mplayer/ffmpeg"""

import math
import time
import sys
import struct
from raytracer import Vec3, Ray, Sphere, Plane, trace_ray


def render_frame_rgb(width: int, height: int, ball_pos: Vec3) -> bytes:
    """Render frame as raw RGB24 bytes"""
    objects = [
        Sphere(ball_pos, 0.8, (1.0, 0.3, 0.3)),              # Bouncing red ball
        Sphere(Vec3(2.5, -0.3, -6), 1.0, (0.3, 0.3, 1.0)),   # Static blue sphere
        Plane(Vec3(0, -1.5, 0), Vec3(0, 1, 0), (0.7, 0.7, 0.7))  # Ground
    ]

    light_dir = Vec3(0.5, 1, 0.3).normalize()
    camera_pos = Vec3(0, 0, 0)

    aspect_ratio = width / height
    fov = math.pi / 3

    pixels = []

    for y in range(height):
        for x in range(width):
            px = (2 * (x + 0.5) / width - 1) * aspect_ratio * math.tan(fov / 2)
            py = (1 - 2 * (y + 0.5) / height) * math.tan(fov / 2)

            direction = Vec3(px, py, -1).normalize()
            ray = Ray(camera_pos, direction)

            r, g, b = trace_ray(ray, objects, light_dir)

            # Convert to 8-bit RGB
            r_int = int(min(255, r * 255))
            g_int = int(min(255, g * 255))
            b_int = int(min(255, b * 255))

            pixels.append(struct.pack('BBB', r_int, g_int, b_int))

    return b''.join(pixels)


def animate_to_stdout(width=320, height=240):
    """Generate animation frames and write to stdout as raw RGB"""

    # Physics parameters
    gravity = 9.8

    # Ball initial position
    x0, y0, z0 = -2.0, 2.0, -4.0
    vx, vy, vz = 1.5, 0.0, 0.0
    x, y, z = x0, y0, z0

    ground_y = -1.5 + 0.8
    damping = 0.7

    frame_count = 0
    fps_update_interval = 10
    last_fps_time = time.time()
    last_frame_time = time.time()
    fps = 0.0

    try:
        while True:
            # Measure actual frame time
            current_time = time.time()
            dt = current_time - last_frame_time
            last_frame_time = current_time

            # Update physics
            vy -= gravity * dt
            y += vy * dt
            x += vx * dt
            z += vz * dt

            if y <= ground_y:
                y = ground_y
                vy = -vy * damping
                if abs(vy) < 0.3:
                    vy = 0

            # Render and output frame
            ball_pos = Vec3(x, y, z)
            frame_data = render_frame_rgb(width, height, ball_pos)
            sys.stdout.buffer.write(frame_data)
            sys.stdout.buffer.flush()

            frame_count += 1

            # Update and report FPS
            if frame_count % fps_update_interval == 0:
                elapsed = current_time - last_fps_time
                fps = fps_update_interval / elapsed
                last_fps_time = current_time
                sys.stderr.write(f"Frame: {frame_count} | FPS: {fps:.1f}\n")
                sys.stderr.flush()

            # Reset if ball goes too far
            if x > 5:
                x, y, z = x0, y0, z0
                vx, vy, vz = 1.5, 0.0, 0.0

    except (KeyboardInterrupt, BrokenPipeError):
        sys.stderr.write(f"\nStopped after {frame_count} frames | Final FPS: {fps:.1f}\n")


if __name__ == '__main__':
    # Usage examples in comments:
    # mplayer: ./play.py | mplayer -demuxer rawvideo -rawvideo w=320:h=240:fps=30:format=rgb24 -
    # ffmpeg record: ./play.py | ffmpeg -f rawvideo -pixel_format rgb24 -video_size 320x240 -framerate 30 -i - output.mp4
    # ffmpeg play: ./play.py | ffplay -f rawvideo -pixel_format rgb24 -video_size 320x240 -framerate 30 -
    animate_to_stdout(width=320, height=240)
