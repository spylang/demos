#!/usr/bin/env python3
"""Benchmark for the raytracer rendering engine"""

import time
from raytracer import Vec3, Ray, Sphere, Plane, trace_ray

def render_frame(width: int, height: int, ball_pos: Vec3) -> None:
    """Render a single frame (no output)"""
    # Scene setup
    objects = [
        Sphere(ball_pos, 0.8, (1.0, 0.3, 0.3)),
        Sphere(Vec3(2.5, -0.3, -6), 1.0, (0.3, 0.3, 1.0)),
        Plane(Vec3(0, -1.5, 0), Vec3(0, 1, 0), (0.7, 0.7, 0.7))
    ]

    light_dir = Vec3(0.5, 1, 0.3).normalize()
    camera_pos = Vec3(0, 0, 0)

    aspect_ratio = width / height
    fov = 3.14159265359 / 3

    for y in range(height):
        for x in range(width):
            # Calculate ray direction
            px = (2 * (x + 0.5) / width - 1) * aspect_ratio * (fov / 2) ** 0.5
            py = (1 - 2 * (y + 0.5) / height) * (fov / 2) ** 0.5

            direction = Vec3(px, py, -1).normalize()
            ray = Ray(camera_pos, direction)

            # Trace ray
            trace_ray(ray, objects, light_dir)


def benchmark():
    """Run rendering benchmark"""
    width = 80
    height = 30
    num_frames = 100

    print(f"Benchmarking raytracer...")
    print(f"Resolution: {width}x{height}")
    print(f"Frames: {num_frames}")
    print(f"Total rays: {width * height * num_frames:,}")
    print()

    # Warm up
    print("Warming up...")
    for i in range(5):
        ball_pos = Vec3(-2.0 + i * 0.5, 0.0, -4.0)
        render_frame(width, height, ball_pos)

    # Benchmark
    print("Running benchmark...")
    start_time = time.time()

    for i in range(num_frames):
        ball_pos = Vec3(-2.0 + i * 0.05, 0.0, -4.0)
        render_frame(width, height, ball_pos)

    end_time = time.time()
    elapsed = end_time - start_time

    # Results
    total_rays = width * height * num_frames
    fps = num_frames / elapsed
    rays_per_sec = total_rays / elapsed

    print()
    print("=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Total time: {elapsed:.3f} seconds")
    print(f"FPS: {fps:.2f}")
    print(f"Time per frame: {elapsed / num_frames * 1000:.2f} ms")
    print(f"Rays per second: {rays_per_sec:,.0f}")
    print(f"Time per ray: {elapsed / total_rays * 1e6:.2f} µs")
    print("=" * 50)


if __name__ == '__main__':
    benchmark()
