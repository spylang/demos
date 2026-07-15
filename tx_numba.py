"""
Numba version of the texture-mapping demo.

The rendered frames are written to stdout as a stream of P6 PPM images.
Pipe them into ffplay for display:
    python tx_numba.py | ffplay -loglevel error -autoexit \
        -f image2pipe -vcodec ppm -i -
"""

import math
import time
import sys
import numpy as np
from PIL import Image
from numba import njit
from dataclasses import dataclass

W = 1920
H = 1080
N = 7
M = 13
R1 = 1.5
R2 = 0.5

VN = N * M       # number of vertices
FN = N * M       # number of quad faces
NTEX = 4


@dataclass
class Vec3:
    x: float
    y: float
    z: float


@dataclass
class XPt:
    px: float
    py: float
    x: float
    y: float
    z: float


@dataclass
class Tex:
    buf: object             # pixel buffer (flat uint8 numpy array)
    off: int                # byte offset where pixel data starts (0 for PIL-loaded)
    tw: int
    th: int


@dataclass
class Face:
    tex: int
    a: int
    b: int
    c: int
    d: int


def load_image(filename):
    """Load an image via PIL and return a Tex wrapping its flat uint8 buffer."""
    buf = np.uint8(Image.open(filename)).copy()
    th, tw = buf.shape[:2]
    return Tex(buf.reshape(-1), 0, tw, th)


@njit(cache=True, fastmath=True, boundscheck=False)
def draw_triangle(x0, y0, u0, v0,
                  x1, y1, u1, v1,
                  x2, y2, u2, v2,
                  L,
                  tx, off, tw, th,
                  img):
    delta = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
    ux = ((u1 - u0) * (y2 - y0) - (u2 - u0) * (y1 - y0)) / delta
    uy = ((x1 - x0) * (u2 - u0) - (x2 - x0) * (u1 - u0)) / delta
    uk = u0 - x0 * ux - y0 * uy
    vx = ((v1 - v0) * (y2 - y0) - (v2 - v0) * (y1 - y0)) / delta
    vy = ((x1 - x0) * (v2 - v0) - (x2 - x0) * (v1 - v0)) / delta
    vk = v0 - x0 * vx - y0 * vy

    nx01 = y1 - y0
    ny01 = x0 - x1
    nx12 = y2 - y1
    ny12 = x1 - x2
    nx20 = y0 - y2
    ny20 = x2 - x0
    k01 = -(x0 * nx01 + y0 * ny01)
    k12 = -(x1 * nx12 + y1 * ny12)
    k20 = -(x2 * nx20 + y2 * ny20)

    umask = tw - 1
    vmask = th - 1

    xa = max(0, int(min(x0, min(x1, x2))))
    ya = max(0, int(min(y0, min(y1, y2))))
    xb = min(W, int(max(x0, max(x1, x2))) + 1)
    yb = min(H, int(max(y0, max(y1, y2))) + 1)

    for y in range(ya, yb):
        yf = y + 0.5
        xf = xa + 0.5
        e01 = xf * nx01 + yf * ny01 + k01
        e12 = xf * nx12 + yf * ny12 + k12
        e20 = xf * nx20 + yf * ny20 + k20
        u = xf * ux + yf * uy + uk
        v = xf * vx + yf * vy + vk
        row_base = y * W * 3
        for x in range(xa, xb):
            if e01 <= 0.0 and e12 <= 0.0 and e20 <= 0.0:
                ui = int(u) & umask
                vi = int(v) & vmask
                tx_idx = (vi * tw + ui) * 3 + off
                img_idx = row_base + x * 3
                img[img_idx] = int(tx[tx_idx] * L)
                img[img_idx + 1] = int(tx[tx_idx + 1] * L)
                img[img_idx + 2] = int(tx[tx_idx + 2] * L)
            e01 = e01 + nx01
            e12 = e12 + nx12
            e20 = e20 + nx20
            u = u + ux
            v = v + vx


