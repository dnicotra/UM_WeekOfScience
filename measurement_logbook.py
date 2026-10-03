# /// script
# requires-python = ">=3.13"
# dependencies = ["marimo", "plotly"]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")

with app.setup:
    import asyncio
    import csv
    import datetime
    import html
    import io
    import json
    import math
    import os
    import sys
    import uuid

    import marimo as mo
    import plotly.graph_objects as go

    # The page's language, "en" or "nl". tools/build_site.sh exports each notebook once per
    # language by rewriting this line, so keep it a plain literal on a line of its own.
    LANG = "en"

    # Where the logbook is kept: a file next to the notebook when it runs locally, a folder in
    # the browser's own storage on the published site (see LogbookFile).
    FILE_NAME = "measurement_logbook.json"
    BROWSER_DIR = "/weekend-of-science-logbook"

    # The wavelengths our eyes can see, in nanometres.
    VISIBLE_NM = (380.0, 780.0)
    # A hair is about 70 µm thick.
    HAIR_NM = 70_000.0


@app.function(hide_code=True)
def tr(en, nl):
    """The text for this page's language. Both sit side by side so they stay in step."""
    return nl if LANG == "nl" else en


@app.function(hide_code=True)
def num(x, digits):
    """A number with this page's decimal mark: 2.50 in English, 2,50 in Dutch."""
    text = f"{x:.{digits}f}"
    return text.replace(".", ",") if LANG == "nl" else text


@app.function(hide_code=True)
def plain(x):
    """A number the way someone would type it (250, 0.25), with this page's decimal mark."""
    if x is None:
        return ""
    text = f"{x:.6g}"
    return text.replace(".", ",") if LANG == "nl" else text


@app.function(hide_code=True)
def parse_number(text):
    """A number typed by hand, or None. People write 0,25 as often as 0.25, so both work."""
    if text is None:
        return None
    try:
        x = float(str(text).strip().replace(",", "."))
    except ValueError:
        return None
    return x if math.isfinite(x) else None


@app.function(hide_code=True)
def read_form(value):
    """The form's numbers, ready for the logbook, or what is wrong with them.

    Returns (fields, None) or (None, message). The slit width is the only optional number:
    it does not enter the wavelength, so a missing one should not stop anybody.
    """
    fields = {
        "name": str(value.get("name") or "").strip()[:40],
        "screen_cm": parse_number(value.get("screen_cm")),
        "slit_sep_mm": parse_number(value.get("slit_sep_mm")),
        "slit_width_mm": parse_number(value.get("slit_width_mm")),
        "span_mm": parse_number(value.get("span_mm")),
        "steps": value.get("steps"),
    }

    def missing(key):
        return fields[key] is None or fields[key] <= 0

    if missing("screen_cm"):
        return None, tr(
            "Fill in L, the distance from the slits to the screen, in centimetres.",
            "Vul L in, de afstand van de spleetjes tot het scherm, in centimeter.",
        )
    if missing("slit_sep_mm"):
        return None, tr(
            "Fill in d, the distance between the two slits, in millimetres.",
            "Vul d in, de afstand tussen de twee spleetjes, in millimeter.",
        )
    if str(value.get("slit_width_mm") or "").strip() and missing("slit_width_mm"):
        return None, tr(
            "a, the width of one slit, must be a number in millimetres. Or leave it empty.",
            "a, de breedte van één spleetje, moet een getal in millimeter zijn. Of laat het leeg.",
        )
    if missing("span_mm"):
        return None, tr(
            "Fill in the distance you measured across the stripes, in millimetres.",
            "Vul de afstand in die je over de strepen hebt gemeten, in millimeter.",
        )
    steps = fields["steps"]
    if not isinstance(steps, (int, float)) or steps < 1 or steps != int(steps):
        return None, tr(
            "The number of steps must be a whole number: 1 or more.",
            "Het aantal stappen moet een heel getal zijn: 1 of meer.",
        )
    fields["steps"] = int(steps)
    if fields["slit_width_mm"] is not None and fields["slit_width_mm"] >= fields["slit_sep_mm"]:
        return None, tr(
            "Each slit must be narrower than the distance between the slits. "
            "Did you swap a and d?",
            "Elk spleetje moet smaller zijn dan de afstand tussen de spleetjes. "
            "Heb je a en d omgewisseld?",
        )
    return fields, None


@app.function(hide_code=True)
def new_entry(fields):
    """A line for the logbook: what was typed, when, and an id to remove it by."""
    return {
        "id": uuid.uuid4().hex[:12],
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
        **fields,
    }


@app.function(hide_code=True)
def is_entry(entry):
    """Whether a line read back from storage is one this notebook can use."""
    try:
        return (
            isinstance(entry["id"], str)
            and isinstance(entry["time"], str)
            and isinstance(entry["name"], str)
            and entry["screen_cm"] > 0
            and entry["slit_sep_mm"] > 0
            and (entry["slit_width_mm"] is None or entry["slit_width_mm"] > 0)
            and entry["span_mm"] > 0
            and entry["steps"] >= 1
        )
    except (KeyError, TypeError):
        return False


