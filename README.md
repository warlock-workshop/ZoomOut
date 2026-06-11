# ZoomOut

Guess the painting. You start zoomed deep into a famous artwork — every zoom-out
costs points, every wrong guess too. Guess without zooming at all and you take
the full 1000.

A single-file mobile-first web game: open `index.html` in any browser and play.
No build, no server, no dependencies.

## How it works

- 50 famous public-domain paintings, images hotlinked from Wikimedia Commons.
- Hold the blue **−** button (or pinch) to zoom out — fluidly, and one-way only:
  there's no zooming back in.
- Green **✓** opens the guess field (autocomplete over titles and artists),
  red **✕** gives up.
- Scoring: 1000 untouched; first zoom-out costs a flat 200, then a gentle slide
  down to 100 at full view. Wrong guesses cost 120.
- Tap the painting to hide the UI and just look.

## Development

`generate.py` (Python 3, stdlib only) refreshes the painting data: it resolves
image URLs and two-sentence descriptions from Wikipedia and injects them into
`index.html` between the `PAINTINGS:START/END` markers. Edit the `CURATED`
list to change the roster. Re-running preserves hand-tuned `focal` /
`startScale` values. The game itself never needs Python.

All paintings are public domain; descriptions are from Wikipedia
(CC BY-SA).
