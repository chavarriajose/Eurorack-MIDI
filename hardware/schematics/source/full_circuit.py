"""Draws ../full-circuit.svg: the complete Eurorack-MIDI v0 circuit."""

import os
import sys
import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import layout as L

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(L.HERE, '..', 'full-circuit.svg')

P = 7.0  # vertical distance between channels

# jack name, CD40106 gate, gate input pin, gate output pin, ESP32-S3 pin
inputs = [
    ('Input_1', 'U1D', '9', '8', 'GPIO 15'),
    ('Input_2', 'U1C', '5', '6', 'GPIO 16'),
    ('Input_3', 'U1B', '3', '4', 'GPIO 17'),
    ('Input_4', 'U1A', '1', '2', 'GPIO 18'),
    ('Input_5', 'U1E', '11', '10', 'GPIO 6'),
]
outputs = [
    ('Output_1', 'GPIO 8'), ('Output_2', 'GPIO 9'), ('Output_3', 'GPIO 10'),
    ('Output_4', 'GPIO 11'), ('Output_5', 'GPIO 12'),
]

_jack = elm.AudioJack()
_jack._place((0, 0), 0)
TIP_DY = _jack.anchors['tip'][1]


def pin(name, side):
    return elm.IcPin(name=name, side=side, anchorname=name.replace(' ', ''), lblsize=L.BODY)


# ---------- circuit ----------
with schemdraw.Drawing(show=False) as main:
    L.setup_drawing(main)

    # left and right pins are listed bottom to top
    pins = [pin(p[4], 'left') for p in reversed(inputs)]
    pins += [pin(o[1], 'right') for o in reversed(outputs)]
    pins += [pin('3V3', 'top'), pin('5V', 'top'), pin('GND', 'bottom')]
    esp = elm.Ic(pins=pins, pinspacing=P, edgepadH=1.5, edgepadW=2.0, leadlen=1.0,
                 lofst=0.2).at((0, 0)).label('ESP32-S3\nDevKitC-1', fontsize=L.BODY)
    elm.Dot(radius=0.001).at((0, 0))  # places the IC so its pin positions exist

    elm.Line().at(esp.anchors['3V3']).up(0.6)
    elm.Vdd().label('+3.3V')
    elm.Line().at(esp.anchors['5V']).up(0.6)
    elm.Vdd().label('+5V')
    elm.Line().at(esp.anchors['GND']).down(0.4)
    elm.Ground()

    # inputs
    for name, gate, pin_in, pin_out, gpio in inputs:
        a = esp.anchors[gpio.replace(' ', '')]
        J = elm.AudioJack().right().at((a[0] - 19, a[1] - TIP_DY)).label(name, loc='top')
        elm.Line().at(J.sleeve).down(0.4)
        elm.Ground()
        elm.Line().at(J.tip).right(0.8)
        elm.Resistor().right().label('22k')
        n1 = elm.Dot()
        L.side_label(elm.Diode().at(n1.center).up(1.6), '1N5819')
        elm.Vdd().label('+3.3V')
        elm.Line().at(n1.center).right(1.8)
        n2 = elm.Dot()
        L.side_label(elm.Resistor().at(n2.center).down(2.2), '100k')
        elm.Ground()
        elm.Line().at(n2.center).right(2.0)
        n3 = elm.Dot()
        L.side_label(elm.Diode().at(n3.center).down(2.2).reverse(), '1N5819')
        elm.Ground()
        elm.Line().at(n3.center).right(2.6)
        U = logic.SchmittNot().anchor('in1').right().label(gate, loc='bottom')
        L.pin_numbers(U, pin_in, pin_out)
        elm.Line().at(U.out).to(a)

    # outputs
    for name, gpio in outputs:
        a = esp.anchors[gpio.replace(' ', '')]
        elm.Line().at(a).right(0.8)
        elm.Resistor().right().label('10k')
        b = elm.Dot()
        L.side_label(elm.Resistor().at(b.center).down(2.2), '100k')
        elm.Ground()
        elm.Line().at(b.center).right(1.2)
        Q = elm.BjtNpn(circle=True).anchor('base')
        elm.Label().at((Q.center[0] + 0.75, Q.center[1] - 0.25)).label('2N3904', halign='left', valign='center')
        elm.Line().at(Q.emitter).down(0.5)
        elm.Ground()
        elm.Line().at(Q.collector).up(0.4)
        c = elm.Dot()
        L.side_label(elm.Resistor().at(c.center).up(1.8), '1k')
        elm.Vdd().label('+5V')
        elm.Resistor().at(c.center).right(2.6).label('1k')
        elm.Line().right(1.4)
        J = elm.AudioJack().anchor('tip').reverse().label(name, loc='top')
        elm.Line().at(J.sleeve).down(0.4)
        elm.Ground()

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
_, _, _, main_w, _ = L.drawing_svg(main)
page = L.Page(int(main_w + 2 * L.MARGIN))
page.header('Full circuit',
            '5 protected inputs through a CD40106, 5 transistor outputs, and an ESP32-S3 as a USB MIDI device.')

y = page.heading('Circuit', L.MARGIN, page.y)
_, h = page.schematic(main, L.MARGIN, y)
page.y = y + h + L.SECTION

(x1, w1), (x2, w2), (x3, w3) = page.columns(3)
top = page.y

y = page.heading('CD40106 power', x1, top)
_, h1 = page.schematic(power, x1, y)
bottom1 = y + h1

y = page.heading('Spare gate', x2, top)
_, h2 = page.schematic(spare, x2, y)
bottom2 = y + h2

y = page.heading('Notes', x3, top)
notes = [
    'Input_5 is also the clock input.',
    'All jack sleeves and grounds connect together.',
    'On clone ESP32-S3 boards, bridge the IN-OUT pad so the 5V pin carries USB power.',
    'GPIO 0, 3, 45 and 46 are avoided: they decide how the ESP32-S3 boots.',
    'A 1N4148 can replace the 1N5819.',
]
bottom3 = page.lines(L.numbered(notes, w3), x3, y + L.BODY)

page.y = max(bottom1, bottom2, bottom3)
page.footer()
page.save(out)