@app.function(hide_code=True)
def wavelength_nm(entry):
    """The wavelength this measurement gives, λ = d·Δy / L, in nanometres."""
    spacing_mm = entry["span_mm"] / entry["steps"]
    return entry["slit_sep_mm"] * spacing_mm / (entry["screen_cm"] * 10.0) * 1e6


@app.function(hide_code=True)
def when(entry):
    """The time of a measurement, with the date too if it was not today."""
    moment = datetime.datetime.fromisoformat(entry["time"])
    if moment.date() == datetime.date.today():
        return moment.strftime("%H:%M")
    return moment.strftime("%d-%m %H:%M")


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


@app.function(hide_code=True)
def colour_name(nm):
    """The everyday name of the colour of light this long, or None if our eyes cannot see it."""
    for upper, name in (
        (450, tr("violet", "paars")),
        (495, tr("blue", "blauw")),
        (570, tr("green", "groen")),
        (590, tr("yellow", "geel")),
        (620, tr("orange", "oranje")),
        (VISIBLE_NM[1], tr("red", "rood")),
    ):
        if VISIBLE_NM[0] <= nm <= upper:
            return name
    return None


@app.function(hide_code=True)
def latest_result(entry):
    """What one measurement says, for the person who just made it."""
    lam = wavelength_nm(entry)
    who = html.escape(entry["name"])
    yours = (
        tr(f"<strong>{who}</strong>, your light", f"<strong>{who}</strong>, jouw licht")
        if who
        else tr("Your light", "Jouw licht")
    )
    colour = colour_name(lam)

    if colour is not None:
        waves = int(round(HAIR_NM / lam, -1))
        text = tr(
            f"{yours} has a wavelength of <strong>{num(lam, 0)} nm</strong>. That is "
            f"<strong>{colour}</strong> light! About {waves} of these waves side by side are "
            "as thick as one hair.",
            f"{yours} heeft een golflengte van <strong>{num(lam, 0)} nm</strong>. Dat is "
            f"<strong>{colour}</strong> licht! Ongeveer {waves} van deze golven naast elkaar "
            "zijn zo dik als één haar.",
        )
        swatch = mo.Html(
            '<div style="width: 3.5rem; height: 3.5rem; border-radius: 10px; flex: none; '
            'background: rgb{}"></div>'.format(wavelength_to_rgb(lam))
        )
        return mo.hstack(
            [swatch, mo.Html(f"<p style='margin: 0'>{text}</p>")],
            justify="start",
            align="center",
            gap=1.25,
        ).callout(kind="success")

    # Measuring the big patches (the envelope of one slit) instead of the small stripes gives
    # an answer d/a times too long. If undoing that lands on a colour, that is what happened.
    width = entry["slit_width_mm"]
    patches = (
        tr(
            "It looks like you measured the <strong>big bright patches</strong>. Measure the "
            "small stripes inside them instead! ",
            "Het lijkt erop dat je de <strong>grote lichte vlekken</strong> hebt gemeten. Meet "
            "in plaats daarvan de kleine strepen erin! ",
        )
        if width and lam > VISIBLE_NM[1]
        and VISIBLE_NM[0] <= lam * width / entry["slit_sep_mm"] <= VISIBLE_NM[1]
        else ""
    )
    text = tr(
        f"{yours} comes out at <strong>{num(lam, 0)} nm</strong>, and that is not a colour our "
        f"eyes can see, so something went wrong. {patches}Did you measure from the middle of "
        "one bright stripe to the middle of another, and count the steps in between? Is L in "
        "centimetres, and everything else in millimetres?",
        f"{yours} komt uit op <strong>{num(lam, 0)} nm</strong>, en dat is geen kleur die onze "
        f"ogen kunnen zien. Er is dus iets misgegaan. {patches}Heb je gemeten van het midden "
        "van een lichte streep tot het midden van een andere, en de stappen ertussen geteld? "
        "Staat L in centimeter, en de rest in millimeter?",
    )
    return mo.Html(f"<p style='margin: 0'>{text}</p>").callout(kind="warn")


@app.function(hide_code=True)
def entry_label(number, entry):
    """One measurement on a single line, to pick it from a list."""
    name = entry["name"] or "–"
    return f"#{number} · {when(entry)} · {name} · {num(wavelength_nm(entry), 0)} nm"


