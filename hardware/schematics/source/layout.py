"""
Shared page layout for the Eurorack-MIDI schematics.

Every image uses the same grid, the same three text styles and the
same font (JetBrains Mono). All text is converted to paths, so the
images look the same on every computer and on GitHub.

Text styles:
  title    bold, 28
  heading  bold, 15
  body     regular, 13 (also used for every label inside the schematics)
"""

import os
import re
import xml.etree.ElementTree as ET

import schemdraw
import ziafont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_REGULAR = os.path.join(HERE, 'fonts', 'JetBrainsMono-Regular.ttf')
FONT_BOLD = os.path.join(HERE, 'fonts', 'JetBrainsMono-Bold.ttf')

# text sizes
TITLE = 28
HEADING = 15
BODY = 13
LINE = 21            # line height for body text
CHAR = BODY * 0.6    # JetBrains Mono is monospaced: every character is 0.6 em wide

# colours
INK = '#111111'
GREY = '#6f6f6f'
RULE = '#d6d6d6'
ACCENT = '#e4572e'
PAPER = '#ffffff'

# grid
MARGIN = 56
GUTTER = 40
SECTION = 48   # space between sections

ziafont.config.svg2 = False
schemdraw.use('svg')
schemdraw.svgconfig.text = 'path'
schemdraw.svgconfig.svg2 = False

_fonts = {}


def font(bold=False):
    path = FONT_BOLD if bold else FONT_REGULAR
    if path not in _fonts:
        _fonts[path] = ziafont.Font(path)
    return _fonts[path]


def setup_drawing(d):
    """Common settings for every schemdraw drawing."""
    d.config(unit=2.5, fontsize=BODY, font=FONT_REGULAR, lw=1.6, color=INK)


def drawing_svg(d):
    """Returns (inner svg markup, x, y, width, height) of a schemdraw drawing."""
    data = d.get_imagedata('svg')
    if isinstance(data, bytes):
        data = data.decode()
    vb = re.search(r'viewBox="([-\d.e]+) ([-\d.e]+) ([-\d.e]+) ([-\d.e]+)"', data)
    x, y, w, h = (float(v) for v in vb.groups())
    inner = data[data.index('>', data.index('<svg')) + 1:data.rindex('</svg>')]
    return inner, x, y, w, h


class Page:
    def __init__(self, width):
        self.width = width
        self.parts = []
        self.y = MARGIN

    # ---------- text ----------

    def text(self, s, x, y, size=BODY, bold=False, color=INK, halign='left'):
        g = ET.Element('g')
        ziafont.Text(s, font=font(bold), size=size, halign=halign,
                     valign='base', color=color).drawon(g, x, y)
        self.parts.append(''.join(ET.tostring(c, encoding='unicode') for c in g))

    def lines(self, rows, x, y, color=INK):
        """Body text lines on the baseline grid, first baseline at y. Returns the bottom of the text."""
        for i, row in enumerate(rows):
            if row:
                self.text(row, x, y + i * LINE, color=color)
        return y + (len(rows) - 1) * LINE + 5

    def table(self, header, rows, x, y):
        """Header row in grey, then body rows. Starts at the top y of the block. Returns the bottom."""
        self.text(header, x, y + BODY, color=GREY)
        return self.lines(rows, x, y + BODY + LINE)

    def rule(self, y, x1=None, x2=None):
        x1 = MARGIN if x1 is None else x1
        x2 = self.width - MARGIN if x2 is None else x2
        self.parts.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{RULE}" stroke-width="1"/>')

    # ---------- blocks ----------

    def header(self, title, subtitle):
        self.text('EURORACK-MIDI  /  V0', MARGIN, self.y + BODY, color=ACCENT, bold=True)
        self.text(title, MARGIN, self.y + BODY + 44, size=TITLE, bold=True)
        self.text(subtitle, MARGIN, self.y + BODY + 44 + 30, color=GREY)
        self.y += BODY + 44 + 30 + 28
        self.rule(self.y)
        self.y += 44

    def schematic(self, d, x, y):
        """Places a schemdraw drawing with its top left corner at (x, y). Returns its size."""
        inner, vx, vy, w, h = drawing_svg(d)
        self.parts.append(f'<g transform="translate({x - vx:.2f} {y - vy:.2f})">{inner}</g>')
        return w, h

    def heading(self, s, x, y):
        """Section heading with a short accent bar. Returns the y where content starts."""
        self.parts.append(f'<rect x="{x}" y="{y}" width="24" height="3" fill="{ACCENT}"/>')
        self.text(s, x, y + 3 + 26, size=HEADING, bold=True)
        return y + 3 + 26 + 24

    def columns(self, n):
        """x position and width of n equal columns between the margins."""
        width = (self.width - 2 * MARGIN - (n - 1) * GUTTER) / n
        return [(MARGIN + i * (width + GUTTER), width) for i in range(n)]

    def footer(self):
        self.y += SECTION
        self.rule(self.y)
        self.y += 32
        self.text('Jose Chavarria  /  CC BY-SA 4.0', MARGIN, self.y, color=GREY)
        self.text('Eurorack-MIDI v0  /  Oct 2026', self.width - MARGIN, self.y, color=GREY, halign='right')
        self.y += MARGIN - 8

    def save(self, path):
        h = self.y
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'width="{self.width}" height="{h:.0f}" viewBox="0 0 {self.width} {h:.0f}">'
               f'<rect width="100%" height="100%" fill="{PAPER}"/>'
               + ''.join(self.parts) + '</svg>')
        with open(path, 'w') as f:
            f.write(svg)
        return svg


def wrap(s, width_px):
    """Wraps a string to fit a column width (monospaced font, so this is exact)."""
    n = int(width_px // CHAR)
    words, rows, row = s.split(), [], ''
    for w in words:
        if len(row) + len(w) + (1 if row else 0) > n:
            rows.append(row)
            row = w
        else:
            row = f'{row} {w}' if row else w
    if row:
        rows.append(row)
    return rows


# ---------- label helpers for schemdraw (keep labels aligned) ----------

def side_label(el, text, dx=0.5):
    """Label to the right of a vertical part, left aligned and centred on the part."""
    import schemdraw.elements as elm
    c = el.center
    elm.Label().at((c[0] + dx, c[1])).label(text, halign='left', valign='center')


def pin_numbers(gate, pin_in, pin_out):
    """Pin numbers above the input and output wires of a logic gate."""
    import schemdraw.elements as elm
    elm.Label().at((gate.in1[0] - 0.25, gate.in1[1] + 0.12)).label(pin_in, halign='right', valign='bottom')
    elm.Label().at((gate.out[0] + 0.25, gate.out[1] + 0.12)).label(pin_out, halign='left', valign='bottom')


def numbered(notes, width_px):
    """Numbered list with a hanging indent, wrapped to a column width."""
    rows = []
    for i, note in enumerate(notes, 1):
        prefix = f'{i}. '
        wrapped = wrap(note, width_px - len(prefix) * CHAR)
        rows.append(prefix + wrapped[0])
        rows += [' ' * len(prefix) + r for r in wrapped[1:]]
    return rows
