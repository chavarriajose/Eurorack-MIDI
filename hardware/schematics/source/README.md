# Schematic sources

The schematics are drawn in Python with [schemdraw](https://schemdraw.readthedocs.io/) and laid out on a shared page grid (`layout.py`). All text is set in JetBrains Mono and converted to paths, so the images look the same everywhere.

| File | Draws |
|---|---|
| `layout.py` | Page grid, text styles, header, footer and helpers |
| `input_channel.py` | `../input-channel.svg` |
| `output_channel.py` | `../output-channel.svg` |
| `full_circuit.py` | `../full-circuit.svg` |
| `fonts/` | JetBrains Mono Regular and Bold, with their license (SIL Open Font License 1.1) |

To regenerate the images, from this folder:

```
pip install schemdraw ziafont ziamath
python3 input_channel.py
python3 output_channel.py
python3 full_circuit.py
```

To make the PNG versions:

```
pip install cairosvg
python3 -c "import cairosvg; [cairosvg.svg2png(url=f'../{n}.svg', write_to=f'../{n}.png', scale=2) for n in ['input-channel', 'output-channel', 'full-circuit']]"
```

Text styles: titles in bold 28, section headings in bold 15, and all other text (including every label in the schematics) in regular 13.
