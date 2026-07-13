import math, time, sys, subprocess, array
from dataclasses import dataclass

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
    buf: object
    off: int
    tw: int
    th: int

@dataclass
class Face:
    tex: int
    a: int
    b: int
    c: int
    d: int


def skip_ws(ll, n, cur):
    while cur[0] < n:
        c = ll[cur[0]]
        if c == 32 or c == 9 or c == 10 or c == 13:
            cur[0] = cur[0] + 1
        elif c == 35:  # '#'
            while cur[0] < n:
                d = ll[cur[0]]
                if d == 10:
                    break
                cur[0] = cur[0] + 1
        else:
            return

def read_int(ll, n, cur):
    skip_ws(ll, n, cur)
    val = 0
    while cur[0] < n:
        c = ll[cur[0]]
        if c >= 48 and c <= 57:
            val = val * 10 + (c - 48)
            cur[0] = cur[0] + 1
        else:
            break
    return val

def load_image(filename):
    with open(filename, "rb") as f:
        buf = f.read()
    n = len(buf)
    cur = [0]
    skip_ws(buf, n, cur)
    cur[0] = cur[0] + 2          # skip the "P6" magic
    tw = read_int(buf, n, cur)
    th = read_int(buf, n, cur)
    mx = read_int(buf, n, cur)   # maxval, assumed 255
    cur[0] = cur[0] + 1          # single whitespace before the pixel data
    return Tex(buf, cur[0], tw, th)

w, h = 1920, 1080

texs = [load_image("3dswr.ppm"),
        load_image("pyodide_logo.ppm"),
        load_image("python_logo.ppm"),
        load_image("numpy_logo.ppm")]
NTEX = len(texs)

img = array.array('B', [0]) * (w*h*3)
ZEROS = array.array('B', [0]) * (w*h*3)

def triangle(x0, y0, u0, v0,
             x1, y1, u1, v1,
             x2, y2, u2, v2,
             L, tx, off, tw, th):
    delta = (x1-x0)*(y2-y0) - (x2-x0)*(y1-y0)
    ux = ((u1-u0)*(y2-y0) - (u2-u0)*(y1-y0)) / delta
    uy = ((x1-x0)*(u2-u0) - (x2-x0)*(u1-u0)) / delta
    uk = u0 - x0*ux - y0*uy
    vx = ((v1-v0)*(y2-y0) - (v2-v0)*(y1-y0)) / delta
    vy = ((x1-x0)*(v2-v0) - (x2-x0)*(v1-v0)) / delta
    vk = v0 - x0*vx - y0*vy

    nx01, ny01 = y1-y0, x0-x1
    nx12, ny12 = y2-y1, x1-x2
    nx20, ny20 = y0-y2, x2-x0
    k01 = -(x0*nx01 + y0*ny01)
    k12 = -(x1*nx12 + y1*ny12)
    k20 = -(x2*nx20 + y2*ny20)

    umask = tw - 1
    vmask = th - 1
    xa = max(0, int(min(x0, x1, x2)))
    ya = max(0, int(min(y0, y1, y2)))
    xb = min(w, int(max(x0, x1, x2))+1)
    yb = min(h, int(max(y0, y1, y2))+1)

    for y in range(ya, yb):
        yf = y + 0.5
        xf = xa + 0.5
        e01 = xf*nx01 + yf*ny01 + k01
        e12 = xf*nx12 + yf*ny12 + k12
        e20 = xf*nx20 + yf*ny20 + k20
        u = xf*ux + yf*uy + uk
        v = xf*vx + yf*vy + vk
        wp = (y*w + xa) * 3
        for x in range(xa, xb):
            if e01 <= 0 and e12 <= 0 and e20 <= 0:
                ui = int(u) & umask
                vi = int(v) & vmask
                tx_idx = (vi*tw + ui)*3 + off
                img[wp] = int(tx[tx_idx] * L)
                img[wp+1] = int(tx[tx_idx+1] * L)
                img[wp+2] = int(tx[tx_idx+2] * L)
            e01 += nx01
            e12 += nx12
            e20 += nx20
            u += ux
            v += vx
            wp += 3

N = 7
M = 13
R1 = 1.5
R2 = 0.5

