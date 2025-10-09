#!/usr/bin/env python3
"""Simple ASCII raytracer with ANSI color support"""

import os
import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Vec3:
    x: float
    y: float
    z: float

    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar):
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar):
        return self * scalar

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def length(self):
        return math.sqrt(self.dot(self))

    def normalize(self):
        l = self.length()
        return Vec3(self.x / l, self.y / l, self.z / l)


@dataclass
class Ray:
    origin: Vec3
    direction: Vec3


@dataclass
class HitRecord:
    point: Vec3
    normal: Vec3
    t: float
    color: Tuple[float, float, float]


class Sphere:
    def __init__(self, center: Vec3, radius: float, color: Tuple[float, float, float]):
        self.center = center
        self.radius = radius
        self.color = color

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        oc = ray.origin - self.center
        a = ray.direction.dot(ray.direction)
        b = 2.0 * oc.dot(ray.direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return None

        t = (-b - math.sqrt(discriminant)) / (2.0 * a)
        if t < 0.001:
            return None

        point = ray.origin + ray.direction * t
        normal = (point - self.center).normalize()
        return HitRecord(point, normal, t, self.color)


class Plane:
    def __init__(self, point: Vec3, normal: Vec3, color: Tuple[float, float, float]):
        self.point = point
        self.normal = normal.normalize()
        self.color = color

    def intersect(self, ray: Ray) -> Optional[HitRecord]:
        denom = self.normal.dot(ray.direction)
        if abs(denom) < 0.0001:
            return None

        t = (self.point - ray.origin).dot(self.normal) / denom
        if t < 0.001:
            return None

        point = ray.origin + ray.direction * t

        # Checkerboard pattern
        color = self.color
        checker_size = 2.0
        if (int(point.x / checker_size) + int(point.z / checker_size)) % 2 == 0:
            color = (0.9, 0.9, 0.9)

        return HitRecord(point, self.normal, t, color)


def trace_ray(ray: Ray, objects, light_dir: Vec3) -> Tuple[float, float, float]:
    closest_hit = None
    closest_t = float('inf')

    for obj in objects:
        hit = obj.intersect(ray)
        if hit and hit.t < closest_t:
            closest_hit = hit
            closest_t = hit.t

    if closest_hit is None:
        # Sky gradient
        t = 0.5 * (ray.direction.y + 1.0)
        return (0.5 + 0.5*t, 0.7 + 0.3*t, 1.0)

    # Simple diffuse lighting
    light_intensity = max(0.0, closest_hit.normal.dot(light_dir))

    # Ambient + diffuse
    ambient = 0.2
    total_intensity = ambient + (1.0 - ambient) * light_intensity

    # Apply color
    r = closest_hit.color[0] * total_intensity
    g = closest_hit.color[1] * total_intensity
    b = closest_hit.color[2] * total_intensity

    return (r, g, b)


def render(width: int, height: int):
    # Scene setup
    objects = [
        Sphere(Vec3(0, 0, -5), 1.5, (1.0, 0.3, 0.3)),        # Red sphere
        Sphere(Vec3(-2, -0.5, -4), 0.8, (0.3, 1.0, 0.3)),    # Green sphere
        Sphere(Vec3(2.5, -0.3, -6), 1.0, (0.3, 0.3, 1.0)),   # Blue sphere
        Plane(Vec3(0, -1.5, 0), Vec3(0, 1, 0), (0.7, 0.7, 0.7))  # Ground
    ]

    light_dir = Vec3(0.5, 1, 0.3).normalize()
    camera_pos = Vec3(0, 0, 0)

    aspect_ratio = width / height
    fov = math.pi / 3

    for y in range(height):
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

            # Use ANSI 24-bit color escape code to set background color
            print(f'\033[48;2;{r_int};{g_int};{b_int}m ', end='')

        # Reset color at end of line
        print('\033[0m')


if __name__ == '__main__':
    size = os.get_terminal_size()
    #render(120, 40)
    render(size.columns, size.lines)
