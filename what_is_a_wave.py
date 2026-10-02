# /// script
# requires-python = ">=3.13"
# dependencies = ["marimo"]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")

with app.setup:
    import json

    import marimo as mo

    # The page's language, "en" or "nl". tools/build_site.sh exports each notebook once per
    # language by rewriting this line, so keep it a plain literal on a line of its own.
    LANG = "en"

    # A side view of a stretch of water, in centimetres. Flat water is at height 0.
    X_LEN = 250.0
    Y_MIN, Y_MAX = -34.0, 36.0
    DUCK_X = 195.0
    # Every wave here travels this fast, whatever its length (see the note for grown-ups).
    SPEED_CM_S = 40.0


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
    # What is a wave?

    A wave is a movement that travels. Drop a pebble in a pond, shake one end of a skipping
    rope, or do a stadium wave with your friends: each time, a movement travels from one place
    to another.

    Now here is the strange part: **the water itself stays where it is**. Just watch the duck:
    when a wave passes, it only goes up and down. It does not travel along with the wave.

    Two words describe every wave:

    - the **amplitude**: how high the wave is, from flat water up to the top;
    - the **wavelength**: how long the wave is, from one top to the next.

    The dashed line shows where the water would be if it were flat. Change the waves with the
    sliders!
    """,
            nl=r"""
    # Wat is een golf?

    Een golf is een beweging die zich verplaatst. Gooi een steentje in een vijver, schud aan
    één kant van een springtouw, of doe de wave in een stadion met je vrienden: elke keer reist
    er een beweging van de ene plek naar de andere.

    En nu het rare: **het water zelf blijft gewoon waar het is**. Kijk maar naar het eendje: als
    er een golf langskomt, gaat het alleen op en neer. Het reist niet mee met de golf.

    Elke golf beschrijf je met twee woorden:

    - de **amplitude**: hoe hoog de golf is, van vlak water tot aan de top;
    - de **golflengte**: hoe lang de golf is, van de ene top tot de volgende.

    De streepjeslijn laat zien waar het water zou staan als het vlak was. Verander de golven met
    de schuifjes!
    """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    amplitude_cm = mo.ui.slider(
        0,
        20,
        value=8,
        step=1,
        label=tr(
            "amplitude: how high the waves are (cm)",
            "amplitude: hoe hoog de golven zijn (cm)",
        ),
        show_value=True,
    )
    wavelength_cm = mo.ui.slider(
        20,
        120,
        value=60,
        step=5,
        label=tr(
            "wavelength: how long the waves are (cm)",
            "golflengte: hoe lang de golven zijn (cm)",
        ),
        show_value=True,
    )

    mo.hstack([amplitude_cm, wavelength_cm], widths="equal", gap=2)
    return amplitude_cm, wavelength_cm


@app.cell(hide_code=True)
def _():
    try:
        _dark = mo.app_meta().theme == "dark"
    except Exception:
        _dark = False

    # The water is slightly see-through, so the duck's track still shows faintly below the
    # surface. "halo" is the water as it ends up on screen, used to keep labels legible on it.
    if _dark:
        theme = dict(
            surface="#1a1a19", ink="#ffffff", muted="#898781", hair="#2c2c2a",
            water="rgba(24, 79, 149, 0.88)", halo="#184886", line="#6da7ec",
            accent="#f1aea8",
        )
    else:
        theme = dict(
            surface="#fcfcfb", ink="#0b0b0b", muted="#898781", hair="#e1e0d9",
            water="rgba(158, 197, 244, 0.85)", halo="#accdf5", line="#2a78d6",
            accent="#b13f3c",
        )
    return (theme,)


@app.cell(hide_code=True)
def _(theme):
    # Built like the ripple tank: a self-contained page whose canvas animates itself, so it
    # starts on its own and Python does nothing per frame. The sliders only change the numbers
    # it is handed.
    WAVE_PAGE = """<!doctype html>
    <html lang="__LANG__">
    <head>
    <meta charset="utf-8">
    <style>
      html, body { margin: 0; padding: 0; background: __SURFACE__; overflow: hidden; }
      body { font: 12px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; color: __INK__; }
      #bar { display: flex; align-items: center; gap: 12px; height: 28px; padding: 4px 0 0 52px; }
      #toggle { font: inherit; color: __INK__; background: transparent; cursor: pointer;
                border: 1px solid __MUTED__; border-radius: 6px; padding: 3px 11px; }
      #toggle:hover, #toggle:focus-visible { border-color: __LINE__; }
      #hint { color: __MUTED__; }
      canvas { display: block; }
    </style>
    </head>
    <body>
    <div id="bar">
      <button id="toggle" type="button"></button>
      <span id="hint"></span>
    </div>
    <canvas id="wave"></canvas>
    <script type="application/json" id="wave-data">__DATA__</script>
    <script>
    (function () {
      "use strict";

      var D = JSON.parse(document.getElementById("wave-data").textContent);
      var T = D.theme;
      var S = D.text;

      var canvas = document.getElementById("wave");
      var ctx = canvas.getContext("2d");
      var toggle = document.getElementById("toggle");
      var bar = document.getElementById("bar");
      document.getElementById("hint").textContent = S.hint;

      var FONT = "12px system-ui, -apple-system, 'Segoe UI', sans-serif";
      var PAD_L = 52, PAD_R = 16, PAD_T = 6, PAD_B = 38;
      var geo = null;

      function layout() {
        var aspect = (D.yMax - D.yMin) / D.xLen;
        var available = document.documentElement.clientWidth - PAD_L - PAD_R;
        var room = window.innerHeight - bar.offsetHeight - PAD_T - PAD_B - 4;
        if (!(room > 120)) { room = 120; }
        var w = Math.min(available, room / aspect);
        if (!(w > 80)) { w = 80; }
        var h = w * aspect;
        var dpr = window.devicePixelRatio || 1;
        canvas.style.width = (w + PAD_L + PAD_R) + "px";
        canvas.style.height = (h + PAD_T + PAD_B) + "px";
        canvas.width = Math.round((w + PAD_L + PAD_R) * dpr);
        canvas.height = Math.round((h + PAD_T + PAD_B) * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        geo = { w: w, h: h, cm: w / D.xLen };
      }

      function xPix(xcm) { return PAD_L + xcm / D.xLen * geo.w; }
      function yPix(ycm) { return PAD_T + (D.yMax - ycm) / (D.yMax - D.yMin) * geo.h; }

      var A = D.amplitude, LAM = D.wavelength, V = D.speed, K = 2 * Math.PI / LAM;

      // The height of the water at x, at time t: a sine wave sliding to the right.
      function surface(x, t) { return A * Math.sin(K * (x - V * t)); }

      function arrowHead(x, y, angle) {
        var s = 7;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x - s * Math.cos(angle - 0.45), y - s * Math.sin(angle - 0.45));
        ctx.lineTo(x - s * Math.cos(angle + 0.45), y - s * Math.sin(angle + 0.45));
        ctx.closePath();
        ctx.fill();
      }

      // A line with a head at both ends, unless it is too short to carry them.
      function arrow(x0, y0, x1, y1) {
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.stroke();
        if (Math.sqrt((x1 - x0) * (x1 - x0) + (y1 - y0) * (y1 - y0)) > 16) {
          arrowHead(x1, y1, Math.atan2(y1 - y0, x1 - x0));
          arrowHead(x0, y0, Math.atan2(y0 - y1, x0 - x1));
        }
      }

      function label(text, x, y, colour, halo, align, baseline) {
        ctx.font = "600 " + FONT;
        ctx.textAlign = align;
        ctx.textBaseline = baseline;
        ctx.lineJoin = "round";
        ctx.lineWidth = 4;
        ctx.strokeStyle = halo;
        ctx.strokeText(text, x, y);
        ctx.fillStyle = colour;
        ctx.fillText(text, x, y);
      }

      function drawDuck(x, y) {
        // Shapes in centimetres from where the duck meets the water, y up, facing left. Drawn
        // a little larger than the water's own scale, so it reads at a glance.
        var u = Math.max(1.4 * geo.cm, 3);
        var cx = xPix(x), cy = yPix(y);
        function px(dx) { return cx + dx * u; }
        function py(dy) { return cy - dy * u; }
        function triangle(x0, y0, x1, y1, x2, y2) {
          ctx.beginPath();
          ctx.moveTo(px(x0), py(y0));
          ctx.lineTo(px(x1), py(y1));
          ctx.lineTo(px(x2), py(y2));
          ctx.closePath();
          ctx.fill();
        }
        ctx.fillStyle = "#f2c12e";
        triangle(5.2, 2.2, 8.2, 4.6, 4.2, 3.8);                                   // tail
        ctx.beginPath();
        ctx.ellipse(px(0), py(1.2), 6.0 * u, 3.2 * u, 0, 0, 2 * Math.PI);         // body
        ctx.fill();
        ctx.beginPath();
        ctx.arc(px(-4.0), py(6.0), 2.6 * u, 0, 2 * Math.PI);                      // head
        ctx.fill();
        ctx.fillStyle = "#d9a514";
        ctx.beginPath();
        ctx.ellipse(px(1.2), py(2.0), 3.0 * u, 1.4 * u, -0.15, 0, 2 * Math.PI);   // wing
        ctx.fill();
        ctx.fillStyle = "#e8771a";
        triangle(-6.3, 6.5, -9.0, 5.7, -6.2, 5.0);                                // beak
        ctx.fillStyle = "#1a1a19";
        ctx.beginPath();
        ctx.arc(px(-4.6), py(6.8), 0.45 * u, 0, 2 * Math.PI);                     // eye
        ctx.fill();
      }

      function drawAnnotations(t) {
        // Ride along with one crest, so the arrows always point at a real top. The crests sit
        // where x - V t = LAM/4 + n LAM; taking the first one past xRef keeps the amplitude
        // arrow and the wavelength bracket on screen, left of the duck.
        var xRef = (D.xLen - 2 * LAM) / 2;
        var off = (LAM / 4 + V * t - xRef) % LAM;
        if (off < 0) { off += LAM; }
        var p0 = xPix(xRef + off), p1 = xPix(xRef + off + LAM);
        var yTop = yPix(A), yFlat = yPix(0), yBracket = yPix(-A - 5);

        // wavelength: from this top to the next
        ctx.save();
        ctx.globalAlpha = 0.55;
        ctx.setLineDash([2, 3]);
        ctx.strokeStyle = T.ink;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(p0, yTop);
        ctx.lineTo(p0, yBracket);
        ctx.moveTo(p1, yTop);
        ctx.lineTo(p1, yBracket);
        ctx.stroke();
        ctx.restore();
        ctx.strokeStyle = T.ink;
        ctx.fillStyle = T.ink;
        ctx.lineWidth = 1.5;
        arrow(p0, yBracket, p1, yBracket);
        label(S.wavelength, (p0 + p1) / 2, yBracket + 5, T.ink, T.halo, "center", "top");

        // amplitude: from flat water up to the top
        ctx.strokeStyle = T.accent;
        ctx.fillStyle = T.accent;
        ctx.lineWidth = 2;
        arrow(p0, yFlat, p0, yTop);
        label(S.amplitude, p0, yTop - 6, T.accent, T.surface, "center", "bottom");
      }

      function drawAxes() {
        ctx.font = FONT;
        ctx.strokeStyle = T.hair;
        ctx.fillStyle = T.muted;
        ctx.lineWidth = 1;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        var yb = PAD_T + geo.h;
        for (var x = 0; x <= D.xLen; x += 25) {
          var px = Math.round(xPix(x)) + 0.5;
          ctx.beginPath();
          ctx.moveTo(px, yb);
          ctx.lineTo(px, yb + 4);
          ctx.stroke();
          ctx.fillText(String(x), px, yb + 6);
        }
        ctx.fillText(S.distance, PAD_L + geo.w / 2, yb + 21);
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        for (var y = -30; y <= 30; y += 10) {
          var py = Math.round(yPix(y)) + 0.5;
          ctx.beginPath();
          ctx.moveTo(PAD_L - 4, py);
          ctx.lineTo(PAD_L, py);
          ctx.stroke();
          ctx.fillText(String(y), PAD_L - 7, py);
        }
        ctx.save();
        ctx.translate(11, PAD_T + geo.h / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText(S.height, 0, 0);
        ctx.restore();
      }

      function paint(t) {
        ctx.fillStyle = T.surface;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.save();
        ctx.beginPath();
        ctx.rect(PAD_L, PAD_T, geo.w, geo.h);
        ctx.clip();

        // The duck's track: it only ever moves along this line.
        var tx = Math.round(xPix(D.duckX)) + 0.5;
        if (A >= 0.5) {
          ctx.setLineDash([2, 3]);
          ctx.strokeStyle = T.muted;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(tx, yPix(A));
          ctx.lineTo(tx, yPix(-A));
          ctx.stroke();
          ctx.setLineDash([]);
        }

        var n = Math.ceil(geo.w), xs = [], ys = [];
        for (var i = 0; i <= n; i++) {
          var x = i / n * D.xLen;
          xs.push(xPix(x));
          ys.push(yPix(surface(x, t)));
        }
        ctx.beginPath();
        ctx.moveTo(xs[0], ys[0]);
        for (i = 1; i <= n; i++) { ctx.lineTo(xs[i], ys[i]); }
        ctx.lineTo(PAD_L + geo.w, PAD_T + geo.h);
        ctx.lineTo(PAD_L, PAD_T + geo.h);
        ctx.closePath();
        ctx.fillStyle = T.water;
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(xs[0], ys[0]);
        for (i = 1; i <= n; i++) { ctx.lineTo(xs[i], ys[i]); }
        ctx.strokeStyle = T.line;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // where the water would be if it were flat
        var y0 = Math.round(yPix(0)) + 0.5;
        ctx.setLineDash([6, 5]);
        ctx.strokeStyle = T.muted;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(PAD_L, y0);
        ctx.lineTo(PAD_L + geo.w, y0);
        ctx.stroke();
        ctx.setLineDash([]);

        if (A >= 0.5) {
          // the two ends of the duck's track, highest and lowest
          ctx.strokeStyle = T.muted;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(tx - 6, Math.round(yPix(A)) + 0.5);
          ctx.lineTo(tx + 6, Math.round(yPix(A)) + 0.5);
          ctx.moveTo(tx - 6, Math.round(yPix(-A)) + 0.5);
          ctx.lineTo(tx + 6, Math.round(yPix(-A)) + 0.5);
          ctx.stroke();
          drawAnnotations(t);
        } else {
          label(S.flat, xPix(D.xLen * 0.4), yPix(4), T.ink, T.surface, "center", "bottom");
        }

        // The duck goes last, cut off at its own waterline so it sits in the water. On top of
        // everything, a steep crest next to it can never hide it.
        var yDuck = surface(D.duckX, t);
        ctx.save();
        ctx.beginPath();
        ctx.rect(PAD_L, PAD_T, geo.w, yPix(yDuck) - PAD_T);
        ctx.clip();
        drawDuck(D.duckX, yDuck);
        ctx.restore();
        ctx.restore();

        ctx.strokeStyle = T.hair;
        ctx.lineWidth = 1;
        ctx.strokeRect(PAD_L + 0.5, PAD_T + 0.5, geo.w - 1, geo.h - 1);
        drawAxes();
      }

      var playing = true, last = 0;
      // Time runs off the wall clock, so when a slider change redraws the page the wave
      // carries on where it was instead of starting over.
      var t = (Date.now() / 1000) % 3600;
      try {
        if (window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches) { playing = false; }
      } catch (err) { playing = true; }

      function setLabel() { toggle.textContent = playing ? S.pause : S.play; }

      toggle.addEventListener("click", function () {
        playing = !playing;
        setLabel();
      });
      window.addEventListener("resize", layout);

      function frame(now) {
        if (!last) { last = now; }
        var dt = (now - last) / 1000;
        last = now;
        if (playing) { t += dt; }
        paint(t);
        requestAnimationFrame(frame);
      }

      setLabel();
      layout();
      requestAnimationFrame(frame);
    })();
    </script>
    </body>
    </html>
    """
    wave_page = (
        WAVE_PAGE.replace("__LANG__", LANG)
        .replace("__SURFACE__", theme["surface"])
        .replace("__INK__", theme["ink"])
        .replace("__MUTED__", theme["muted"])
        .replace("__LINE__", theme["line"])
    )
    return (wave_page,)


@app.cell(hide_code=True)
def _(amplitude_cm, theme, wave_page, wavelength_cm):
    _payload = {
        "amplitude": amplitude_cm.value,
        "wavelength": wavelength_cm.value,
        "speed": SPEED_CM_S,
        "xLen": X_LEN,
        "yMin": Y_MIN,
        "yMax": Y_MAX,
        "duckX": DUCK_X,
        "theme": theme,
        "text": {
            "pause": tr("Pause", "Pauze"),
            "play": tr("Play", "Afspelen"),
            "hint": tr(
                "watch the duck: it only goes up and down",
                "kijk naar het eendje: het gaat alleen op en neer",
            ),
            "amplitude": tr("amplitude", "amplitude"),
            "wavelength": tr("wavelength", "golflengte"),
            "flat": tr("flat water: no wave!", "vlak water: geen golf!"),
            "distance": tr("distance (cm)", "afstand (cm)"),
            "height": tr("height (cm)", "hoogte (cm)"),
        },
    }

    mo.iframe(wave_page.replace("__DATA__", json.dumps(_payload)), width="100%", height="350")
    return


@app.cell(hide_code=True)
def _(amplitude_cm, wavelength_cm):
    _a = amplitude_cm.value
    _lam = wavelength_cm.value
    # One top passes the duck every λ/v seconds. Trailing zeros dropped: 1.5, not 1.50.
    _period = num(_lam / SPEED_CM_S, 2).rstrip("0").rstrip(".,")

    mo.md(
        tr(
            en=f"""
        | | |
        |:--|--:|
        | amplitude: from flat water to the top of a wave | **{num(_a, 0)} cm** |
        | from the bottom of a dip to the top of a wave (twice the amplitude) | {num(2 * _a, 0)} cm |
        | wavelength: from one top to the next | **{num(_lam, 0)} cm** |
        | time for the duck to go up and down once | **{_period} seconds** |
        | how fast the waves travel (the same for every wave here) | {num(SPEED_CM_S, 0)} cm per second |
        """,
            nl=f"""
        | | |
        |:--|--:|
        | amplitude: van vlak water tot de top van een golf | **{num(_a, 0)} cm** |
        | van de bodem van een dal tot de top van een golf (twee keer de amplitude) | {num(2 * _a, 0)} cm |
        | golflengte: van de ene top tot de volgende | **{num(_lam, 0)} cm** |
        | tijd die het eendje nodig heeft om één keer op en neer te gaan | **{_period} seconden** |
        | hoe snel de golven gaan (hier voor elke golf hetzelfde) | {num(SPEED_CM_S, 0)} cm per seconde |
        """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    mo.md(
        tr(
            en=r"""
    ### Things to try

    - 🦆 **Watch the duck.** The waves travel from left to right, but the duck does not come
      along: it only goes up and down. A wave carries the movement, not the water!
    - ⬆️ **Make the amplitude bigger.** The waves get taller and the duck goes higher. But does
      it go up and down any faster? No!
    - ↔️ **Make the wavelength shorter.** The tops come closer together, so they reach the duck
      more often and it bobs faster. Long waves rock it slowly.
    - 😴 **Set the amplitude to 0.** No height, no wave: the water is flat and the duck sits
      still.
    - 📏 **Press Pause and measure.** Use the ruler along the bottom to measure from one top to
      the next. Is it the wavelength you picked?

    **Did you know?**

    - Light is a wave too, but a tiny one: the waves of green light are about half a micrometre
      long, so almost 2 000 of them fit in one millimetre.
    - Sound is a wave in the air. When you talk, your voice makes waves about one to three
      metres long.
    - Out at sea, waves can be more than 100 metres long.

    Want to see what happens when waves squeeze through two gaps? Try the water waves next.
    """,
            nl=r"""
    ### Probeer dit eens

    - 🦆 **Kijk naar het eendje.** De golven gaan van links naar rechts, maar het eendje gaat
      niet mee: het gaat alleen op en neer. Een golf neemt de beweging mee, niet het water!
    - ⬆️ **Maak de amplitude groter.** De golven worden hoger en het eendje gaat hoger. Maar
      gaat het ook sneller op en neer? Nee!
    - ↔️ **Maak de golflengte korter.** De toppen komen dichter bij elkaar, dus ze komen vaker
      bij het eendje en het dobbert sneller. Lange golven wiegen het langzaam.
    - 😴 **Zet de amplitude op 0.** Geen hoogte, geen golf: het water is vlak en het eendje ligt
      stil.
    - 📏 **Druk op Pauze en meet.** Meet met de liniaal onderaan van de ene top tot de volgende.
      Is dat de golflengte die je hebt gekozen?

    **Wist je dat?**

    - Licht is ook een golf, maar een piepkleine: de golven van groen licht zijn ongeveer een
      halve micrometer lang. Er passen er bijna 2000 in één millimeter.
    - Geluid is een golf in de lucht. Als je praat, maakt je stem golven van ongeveer één tot
      drie meter lang.
    - Op zee kunnen golven meer dan 100 meter lang zijn.

    Wil je zien wat er gebeurt als golven door twee openingen moeten? Kijk dan bij de
    watergolven.
    """,
        )
    )
    return


@app.cell(hide_code=True)
def _():
    _maths = mo.md(
        tr(
            en=r"""
    The surface is a travelling sine wave,

    $$
    \eta(x, t) \;=\; A \sin\!\left(\frac{2\pi}{\lambda}\,(x - vt)\right),
    $$

    with amplitude $A$, wavelength $\lambda$ and speed $v$. A fixed point such as the duck
    oscillates with period $T = \lambda/v$, or frequency $f = v/\lambda$: the familiar
    $v = f\lambda$. The amplitude does not appear in it, which is why the duck keeps the same
    rhythm however tall the waves get.

    The speed is the same for every wavelength here, as on a stretched string. Real water waves
    are dispersive: in deep water $v = \sqrt{g\lambda/2\pi}$, so longer waves travel faster.
    They also break once they are steeper than about 1 in 7 (crest-to-trough height over
    wavelength), and the sliders go well past that. Nor does a real duck move straight up and
    down: in deep water each bit of the surface traces a small circle as a wave goes by, so the
    duck also rocks a little back and forth.
    """,
            nl=r"""
    Het oppervlak is een lopende sinusgolf,

    $$
    \eta(x, t) \;=\; A \sin\!\left(\frac{2\pi}{\lambda}\,(x - vt)\right),
    $$

    met amplitude $A$, golflengte $\lambda$ en snelheid $v$. Een vast punt, zoals het eendje,
    trilt met periode $T = \lambda/v$, oftewel frequentie $f = v/\lambda$: de bekende
    $v = f\lambda$. De amplitude komt er niet in voor, en daarom houdt het eendje hetzelfde
    ritme, hoe hoog de golven ook worden.

    De snelheid is hier voor elke golflengte hetzelfde, zoals bij een gespannen snaar. Echte
    watergolven zijn dispersief: op diep water is $v = \sqrt{g\lambda/2\pi}$, dus langere golven
    gaan sneller. Ze breken ook zodra ze steiler zijn dan ongeveer 1 op 7 (hoogte van dal tot
    top gedeeld door de golflengte), en de schuifjes gaan daar ruim overheen. En een echt
    eendje gaat niet precies recht op en neer: op diep water beschrijft elk stukje oppervlak een
    klein cirkeltje als er een golf langskomt, dus het eendje schommelt ook een beetje heen en
    weer.
    """,
        )
    )
    mo.accordion(
        {tr("For grown-ups: the maths behind it", "Voor volwassenen: de wiskunde erachter"): _maths}
    )
    return


if __name__ == "__main__":
    app.run()