def render_quads(verts, faces, texs, xpts, img, ra, rb, rc):
    cra = math.cos(ra)
    sra = math.sin(ra)
    crb = math.cos(rb)
    srb = math.sin(rb)
    crc = math.cos(rc)
    src = math.sin(rc)

    hw = W / 2.0
    hh = H / 2.0
    wf = W

    for k in range(VN):
        vk = verts[k]
        x = vk.x
        y = vk.y
        z = vk.z
        nx = x * cra + y * sra
        ny = y * cra - x * sra
        x = nx
        y = ny
        nx2 = x * crb + z * srb
        nz = z * crb - x * srb
        x = nx2
        z = nz
        ny2 = y * crc + z * src
        nz2 = z * crc - y * src
        y = ny2
        z = nz2
        px = hw + x * wf / (8.0 + z)
        py = hh - y * wf / (8.0 + z)
        xpts[k] = XPt(px, py, x, y, z)

    # painter's algorithm: sort faces back-to-front by the z of their first vertex
    for fc in sorted(faces, key=lambda f: -xpts[f.a].z):
        xpa = xpts[fc.a]
        xpb = xpts[fc.b]
        xpc = xpts[fc.c]
        xpd = xpts[fc.d]
        pax = xpa.px
        pay = xpa.py
        pbx = xpb.px
        pby = xpb.py
        pcx = xpc.px
        pcy = xpc.py
        pdx = xpd.px
        pdy = xpd.py
        if (pbx - pcx) * (pay - pcy) - (pby - pcy) * (pax - pcx) > 0.0:
            ax = xpa.x
            ay = xpa.y
            az = xpa.z
            bx = xpb.x
            by = xpb.y
            bz = xpb.z
            cx = xpc.x
            cy = xpc.y
            cz = xpc.z
            nrx = (cy - ay) * (bz - az) - (cz - az) * (by - ay)
            nry = (cz - az) * (bx - ax) - (cx - ax) * (bz - az)
            nrz = (cx - ax) * (by - ay) - (cy - ay) * (bx - ax)
            nl = math.sqrt(nrx * nrx + nry * nry + nrz * nrz)
            L = 0.5 + 0.49 * abs(nrz / nl)
            tex = texs[fc.tex]
            tx = tex.buf
            off = tex.off
            tw = tex.tw
            th = tex.th
            draw_triangle(pbx, pby, 512.0, 256.0,
                          pax, pay, 0.0, 256.0,
                          pcx, pcy, 512.0, 0.0,
                          L, tx, off, tw, th, img)
            draw_triangle(pcx, pcy, 512.0, 0.0,
                          pax, pay, 0.0, 256.0,
                          pdx, pdy, 0.0, 0.0,
                          L, tx, off, tw, th, img)


def build_geometry(verts, faces):
    circle = [Vec3(0.0, 0.0, 0.0)] * N
    for i in range(N):
        ang = i * 2.0 * math.pi / N
        circle[i] = Vec3(R1 + R2 * math.cos(ang), R2 * math.sin(ang), 0.0)

    for j in range(M):
        aj = j * 2.0 * math.pi / M
        caj = math.cos(aj)
        saj = math.sin(aj)
        for k in range(N):
            cp = circle[k]
            x = cp.x
            y = cp.y
            z = cp.z
            verts[j * N + k] = Vec3(x * caj + z * saj, y, z * caj - x * saj)

    for j2 in range(M):
        for i2 in range(N):
            t = j2 * N + i2
            faces[t] = Face((i2 * M + j2) % NTEX,
                            (i2 + 1) % N + j2 * N,
                            (i2 + 1) % N + (j2 + 1) % M * N,
                            i2 + (j2 + 1) % M * N,
                            i2 + j2 * N)


def parse_max_frames(argv):
    max_frames = -1
    i = 1
    while i < len(argv):
        if argv[i] == "-n" and i + 1 < len(argv):
            max_frames = int(argv[i + 1])
            i += 2
        else:
            i += 1
    return max_frames


def main():
    max_frames = parse_max_frames(sys.argv)
    err = sys.stderr
    err.write("Loading textures...\n")

    texs = [load_image("3dswr.png"),
            load_image("pyodide_logo.png"),
            load_image("python_logo.png"),
            load_image("numpy_logo.png")]
    for tex in texs:
        err.write("  " + str(tex.tw) + "x" + str(tex.th) + "\n")
    err.flush()

    # framebuffer: a flat uint8 numpy array we mutate every frame.
    npix = W * H * 3
    img = np.zeros(npix, dtype=np.uint8)

    verts = [Vec3(0.0, 0.0, 0.0)] * VN
    faces = [Face(0, 0, 0, 0, 0)] * FN
    build_geometry(verts, faces)

    xpts = [XPt(0.0, 0.0, 0.0, 0.0, 0.0)] * VN

    out = sys.stdout.buffer
    header = ("P6\n%d %d\n255\n" % (W, H)).encode()

    sa = 2.0 * 0.21
    sb = 2.0 * 0.2345
    sc = 2.0 * 0.2456

    err.write("Warming up JIT...\n")
    err.flush()
    render_quads(verts, faces, texs, xpts, img, 0.0, 0.0, 0.0)
    img[:] = 0

    frame_num = 0
    total_frames = 0
    tt = 0.0
    acc = 0.0
    last = time.time()

    try:
        while max_frames < 0 or total_frames < max_frames:
            frame_num = frame_num + 1
            total_frames = total_frames + 1
            tt = tt + 0.03
            img[:] = 0
            t0 = time.time()
            render_quads(verts, faces, texs, xpts, img,
                         sa * tt, sb * tt, sc * tt)
            acc = acc + (time.time() - t0)

            try:
                out.write(header)
                out.write(img.tobytes())
                out.flush()
            except (BrokenPipeError, OSError):
                break

            delta = time.time() - last
            if delta > 1.0:
                fnf = float(frame_num)
                ms = acc * 1000.0 / fnf
                fps = fnf / delta
                err.write(str(ms) + " ms (" + str(fps) + " FPS)\n")
                err.flush()
                acc = 0.0
                frame_num = 0
                last = time.time()
    except KeyboardInterrupt:
        pass


main()
