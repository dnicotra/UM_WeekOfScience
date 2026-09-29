# /// script
# requires-python = ">=3.13"
# dependencies = ["marimo", "numpy", "plotly"]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go

    # The tank, in centimetres. The barrier sits at y = 0, the wave travels +y.
    X_MIN, X_MAX = -14.0, 14.0
    Y_MIN, Y_MAX = -5.0, 19.0
    BARRIER_HALF_T = 0.25
    N_FRAMES = 16  # one period, so the loop is seamless


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    # A ripple tank with two slits

    Plane waves roll in from the bottom, meet a barrier with two gaps, and each gap sends out
    circular wavelets that cross and add. Where two crests meet the water heaves; where a crest
    meets a trough it goes still.

    Every point of an opening is treated as a source of circular wavelets (Huygens), and the
    surface height is their sum — on a 2-D surface each wavelet spreads as $1/\sqrt{r}$:

    $$
    \eta(x, y, t) \;=\; \operatorname{Re}\left\{ e^{-i\omega t} \sum_j \frac{e^{i k r_j}}{\sqrt{r_j}} \right\},
    \qquad r_j = \sqrt{(x - x_j)^2 + y^2},\qquad k = \frac{2\pi}{\lambda}
    $$

    Nothing here is approximated away, so the picture is honest close to the barrier as well as
    far from it — unlike the far-field formula in the companion notebook. Reflection off the
    barrier is the one thing left out.

    **Press ▶ Play on the figure to set the water moving.**
    """
    )
    return


@app.cell(hide_code=True)
def _():
    wavelength_cm = mo.ui.slider(
        1.0, 4.0, value=1.8, step=0.1, label="$\\lambda$ — wavelength (cm)", show_value=True
    )
    slit_sep_cm = mo.ui.slider(
        1.0, 12.0, value=4.0, step=0.1, label="$d$ — slit separation (cm)", show_value=True
    )
    slit_width_cm = mo.ui.slider(
        0.2, 4.0, value=0.6, step=0.1, label="$a$ — slit width (cm)", show_value=True
    )
    speed_ms = mo.ui.dropdown(
        {"slow": 170, "normal": 95, "fast": 55}, value="normal", label="playback"
    )
    quality = mo.ui.dropdown(
        {"fast": (8, 25000), "smooth": (12, 50000), "sharp (slow)": (18, 90000)},
        value="smooth",
        label="grid detail",
    )
    show_incoming = mo.ui.checkbox(True, label="show the incoming plane wave")

    mo.hstack(
        [
            mo.vstack([wavelength_cm, slit_sep_cm, slit_width_cm]),
            mo.vstack([speed_ms, quality, show_incoming]),
        ],
        widths="equal",
        gap=2,
    )
    return (
        quality,
        show_incoming,
        slit_sep_cm,
        slit_width_cm,
        speed_ms,
        wavelength_cm,
    )


@app.function(hide_code=True)
def slit_sources(sep_cm, width_cm, lam_cm):
    """Huygens point sources filling both openings, spaced no coarser than lambda/4."""
    n = int(np.clip(np.ceil(width_cm / (lam_cm / 4.0)) + 1, 1, 21))
    offsets = np.linspace(-width_cm / 2.0, width_cm / 2.0, n) if n > 1 else np.zeros(1)
    return np.concatenate([-sep_cm / 2.0 + offsets, sep_cm / 2.0 + offsets])


@app.function(hide_code=True)
def tank_grid(lam_cm, per_wavelength, max_points):
    """Square cells: this many per wavelength, unless the point budget says coarser."""
    dx = max(lam_cm / per_wavelength, np.sqrt((X_MAX - X_MIN) * (Y_MAX - Y_MIN) / max_points))
    xs = np.linspace(X_MIN, X_MAX, int(round((X_MAX - X_MIN) / dx)) + 1)
    ys = np.linspace(Y_MIN, Y_MAX, int(round((Y_MAX - Y_MIN) / dx)) + 1)
    return xs, ys


@app.function(hide_code=True)
def complex_field(xs, ys, sources, lam_cm, with_incoming):
    """Time-independent amplitude: wavelets past the barrier, plane wave in front of it."""
    k = 2.0 * np.pi / lam_cm
    X, Y = np.meshgrid(xs, ys)

    wavelets = np.zeros(X.shape, dtype=np.complex128)
    for x0 in sources:  # accumulate rather than broadcast, to keep memory flat
        r = np.hypot(X - x0, Y)
        np.maximum(r, 0.15, out=r)
        wavelets += np.exp(1j * k * r) / np.sqrt(r)

    downstream = Y > BARRIER_HALF_T
    # Scale on a high percentile, not the max: the cells touching a slit are singular.
    wavelets /= max(np.percentile(np.abs(wavelets[downstream]), 98.0), 1e-9)

    incoming = np.exp(1j * k * Y) if with_incoming else np.zeros_like(wavelets)
    return np.where(downstream, wavelets, np.where(Y < -BARRIER_HALF_T, incoming, 0.0))


@app.function(hide_code=True)
def period_frames(field):
    """One period of Re{U e^(-i omega t)}, quantised to int8 for a compact payload."""
    return [
        (np.clip(np.real(field * np.exp(-2j * np.pi * i / N_FRAMES)), -1.0, 1.0) * 100.0).astype(
            np.int8
        )
        for i in range(N_FRAMES)
    ]


@app.function(hide_code=True)
def barrier_segments(sep_cm, width_cm):
    """The solid stretches of barrier: everything except the two openings."""
    left, right = -sep_cm / 2.0, sep_cm / 2.0
    edges = [X_MIN, left - width_cm / 2.0, left + width_cm / 2.0,
             right - width_cm / 2.0, right + width_cm / 2.0, X_MAX]
    return [(a, b) for a, b in zip(edges[::2], edges[1::2]) if b - a > 1e-9]


@app.function(hide_code=True)
def far_field_maxima(lam_cm, sep_cm, y_screen):
    """Where the Fraunhofer orders would land on the far edge of the tank."""
    out = []
    for m in range(-12, 13):
        s = m * lam_cm / sep_cm
        if abs(s) < 0.98:
            out.append((m, y_screen * s / np.sqrt(1.0 - s * s)))
    return [(m, x) for m, x in out if X_MIN < x < X_MAX]


@app.cell(hide_code=True)
def _(quality, show_incoming, slit_sep_cm, slit_width_cm, wavelength_cm):
    lam = wavelength_cm.value
    sep = slit_sep_cm.value
    width = slit_width_cm.value

    _per_wavelength, _budget = quality.value
    xs, ys = tank_grid(lam, _per_wavelength, _budget)
    sources = slit_sources(sep, width, lam)
    field = complex_field(xs, ys, sources, lam, show_incoming.value)
    frames = period_frames(field)

    # Time-averaged intensity read off the far edge of the tank, as on a screen.
    screen = np.abs(field[-1]) ** 2
    screen = screen / max(screen.max(), 1e-12)
    return field, frames, lam, screen, sep, sources, width, xs, ys


@app.cell(hide_code=True)
def _():
    # Diverging blue <-> red with a neutral midpoint: the surface height is signed, and zero
    # means "flat water". The red arm is the blue ramp's hues held at matching OKLab lightness,
    # so neither crests nor troughs read as the heavier half.
    _blue = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]
    _red = ["#fad6d2", "#f1aea8", "#e4857d", "#d75852", "#b13f3c", "#892c2a", "#621b1a"]

    try:
        _dark = mo.app_meta().theme == "dark"
    except Exception:
        _dark = False

    if _dark:
        # Selected for the dark surface, not flipped: the extremes stay bright and the flat
        # water sinks into the background.
        _ramp = _blue[::-1] + ["#383835"] + _red[::-1]
        theme = dict(
            surface="#1a1a19", ink="#ffffff", muted="#898781", grid="#2c2c2a",
            barrier="#c3c2b7", series="#3987e5", series_soft="rgba(57, 135, 229, 0.22)",
            template="plotly_dark",
        )
    else:
        _ramp = _blue + ["#f0efec"] + _red
        theme = dict(
            surface="#fcfcfb", ink="#0b0b0b", muted="#898781", grid="#e1e0d9",
            barrier="#52514e", series="#2a78d6", series_soft="rgba(42, 120, 214, 0.18)",
            template="plotly_white",
        )

    water = [[i / (len(_ramp) - 1), c] for i, c in enumerate(_ramp)]
    return theme, water


@app.cell(hide_code=True)
def _(frames, sep, speed_ms, theme, water, width, xs, ys):
    tank = go.Figure(
        data=[
            go.Heatmap(
                z=frames[0],
                x=xs,
                y=ys,
                zmin=-100,
                zmax=100,
                colorscale=water,
                showscale=False,
                zsmooth="best",
                hovertemplate="x = %{x:.1f} cm<br>y = %{y:.1f} cm<br>height = %{z} %<extra></extra>",
            )
        ],
        frames=[
            go.Frame(data=[go.Heatmap(z=z)], traces=[0], name=str(i))
            for i, z in enumerate(frames)
        ],
    )

    for _x0, _x1 in barrier_segments(sep, width):
        tank.add_shape(
            type="rect",
            x0=_x0,
            x1=_x1,
            y0=-BARRIER_HALF_T,
            y1=BARRIER_HALF_T,
            fillcolor=theme["barrier"],
            line_width=0,
            layer="above",
        )

    tank.update_layout(
        template=theme["template"],
        height=620,
        margin=dict(l=60, r=20, t=60, b=55),
        paper_bgcolor=theme["surface"],
        plot_bgcolor=theme["surface"],
        font=dict(color=theme["ink"]),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                showactive=False,
                x=0.0,
                y=1.04,
                xanchor="left",
                yanchor="bottom",
                pad=dict(r=8, t=0),
                bgcolor=theme["surface"],
                bordercolor=theme["muted"],
                font=dict(color=theme["ink"], size=13),
                buttons=[
                    dict(
                        label="▶  Play",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=speed_ms.value, redraw=True),
                                fromcurrent=True,
                                transition=dict(duration=0),
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏸  Pause",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
    )
    tank.update_xaxes(
        title_text="across the tank, x (cm)", constrain="domain", showgrid=False, zeroline=False
    )
    tank.update_yaxes(
        title_text="direction of travel, y (cm)",
        scaleanchor="x",
        scaleratio=1,
        constrain="domain",
        showgrid=False,
        zeroline=False,
    )
    tank
    return


@app.cell(hide_code=True)
def _(lam, screen, sep, theme, xs, ys):
    profile = go.Figure()
    profile.add_trace(
        go.Scatter(
            x=xs,
            y=screen,
            mode="lines",
            line=dict(color=theme["series"], width=2),
            fill="tozeroy",
            fillcolor=theme["series_soft"],
            hovertemplate="x = %{x:.1f} cm<br>intensity = %{y:.2f}<extra></extra>",
        )
    )

    for _m, _x in far_field_maxima(lam, sep, ys[-1]):
        profile.add_vline(
            x=_x,
            line=dict(color=theme["muted"], width=1, dash="dot"),
            annotation_text=f"m={_m}",
            annotation_position="top",
            annotation_font=dict(color=theme["muted"], size=10),
        )

    profile.update_layout(
        template=theme["template"],
        height=260,
        margin=dict(l=60, r=20, t=40, b=55),
        paper_bgcolor=theme["surface"],
        plot_bgcolor=theme["surface"],
        font=dict(color=theme["ink"]),
        showlegend=False,
        title=dict(
            text=f"Time-averaged intensity along the far edge of the tank (y = {ys[-1]:.0f} cm)",
            font=dict(size=13, color=theme["ink"]),
            x=0.0,
            xanchor="left",
        ),
    )
    profile.update_xaxes(
        title_text="across the tank, x (cm)",
        range=[xs[0], xs[-1]],
        gridcolor=theme["grid"],
        zeroline=False,
    )
    profile.update_yaxes(
        title_text="intensity (normalised)", range=[0, 1.05], gridcolor=theme["grid"], zeroline=False
    )
    profile
    return


@app.cell(hide_code=True)
def _(lam, sep, sources, width, xs, ys):
    _orders = far_field_maxima(lam, sep, ys[-1])
    _theta = np.degrees(np.arcsin(min(lam / sep, 1.0)))
    _cells = f"{len(xs)} × {len(ys)}"

    _table = mo.md(
        f"""
        | | |
        |:--|--:|
        | angle of the first side maximum, $\\sin\\theta = \\lambda/d$ | **{_theta:.1f}°** |
        | orders reaching the far edge | **{len(_orders)}** (m = {_orders[0][0]} … {_orders[-1][0]}) |
        | $d/\\lambda$ | {sep / lam:.2f} |
        | Huygens sources across the two openings | {len(sources)} |
        | grid | {_cells} cells, {N_FRAMES} frames per period |
        """
        if _orders
        else f"""
        | | |
        |:--|--:|
        | $\\lambda/d$ | {lam / sep:.2f} — **larger than 1, so there are no side maxima at all** |
        | Huygens sources across the two openings | {len(sources)} |
        | grid | {_cells} cells, {N_FRAMES} frames per period |
        """
    )

    _merged = (
        mo.md(
            "**The two openings have merged.** With $a \\ge d$ there is one wide gap left, so "
            "what you see is single-slit diffraction, not two-slit interference."
        ).callout(kind="warn")
        if width >= sep
        else mo.md("")
    )

    mo.vstack([_table, _merged])
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        r"""
    ### Things to try

    - **Pull the slits apart** ($d$ up): the beams fan out into more, narrower lobes — the first
      side maximum swings in towards the axis as $\sin\theta = \lambda/d$.
    - **Push them together** until $d < \lambda$: every side maximum leaves the tank and the pair
      radiates like a single source. Two slits closer than a wavelength cannot interfere on the
      screen.
    - **Widen the slits** ($a$ up): each opening starts beaming forward instead of spreading, so
      the outer lobes fade — that is the diffraction envelope, arriving on its own out of the
      Huygens sum.
    - **Longer wavelength** with $d$ fixed: everything spreads. Ripple tanks are run at long
      wavelengths for exactly this reason.
    - Compare the dotted far-field orders on the lower plot with the peaks the exact sum
      actually produces. Close to the barrier they do not quite agree, and that gap is the
      difference between this notebook and the Fraunhofer one.
    """
    )
    return


if __name__ == "__main__":
    app.run()
