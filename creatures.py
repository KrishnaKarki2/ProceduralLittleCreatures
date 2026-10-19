import colorsys 
import math
import random
import tkinter as tk

use_set_seed = False # set to True to use a set seed
set_seed = 0xf47c9d23 # if use_set_seed True, set your seed here 

SCALE = 3.5 
PAD = 20 
BG, INK, MUTE = "#e8e6f0", "#2a2640", "#6f6a8c"
SYLLABLES = "ba bo bu di fi ga ju ka k o nu pa po ri sko tu wib zo zu ple nok fen".split()


def color(hue, sat, light):
    r, g, b = colorsys.hls_to_rgb(hue % 360 / 360, light / 100, sat / 100)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def curve(p0, p1, p2, steps=8):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t * t
        pts.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))
    return pts


def blob(r, cx, cy, rx, ry, n):
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = r.uniform(0.8, 1.2)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    out = []
    for i in range(n):
        out += curve(mid(pts[i - 1], pts[i]), pts[i], mid(pts[i], pts[(i + 1) % n]))
    return out


def creature(seed):
    r = random.Random(seed)
    f, pick = r.uniform, r.choice
    hue, sat, light = f(0, 360), f(50, 80), f(58, 72)
    body, belly = color(hue, sat, light), color(hue, sat, light + 14)
    accent, dark = color(hue + f(40, 90), sat, light - 4), color(hue, sat * 0.6, 22)
    shapes = []

    def limb(*pts):
        shapes.append(("line", pts, dark, 7))
        shapes.append(("line", pts, body, 3))

    def oval(x, y, rw, rh, fill, outline="", width=0):
        shapes.append(("oval", x - rw, y - rh, x + rw, y + rh, fill, outline, width))

    X, Y = 50, 54 # body center
    rx, ry = f(22, 32), f(20, 30) # body radii
    sides = (-1, 1) # left, right

    # legs, arms, tail, ears/horns/antennae 
    legs = pick([0, 2, 2, 4])
    for i in range(legs):
        x = X + (i / (legs - 1) - 0.5) * rx * 1.2
        limb((x, Y + ry * 0.6), (x + f(-3, 3), Y + ry + f(3, 9)))
    if r.random() < 0.5:
        reach, drop = f(4, 9), f(-6, 6)
        for d in sides:
            limb((X + d * rx * 0.8, Y), (X + d * (rx + reach), Y + drop))
    if r.random() < 0.5:
        limb(*curve((X + rx * 0.8, Y + ry * 0.3), (X + rx + 14, Y + ry * 0.6), (X + rx + f(6, 12), Y - f(0, 12))))
    top, ear, tall = pick(["ears", "horns", "antennae", None]), f(5, 9), f(7, 14)
    for d in sides:
        if top == "ears":
            oval(X + d * rx * 0.6, Y - ry * 0.8, ear, ear, body, dark, 3)
        elif top == "horns":
            shapes.append(("poly", [(X + d * rx * 0.5 - 4, Y - ry * 0.75),
                                    (X + d * rx * 0.7, Y - ry * 0.8 - tall),
                                    (X + d * rx * 0.5 + 4, Y - ry * 0.75)], accent, dark, 3))
        elif top == "antennae":
            tip = (X + d * rx * 0.5, Y - ry - tall)
            limb((X + d * rx * 0.3, Y - ry * 0.9), tip)
            oval(tip[0], tip[1], 3.5, 3.5, accent, dark, 2)

    # body, then a belly patch or spots 
    shapes.append(("poly", blob(r, X, Y, rx, ry, pick([7, 8, 9, 10])), body, dark, 3))
    pattern = pick(["belly", "spots", None])
    if pattern == "belly":
        oval(X, Y + ry * 0.35, rx * 0.55, ry * 0.4, belly)
    elif pattern == "spots":
        for _ in range(r.randint(3, 6)):
            a, d, size = f(0, 2 * math.pi), f(0, 0.5), f(2.5, 5)
            oval(X + math.cos(a) * rx * d, Y + math.sin(a) * ry * d, size, size, accent)

    # eyes 
    count, size = pick([1, 2, 2, 2, 3]), f(4.5, 8)
    gaze_x, gaze_y = f(-1, 1), f(-0.4, 0.8)
    for i in range(count):
        spread = (i / (count - 1) - 0.5) if count > 1 else 0
        x = X + spread * rx * (1.1 if count > 2 else 0.8)
        y = Y - ry * 0.2 - (6 if count > 2 and i == 1 else 0)
        oval(x, y, size, size, "#ffffff", dark, 2.2)
        oval(x + gaze_x * size * 0.3, y + gaze_y * size * 0.3, size * 0.55, size * 0.55, dark)

    # mouth 
    my = Y + ry * 0.4
    if r.random() < 0.25:
        oval(X, my, 3, f(3, 5), dark)
    else:
        bend = pick([6, 6, 0, -4])
        shapes.append(("line", curve((X - 5, my), (X, my + bend), (X + 5, my), 6), dark, 2.5))

    name = "".join(pick(SYLLABLES) for _ in range(3 if r.random() < 0.4 else 2)).capitalize()
    return shapes, name


def paint(canvas, shapes, ox, oy):
    def xy(pts):
        return [c for x, y in pts for c in (ox + x * SCALE, oy + y * SCALE)]

    for kind, *a in shapes:
        if kind == "line":
            pts, col, w = a
            canvas.create_line(xy(pts), fill=col, width=w * SCALE, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        elif kind == "poly":
            pts, fill, outline, w = a
            canvas.create_polygon(xy(pts), fill=fill, outline=outline, width=w * SCALE, joinstyle=tk.ROUND)
        else:
            x0, y0, x1, y1, fill, outline, w = a
            canvas.create_oval(xy([(x0, y0), (x1, y1)]), fill=fill, outline=outline, width=w * SCALE)


def main():
    root = tk.Tk()
    root.title("Little creature")
    root.configure(bg=BG)
    root.resizable(False, False)

    size = 100 * SCALE
    canvas = tk.Canvas(root, width=size + 2 * PAD, height=size + PAD + 70,
                       bg=BG, highlightthickness=0, cursor="hand2")

    def reroll(event=None):
        if use_set_seed:
            seed = set_seed
        else:
            seed = random.randrange(2 ** 32)
            
        shapes, name = creature(seed)
        canvas.delete("all")
        paint(canvas, shapes, PAD, PAD)
        canvas.create_text(PAD + size / 2, PAD + size + 20, text=name, fill=INK, font=("Segoe UI", 16, "bold"))
        canvas.create_text(PAD + size / 2, PAD + size + 44, text="#%x" % seed, fill=MUTE, font=("Segoe UI", 10))

    canvas.pack()
    canvas.bind("<Button-1>", reroll)
    reroll()
    root.mainloop()


if __name__ == "__main__":
    assert creature(1) == creature(1), "same seed must give the same creature"
    main()
