#!/usr/bin/env python3
"""Animated bouncing ball demo using the raytracer"""

import math
import time
import sys
import os
from raytracer import Vec3, Ray, Sphere, Plane, trace_ray

BENCHMARK = False


def render_frame(width: int, height: int, ball_pos: Vec3) -> str:
    """Render frame to a string buffer"""
    # Scene setup
    objects = [
        Sphere(ball_pos, 0.8, (1.0, 0.3, 0.3)),              # Bouncing red ball
        Sphere(Vec3(2.5, -0.3, -6), 1.0, (0.3, 0.3, 1.0)),   # Static blue sphere
        Plane(Vec3(0, -1.5, 0), Vec3(0, 1, 0), (0.7, 0.7, 0.7))  # Ground
    ]

    light_dir = Vec3(0.5, 1, 0.3).normalize()
    camera_pos = Vec3(0, 0, 0)

    aspect_ratio = width / height
    fov = math.pi / 3

    # Build frame in memory
    buffer = []

    for y in range(height):
        line = []
        for x in range(width):
            # Calculate ray direction
            px = (2 * (x + 0.5) / width - 1) * aspect_ratio * math.tan(fov / 2)
            py = (1 - 2 * (y + 0.5) / height) * math.tan(fov / 2)

            direction = Vec3(px, py, -1).normalize()
            ray = Ray(camera_pos, direction)

            # Trace ray
            r, g, b = trace_ray(ray, objects, light_dir)

            # Convert to 8-bit color
            r_int = int(min(255, r * 255))
            g_int = int(min(255, g * 255))
            b_int = int(min(255, b * 255))

            # Use ANSI 24-bit color escape code
            line.append(f'\033[48;2;{r_int};{g_int};{b_int}m ')

        # Reset color at end of line
        line.append('\033[0m\n')
        buffer.append(''.join(line))

    return ''.join(buffer)


def animate():
    # Get terminal size
    term_size = os.get_terminal_size()
    width = term_size.columns
    height = term_size.lines - 2  # Reserve 2 lines for info text

    # Physics parameters
    gravity = 9.8

    # Ball initial position (up-left)
    x0 = -2.0
    y0 = 2.0
    z0 = -4.0

    # Initial velocity
    vx = 1.5  # Move right
    vy = 0.0
    vz = 0.0

    # Current position and velocity
    x, y, z = x0, y0, z0

    # Bounce parameters
    ground_y = -1.5 + 0.8  # ground plane + ball radius
    damping = 0.7  # Energy loss on bounce

    # FPS tracking
    frame_count = 0
    fps_update_interval = 10
    last_fps_time = time.time()
    fps = 0.0

    if not BENCHMARK:
        # Enter alternate screen buffer
        print('\033[?1049h', end='')
        # Hide cursor
        print('\033[?25l', end='')

    last_frame_time = time.time()

    try:
        max_frames = 300 if BENCHMARK else None
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

            # Check for ground collision
            if y <= ground_y:
                y = ground_y
                vy = -vy * damping

                # Stop bouncing if velocity is too small
                if abs(vy) < 0.3:
                    vy = 0

            # Render current frame to buffer
            ball_pos = Vec3(x, y, z)
            if not BENCHMARK:
                frame = render_frame(width, height, ball_pos)
            else:
                # In benchmark mode, still trace rays but don't build frame string
                objects = [
                    Sphere(ball_pos, 0.8, (1.0, 0.3, 0.3)),
                    Sphere(Vec3(2.5, -0.3, -6), 1.0, (0.3, 0.3, 1.0)),
                    Plane(Vec3(0, -1.5, 0), Vec3(0, 1, 0), (0.7, 0.7, 0.7))
                ]
                light_dir = Vec3(0.5, 1, 0.3).normalize()
                camera_pos = Vec3(0, 0, 0)
                aspect_ratio = width / height
                fov = math.pi / 3

                for py in range(height):
                    for px in range(width):
                        px_norm = (2 * (px + 0.5) / width - 1) * aspect_ratio * math.tan(fov / 2)
                        py_norm = (1 - 2 * (py + 0.5) / height) * math.tan(fov / 2)
                        direction = Vec3(px_norm, py_norm, -1).normalize()
                        ray = Ray(camera_pos, direction)
                        trace_ray(ray, objects, light_dir)

            # Update FPS counter
            frame_count += 1
            if frame_count % fps_update_interval == 0:
                elapsed = current_time - last_fps_time
                fps = fps_update_interval / elapsed
                last_fps_time = current_time

                if BENCHMARK:
                    print(f"Frame: {frame_count} | FPS: {fps:.1f}")

            if not BENCHMARK:
                # Display info
                info = f"\nBall position: ({x:.2f}, {y:.2f}, {z:.2f}) | velocity: {vy:.2f} | FPS: {fps:.1f} | Press Ctrl+C to exit"

                # Move cursor to home and output everything at once
                sys.stdout.write('\033[H' + frame + info)
                sys.stdout.flush()

            # Reset if ball goes too far right
            if x > 5:
                x, y, z = x0, y0, z0
                vx, vy, vz = 1.5, 0.0, 0.0

            # Stop after max_frames in benchmark mode
            if max_frames and frame_count >= max_frames:
                break

    except KeyboardInterrupt:
        pass
    finally:
        if not BENCHMARK:
            # Show cursor
            print('\033[?25h', end='')
            # Exit alternate screen buffer
            print('\033[?1049l', end='')
        print(f"\nAnimation stopped. Final FPS: {fps:.1f}, Total frames: {frame_count}")


if __name__ == '__main__':
    animate()
