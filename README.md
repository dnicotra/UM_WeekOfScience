# Playing with waves

Three interactive [marimo](https://marimo.io) notebooks for the Weekend of Science, plus a
logbook for the real double-slit experiment at the stand, written for children aged 6–14 and
their parents, in English and Dutch. They are published together as one static site that runs
entirely in the visitor's browser. The text is kept plain; each notebook keeps its formulas in
a collapsed "For grown-ups" section at the bottom.

| Notebook | What it shows |
|---|---|
| `what_is_a_wave.py` | A travelling sine wave seen from the side, with a duck that only bobs up and down as it passes. Sliders for the amplitude and the wavelength; the speed is fixed, so shorter waves make the duck bob faster. Animated on a canvas, like the ripple tank. |
| `double_slit.py` | The far-field (Fraunhofer) pattern of a double slit: two-slit interference under the single-slit diffraction envelope, as you change $\lambda$, the slit width $a$, the separation $d$ and the distance $L$ to the screen. Missing orders appear when $d/a$ is an integer. |
| `water_waves.py` | A ripple tank. Plane waves meet a barrier with two gaps, and the field beyond it is summed from Huygens wavelets — exactly, with no far-field approximation. It starts moving on its own and loops, with the time-averaged intensity plotted above it on the same horizontal scale. |
| `measurement_logbook.py` | A logbook for the real Young's experiment. Each visitor enters $L$, the slits' $d$ and $a$, and a distance measured across $n$ fringe spacings; it works out $\lambda = d\,\Delta y/L$, names the colour, and flags a result outside the visible range (and the classic slip of measuring the envelope instead of the fringes). Everyone's results are plotted and tabled, and the logbook survives a page refresh (see below). |

The first is a closed-form formula, the second an explicit sum over sources, so the two
disagree slightly near the barrier — the ripple tank plots the far-field orders as dotted
lines next to the peaks the exact sum actually produces.

The ripple tank animates on a `<canvas>` inside `mo.iframe` rather than with a plotting
library. The field is time-harmonic, so one complex amplitude is computed in Python and every
frame is a phase rotation of it done in the browser: that is what lets it start by itself (no
library offers declarative autoplay), loop seamlessly, run at refresh rate with no Python per
frame, and put the intensity plot on the same pixel grid as the tank so the two genuinely
line up. It costs the zoom and hover that a plotting library gives for free; a crosshair
readout stands in.

## Run them locally

No install beyond [uv](https://docs.astral.sh/uv/) — the dependencies are in each script
header:

```bash
uvx marimo edit --sandbox double_slit.py     # edit
uvx marimo run  --sandbox water_waves.py     # present, code hidden
```

## Two languages, one source

Each notebook holds its English and Dutch text side by side, as `tr(en=..., nl=...)`, and
shows the language named on the `LANG = "en"` line of its setup cell. Numbers follow it too
(`num()` writes 2,50 in Dutch). The build exports every notebook once per language by
rewriting that line in a copy, so the code exists once and only the wording can differ.

To preview Dutch locally, set `LANG = "nl"` in the editor, and set it back before
committing: the build refuses a notebook whose line does not say `"en"`. Adding a language
means another argument to `tr`, and another line in the build's `NOTEBOOKS` list.

## Where the logbook keeps its measurements

The logbook is a JSON file, written after every change, so a refresh or a closed tab loses
nothing:

- **Run locally** (`marimo run measurement_logbook.py`), it is `measurement_logbook.json` next
  to the notebook (git-ignored).
- **On the published site** Python runs in the browser, where files live in memory and vanish
  with the page. The notebook therefore mounts Emscripten's IDBFS on its folder: the folder is
  filled from the browser's IndexedDB when the page opens, and copied back after every write.
  It is per browser and per site, so the English and Dutch pages share one logbook, and
  clearing the site's data in the browser deletes it. If the browser refuses IndexedDB, the
  page says so and keeps the logbook in memory only.

Either way the page can download the logbook as a CSV (with `;` and decimal commas on the Dutch
page, as Dutch Excel expects). Use one tab at a time: two tabs each keep their own copy, and the
one that saves last wins.

## The published site

`tools/build_site.sh` exports each notebook to WebAssembly once per language and merges
them into one tree:

```
site/index.html                                    <- pages/index.html, the landing page
site/what-is-a-wave.html   site/wat-is-een-golf.html
site/water-waves.html      site/watergolven.html
site/double-slit.html      site/dubbele-spleet.html
site/measurement-logbook.html  site/meetlogboek.html
site/assets/                                       <- marimo's frontend, shared by all eight
```

The Dutch pages get Dutch names because the export titles a page after its file name. The
landing page carries both languages and shows one: the visitor's choice if they made one,
otherwise Dutch for a Dutch browser and English for everyone else.

All eight exports ship the same content-hashed frontend, so merging them leaves one 27 MB copy
instead of eight. `tools/check_site.py` then verifies that every relative reference on every page
resolves inside the tree, which is the failure mode that merging could introduce.

Pushing to `main` runs that script and publishes the result
(`.github/workflows/deploy.yml`). The pages need no server: Pyodide runs the notebooks in the
browser. It does fetch the Python runtime and numpy from a CDN on first load, so expect a few
seconds of spinner.

To build it by hand:

```bash
tools/build_site.sh site
python -m http.server --directory site
```

> **Keep the dependencies unpinned** in the script headers. Exporting from an environment that
> has numpy and plotly installed makes marimo rewrite the header with exact versions, and a
> pinned numpy cannot be installed in the browser — Pyodide ships its own wasm32 build (numpy
> 2.4.3 on Python 3.14 at the time of writing) and nothing can be compiled there. The build
> exports from a marimo-only environment, and the workflow fails if a pin sneaks back in.