@app.function(hide_code=True)
def logbook_csv(entries):
    """The logbook as a spreadsheet. Dutch Excel expects ; between columns and a decimal comma."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=tr(",", ";"))
    writer.writerow(
        [
            tr("number", "nummer"),
            tr("date and time", "datum en tijd"),
            tr("name", "naam"),
            "L (cm)",
            "d (mm)",
            "a (mm)",
            tr("measured (mm)", "gemeten (mm)"),
            tr("steps", "stappen"),
            tr("stripe spacing (mm)", "streepafstand (mm)"),
            tr("wavelength (nm)", "golflengte (nm)"),
        ]
    )
    for number, entry in enumerate(entries, start=1):
        writer.writerow(
            [
                number,
                entry["time"].replace("T", " "),
                entry["name"],
                plain(entry["screen_cm"]),
                plain(entry["slit_sep_mm"]),
                plain(entry["slit_width_mm"]),
                plain(entry["span_mm"]),
                entry["steps"],
                plain(entry["span_mm"] / entry["steps"]),
                num(wavelength_nm(entry), 1),
            ]
        )
    return out.getvalue()


@app.class_definition(hide_code=True)
class LogbookFile:
    """The logbook as a JSON file, kept where a page refresh cannot wipe it.

    Run locally, it is a file next to the notebook. On the published site Python runs inside
    the browser, where files vanish with the page, so there the folder is backed by the
    browser's IndexedDB (Emscripten's IDBFS): it is filled from that storage on opening and
    copied back to it after every write. If the browser refuses (some private windows do),
    the logbook still works, but only until the page closes, and `kept` says so.
    """

    def __init__(self, path, in_browser, kept):
        self.path = path
        self.in_browser = in_browser
        self.kept = kept

    @classmethod
    async def open(cls):
        if sys.platform != "emscripten":
            folder = mo.notebook_dir() or os.getcwd()
            return cls(os.path.join(folder, FILE_NAME), in_browser=False, kept=True)

        import js
        import pyodide_js

        fs = pyodide_js.FS
        fs.mkdirTree(BROWSER_DIR)
        try:
            fs.mount(fs.filesystems.IDBFS, js.Object.new(), BROWSER_DIR)
        except Exception:
            pass  # mounted already: this cell has run before on this page
        logbook = cls(f"{BROWSER_DIR}/{FILE_NAME}", in_browser=True, kept=True)
        try:
            await cls._sync(populate=True)
        except OSError:
            logbook.kept = False
        return logbook

    @staticmethod
    def _sync(populate):
        """Copy the browser folder in from the browser's storage (populate), or back out."""
        import pyodide_js
        from pyodide.ffi import create_once_callable

        done = asyncio.get_running_loop().create_future()

        def finish(error=None):
            if error is None:
                done.set_result(None)
            else:
                done.set_exception(OSError(f"browser storage: {error}"))

        pyodide_js.FS.syncfs(populate, create_once_callable(finish))
        return done

    def read(self):
        """The measurements saved so far: none the first time."""
        try:
            with open(self.path, encoding="utf-8") as f:
                entries = json.load(f)["entries"]
        except FileNotFoundError:
            return []
        except (OSError, ValueError, KeyError, TypeError):
            # Unreadable. Move it aside rather than let the next save write over it.
            try:
                os.replace(self.path, self.path + ".unreadable")
            except OSError:
                pass
            return []
        return [entry for entry in entries if is_entry(entry)]

    async def write(self, entries):
        """Save the measurements. False if they could not be saved."""
        temporary = self.path + ".tmp"
        try:
            with open(temporary, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "entries": entries}, f, ensure_ascii=False, indent=1)
            os.replace(temporary, self.path)  # all or nothing: never a half-written logbook
            if self.in_browser and self.kept:
                await self._sync(populate=False)
        except OSError:
            return False
        return True


