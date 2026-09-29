# Waves through two slits

Two interactive [marimo](https://marimo.io) notebooks for the Week of Science, published
together as one static site that runs entirely in the visitor's browser.

| Notebook | What it shows |
|---|---|
| `double_slit.py` | The far-field (Fraunhofer) pattern of a double slit: two-slit interference under the single-slit diffraction envelope, as you change $\lambda$, the slit width $a$, the separation $d$ and the distance $L$ to the screen. Missing orders appear when $d/a$ is an integer. |
| `water_waves.py` | A ripple tank. Plane waves meet a barrier with two gaps, and the field beyond it is summed from Huygens wavelets — exactly, with no far-field approximation. Press ▶ Play to set the water moving. |

The first is a closed-form formula, the second an explicit sum over sources, so the two
disagree slightly near the barrier — the ripple tank plots the far-field orders as dotted
lines next to the peaks the exact sum actually produces.

## Run them locally

No install beyond [uv](https://docs.astral.sh/uv/) — the dependencies are in each script
header:

```bash
uvx marimo edit --sandbox double_slit.py     # edit
uvx marimo run  --sandbox water_waves.py     # present, code hidden
```

## The published site

`tools/build_site.sh` exports each notebook to WebAssembly and merges them into one tree:

```
site/index.html          <- pages/index.html, the landing page
site/double-slit.html
site/water-waves.html
site/assets/             <- marimo's frontend, one copy shared by both pages
```

Both exports ship the same content-hashed frontend, so merging them leaves one 27 MB copy
instead of two. `tools/check_site.py` then verifies that every relative reference on every page
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
