# Young's double slit

An interactive [marimo](https://marimo.io) notebook for the Week of Science: it plots the
far-field pattern of a double slit — the interference of the two slits under the diffraction
envelope of a single one — as you drag the wavelength, the slit width, the slit separation and
the distance to the screen.

$$
\frac{I(\theta)}{I_0} = \operatorname{sinc}^2\!\left(\frac{a\sin\theta}{\lambda}\right)\cos^2\!\left(\frac{\pi d\sin\theta}{\lambda}\right),
\qquad \sin\theta = \frac{y}{\sqrt{y^2+L^2}}
$$

## Run it locally

No install needed beyond [uv](https://docs.astral.sh/uv/) — the dependencies live in the
script header:

```bash
uvx marimo edit --sandbox double_slit.py    # edit
uvx marimo run  --sandbox double_slit.py    # present, code hidden
```

## Published version

Pushing to `main` builds a WebAssembly export and publishes it to GitHub Pages
(`.github/workflows/deploy.yml`), so the notebook runs entirely in the visitor's browser
through Pyodide — no server. The first load pulls the Python runtime and numpy from a CDN, so
give it a few seconds.

To build the same thing by hand:

```bash
uvx marimo export html-wasm double_slit.py -o site --mode run
python -m http.server --directory site
```

> **Keep the dependencies unpinned** in the script header. Exporting from an environment that
> has numpy and plotly installed makes marimo rewrite the header with exact versions, and a
> pinned numpy cannot be installed in the browser — Pyodide ships its own wasm32 build (numpy
> 2.4.3 on Python 3.14 at the time of writing) and nothing can be compiled there. The workflow
> exports from a marimo-only environment and fails the build if a pin sneaks back in.