@app.function(hide_code=True)
def setup_drawing():
    """A sketch of what to measure: L from above, a and d on the slits, the steps on the screen."""
    grey, laser = "#6b6b6b", "#e0312b"
    label = 'fill="currentColor"'
    muted = 'fill="currentColor" opacity="0.62"'

    # The screen up close: the stripes of two slits under the big patches of one slit, drawn
    # as thin columns of light. The slits beside it have d = 4a, so the 4th stripe is missing.
    centre, step = 520, 22
    columns = []
    for x in range(332, 708, 2):
        u = (x + 1 - centre) / step
        envelope = (math.sin(math.pi * u / 4) / (math.pi * u / 4)) ** 2 if u else 1.0
        brightness = envelope * math.cos(math.pi * u) ** 2
        if brightness > 0.004:
            columns.append(
                f'<rect x="{x}" y="218" width="2" height="44" fill="{laser}" '
                f'opacity="{brightness**0.6:.3f}"/>'
            )
    ticks = "".join(
        f'<line x1="{centre + k * step}" y1="270" x2="{centre + k * step}" y2="280" '
        f'stroke="currentColor" stroke-width="1.5"/>'
        for k in range(-2, 3)
    )
    numbers = "".join(
        f'<text x="{centre + (k + 0.5) * step}" y="294" {muted} text-anchor="middle" '
        f'font-size="11">{k + 3}</text>'
        for k in range(-2, 2)
    )

    return mo.Html(
        f"""
<svg viewBox="0 0 720 324" role="img" style="display: block; width: 100%; max-width: 760px;
     height: auto; font: 13px system-ui, -apple-system, 'Segoe UI', sans-serif"
     aria-label="{tr(
         "The set-up seen from above, the two slits up close and the screen up close.",
         "De opstelling van bovenaf, de twee spleetjes van dichtbij en het scherm van dichtbij.",
     )}">
  <text x="10" y="16" {muted}>{tr("seen from above", "van bovenaf gezien")}</text>
  <rect x="10" y="58" width="74" height="28" rx="4" fill="{grey}"/>
  <text x="47" y="77" fill="#ffffff" text-anchor="middle">laser</text>
  <line x1="84" y1="72" x2="200" y2="72" stroke="{laser}" stroke-width="2"/>
  <polygon points="206,70 206,74 640,114 640,30" fill="{laser}" opacity="0.14"/>
  <rect x="200" y="32" width="6" height="80" fill="{grey}"/>
  <text x="203" y="26" {label} text-anchor="middle">{tr("two slits", "twee spleetjes")}</text>
  <rect x="640" y="20" width="8" height="104" fill="{grey}"/>
  <text x="644" y="14" {label} text-anchor="middle">{tr("screen", "scherm")}</text>
  <line x1="203" y1="146" x2="644" y2="146" stroke="currentColor" stroke-width="1.5"/>
  <line x1="203" y1="139" x2="203" y2="153" stroke="currentColor" stroke-width="1.5"/>
  <line x1="644" y1="139" x2="644" y2="153" stroke="currentColor" stroke-width="1.5"/>
  <text x="423" y="140" {label} text-anchor="middle"><tspan font-weight="700">L</tspan>
    {tr("from the slits to the screen", "van de spleetjes tot het scherm")}</text>

  <line x1="10" y1="162" x2="710" y2="162" stroke="currentColor" opacity="0.15"/>

  <text x="10" y="180" {muted}>{tr("the two slits up close", "de twee spleetjes van dichtbij")}</text>
  <line x1="110" y1="206" x2="126" y2="206" stroke="currentColor" stroke-width="1.5"/>
  <line x1="110" y1="200" x2="110" y2="212" stroke="currentColor" stroke-width="1.5"/>
  <line x1="126" y1="200" x2="126" y2="212" stroke="currentColor" stroke-width="1.5"/>
  <text x="134" y="210" {label}><tspan font-weight="700">a</tspan>
    {tr("the width of one slit", "de breedte van één spleetje")}</text>
  <rect x="40" y="218" width="220" height="44" rx="3" fill="{grey}"/>
  <rect x="110" y="218" width="16" height="44" fill="#fdf6d8"/>
  <rect x="174" y="218" width="16" height="44" fill="#fdf6d8"/>
  <line x1="118" y1="262" x2="118" y2="288" stroke="currentColor" stroke-dasharray="2 3"/>
  <line x1="182" y1="262" x2="182" y2="288" stroke="currentColor" stroke-dasharray="2 3"/>
  <line x1="118" y1="282" x2="182" y2="282" stroke="currentColor" stroke-width="1.5"/>
  <text x="192" y="286" {label}><tspan font-weight="700">d</tspan>
    {tr("from slit to slit", "van spleetje tot spleetje")}</text>

  <text x="330" y="180" {muted}>{tr("the screen up close", "het scherm van dichtbij")}</text>
  <text x="520" y="202" {muted} text-anchor="middle">{tr(
      "✗ not this: one big patch", "✗ niet dit: één grote vlek"
  )}</text>
  <path d="M432,214 V208 H608 V214" fill="none" stroke="currentColor" stroke-opacity="0.62"/>
  <rect x="330" y="218" width="380" height="44" rx="4" fill="#111111"/>
  {"".join(columns)}
  <line x1="476" y1="275" x2="564" y2="275" stroke="currentColor" stroke-width="1.5"/>
  {ticks}
  {numbers}
  <text x="520" y="314" {label} text-anchor="middle" font-weight="700">{tr(
      "✓ measure this: 4 steps", "✓ meet dit: 4 stappen"
  )}</text>
</svg>
"""
    )


