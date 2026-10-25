"""Draws ../input-channel.svg: one input channel, the CD40106 power and the spare gate."""

import os
import sys
import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import layout as L

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(L.HERE, '..', 'input-channel.svg')


# ---------- main signal path ----------
with schemdraw.Drawing(show=False) as main:
    L.setup_drawing(main)
    J = elm.AudioJack().right().label('Input_1', loc='top')
    elm.Line().at(J.sleeve).down(0.6)
    elm.Ground()
    elm.Line().at(J.tip).right(1)
    elm.Resistor().right().label('R1 22k')
    n1 = elm.Dot()
    L.side_label(elm.Diode().at(n1.center).up(2), 'D1\n1N5819')
    elm.Vdd().label('+3.3V')
    elm.Line().at(n1.center).right(1.8)
    n2 = elm.Dot()
    L.side_label(elm.Resistor().at(n2.center).down(2.5), 'R2\n100k')
    elm.Ground()
    elm.Line().at(n2.center).right(1.8)
    n3 = elm.Dot()
    L.side_label(elm.Diode().at(n3.center).down(2.5).reverse(), 'D2\n1N5819')
    elm.Ground()
    elm.Line().at(n3.center).right(1.4)
    U = logic.SchmittNot().anchor('in1').right().label('U1D', loc='bottom')
    L.pin_numbers(U, '9', '8')
    elm.Line().at(U.out).right(1.8)
    elm.Dot(open=True).label('ESP32-S3\nGPIO 15', loc='right', halign='left')

# ---------- CD40106 power ----------
with schemdraw.Drawing(show=False) as power:
    L.setup_drawing(power)
    elm.Vdd().at((0, 0)).label('+3.3V')
    elm.Line().at((0, 0)).down(0.6)
    t = elm.Dot()
    elm.Line().right(1.6)
    elm.Dot(open=True).label('U1 pin 14', loc='right', halign='left')
    L.side_label(elm.Capacitor().at(t.center).down(2), 'C1\n0.22µF')
    elm.Ground()
    elm.Dot(open=True).at((1.6, -2.6)).label('U1 pin 7', loc='right', halign='left')
    elm.Line().down(0.4)
    elm.Ground()

# ---------- spare gate ----------
with schemdraw.Drawing(show=False) as spare:
    L.setup_drawing(spare)
    elm.Vdd().at((0, 0)).label('+3.3V')
    elm.Line().at((0, 0)).down(0.8)
    elm.Line().right(0.8)
    S = logic.SchmittNot().anchor('in1').right().label('U1F', loc='bottom')
    L.pin_numbers(S, '13', '12')
    elm.Label().at((S.out[0] + 1.0, S.out[1])).label('not connected', halign='left', valign='center')

# ---------- page ----------
page = L.Page(900)
page.header('Input channel',
            'Built 5 times, one per input jack. Clamps any eurorack voltage and cleans up the gate.')

y = page.heading('Signal path', L.MARGIN, page.y)
w, h = page.schematic(main, L.MARGIN, y)
page.y = y + h + L.SECTION

cols = page.columns(3)
top = page.y
(x1, w1), (x2, w2), (x3, w3) = cols

y = page.heading('CD40106 power', x1, top)
_, h1 = page.schematic(power, x1, y)
bottom1 = y + h1

y = page.heading('Spare gate', x2, top)
_, h2 = page.schematic(spare, x2, y)
bottom2 = y + h2

y = page.heading('Pin map', x3, top)
rows = ['Input_1  9 / 8      GPIO 15',
        'Input_2  5 / 6      GPIO 16',
        'Input_3  3 / 4      GPIO 17',
        'Input_4  1 / 2      GPIO 18',
        'Input_5  11 / 10    GPIO 6']
bottom3 = page.table('Jack     U1 in/out  ESP32-S3', rows, x3, y)

page.y = max(bottom1, bottom2, bottom3) + L.SECTION
y = page.heading('Notes', L.MARGIN, page.y)
notes = [
    'The signal path shows Input_1. The other inputs use the same parts, see the pin map.',
    'Use the same ground for every jack sleeve and the ESP32-S3.',
    'The CD40106 inverts the signal. The code reads it inverted, so a high gate is a Note On.',
    'A 1N4148 can replace the 1N5819.',
]
notes = L.numbered(notes, page.width - 2 * L.MARGIN)
page.y = page.lines(notes, L.MARGIN, y + L.BODY)
page.footer()
page.save(out)