circle = [Vec3(R1 + R2*math.cos(i*2*math.pi/N), R2*math.sin(i*2*math.pi/N), 0)
          for i in range(N)]

vertices = [Vec3(cp.x*math.cos(i*2*math.pi/M)+cp.z*math.sin(i*2*math.pi/M),
                 cp.y,
                 cp.z*math.cos(i*2*math.pi/M)-cp.x*math.sin(i*2*math.pi/M))
            for i in range(M)
            for cp in circle]

faces = [Face((i*M+j) % NTEX,
              (i+1)%N+j*N, (i+1)%N+(j+1)%M*N, i+(j+1)%M*N, i+j*N)
         for j in range(M)
         for i in range(N)]

def render_quads(verts, faces, texs, ra, rb, rc):
    xpts = []
    for vk in verts:
        x, y, z = vk.x, vk.y, vk.z
        x, y = x*math.cos(ra)+y*math.sin(ra), y*math.cos(ra)-x*math.sin(ra)
        x, z = x*math.cos(rb)+z*math.sin(rb), z*math.cos(rb)-x*math.sin(rb)
        y, z = y*math.cos(rc)+z*math.sin(rc), z*math.cos(rc)-y*math.sin(rc)
        xpts.append(XPt(w/2 + x*w/(8+z), h/2 - y*w/(8+z), x, y, z))
    for fc in sorted(faces, key=lambda f: -xpts[f.a].z):
        xpa, xpb, xpc, xpd = xpts[fc.a], xpts[fc.b], xpts[fc.c], xpts[fc.d]
        if (xpb.px-xpc.px)*(xpa.py-xpc.py) - (xpb.py-xpc.py)*(xpa.px-xpc.px) > 0:
            ax, ay, az = xpa.x, xpa.y, xpa.z
            bx, by, bz = xpb.x, xpb.y, xpb.z
            cx, cy, cz = xpc.x, xpc.y, xpc.z
            nrx = (cy-ay)*(bz-az) - (cz-az)*(by-ay)
            nry = (cz-az)*(bx-ax) - (cx-ax)*(bz-az)
            nrz = (cx-ax)*(by-ay) - (cy-ay)*(bx-ax)
            nl = (nrx**2 + nry**2 + nrz**2) ** 0.5
            L = 0.5 + 0.49*abs(nrz / nl)
            tex = texs[fc.tex]
            tx, off, tw, th = tex.buf, tex.off, tex.tw, tex.th
            triangle(xpb.px, xpb.py, 512, 256,
                     xpa.px, xpa.py, 0, 256,
                     xpc.px, xpc.py, 512, 0,
                     L, tx, off, tw, th)
            triangle(xpc.px, xpc.py, 512, 0,
                     xpa.px, xpa.py, 0, 256,
                     xpd.px, xpd.py, 0, 0,
                     L, tx, off, tw, th)

def animate():
    print("Starting ffplay...", file=sys.stderr)
    ffplay = subprocess.Popen(
        ['ffplay', '-loglevel', 'error', '-autoexit',
         '-f', 'image2pipe', '-vcodec', 'ppm', '-i', '-'],
        stdin=subprocess.PIPE)
    header = ('P6\n%d %d\n255\n' % (w, h)).encode()

    frame_num = 0
    ra = rb = rc = 0
    t = 0
    last = time.time()
    t0 = time.time()
    sa = 2 * 0.21
    sb = 2 * 0.2345
    sc = 2 * 0.2456

    tt = 0
    try:
        while ffplay.poll() is None:
            frame_num += 1
            tt += 0.03
            img[:] = ZEROS
            t -= time.time()
            render_quads(vertices, faces, texs, sa*tt, sb*tt, sc*tt)
            t += time.time()
            try:
                ffplay.stdin.write(header)
                ffplay.stdin.write(img.tobytes())
                ffplay.stdin.flush()
            except (BrokenPipeError, OSError):
                break
            delta = time.time() - last
            if delta > 1:
                print("%0.3f ms (%0.3f FPS)" %
                      (t*1000/delta/frame_num, frame_num/delta),
                      file=sys.stderr)
                t = frame_num = 0
                last = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            ffplay.stdin.close()
        except Exception:
            pass
        ffplay.wait()

animate()
