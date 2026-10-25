"""Draws ../output-channel.svg: one output channel."""

import os
import sys
import schemdraw
import schemdraw.elements as elm
import layout as L

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(L.HERE, '..', 'output-channel.svg')

# ---------- signal path ----------
with schemdraw.Drawing(show=False) as main:
    L.setup_drawing(main)
    elm.Dot(open=True).at((0, 0)).label('ESP32-S3\nGPIO 8', loc='left', halign='right')
    elm.Resistor().right().label('R1 10k')
    b = elm.Dot()
    L.side_label(elm.Resistor().at(b.center).down(2.5), 'R2\n100k')
    elm.Ground()
    elm.Line().at(b.center).right(1)
    Q = elm.BjtNpn(circle=True).anchor('base')
    elm.Label().at((Q.center[0] + 0.75, Q.center[1] - 0.2)).label('Q1\n2N3904', halign='left', valign='center')
    elm.Line().at(Q.emitter).down(0.8)
    elm.Ground()
    elm.Line().at(Q.collector).up(0.6)
    c = elm.Dot()
    L.side_label(elm.Resistor().at(c.center).up(2), 'R3\n1k')
    elm.Vdd().label('+5V')
    elm.Resistor().at(c.center).right(3).label('R4 1k')
    elm.Line().right(1)
    J = elm.AudioJack().anchor('tip').reverse().label('Output_1', loc='top')
    elm.Line().at(J.sleeve).down(0.6)
    elm.Ground()

# ---------- page ----------
page = L.Page(900)
page.header('Output channel',
            'Built 5 times, one per output jack. Turns the 3.3V of the ESP32-S3 into a 5V trigger.')

y = page.heading('Signal path', L.MARGIN, page.y)
_, h = page.schematic(main, L.MARGIN, y)
page.y = y + h + L.SECTION

(x1, w1), (x2, w2), (x3, w3) = page.columns(3)
top = page.y

y = page.heading('How it works', x1, top)
bottom1 = page.table('GPIO   Q1    Jack', ['HIGH   on    0V', 'LOW    off   about 5V'], x1, y)

y = page.heading('Pin map', x2, top)
rows = ['Output_1  GPIO 8',
        'Output_2  GPIO 9',
        'Output_3  GPIO 10',
        'Output_4  GPIO 11',
        'Output_5  GPIO 12']
bottom2 = page.table('Jack      ESP32-S3', rows, x2, y)

y = page.heading('Parts', x3, top)
bottom3 = page.table('Ref  Value', ['R1   10k', 'R2   100k', 'R3   1k', 'R4   1k', 'Q1   2N3904'], x3, y)

page.y = max(bottom1, bottom2, bottom3) + L.SECTION
y = page.heading('Notes', L.MARGIN, page.y)
notes = [
    'The stage inverts the signal. The code handles it, so a Note On makes the jack high.',
    '+5V comes from the USB power on the 5V pin of the ESP32-S3. On clone boards, bridge the IN-OUT pad to get it.',
    'R2 keeps Q1 off while the ESP32-S3 boots.',
    'R4 protects the output if it is patched into another output.',
    'BC547 or BC548 can replace the 2N3904. Their pinout is reversed.',
]
notes = L.numbered(notes, page.width - 2 * L.MARGIN)
page.y = page.lines(notes, L.MARGIN, y + L.BODY)
page.footer()
page.save(out)
