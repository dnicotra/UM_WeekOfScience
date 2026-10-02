# /// script
# requires-python = ">=3.13"
# dependencies = ["marimo", "numpy", "plotly"]
# ///

import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    # The page's language, "en" or "nl". tools/build_site.sh exports each notebook once per
    # language by rewriting this line, so keep it a plain literal on a line of its own.
    LANG = "en"


@app.function(hide_code=True)
def tr(en, nl):
    """The text for this page's language. Both sit side by side so they stay in step."""
    return nl if LANG == "nl" else en


@app.function(hide_code=True)
def num(x, digits):
    """A number with this page's decimal mark: 2.50 in English, 2,50 in Dutch."""
    text = f"{x:.{digits}f}"
    return text.replace(".", ",") if LANG == "nl" else text


@app.cell(hide_code=True)
def _():
    mo.md(
        tr(
            en=r"""
    # Light through two tiny slits

    What happens if you shine light through **two very thin slits**, right next to each other?
    You might expect two bright lines on the wall behind them. Instead you get a whole row of
    **bright and dark stripes**!

    That is because light is a **wave**, just like the ripples on a pond. The waves coming out
    of the two slits overlap on the screen:

    - where the top of one wave meets the top of another, they add up and the screen is **bright**;
    - where a top meets a dip, they cancel each other out and the screen stays **dark**.

    More than 200 years ago, Thomas Young did this experiment and showed that light really is
    a wave.

    The coloured strip at the top of the picture is what you would see on the screen. The curve
    under it shows how bright each spot is. Move the sliders and see what happens!

    **Tiny sizes:** light waves are so small that almost 2 000 of them fit in one millimetre, so
    the colour of the light is measured in *nanometres* (nm, a millionth of a millimetre). The
    slits are measured in *micrometres* (µm, a thousandth of a millimetre). A hair is about
    70 µm thick.
    """,
            nl=r"""
    # Licht door twee smalle spleetjes

    Wat gebeurt er als je licht door **twee heel smalle spleetjes** vlak naast elkaar laat
    schijnen? Je zou twee lichte strepen op de muur erachter verwachten. Maar je krijgt een hele
    rij **lichte en donkere strepen**!

    Dat komt doordat licht een **golf** is, net als de rimpels op een vijver. De golven die uit
    de twee spleetjes komen, komen elkaar tegen op het scherm:

    - waar de top van de ene golf de top van een andere tegenkomt, tellen ze op en is het
      scherm **licht**;
    - waar een top een dal tegenkomt, heffen ze elkaar op en blijft het scherm **donker**.

    Meer dan 200 jaar geleden deed Thomas Young dit experiment. Zo liet hij zien dat licht echt
    een golf is.

    De gekleurde strook bovenaan het plaatje is wat je op het scherm zou zien. De lijn eronder
    laat zien hoe helder elk plekje is. Speel met de schuifjes en kijk wat er gebeurt!

    **Piepkleine maten:** lichtgolven zijn zo klein dat er bijna 2000 in één millimeter passen.
    Daarom meten we de kleur van het licht in *nanometers* (nm, een miljoenste millimeter). De
    spleetjes meten we in *micrometers* (µm, een duizendste millimeter). Een haar is ongeveer
    70 µm dik.
    """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    wavelength_nm = mo.ui.slider(
        380,
        780,
        value=550,
        step=1,
        label=tr("colour of the light (nm)", "kleur van het licht (nm)"),
        show_value=True,
    )
    slit_width_um = mo.ui.slider(
        5.0,
        300.0,
        value=40.0,
        step=1.0,
        label=tr("width of each slit (µm)", "breedte van elk spleetje (µm)"),
        show_value=True,
    )
    slit_sep_um = mo.ui.slider(
        20.0,
        1500.0,
        value=250.0,
        step=5.0,
        label=tr("distance between the slits (µm)", "afstand tussen de spleetjes (µm)"),
        show_value=True,
    )
    screen_dist_m = mo.ui.slider(
        0.2,
        5.0,
        value=2.0,
        step=0.05,
        label=tr("distance to the screen (m)", "afstand tot het scherm (m)"),
        show_value=True,
    )
    half_width_mm = mo.ui.slider(
        2.0,
        120.0,
        value=30.0,
        step=1.0,
        label=tr("zoom: screen shown each side (mm)", "zoom: zichtbaar scherm aan elke kant (mm)"),
        show_value=True,
    )
    show_parts = mo.ui.checkbox(
        True,
        label=tr(
            "show what each slit does, and what two slits do",
            "laat zien wat één spleetje doet, en wat twee spleetjes doen",
        ),
    )

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
                name=tr("one slit on its own", "één spleetje alleen"),
                line=dict(color="#555555", dash="dash", width=1.6),
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=y_mm,
                y=interference,
                name=tr("two waves meeting", "twee golven die elkaar tegenkomen"),
                line=dict(color="#aaaaaa", dash="dot", width=1.2),
            ),
            row=2,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=y_mm,
            y=total,
            name=tr("brightness on the screen", "helderheid op het scherm"),
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
        separators=tr(".,", ",."),  # decimal mark, then thousands
    )
    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        title_text=tr("screen", "scherm"),
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text=tr("brightness", "helderheid"), range=[0.0, 1.05], row=2, col=1
    )
    fig.update_xaxes(
        title_text=tr("position on the screen (mm)", "plek op het scherm (mm)"), row=2, col=1
    )
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
        tr("number {}, {}, … on each side", "nummer {}, {}, … aan elke kant").format(
            round(_ratio), 2 * round(_ratio)
        )
        if abs(_ratio - round(_ratio)) < 1e-6 and _ratio >= 1
        else tr(
            "none right now (make the distance an exact number of slit widths)",
            "nu geen (maak de afstand precies een aantal keer de breedte van een spleetje)",
        )
    )

    _table = mo.md(
        tr(
            en=f"""
        | | |
        |:--|--:|
        | distance from one bright stripe to the next | **{num(_spacing_mm, 2)} mm** |
        | from the centre to the edge of the middle bright patch | **{num(_env_mm, 1)} mm** |
        | bright stripes in the middle patch | **{_n_fringes}** |
        | stripes that vanish | {_missing} |
        | distance between the slits ÷ width of a slit | {num(_ratio, 2)} |
        """,
            nl=f"""
        | | |
        |:--|--:|
        | afstand van de ene lichte streep tot de volgende | **{num(_spacing_mm, 2)} mm** |
        | van het midden tot de rand van de middelste lichte vlek | **{num(_env_mm, 1)} mm** |
        | lichte strepen in de middelste vlek | **{_n_fringes}** |
        | strepen die verdwijnen | {_missing} |
        | afstand tussen de spleetjes ÷ breedte van een spleetje | {num(_ratio, 2)} |
        """,
        )
    )

    _warning = (
        mo.md(
            tr(
                "**Careful:** each slit is now at least as wide as the distance between them, "
                "so the two slits run into each other. The computer still draws a pattern, but "
                "it is not a real double slit any more.",
                "**Let op:** elk spleetje is nu minstens zo breed als de afstand ertussen, dus "
                "de twee spleetjes lopen in elkaar over. De computer tekent nog steeds een "
                "patroon, maar het is geen echte dubbele spleet meer.",
            )
        ).callout(kind="warn")
        if d_m <= a_m
        else mo.md("")
    )

    mo.vstack([_table, _warning])
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        tr(
            en=r"""
    ### Things to try

    - 🌈 **Change the colour** from violet to red. Red light has longer waves than blue light,
      so its stripes are further apart.
    - ↔️ **Move the slits further apart.** The stripes squeeze closer together, but the big
      outline they sit in (the dashed line) stays where it is.
    - 🔍 **Make the slits narrower.** The outline gets wider and you can count more stripes.
      Make the slits wider and the outline shrinks, until only a few stripes are left.
    - ✨ **Make stripes vanish!** Set the width of each slit to 50 µm and the distance between
      the slits to 250 µm, exactly 5 times as much. Now the 5th stripe on each side is gone
      (and the 10th too: zoom out to see it). It lands right where one slit on its own sends no
      light at all.
    - 📏 **Move the screen further away.** The whole pattern just gets bigger, like a picture
      from a projector.

    **Did you know?** Hold a CD or a DVD in the light and you will see rainbow colours. They come
    from the same trick, with thousands of tiny grooves instead of two slits.
    """,
            nl=r"""
    ### Probeer dit eens

    - 🌈 **Verander de kleur** van paars naar rood. Rood licht heeft langere golven dan blauw
      licht, dus de strepen liggen verder uit elkaar.
    - ↔️ **Zet de spleetjes verder uit elkaar.** De strepen schuiven dichter naar elkaar toe,
      maar de grote boog waar ze onder passen (de streepjeslijn) blijft op zijn plek.
    - 🔍 **Maak de spleetjes smaller.** De boog wordt breder en je kunt meer strepen tellen.
      Maak je de spleetjes breder, dan krimpt de boog tot er nog maar een paar strepen over zijn.
    - ✨ **Laat strepen verdwijnen!** Zet de breedte van elk spleetje op 50 µm en de afstand
      tussen de spleetjes op 250 µm, precies 5 keer zoveel. Nu is de 5e streep aan elke kant
      weg (en de 10e ook: zoom uit om dat te zien). Die valt precies op een plek waar één
      spleetje in zijn eentje helemaal geen licht naartoe stuurt.
    - 📏 **Zet het scherm verder weg.** Het hele patroon wordt gewoon groter, net als een plaatje
      van een beamer.

    **Wist je dat?** Als je een cd of dvd in het licht houdt, zie je regenboogkleuren. Die komen
    van hetzelfde trucje, maar dan met duizenden piepkleine groefjes in plaats van twee
    spleetjes.
    """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    _maths = mo.md(
        tr(
            en=r"""
    Two slits of width $a$, a distance $d$ apart (centre to centre), are lit by a plane wave of
    wavelength $\lambda$ and seen on a screen a distance $L$ away. Far from the slits (the
    Fraunhofer limit) the pattern is the **interference** of the two slits multiplied by the
    **diffraction** envelope of a single slit:

    $$
    \frac{I(\theta)}{I_0} \;=\;
    \underbrace{\operatorname{sinc}^2\!\left(\frac{a\sin\theta}{\lambda}\right)}_{\text{one slit: diffraction}}
    \;\times\;
    \underbrace{\cos^2\!\left(\frac{\pi d\sin\theta}{\lambda}\right)}_{\text{two slits: interference}}
    \qquad \sin\theta = \frac{y}{\sqrt{y^2+L^2}}
    $$

    The dashed curve is the first factor and the dotted curve the second. Near the centre the
    bright fringes are $\Delta y = \lambda L/d$ apart and the envelope has its first zero at
    $y = \lambda L/a$, so the slit separation sets the fringes and the slit width sets the
    envelope. When $d/a$ is a whole number, the interference maxima of order
    $m = \pm d/a, \pm 2d/a, \dots$ land on zeros of the envelope and vanish: these are the
    *missing orders*.
    """,
            nl=r"""
    Twee spleten met breedte $a$, op afstand $d$ van elkaar (van midden tot midden), worden
    belicht met een vlakke golf met golflengte $\lambda$ en bekeken op een scherm op afstand
    $L$. Ver van de spleten (de Fraunhofer-limiet) is het patroon de **interferentie** van de
    twee spleten, vermenigvuldigd met de **diffractie**-omhullende van één spleet:

    $$
    \frac{I(\theta)}{I_0} \;=\;
    \underbrace{\operatorname{sinc}^2\!\left(\frac{a\sin\theta}{\lambda}\right)}_{\text{één spleet: diffractie}}
    \;\times\;
    \underbrace{\cos^2\!\left(\frac{\pi d\sin\theta}{\lambda}\right)}_{\text{twee spleten: interferentie}}
    \qquad \sin\theta = \frac{y}{\sqrt{y^2+L^2}}
    $$

    De streepjeslijn is de eerste factor en de stippellijn de tweede. Dicht bij het midden
    liggen de lichte interferentiestrepen $\Delta y = \lambda L/d$ uit elkaar en heeft de
    omhullende zijn eerste nulpunt bij $y = \lambda L/a$: de spleetafstand bepaalt dus de
    strepen en de spleetbreedte de omhullende. Is $d/a$ een geheel getal, dan vallen de
    interferentiemaxima van orde $m = \pm d/a, \pm 2d/a, \dots$ op nulpunten van de omhullende
    en verdwijnen ze: de *ontbrekende ordes*.
    """,
        )
    )
    mo.accordion(
        {tr("For grown-ups: the maths behind it", "Voor volwassenen: de wiskunde erachter"): _maths}
    )
    return


if __name__ == "__main__":
    app.run()
