# /// script
# requires-python = ">=3.13"
# dependencies = ["marimo", "numpy"]
# ///

import marimo

__generated_with = "0.25.0"
app = marimo.App(width="medium")

with app.setup:
    import base64

    import marimo as mo
    import numpy as np

    # The tank, in centimetres. The barrier sits at y = 0, the wave travels +y.
    X_MIN, X_MAX = -14.0, 14.0
    Y_MIN, Y_MAX = -5.0, 19.0
    BARRIER_HALF_T = 0.25


@app.cell(hide_code=True)
def _():
    mo.md(r"""
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

    The water starts moving on its own and loops forever. Above the tank is the **time-averaged**
    intensity along its far edge — what a long exposure of the surface would record — drawn on
    the same horizontal scale, so each peak sits directly over the lobe that makes it.
    """)
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
    period_ms = mo.ui.dropdown(
        {"slow": 2600, "normal": 1500, "fast": 850}, value="normal", label="one period lasts"
    )
    quality = mo.ui.dropdown(
        {"fast": (8, 25000), "smooth": (12, 50000), "sharp": (18, 90000)},
        value="smooth",
        label="grid detail",
    )
    show_incoming = mo.ui.checkbox(True, label="show the incoming plane wave")

    mo.hstack(
        [
            mo.vstack([wavelength_cm, slit_sep_cm, slit_width_cm]),
            mo.vstack([period_ms, quality, show_incoming]),
        ],
        widths="equal",
        gap=2,
    )
    return (
        period_ms,
        quality,
        show_incoming,
        slit_sep_cm,
        slit_width_cm,
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
    """Time-independent amplitude: wavelets past the barrier, plane wave in front of it.

    The animation is a phase rotation of this one array, which is why it can run at screen
    refresh rate without Python doing anything per frame.
    """
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
    # The barrier band itself keeps the wavelets, so the openings show water moving through;
    # the solid stretches are painted over it.
    field = np.where(Y < -BARRIER_HALF_T, incoming, wavelets)

    # Clamp the magnitude rather than the real part, so the saturated cells right at the
    # openings keep their phase and still travel.
    over = np.abs(field) > 1.0
    field[over] /= np.abs(field[over])
    return field


@app.function(hide_code=True)
def as_int8_b64(values):
    """Quantise [-1, 1] to int8 and base64 it, for embedding in the page."""
    q = np.clip(np.round(values * 127.0), -127, 127).astype(np.int8)
    return base64.b64encode(np.ascontiguousarray(q).tobytes()).decode("ascii")


@app.function(hide_code=True)
def colour_lut_b64(stops):
    """256 RGB triples interpolated through the colour stops, base64'd for the canvas."""
    rgb = np.array(
        [[int(s[i : i + 2], 16) for i in (1, 3, 5)] for s in stops], dtype=float
    )
    at = np.linspace(0.0, 1.0, len(stops))
    want = np.linspace(0.0, 1.0, 256)
    table = np.stack([np.interp(want, at, rgb[:, c]) for c in range(3)], axis=1)
    return base64.b64encode(table.round().astype(np.uint8).tobytes()).decode("ascii")


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

    # Time-averaged intensity read off the far edge of the tank, as on a screen.
    screen = np.abs(field[-1]) ** 2
    screen = screen / max(screen.max(), 1e-12)
    return field, lam, screen, sep, sources, width, xs, ys


@app.cell(hide_code=True)
def _():
    # Diverging blue <-> red with a neutral midpoint: the surface height is signed, and zero
    # means "flat water". The red arm is the blue ramp's steps held at matching OKLab
    # lightness, so neither crests nor troughs read as the heavier half.
    _blue = ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"]
    _red = ["#fad6d2", "#f1aea8", "#e4857d", "#d75852", "#b13f3c", "#892c2a", "#621b1a"]

    try:
        _dark = mo.app_meta().theme == "dark"
    except Exception:
        _dark = False

    if _dark:
        # Selected for the dark surface, not flipped: the extremes stay bright and the flat
        # water sinks into the background.
        theme = dict(
            stops=_blue[::-1] + ["#383835"] + _red[::-1],
            surface="#1a1a19", ink="#ffffff", muted="#898781", hair="#2c2c2a",
            barrier="#c3c2b7", series="#3987e5", series_soft="rgba(57, 135, 229, 0.20)",
        )
    else:
        theme = dict(
            stops=_blue + ["#f0efec"] + _red,
            surface="#fcfcfb", ink="#0b0b0b", muted="#898781", hair="#e1e0d9",
            barrier="#52514e", series="#2a78d6", series_soft="rgba(42, 120, 214, 0.16)",
        )
    return (theme,)


@app.cell(hide_code=True)
def _(theme):
    # A self-contained page: the animation runs on a canvas so it can start by itself, loop
    # seamlessly and share one x mapping between the intensity plot and the tank. Every frame
    # is a phase rotation of the amplitude array computed above, done in the browser, so
    # Python does nothing per frame.
    RIPPLE_PAGE = """<!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <style>
      html, body { margin: 0; padding: 0; background: __SURFACE__; overflow: hidden; }
      body { font: 12px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; color: __INK__; }
      #bar { display: flex; align-items: center; gap: 12px; height: 28px; padding: 4px 0 0 52px; }
      #toggle { font: inherit; color: __INK__; background: transparent; cursor: pointer;
                border: 1px solid __MUTED__; border-radius: 6px; padding: 3px 11px; }
      #toggle:hover, #toggle:focus-visible { border-color: __SERIES__; }
      #readout { color: __MUTED__; font-variant-numeric: tabular-nums; }
      canvas { display: block; }
    </style>
    </head>
    <body>
    <div id="bar">
      <button id="toggle" type="button">Pause</button>
      <span id="readout"></span>
    </div>
    <canvas id="tank"></canvas>
    <script type="application/json" id="ripple-data">__DATA__</script>
    <script>
    (function () {
      "use strict";

      var D = JSON.parse(document.getElementById("ripple-data").textContent);
      var T = D.theme;
      var HINT = "loops continuously \\u2014 hover to read the intensity off";

      function bytes(b64) {
        var bin = atob(b64);
        var u = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) { u[i] = bin.charCodeAt(i); }
        return u;
      }

      var re = new Int8Array(bytes(D.re).buffer);
      var im = new Int8Array(bytes(D.im).buffer);
      var lut = bytes(D.lut);
      var nx = D.nx;
      var ny = D.ny;

      var canvas = document.getElementById("tank");
      var ctx = canvas.getContext("2d");
      var toggle = document.getElementById("toggle");
      var readout = document.getElementById("readout");
      var bar = document.getElementById("bar");

      var off = document.createElement("canvas");
      off.width = nx;
      off.height = ny;
      var offCtx = off.getContext("2d");
      var img = offCtx.createImageData(nx, ny);
      var pix = img.data;
      for (var a = 3; a < pix.length; a += 4) { pix[a] = 255; }

      var PAD_L = 52, PAD_R = 16, PAD_T = 4, PAD_B = 34, PROFILE_H = 92, GAP = 10;
      var geo = null;

      function layout() {
        var chrome = PAD_T + PROFILE_H + GAP + PAD_B;
        var aspect = (D.yMax - D.yMin) / (D.xMax - D.xMin);
        var available = document.documentElement.clientWidth - PAD_L - PAD_R;
        var room = window.innerHeight - bar.offsetHeight - chrome - 4;
        if (!(room > 200)) { room = 200; }
        var w = Math.min(available, room / aspect);
        if (!(w > 80)) { w = 80; }
        var h = w * aspect;
        var dpr = window.devicePixelRatio || 1;
        canvas.style.width = (w + PAD_L + PAD_R) + "px";
        canvas.style.height = (h + chrome) + "px";
        canvas.width = Math.round((w + PAD_L + PAD_R) * dpr);
        canvas.height = Math.round((h + chrome) * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        geo = { w: w, h: h, tankTop: PAD_T + PROFILE_H + GAP,
                profileTop: PAD_T + 12, profileBase: PAD_T + PROFILE_H };
      }

      function xPix(xcm) { return PAD_L + (xcm - D.xMin) / (D.xMax - D.xMin) * geo.w; }
      function yPix(ycm) { return geo.tankTop + (D.yMax - ycm) / (D.yMax - D.yMin) * geo.h; }

      function renderField(phase) {
        var c = Math.cos(phase), s = Math.sin(phase), p = 0;
        for (var j = ny - 1; j >= 0; j--) {
          var row = j * nx;
          for (var i = 0; i < nx; i++) {
            var v = (re[row + i] * c - im[row + i] * s) * 0.0078740157;
            var k = (v + 1.0) * 127.5;
            if (k < 0) { k = 0; } else if (k > 255) { k = 255; }
            var q = (k | 0) * 3;
            pix[p] = lut[q];
            pix[p + 1] = lut[q + 1];
            pix[p + 2] = lut[q + 2];
            p += 4;
          }
        }
        offCtx.putImageData(img, 0, 0);
      }

      function drawTank() {
        // The samples are nodes, but drawImage treats them as cells, so stretch by half a
        // cell each way: then column i lands exactly where the intensity plot puts sample i,
        // and the ticks fall on the values they name. Clipped, as it now overhangs the panel.
        var halfX = 0.5 * geo.w / (nx - 1), halfY = 0.5 * geo.h / (ny - 1);
        ctx.save();
        ctx.beginPath();
        ctx.rect(PAD_L, geo.tankTop, geo.w, geo.h);
        ctx.clip();
        ctx.imageSmoothingEnabled = true;
        ctx.drawImage(off, 0, 0, nx, ny, PAD_L - halfX, geo.tankTop - halfY,
                      geo.w + 2 * halfX, geo.h + 2 * halfY);
        ctx.restore();
        ctx.fillStyle = T.barrier;
        var yTop = yPix(D.barrierT), yBot = yPix(-D.barrierT);
        for (var i = 0; i < D.barrier.length; i++) {
          var x0 = xPix(D.barrier[i][0]), x1 = xPix(D.barrier[i][1]);
          ctx.fillRect(x0, yTop, x1 - x0, Math.max(yBot - yTop, 1.5));
        }
        ctx.strokeStyle = T.hair;
        ctx.lineWidth = 1;
        ctx.strokeRect(PAD_L + 0.5, geo.tankTop + 0.5, geo.w - 1, geo.h - 1);
      }

      function drawProfile() {
        var n = D.intensity.length, base = geo.profileBase, top = geo.profileTop;
        ctx.setLineDash([2, 3]);
        ctx.strokeStyle = T.muted;
        ctx.fillStyle = T.muted;
        ctx.lineWidth = 1;
        ctx.textAlign = "center";
        ctx.textBaseline = "bottom";
        for (var i = 0; i < D.orders.length; i++) {
          var px = Math.round(xPix(D.orders[i][1])) + 0.5;
          ctx.beginPath();
          ctx.moveTo(px, top);
          ctx.lineTo(px, base);
          ctx.stroke();
          ctx.fillText("m=" + D.orders[i][0], px, top - 1);
        }
        ctx.setLineDash([]);

        ctx.beginPath();
        for (var j = 0; j < n; j++) {
          var x = PAD_L + (j / (n - 1)) * geo.w;
          var y = base - D.intensity[j] * (base - top);
          if (j === 0) { ctx.moveTo(x, y); } else { ctx.lineTo(x, y); }
        }
        ctx.strokeStyle = T.series;
        ctx.lineWidth = 2;
        ctx.stroke();
        ctx.lineTo(PAD_L + geo.w, base);
        ctx.lineTo(PAD_L, base);
        ctx.closePath();
        ctx.fillStyle = T.series_soft;
        ctx.fill();

        ctx.strokeStyle = T.hair;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(PAD_L, base + 0.5);
        ctx.lineTo(PAD_L + geo.w, base + 0.5);
        ctx.stroke();

        ctx.fillStyle = T.muted;
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        ctx.fillText("1", PAD_L - 7, top);
        ctx.fillText("0", PAD_L - 7, base);
      }

      function drawAxes() {
        ctx.strokeStyle = T.hair;
        ctx.fillStyle = T.muted;
        ctx.lineWidth = 1;
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        var yb = geo.tankTop + geo.h;
        for (var x = Math.ceil(D.xMin / 5) * 5; x <= D.xMax; x += 5) {
          var px = Math.round(xPix(x)) + 0.5;
          ctx.beginPath();
          ctx.moveTo(px, yb);
          ctx.lineTo(px, yb + 4);
          ctx.stroke();
          ctx.fillText(String(x), px, yb + 6);
        }
        ctx.fillText("across the tank, x (cm)", PAD_L + geo.w / 2, yb + 20);
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        for (var y = Math.ceil(D.yMin / 5) * 5; y <= D.yMax; y += 5) {
          var py = Math.round(yPix(y)) + 0.5;
          ctx.beginPath();
          ctx.moveTo(PAD_L - 4, py);
          ctx.lineTo(PAD_L, py);
          ctx.stroke();
          ctx.fillText(String(y), PAD_L - 7, py);
        }
        ctx.save();
        ctx.translate(11, geo.tankTop + geo.h / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText("direction of travel, y (cm)", 0, 0);
        ctx.restore();
        ctx.save();
        ctx.translate(11, (geo.profileTop + geo.profileBase) / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        ctx.fillText("mean intensity", 0, 0);
        ctx.restore();
      }

      var cursor = null;

      function drawCursor() {
        if (cursor === null) {
          readout.textContent = HINT;
          return;
        }
        var frac = (cursor - PAD_L) / geo.w;
        var idx = Math.round(frac * (D.intensity.length - 1));
        if (idx < 0) { idx = 0; }
        if (idx > D.intensity.length - 1) { idx = D.intensity.length - 1; }
        ctx.save();
        ctx.globalAlpha = 0.4;
        ctx.strokeStyle = T.ink;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(Math.round(cursor) + 0.5, geo.profileTop);
        ctx.lineTo(Math.round(cursor) + 0.5, geo.tankTop + geo.h);
        ctx.stroke();
        ctx.restore();
        readout.textContent = "x = " + (D.xMin + frac * (D.xMax - D.xMin)).toFixed(1) +
          " cm    mean intensity = " + D.intensity[idx].toFixed(2);
      }

      function paint() {
        ctx.fillStyle = T.surface;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        drawTank();
        drawProfile();
        drawAxes();
        drawCursor();
      }

      var phase = 0, last = 0, needsField = true, playing = true;
      try {
        if (window.matchMedia &&
            window.matchMedia("(prefers-reduced-motion: reduce)").matches) { playing = false; }
      } catch (err) { playing = true; }

      function label() { toggle.textContent = playing ? "Pause" : "Play"; }

      toggle.addEventListener("click", function () {
        playing = !playing;
        label();
      });

      canvas.addEventListener("mousemove", function (ev) {
        var box = canvas.getBoundingClientRect();
        var px = ev.clientX - box.left;
        cursor = (px >= PAD_L && px <= PAD_L + geo.w) ? px : null;
      });
      canvas.addEventListener("mouseleave", function () { cursor = null; });
      window.addEventListener("resize", function () {
        layout();
        needsField = true;
      });

      function frame(now) {
        if (!last) { last = now; }
        var dt = now - last;
        last = now;
        if (playing) {
          phase = (phase - 2 * Math.PI * (dt / D.periodMs)) % (2 * Math.PI);
          needsField = true;
        }
        if (needsField) {
          renderField(phase);
          needsField = false;
        }
        paint();
        requestAnimationFrame(frame);
      }

      label();
      layout();
      requestAnimationFrame(frame);
    })();
    </script>
    </body>
    </html>
    """
    ripple_page = (
        RIPPLE_PAGE.replace("__SURFACE__", theme["surface"])
        .replace("__INK__", theme["ink"])
        .replace("__MUTED__", theme["muted"])
        .replace("__SERIES__", theme["series"])
    )
    return (ripple_page,)


@app.cell(hide_code=True)
def _(field, lam, period_ms, ripple_page, screen, sep, theme, width, xs, ys):
    import json

    _payload = {
        "re": as_int8_b64(np.real(field)),
        "im": as_int8_b64(np.imag(field)),
        "lut": colour_lut_b64(theme["stops"]),
        "nx": len(xs),
        "ny": len(ys),
        "xMin": X_MIN,
        "xMax": X_MAX,
        "yMin": Y_MIN,
        "yMax": Y_MAX,
        "barrierT": BARRIER_HALF_T,
        "barrier": barrier_segments(sep, width),
        "orders": far_field_maxima(lam, sep, ys[-1]),
        "intensity": [round(float(v), 4) for v in screen],
        "periodMs": period_ms.value,
        "screenY": float(ys[-1]),
        "theme": {k: v for k, v in theme.items() if k != "stops"},
    }

    ripple_tank = mo.iframe(
        ripple_page.replace("__DATA__", json.dumps(_payload)), width="100%", height="720"
    )
    ripple_tank
    return


@app.cell(hide_code=True)
def _(lam, screen, sep, sources, width, xs, ys):
    _orders = far_field_maxima(lam, sep, ys[-1])
    _theta = np.degrees(np.arcsin(min(lam / sep, 1.0)))
    _peaks = [
        xs[i]
        for i in range(1, len(xs) - 1)
        if screen[i] > screen[i - 1] and screen[i] >= screen[i + 1] and screen[i] > 0.02
    ]

    _table = mo.md(
        f"""
        | | |
        |:--|--:|
        | angle of the first side maximum, $\\sin\\theta = \\lambda/d$ | **{_theta:.1f}°** |
        | orders reaching the far edge | **{len(_orders)}** (m = {_orders[0][0]} … {_orders[-1][0]}) |
        | peaks the exact sum actually puts there | **{len(_peaks)}** |
        | $d/\\lambda$ | {sep / lam:.2f} |
        | Huygens sources across the two openings | {len(sources)} |
        | grid | {len(xs)} × {len(ys)} cells |
        """
        if _orders
        else f"""
        | | |
        |:--|--:|
        | $\\lambda/d$ | {lam / sep:.2f} — **larger than 1, so there are no side maxima at all** |
        | Huygens sources across the two openings | {len(sources)} |
        | grid | {len(xs)} × {len(ys)} cells |
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
    mo.md(r"""
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
    - Compare the dotted far-field orders with the peaks the exact sum actually produces. Close
      to the barrier they do not quite agree, and that gap is the difference between this
      notebook and the Fraunhofer one.
    """)
    return


if __name__ == "__main__":
    app.run()
