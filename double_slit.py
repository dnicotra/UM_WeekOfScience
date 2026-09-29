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
    from plotly.subplots import make_subplots


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Young's double slit — interference $\times$ diffraction

    Two slits of width $a$, a distance $d$ apart (centre to centre), illuminated by a plane
    wave of wavelength $\lambda$ and observed on a screen a distance $L$ away.
    Far from the slits the pattern is the **interference** of the two slits, modulated by the
    **diffraction** envelope of a single slit:

    $$
    \frac{I(\theta)}{I_0} \;=\;
    \underbrace{\operatorname{sinc}^2\!\left(\frac{a\sin\theta}{\lambda}\right)}_{\text{one slit: diffraction}}
    \;\times\;
    \underbrace{\cos^2\!\left(\frac{\pi d\sin\theta}{\lambda}\right)}_{\text{two slits: interference}}
    \qquad \sin\theta = \frac{y}{\sqrt{y^2+L^2}}
    $$

    Move the sliders and watch which factor is doing what.
    """)
    return


@app.cell(hide_code=True)
def _():
    wavelength_nm = mo.ui.slider(
        380, 780, value=550, step=1, label="$\\lambda$ — wavelength (nm)", show_value=True
    )
    slit_width_um = mo.ui.slider(
        5.0, 300.0, value=40.0, step=1.0, label="$a$ — slit width (µm)", show_value=True
    )
    slit_sep_um = mo.ui.slider(
        20.0, 1500.0, value=250.0, step=5.0, label="$d$ — slit separation (µm)", show_value=True
    )
    screen_dist_m = mo.ui.slider(
        0.2, 5.0, value=2.0, step=0.05, label="$L$ — distance to screen (m)", show_value=True
    )
    half_width_mm = mo.ui.slider(
        2.0, 120.0, value=30.0, step=1.0, label="screen half-width shown (mm)", show_value=True
    )
    show_parts = mo.ui.checkbox(True, label="show the two factors separately")

    mo.hstack(
        [
            mo.vstack([wavelength_nm, slit_width_um, slit_sep_um]),
            mo.vstack([screen_dist_m, half_width_mm, show_parts]),
        ],
        widths="equal",
        gap=2,
    )
    return (
        half_width_mm,
        screen_dist_m,
        show_parts,
        slit_sep_um,
        slit_width_um,
        wavelength_nm,
    )


@app.cell(hide_code=True)
def _(half_width_mm, screen_dist_m, slit_sep_um, slit_width_um, wavelength_nm):
    lam_m = wavelength_nm.value * 1e-9
    a_m = slit_width_um.value * 1e-6
    d_m = slit_sep_um.value * 1e-6
    L_m = screen_dist_m.value

    y_mm = np.linspace(-half_width_mm.value, half_width_mm.value, 2001)
    sin_theta = (y_mm * 1e-3) / np.hypot(y_mm * 1e-3, L_m)

    # np.sinc(x) = sin(pi x) / (pi x), so the argument is a sin(theta) / lambda
    diffraction = np.sinc(a_m * sin_theta / lam_m) ** 2
    interference = np.cos(np.pi * d_m * sin_theta / lam_m) ** 2
    total = diffraction * interference
    return L_m, a_m, d_m, diffraction, interference, lam_m, total, y_mm


@app.function(hide_code=True)
def wavelength_to_rgb(nm, gamma=0.8):
    """Approximate sRGB colour of a monochromatic wavelength (Bruton's algorithm)."""
    nm = float(nm)
    if 380 <= nm < 440:
        r, g, b = -(nm - 440) / 60, 0.0, 1.0
    elif 440 <= nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif 490 <= nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / 20
    elif 510 <= nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif 580 <= nm < 645:
        r, g, b = 1.0, -(nm - 645) / 65, 0.0
    elif 645 <= nm <= 780:
        r, g, b = 1.0, 0.0, 0.0
    else:
        r = g = b = 0.0

    if 380 <= nm < 420:  # eye response fades at both ends of the visible range
        fade = 0.3 + 0.7 * (nm - 380) / 40
    elif 700 < nm <= 780:
        fade = 0.3 + 0.7 * (780 - nm) / 80
    else:
        fade = 1.0

    return tuple(int(round(255 * (c * fade) ** gamma)) for c in (r, g, b))


@app.cell(hide_code=True)
def _(wavelength_nm):
    _rgb = wavelength_to_rgb(wavelength_nm.value)
    colour = "rgb({}, {}, {})".format(*_rgb)
    colour_soft = "rgba({}, {}, {}, 0.25)".format(*_rgb)
    return colour, colour_soft


@app.cell(hide_code=True)
def _(colour, colour_soft, diffraction, interference, show_parts, total, y_mm):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.22, 0.78], vertical_spacing=0.05
    )

    # what the screen actually looks like (gamma-corrected so faint fringes stay visible)
    fig.add_trace(
        go.Heatmap(
            z=[total**0.6],
            x=y_mm,
            colorscale=[[0.0, "rgb(0, 0, 0)"], [1.0, colour]],
            zmin=0.0,
            zmax=1.0,
            showscale=False,
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    if show_parts.value:
        fig.add_trace(
            go.Scatter(
                x=y_mm,
                y=diffraction,
                name="diffraction (one slit)",
                line=dict(color="#555555", dash="dash", width=1.6),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=y_mm,
                y=interference,
                name="interference (two slits)",
                line=dict(color="#aaaaaa", dash="dot", width=1.2),
            ),
            row=2,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=y_mm,
            y=total,
            name="total intensity",
            line=dict(color=colour, width=2),
            fill="tozeroy",
            fillcolor=colour_soft,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        template="plotly_white",
        height=560,
        margin=dict(l=70, r=20, t=40, b=55),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
    )
    fig.update_yaxes(
        showticklabels=False, showgrid=False, zeroline=False, title_text="screen", row=1, col=1
    )
    fig.update_yaxes(title_text="I / I₀", range=[0.0, 1.05], row=2, col=1)
    fig.update_xaxes(title_text="position on the screen, y (mm)", row=2, col=1)
    fig
    return


@app.cell(hide_code=True)
def _(L_m, a_m, d_m, lam_m):
    _spacing_mm = lam_m * L_m / d_m * 1e3           # fringe spacing  Δy = λL/d
    _env_mm = lam_m * L_m / a_m * 1e3               # first diffraction zero  y = λL/a
    _ratio = d_m / a_m

    _orders = [m for m in range(-int(_ratio), int(_ratio) + 1)]
    _n_fringes = sum(
        1 for m in _orders if m == 0 or abs(m / _ratio - round(m / _ratio)) > 1e-6
    )
    _missing = (
        "m = ±{}, ±{}, …".format(round(_ratio), 2 * round(_ratio))
        if abs(_ratio - round(_ratio)) < 1e-6 and _ratio >= 1
        else "none (d/a is not an integer)"
    )

    _table = mo.md(
        f"""
        | | |
        |:--|--:|
        | fringe spacing &nbsp; $\\Delta y = \\lambda L / d$ | **{_spacing_mm:.2f} mm** |
        | central envelope, first zero &nbsp; $y = \\lambda L / a$ | **{_env_mm:.1f} mm** |
        | bright fringes inside the central envelope | **{_n_fringes}** |
        | missing orders | {_missing} |
        | $d/a$ | {_ratio:.2f} |
        """
    )

    _warning = (
        mo.md(
            "**Careful:** $d \\le a$ means the slits overlap — the formula still plots, "
            "but it is no longer a physical double slit."
        ).callout(kind="warn")
        if d_m <= a_m
        else mo.md("")
    )

    mo.vstack([_table, _warning])
    return


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ### Things to try

    - **Wavelength**: drag from violet to red — every length in the pattern scales with $\lambda$.
    - **Slit separation $d$**: only the *fringe spacing* $\lambda L/d$ changes; the envelope stays put.
      Wider apart $\Rightarrow$ finer fringes.
    - **Slit width $a$**: only the *envelope* changes. Narrow slits $\Rightarrow$ broad envelope and many
      fringes; wide slits $\Rightarrow$ the envelope squeezes down onto a few fringes.
    - **Missing orders**: set $d$ to an exact multiple of $a$ (e.g. $a = 50$ µm, $d = 250$ µm) —
      the 5th, 10th, … interference maxima land on diffraction zeros and vanish.
    - **Screen distance $L$**: the whole pattern simply magnifies.
    """)
    return


if __name__ == "__main__":
    app.run()
