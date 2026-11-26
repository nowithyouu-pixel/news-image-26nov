#!/usr/bin/env python3
"""Draw a one-page newspaper front summing up 26 November 2026's world news.

Pure Python 3.13 standard library: text is rendered with a built-in 5x7
bitmap font, shapes with a tiny supersampled rasteriser, and the PNG is
encoded by hand (zlib + struct). No network, no wall clock, no randomness:
two runs write byte-identical files.

Stories (all reported on 26 November 2026):
  1. Houthis claim strikes on Saudi Arabia's Ras Tanura refinery and
     Riyadh; Brent crude tops $94; two tankers hit mines in Hormuz.
  2. US proposes up to 15% tariffs on Taiwan and 13 other partners in a
     Section 301 overcapacity probe; Taiwan shares plunge.
  3. First Pakistani astronaut, Muhammad Zeeshan Ali, flies to China's
     Tiangong station aboard Shenzhou-24.
  4. Israel kills Hamas security chief Mohammad Abuelouf in Gaza;
     ceasefire under strain.
  5. Ukraine strikes Russian oil refineries overnight; Russia's own
     figures put its war dead near 500,000.
  6. BepiColombo reaches Mercury orbit after an eight-year journey.
  Also: Cairo tanker fire kills 30; Sooryavanshi, 15, smashes a record
  204 off 53 balls; Gukesh-Sindarov chess draw; India marks 18 years
  since the 26/11 Mumbai attacks.
"""

import math
import os
import struct
import zlib

W = H = 1024
SS = 2  # supersampling factor

PAPER = (246, 241, 231)
INK = (26, 26, 26)
RED = (179, 38, 30)
BLUE = (29, 78, 137)
TEAL = (31, 111, 102)
GOLD = (192, 138, 30)
GREY = (110, 104, 92)
LIGHT = (232, 226, 214)
ORANGE = (224, 110, 30)
YELLOW = (240, 190, 60)
WHITE = (250, 248, 242)
DARKBLUE = (18, 48, 84)

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font, '#' = on. Uppercase, digits and punctuation only.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "\u2019": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "\u00b7": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}