@app.cell(hide_code=True)
def _():
    mo.md(
        tr(
            en=r"""
    # Measure the wavelength of light

    Shine a laser through two tiny slits and you get a row of bright and dark stripes on the
    screen. With those stripes you can measure something far too small to see: **how long a
    wave of light is**. All you need is a tape measure and a ruler!

    Do the experiment, type your numbers into the form below, and the computer works out the
    wavelength. Every measurement goes into the logbook, so you can see how close everyone
    gets.

    ⚠️ **Never look into the laser, and never point it at anyone.**

    ### How to measure

    1. **L, from the slits to the screen.** Measure it with the tape measure, in centimetres.
    2. **d and a, the slits.** d is the distance between the two slits, from the middle of
       one to the middle of the other, and a is the width of one slit. Both are in
       millimetres. They are often printed on the slide with the slits.
    3. **The stripes.** Look closely: the big bright patches are made of **small stripes**.
       Measure the small stripes, not the big patches! Put your ruler from the middle of one
       bright stripe to the middle of another one a bit further along, and count how many
       steps that is. Measuring across many stripes is more accurate than measuring just one.
    """,
            nl=r"""
    # Meet de golflengte van licht

    Laat een laser door twee piepkleine spleetjes schijnen en je krijgt een rij lichte en
    donkere strepen op het scherm. Met die strepen kun je iets meten dat veel te klein is om te
    zien: **hoe lang een lichtgolf is**. Je hebt alleen een rolmaat en een liniaal nodig!

    Doe het experiment, vul je getallen hieronder in, en de computer rekent de golflengte uit.
    Elke meting komt in het logboek, zodat je kunt zien hoe dicht iedereen erbij zit.

    ⚠️ **Kijk nooit in de laser, en richt hem nooit op iemand.**

    ### Zo meet je

    1. **L, van de spleetjes tot het scherm.** Meet die met de rolmaat, in centimeter.
    2. **d en a, de spleetjes.** d is de afstand tussen de twee spleetjes, van het midden van
       het ene tot het midden van het andere, en a is de breedte van één spleetje. Allebei in
       millimeter. Vaak staan ze op het plaatje met de spleetjes gedrukt.
    3. **De strepen.** Kijk goed: de grote lichte vlekken bestaan uit **kleine strepen**. Meet
       de kleine strepen, niet de grote vlekken! Leg je liniaal van het midden van een lichte
       streep tot het midden van een streep een stukje verderop, en tel hoeveel stappen dat
       is. Over veel strepen meten is nauwkeuriger dan over één.
    """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    setup_drawing()
    return


@app.cell(hide_code=True)
async def _():
    logbook_file = await LogbookFile.open()
    return (logbook_file,)


@app.cell(hide_code=True)
def _(logbook_file):
    # Self-loops on: the form and the list of measurements to remove both live in cells that
    # change the logbook, and should be rebuilt (emptied) when they do. No cell calls the
    # setter while it runs, only from a button or the form, so nothing can loop.
    get_entries, set_entries = mo.state(logbook_file.read(), allow_self_loops=True)
    return get_entries, set_entries


@app.cell(hide_code=True)
def _(get_entries, set_entries):
    # The set-up hardly changes from one visitor to the next, so it stays filled in from the
    # last measurement, while the stripes and the name start empty for the next person.
    _last = get_entries()[-1] if get_entries() else {}

    def _add(value):
        fields, problem = read_form(value or {})
        if problem is None:
            set_entries(lambda entries: entries + [new_entry(fields)])

    entry_form = (
        mo.md(
            tr(
                en="""
    **① The set-up.** It stays filled in for the next person, so only change it if something
    moved.

    {screen_cm} {slit_sep_mm} {slit_width_mm}

    **② Your stripes.** From the middle of one bright stripe to the middle of another.

    {span_mm} {steps}

    **③ Who measured?** {name}
    """,
                nl="""
    **① De opstelling.** Die blijft ingevuld voor de volgende, dus verander hem alleen als er
    iets verschoven is.

    {screen_cm} {slit_sep_mm} {slit_width_mm}

    **② Jouw strepen.** Van het midden van een lichte streep tot het midden van een andere.

    {span_mm} {steps}

    **③ Wie heeft er gemeten?** {name}
    """,
            )
        )
        .batch(
            screen_cm=mo.ui.text(
                value=plain(_last.get("screen_cm")),
                placeholder=plain(200.0),
                label="**L** (cm)",
            ),
            slit_sep_mm=mo.ui.text(
                value=plain(_last.get("slit_sep_mm")),
                placeholder=plain(0.25),
                label="**d** (mm)",
            ),
            slit_width_mm=mo.ui.text(
                value=plain(_last.get("slit_width_mm")),
                placeholder=tr("if you know it", "als je het weet"),
                label="**a** (mm)",
            ),
            span_mm=mo.ui.text(
                placeholder=plain(26.0),
                label=tr("distance measured (mm)", "gemeten afstand (mm)"),
            ),
            steps=mo.ui.number(
                start=1, stop=100, step=1, value=1, label=tr("steps", "stappen")
            ),
            name=mo.ui.text(
                placeholder="Sam", max_length=40, label=tr("name", "naam")
            ),
        )
        .form(
            submit_button_label=tr("📒 Add to the logbook", "📒 Zet in het logboek"),
            validate=lambda value: read_form(value or {})[1],
            on_change=_add,
        )
    )
    entry_form
    return


@app.cell(hide_code=True)
async def _(get_entries, logbook_file):
    # Every change is saved straight away, so a refresh or a closed tab loses nothing.
    _saved = await logbook_file.write(get_entries())
    (
        mo.md(
            tr(
                "**This logbook will not be kept.** The browser does not let the page save "
                "it, so it is gone when the page closes or refreshes. Download a copy before "
                "you close it (see *For the grown-up at the stand* at the bottom).",
                "**Dit logboek wordt niet bewaard.** De browser laat de pagina het niet "
                "opslaan, dus het is weg als de pagina sluit of ververst. Download een kopie "
                "voordat je hem sluit (zie *Voor de begeleider* onderaan).",
            )
        ).callout(kind="warn")
        if not (_saved and logbook_file.kept)
        else mo.md("")
    )
    return


@app.cell(hide_code=True)
def _(get_entries):
    _entries = get_entries()
    (
        latest_result(_entries[-1])
        if _entries
        else mo.md(tr("_No measurements yet. Be the first!_", "_Nog geen metingen. Wees de eerste!_"))
    )
    return


@app.cell(hide_code=True)
def _(get_entries):
    _entries = get_entries()
    _lams = [wavelength_nm(entry) for entry in _entries]
    _seen = [lam for lam in _lams if colour_name(lam) is not None]
    _left_out = len(_lams) - len(_seen)

    # The axis covers what eyes can see and a bit more; anything further out is drawn on the
    # edge as an arrowhead, so one wild measurement cannot squash everyone else's.
    _low, _high = 300.0, 900.0

    _stats = mo.hstack(
        [
            mo.stat(value=str(len(_entries)), label=tr("measurements", "metingen")),
            mo.stat(
                value=f"{num(sum(_seen) / len(_seen), 0)} nm" if _seen else "–",
                label=tr("average wavelength", "gemiddelde golflengte"),
                caption=(
                    tr("of everyone", "van iedereen")
                    if not _left_out
                    else tr(
                        f"leaving out {_left_out} that "
                        f"{'is' if _left_out == 1 else 'are'} not a colour you can see",
                        f"zonder de {_left_out} die geen kleur "
                        f"{'geeft' if _left_out == 1 else 'geven'} die je kunt zien",
                    )
                ),
            ),
        ],
        justify="start",
        gap=3,
    )

    _fig = go.Figure()
    if _entries:
        _numbers = list(range(1, len(_lams) + 1))
        _names = [html.escape(entry["name"]) for entry in _entries]
        _sizes = [12] * len(_lams)
        _sizes[-1] = 18  # the newest one stands out
        _fig.add_trace(
            go.Scatter(
                x=_numbers,
                y=[min(max(lam, _low), _high) for lam in _lams],
                mode="markers",
                cliponaxis=False,  # the arrowheads on the edge must show in full
                marker=dict(
                    size=_sizes,
                    color=[
                        "rgb{}".format(wavelength_to_rgb(lam)) if colour_name(lam) else "#8a8a8a"
                        for lam in _lams
                    ],
                    symbol=[
                        "triangle-up" if lam > _high else "triangle-down" if lam < _low else "circle"
                        for lam in _lams
                    ],
                    line=dict(width=2, color="#ffffff"),
                ),
                customdata=[
                    [f"#{n} {name}".strip(), f"{num(lam, 0)} nm"]
                    for n, name, lam in zip(_numbers, _names, _lams)
                ],
                hovertemplate="%{customdata[0]}<br><b>%{customdata[1]}</b><extra></extra>",
            )
        )
        _fig.add_annotation(
            x=_numbers[-1],
            y=min(max(_lams[-1], _low), _high),
            text=f"{_names[-1] or '#' + str(_numbers[-1])}: {num(_lams[-1], 0)} nm",
            showarrow=False,
            yshift=22,
            font=dict(size=13),
        )
        if _seen:
            _fig.add_hline(
                y=sum(_seen) / len(_seen),
                line=dict(color="#52514e", width=1.5, dash="dash"),
                annotation_text=tr("average", "gemiddelde"),
                annotation_position="bottom right",
                annotation_font_color="#52514e",
            )

    _fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=70, r=30, t=30, b=55),
        showlegend=False,
        hovermode="closest",
        separators=tr(".,", ",."),  # decimal mark, then thousands
        # The colours of the rainbow up the left edge, as a key: where a dot sits is its colour.
        shapes=[
            dict(
                type="rect",
                xref="paper",
                x0=0.0,
                x1=0.014,
                y0=nm,
                y1=nm + 4,
                fillcolor="rgb{}".format(wavelength_to_rgb(nm + 2)),
                line_width=0,
                layer="below",
            )
            for nm in range(int(VISIBLE_NM[0]), int(VISIBLE_NM[1]), 4)
        ],
    )
    _fig.update_xaxes(
        title_text=tr("measurement number", "meting nummer"),
        range=[0.4, max(len(_lams), 5) + 0.6],
        dtick=1 if len(_lams) <= 20 else None,
        zeroline=False,
    )
    _fig.update_yaxes(
        title_text=tr("wavelength (nm)", "golflengte (nm)"), range=[_low, _high], zeroline=False
    )

    (
        mo.vstack(
            [mo.md(tr("### Everyone's measurements", "### De metingen van iedereen")), _stats, _fig]
        )
        if _entries
        else mo.md("")
    )
    return