BLANK = ("00000",) * 7


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap(s, max_w, scale):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    words = s.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------- raster -----
class Canvas:
    def __init__(self):
        self.px = bytearray(W * SS * H * SS * 3)
        self.fill_rect(0, 0, W, H, PAPER)

    def _set(self, x, y, color):
        if 0 <= x < W * SS and 0 <= y < H * SS:
            i = (y * W * SS + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x * SS), max(0, y * SS)
        x1, y1 = min(W * SS, (x + w) * SS), min(H * SS, (y + h) * SS)
        for yy in range(y0, y1):
            base = (yy * W * SS + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def fill_circle(self, cx, cy, r, color):
        rr = r * SS
        ccx, ccy = cx * SS, cy * SS
        for dy in range(-rr, rr + 1):
            dx = int(math.sqrt(max(0, rr * rr - dy * dy)))
            for xx in range(ccx - dx, ccx + dx + 1):
                self._set(xx, ccy + dy, color)

    def circle(self, cx, cy, r, color, t=2):
        rr, ccx, ccy = r * SS, cx * SS, cy * SS
        for deg in range(360):
            a = math.radians(deg)
            for k in range(t * SS):
                self._set(int(ccx + (rr + k - t * SS // 2) * math.cos(a)),
                          int(ccy + (rr + k - t * SS // 2) * math.sin(a)), color)

    def ellipse(self, cx, cy, rx, ry, color, t=2):
        for deg in range(360):
            a = math.radians(deg)
            for k in range(t * SS):
                self._set(int((cx + (rx + (k - t * SS // 2) / SS) * math.cos(a)) * SS),
                          int((cy + (ry + (k - t * SS // 2) / SS) * math.sin(a)) * SS),
                          color)

    def line(self, x0, y0, x1, y1, color, t=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) * SS
        for i in range(steps + 1):
            f = i / steps
            x = x0 + (x1 - x0) * f
            y = y0 + (y1 - y0) * f
            self.fill_circle(int(round(x)), int(round(y)), max(1, t // 2), color)

    def polygon(self, pts, color):
        # Scanline fill of a simple polygon, points in logical coords.
        scaled = [(x * SS, y * SS) for x, y in pts]
        ys = [p[1] for p in scaled]
        for yy in range(min(ys), max(ys) + 1):
            xs = []
            n = len(scaled)
            for i in range(n):
                x0, y0 = scaled[i]
                x1, y1 = scaled[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(int(x0 + (yy - y0) * (x1 - x0) / (y1 - y0)))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for xx in range(xs[k], xs[k + 1] + 1):
                    self._set(xx, yy, color)

    def text(self, x, y, s, scale, color):
        for ci, ch in enumerate(s):
            glyph = FONT.get(ch, BLANK)
            ox = x + ci * 6 * scale
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(ox + col * scale, y + row * scale,
                                       scale, scale, color)
        return text_width(s, scale)

    def text_center(self, cx, y, s, scale, color):
        return self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def downsample(self):
        out = bytearray(W * H * 3)
        for y in range(H):
            for x in range(W):
                r = g = b = 0
                for dy in range(SS):
                    for dx in range(SS):
                        i = ((y * SS + dy) * W * SS + x * SS + dx) * 3
                        r += self.px[i]
                        g += self.px[i + 1]
                        b += self.px[i + 2]
                o = (y * W + x) * 3
                n = SS * SS
                out[o], out[o + 1], out[o + 2] = r // n, g // n, b // n
        return bytes(out)


# ------------------------------------------------------------ icons -------
def draw_flame(cv, cx, base_y, s, outer=ORANGE, inner=YELLOW):
    """Teardrop flame, s = height in px."""
    w = int(s * 0.62)
    pts = [(cx, base_y - s),
           (cx + w // 2, base_y - int(s * 0.55)),
           (cx + w // 2, base_y - int(s * 0.18)),
           (cx + w // 4, base_y),
           (cx - w // 4, base_y),
           (cx - w // 2, base_y - int(s * 0.18)),
           (cx - w // 2, base_y - int(s * 0.55))]
    cv.polygon(pts, outer)
    s2 = int(s * 0.55)
    w2 = int(s2 * 0.5)
    pts2 = [(cx, base_y - s2),
            (cx + w2 // 2, base_y - int(s2 * 0.5)),
            (cx + w2 // 2, base_y - int(s2 * 0.15)),
            (cx, base_y),
            (cx - w2 // 2, base_y - int(s2 * 0.15)),
            (cx - w2 // 2, base_y - int(s2 * 0.5))]
    cv.polygon(pts2, inner)


def draw_bars(cv, x, base_y, w, h, color, accent=RED):
    """Ascending bar chart with a rising arrow."""
    n = 4
    bw = w // (n * 2)
    for i in range(n):
        bh = int(h * (0.35 + 0.2 * i))
        bx = x + i * 2 * bw + bw // 2
        cv.fill_rect(bx, base_y - bh, bw, bh, accent if i == n - 1 else color)
    cv.line(x, base_y - int(h * 0.35), x + w, base_y - h, accent, 3)
    cv.line(x + w, base_y - h, x + w - 14, base_y - h + 2, accent, 3)
    cv.line(x + w, base_y - h, x + w - 2, base_y - h + 14, accent, 3)


def draw_rocket(cv, cx, cy, s, body=WHITE, accent=RED):
    """Small rocket pointing up-right, s = length."""
    w = int(s * 0.28)
    pts = [(cx, cy - s // 2),
           (cx + w // 2, cy - s // 6),
           (cx + w // 2, cy + s // 4),
           (cx, cy + s // 2),
           (cx - w // 2, cy + s // 4),
           (cx - w // 2, cy - s // 6)]
    cv.polygon(pts, body)
    cv.polygon([(cx - w // 2, cy + s // 6), (cx - w, cy + s // 2),
                (cx - w // 2, cy + s // 4)], accent)
    cv.polygon([(cx + w // 2, cy + s // 6), (cx + w, cy + s // 2),
                (cx + w // 2, cy + s // 4)], accent)
    cv.fill_circle(cx, cy - s // 8, max(3, w // 4), BLUE)
    cv.circle(cx, cy - s // 8, max(3, w // 4), INK, 1)
    draw_flame(cv, cx, cy + s // 2 + 4, int(s * 0.28))


def draw_globe(cv, cx, cy, r, color=TEAL):
    cv.circle(cx, cy, r, color, 3)
    cv.ellipse(cx, cy, r, r // 2, color, 2)
    cv.ellipse(cx, cy, r // 2, r, color, 2)
    cv.line(cx - r, cy, cx + r, cy, color, 2)


def draw_planet(cv, cx, cy, r, color=(150, 140, 125)):
    cv.fill_circle(cx, cy, r, color)
    cv.fill_circle(cx - r // 3, cy - r // 4, max(2, r // 5), (120, 110, 96))
    cv.fill_circle(cx + r // 4, cy + r // 3, max(2, r // 6), (120, 110, 96))
    cv.fill_circle(cx + r // 5, cy - r // 2, max(2, r // 7), (120, 110, 96))
    cv.ellipse(cx, cy, int(r * 1.9), int(r * 0.55), GOLD, 2)
    cv.fill_circle(cx + int(r * 1.7), cy - int(r * 0.4), max(2, r // 6), RED)


# ------------------------------------------------------------- layout -----
def draw(cv):
    cv.rect(14, 14, W - 28, H - 28, INK, 2)
    cv.rect(20, 20, W - 40, H - 40, INK, 1)

    # Masthead
    cv.text_center(512, 40, "THE WORLD IN ONE DAY", 6, INK)
    cv.text_center(512, 96, "THURSDAY, 26 NOVEMBER 2026", 3, RED)
    cv.hline(36, 132, W - 72, INK, 3)
    cv.hline(36, 138, W - 72, INK, 1)

    # ---- Lead story: Houthi strike on Saudi refinery ----
    cv.text(40, 158, "MIDDLE EAST \u00b7 ENERGY", 2, RED)
    cv.text(40, 186, "HOUTHIS HIT SAUDI", 4, INK)
    cv.text(40, 220, "REFINERY \u2014 BRENT", 4, INK)
    cv.text(40, 254, "CRUDE TOPS $94", 4, INK)
    deck = wrap("YEMEN'S HOUTHIS CLAIM STRIKES ON RAS TANURA AND "
                "RIYADH; TWO TANKERS HIT MINES IN THE STRAIT OF HORMUZ.",
                600, 2)
    y = 306
    for line in deck:
        cv.text(40, y, line, 2, INK)
        y += 22
    cv.text(40, y + 8, "OIL JUMPS AS SUPPLY FEARS SPREAD", 2, RED)

    # Lead art panel
    cv.fill_rect(668, 152, 316, 288, DARKBLUE)
    cv.text_center(826, 168, "$94", 7, YELLOW)
    cv.text_center(826, 240, "BRENT CRUDE", 2, WHITE)
    # Distillation tower with a flame on top
    cv.fill_rect(700, 300, 46, 120, (120, 150, 185))
    cv.polygon([(700, 300), (746, 300), (723, 272)], (120, 150, 185))
    for yy in (320, 345, 370, 395):
        cv.hline(700, yy, 46, DARKBLUE, 3)
    draw_flame(cv, 723, 272, 46)
    # Storage tanks
    for tx in (772, 878):
        cv.fill_rect(tx, 340, 78, 80, (120, 150, 185))
        cv.fill_circle(tx + 39, 340, 39, (120, 150, 185))
        cv.hline(tx, 368, 78, DARKBLUE, 3)

    cv.hline(36, 456, W - 72, INK, 2)

    # ---- Row 2: two cards ----
    # Card A: tariffs
    cv.rect(28, 474, 468, 218, INK, 2)
    cv.text(48, 492, "TRADE \u00b7 MARKETS", 2, BLUE)
    cv.text(48, 518, "US PLANS 15% TARIFFS", 3, INK)
    cv.text(48, 548, "ON TAIWAN, 14 PARTNERS", 3, INK)
    deck = wrap("TAIWAN SHARES PLUNGE 1,927 POINTS AS WASHINGTON "
                "PROBES OVERCAPACITY.", 428, 2)
    y = 592
    for line in deck:
        cv.text(48, y, line, 2, INK)
        y += 22
    draw_bars(cv, 330, 678, 140, 62, BLUE)

    # Card B: space
    cv.rect(528, 474, 468, 218, INK, 2)
    cv.text(548, 492, "SPACE", 2, TEAL)
    cv.text(548, 518, "FIRST PAKISTANI", 3, INK)
    cv.text(548, 548, "ASTRONAUT FLIES TO", 3, INK)
    cv.text(548, 578, "TIANGONG STATION", 3, INK)
    deck = wrap("MUHAMMAD ZEESHAN ALI JOINS CHINA'S SHENZHOU-24 "
                "CREW.", 340, 2)
    y = 620
    for line in deck:
        cv.text(548, y, line, 2, INK)
        y += 22
    draw_rocket(cv, 928, 616, 84)

    # ---- Row 3: three cards ----
    cards = [
        (28, "GAZA", RED, ["ISRAEL KILLS", "HAMAS CHIEF"],
         "STRIKE KILLS MOHAMMAD ABUELOUF; CEASEFIRE UNDER STRAIN."),
        (360, "UKRAINE", BLUE, ["KYIV HITS", "REFINERIES"],
         "OVERNIGHT STRIKES SET SITES ABLAZE; MOSCOW'S OWN TOLL "
         "NEARS 500,000 DEAD."),
        (692, "SCIENCE", TEAL, ["BEPICOLOMBO", "REACHES", "MERCURY"],
         "PROBE ENTERS ORBIT AFTER AN EIGHT-YEAR JOURNEY."),
    ]
    for x, kicker, color, heads, body in cards:
        cv.rect(x, 710, 304, 196, INK, 2)
        cv.text(x + 18, 728, kicker, 2, color)
        y = 754
        for head in heads:
            cv.text(x + 18, y, head, 3, INK)
            y += 30
        deck = wrap(body, 268, 2)
        y += 4
        for line in deck:
            cv.text(x + 18, y, line, 2, INK)
            y += 20

    # Small icons on row 3 cards, top right beside the kicker
    draw_globe(cv, 306, 740, 13)
    draw_flame(cv, 640, 752, 26)
    draw_planet(cv, 972, 740, 13)

    # ---- Footer: also today ----
    cv.hline(36, 924, W - 72, INK, 2)
    foot = ("ALSO TODAY: CAIRO TANKER FIRE KILLS 30 \u00b7 SOORYAVANSHI, "
            "15, SMASHES RECORD 204 OFF 53 BALLS \u00b7 GUKESH-SINDAROV "
            "DRAW \u00b7 INDIA MARKS 18 YEARS SINCE 26/11")
    lines = wrap(foot, W - 96, 2)
    y = 942
    for line in lines:
        cv.text_center(512, y, line, 2, INK)
        y += 22


# -------------------------------------------------------------- png -------
def chunk(kind, data):
    out = kind + data
    return struct.pack(">I", len(data)) + out + struct.pack(
        ">I", zlib.crc32(out) & 0xFFFFFFFF)


def encode_png(rgb):
    raw = b"".join(b"\x00" + rgb[y * W * 3:(y + 1) * W * 3]
                   for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas()
    draw(cv)
    data = encode_png(cv.downsample())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes)" % (path, len(data)))


if __name__ == "__main__":
    main()