@app.cell(hide_code=True)
def _(get_entries, logbook_file):
    _entries = get_entries()
    _where = (
        tr("kept in this browser", "bewaard in deze browser")
        if logbook_file.in_browser
        else tr(f"kept in `{FILE_NAME}`", f"bewaard in `{FILE_NAME}`")
    )
    _measured = tr("measured (mm)", "gemeten (mm)")
    _table = mo.ui.table(
        [
            {
                "#": number,
                tr("name", "naam"): entry["name"],
                tr("wavelength (nm)", "golflengte (nm)"): round(wavelength_nm(entry)),
                "L (cm)": entry["screen_cm"],
                "d (mm)": entry["slit_sep_mm"],
                "a (mm)": entry["slit_width_mm"],
                _measured: entry["span_mm"],
                tr("steps", "stappen"): entry["steps"],
                tr("time", "tijd"): when(entry),
            }
            for number, entry in reversed(list(enumerate(_entries, start=1)))
        ],
        selection=None,
        page_size=15,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        format_mapping={column: plain for column in ("L (cm)", "d (mm)", "a (mm)", _measured)},
    )
    mo.vstack(
        [
            mo.md(
                tr(
                    f"### The logbook\n\nNewest at the top, {_where}.",
                    f"### Het logboek\n\nNieuwste bovenaan, {_where}.",
                )
            ),
            _table if _entries else mo.md(tr("_Still empty._", "_Nog leeg._")),
        ]
    )
    return


@app.cell(hide_code=True)
def _(get_entries, logbook_file, set_entries):
    _entries = get_entries()

    remove_pick = mo.ui.multiselect(
        options={
            entry_label(number, entry): entry["id"]
            for number, entry in reversed(list(enumerate(_entries, start=1)))
        },
        label=tr("measurements to remove", "metingen om weg te halen"),
        full_width=True,
    )

    def _remove(_):
        _gone = set(remove_pick.value)
        if _gone:
            set_entries(lambda entries: [e for e in entries if e["id"] not in _gone])

    remove_button = mo.ui.button(
        label=tr("Remove them", "Haal ze weg"), kind="danger", on_click=_remove
    )

    wipe_confirm = mo.ui.checkbox(
        label=tr("Yes, delete every measurement", "Ja, wis alle metingen")
    )

    def _wipe(_):
        if wipe_confirm.value:
            set_entries([])

    wipe_button = mo.ui.button(
        label=tr("Start a new, empty logbook", "Begin een nieuw, leeg logboek"),
        kind="danger",
        on_click=_wipe,
    )

    logbook_download = mo.download(
        data=lambda: logbook_csv(get_entries()).encode("utf-8-sig"),  # the BOM tells Excel it is UTF-8
        filename=lambda: f"{tr('logbook', 'logboek')}-{datetime.date.today().isoformat()}.csv",
        mimetype="text/csv",
        label=tr("Download the logbook", "Download het logboek"),
    )

    if not logbook_file.kept:
        _kept = tr(
            "This browser does not let the page save the logbook, so it is lost when the page "
            "closes. Download a copy before you close it.",
            "Deze browser laat de pagina het logboek niet opslaan, dus het is weg als de pagina "
            "sluit. Download een kopie voordat je hem sluit.",
        )
    elif logbook_file.in_browser:
        _kept = tr(
            "The logbook is saved in this browser, on this computer: refreshing or closing the "
            "page loses nothing, and nothing is sent anywhere. Clearing the browser's data for "
            "this site deletes it, so download a copy at the end of the day. It opens in a "
            "spreadsheet such as Excel.",
            "Het logboek wordt bewaard in deze browser, op deze computer: verversen of sluiten "
            "kost niets, en er wordt niets verstuurd. Als je de browsergegevens van deze site "
            "wist, is het weg, dus download aan het eind van de dag een kopie. Die opent in een "
            "spreadsheet zoals Excel.",
        )
    else:
        _kept = tr(
            f"The logbook is saved in `{FILE_NAME}`, next to this notebook. You can also "
            "download it as a spreadsheet that opens in Excel.",
            f"Het logboek wordt bewaard in `{FILE_NAME}`, naast dit notebook. Je kunt het ook "
            "downloaden als spreadsheet die opent in Excel.",
        )

    mo.accordion(
        {
            tr(
                "For the grown-up at the stand: fix mistakes, keep a copy, start over",
                "Voor de begeleider: fouten herstellen, een kopie bewaren, opnieuw beginnen",
            ): mo.vstack(
                [
                    mo.md(
                        tr(
                            "**Fix a mistake.** Pick the measurements that went wrong, and "
                            "remove them.",
                            "**Een fout herstellen.** Kies de metingen die misgingen, en haal "
                            "ze weg.",
                        )
                    ),
                    mo.hstack([remove_pick, remove_button], align="end", widths=[4, 1]),
                    mo.md(tr(f"**Keep a copy.** {_kept}", f"**Een kopie bewaren.** {_kept}")),
                    mo.hstack([logbook_download], justify="start"),
                    mo.md(
                        tr(
                            "**Start over**, for a new day or a new group. This deletes every "
                            "measurement, so download a copy first!",
                            "**Opnieuw beginnen**, voor een nieuwe dag of een nieuwe groep. Dit "
                            "wist alle metingen, dus download eerst een kopie!",
                        )
                    ),
                    mo.hstack([wipe_confirm, wipe_button], justify="start", align="center"),
                ],
                gap=0.75,
            )
        }
    )
    return


@app.cell(hide_code=True)
def _():
    _maths = mo.md(
        tr(
            en=r"""
    Two slits a distance $d$ apart are lit by a laser of wavelength $\lambda$, and the pattern
    falls on a screen a distance $L$ away. A bright stripe appears wherever the paths from the
    two slits differ by a whole number $m$ of wavelengths, $d\sin\theta = m\lambda$. The stripes
    stay close to the middle compared with $L$, so $\sin\theta \approx \tan\theta = y/L$, and
    the $m$-th bright stripe sits at $y_m = m\lambda L/d$. Neighbouring stripes are therefore
    a constant distance apart, and that is what the logbook measures:

    $$
    \Delta y = \frac{\lambda L}{d}
    \qquad\Longrightarrow\qquad
    \lambda = \frac{d\,\Delta y}{L},
    \qquad
    \Delta y = \frac{\text{distance measured}}{\text{number of steps}} .
    $$

    With $L$ in centimetres and $d$, $\Delta y$ in millimetres, $\lambda$ in nanometres is
    $10^5\, d\,\Delta y / L$. The small-angle step is good to a fraction of a percent for
    stripes a few centimetres from the centre of a screen a metre or more away, far better
    than a ruler.

    Measuring across $n$ steps instead of one divides the error of reading the ruler by $n$,
    which is why the form asks for the number of steps.

    The slit width $a$ does not enter. It sets the big patches instead (the diffraction
    envelope of a single slit), whose first dark band is at $y = \lambda L/a$. Measuring the
    patches instead of the stripes therefore gives an answer $d/a$ times too long; when an
    answer is out of the visible range but $\lambda a/d$ is inside it, the notebook says
    that this is probably what happened. The average leaves out answers outside the visible
    range (380–780 nm), and says how many it kept.
    """,
            nl=r"""
    Twee spleten op afstand $d$ van elkaar worden belicht met een laser met golflengte
    $\lambda$, en het patroon valt op een scherm op afstand $L$. Een lichte streep ontstaat
    overal waar de wegen vanaf de twee spleten een geheel aantal $m$ golflengtes verschillen,
    $d\sin\theta = m\lambda$. De strepen blijven dicht bij het midden vergeleken met $L$, dus
    $\sin\theta \approx \tan\theta = y/L$, en de $m$-de lichte streep ligt bij
    $y_m = m\lambda L/d$. Naburige strepen liggen dus steeds even ver uit elkaar, en dat is
    wat het logboek meet:

    $$
    \Delta y = \frac{\lambda L}{d}
    \qquad\Longrightarrow\qquad
    \lambda = \frac{d\,\Delta y}{L},
    \qquad
    \Delta y = \frac{\text{gemeten afstand}}{\text{aantal stappen}} .
    $$

    Met $L$ in centimeter en $d$, $\Delta y$ in millimeter is $\lambda$ in nanometer gelijk
    aan $10^5\, d\,\Delta y / L$. De benadering voor kleine hoeken klopt tot op een fractie van
    een procent voor strepen een paar centimeter van het midden van een scherm op een meter
    of meer afstand, veel beter dan een liniaal.

    Over $n$ stappen meten in plaats van één deelt de afleesfout van de liniaal door $n$;
    daarom vraagt het formulier naar het aantal stappen.

    De spleetbreedte $a$ doet niet mee. Die bepaalt de grote vlekken (de
    diffractie-omhullende van één spleet), met de eerste donkere band bij $y = \lambda L/a$.
    Wie de vlekken meet in plaats van de strepen, krijgt dus een antwoord dat $d/a$ keer te
    lang is; als een antwoord buiten het zichtbare gebied valt maar $\lambda a/d$ erbinnen,
    zegt het notebook dat dit waarschijnlijk is gebeurd. Het gemiddelde laat antwoorden buiten
    het zichtbare gebied (380–780 nm) weg, en zegt hoeveel het er heeft meegeteld.
    """,
        )
    )
    mo.accordion(
        {tr("For grown-ups: the maths behind it", "Voor volwassenen: de wiskunde erachter"): _maths}
    )
    return


if __name__ == "__main__":
    app.run()
