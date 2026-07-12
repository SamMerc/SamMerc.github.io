"""
generate_stars.py
-----------------
Generates star imagery using jaxoplanet:
  images/star_spots.png  — star with active regions (surface features)
  images/star_spots.gif  — active regions rotating into and out of view
  images/star_pulse.gif  — limb-darkening strength pulsating (spots fixed)

Run once locally:
  python generate_stars.py
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')                    # non-interactive — safe in scripts
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image, ImageDraw
import io
import os
import imageio

from jaxoplanet.starry.ylm import Ylm
from jaxoplanet.starry.surface import Surface
from jaxoplanet.starry.visualization import show_surface

# ── Output settings ───────────────────────────────────────────────────────────
OUTPUT_DIR  = 'images'
SIZE_INCHES = 5          # figure size in inches
DPI         = 200        # → 1 000 × 1 000 px output  (SIZE_INCHES × DPI)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Stellar colormap ──────────────────────────────────────────────────────────
STELLAR_CMAP = mcolors.LinearSegmentedColormap.from_list(
    'stellar',
    [
        "#5E0F01",   # dark red   (limb edge)
        "#B03601",   # burnt orange
        "#FA9119",   # amber
        "#FDE650",   # yellow
    ]
)

# Base quadratic limb-darkening coefficients (u1, u2) shared by every render.
u_star = (0.5, 0.2)
# ═════════════════════════════════════════════════════════════════════════════════
def render_surface_to_png(surface, filepath, theta=0.0, verbose=True):
    """
    Render a jaxoplanet Surface and save as a transparent-background PNG.

    Parameters
    ----------
    surface  : jaxoplanet Surface object
    filepath : destination path (must end in .png)
    theta    : rotation angle of the map about its polar axis [radians]
    verbose  : if False, suppress the per-file print (useful inside GIF loops)
    """

    # ── 1. Render ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(SIZE_INCHES, SIZE_INCHES), facecolor='none')
    ax.set_facecolor('none')
    plt.sca(ax)

    rendered_with_cmap = False
    for call in [
        lambda: show_surface(surface, theta=theta, ax=ax, cmap=STELLAR_CMAP),
        lambda: show_surface(surface, theta=theta, ax=ax),
        lambda: show_surface(surface, theta=theta),
    ]:
        try:
            call()
            if 'cmap=STELLAR_CMAP' in str(call.__code__.co_consts):
                rendered_with_cmap = True
            break
        except TypeError:
            continue

    ax = plt.gca()
    ax.set_aspect('equal')
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=DPI,
                transparent=True, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    buf.seek(0)

    # ── 2. Re-colour through STELLAR_CMAP if needed ────────────────────────────
    img        = Image.open(buf).convert('RGBA')
    data       = np.array(img, dtype=np.float32)
    alpha_orig = data[:, :, 3].copy()

    if not rendered_with_cmap:
        brightness = (
            0.2126 * data[:, :, 0] +
            0.7152 * data[:, :, 1] +
            0.0722 * data[:, :, 2]
        ) / 255.0

        disc_mask = alpha_orig > 10
        if disc_mask.any():
            bmin = brightness[disc_mask].min()
            bmax = brightness[disc_mask].max()
            if bmax > bmin:
                brightness[disc_mask] = (
                    (brightness[disc_mask] - bmin) / (bmax - bmin)
                )

        coloured             = (STELLAR_CMAP(brightness) * 255).astype(np.uint8)
        coloured[:, :, 3]    = alpha_orig.astype(np.uint8)
        img = Image.fromarray(coloured, 'RGBA')

    # ── 3 & 4. Circular mask ───────────────────────────────────────────────────
    w, h   = img.size
    margin = max(2, int(min(w, h) * 0.02))

    circle = Image.new('L', (w, h), 0)
    ImageDraw.Draw(circle).ellipse(
        [margin, margin, w - margin, h - margin], fill=255
    )

    ml_alpha = np.array(img.split()[3], dtype=np.uint8)
    ci_alpha = np.array(circle,         dtype=np.uint8)
    img.putalpha(Image.fromarray(np.minimum(ml_alpha, ci_alpha), 'L'))

    img.save(filepath, 'PNG')
    if verbose:
        print(f'  Saved  →  {filepath}  ({w} × {h} px)')


def assemble_gif(png_paths, gif_path, fps):
    """
    Read back a sequence of rendered PNG frames, composite them onto black
    (GIF has no alpha channel), quantise with dithering, and save a looping GIF.
    Shared by every animation below — only the per-frame Surface differs.
    """
    frames = [imageio.v2.imread(p) for p in png_paths]

    pil_frames = []
    for frame_rgba in frames:
        img_rgba = Image.fromarray(frame_rgba, 'RGBA')
        bg = Image.new('RGB', img_rgba.size, (0, 0, 0))
        bg.paste(img_rgba, mask=img_rgba.split()[3])   # use alpha as mask

        # Quantise to 256 colours with Floyd–Steinberg dithering (dither=1)
        pil_frames.append(bg.quantize(colors=256, dither=1))

    frame_w, frame_h = pil_frames[0].size
    pil_frames[0].save(
        gif_path,
        save_all      = True,
        append_images = pil_frames[1:],
        optimize      = False,
        duration      = int(1000 / fps),   # ms per frame
        loop          = 0,                 # loop forever
    )
    print(f'  Saved  →  {gif_path}  '
          f'({frame_w} × {frame_h} px, {len(png_paths)} frames @ {fps} fps)')


# ═════════════════════════════════════════════════════════════════════════════════
# IMAGE — Star with active regions  (static snapshot)
# ═════════════════════════════════════════════════════════════════════════════════
print('Rendering star_spots.png ...')

np.random.seed(42)
y_spots = Ylm.from_dense([1.00, *np.random.normal(0.5, 0.2, size=36)])

surface_spots = Surface(inc=1.0, obl=0.2, period=27.0, u=u_star, y=y_spots)
render_surface_to_png(surface_spots, os.path.join(OUTPUT_DIR, 'star_spots.png'))


# ═════════════════════════════════════════════════════════════════════════════════
# GIF — Stellar surface rotating into and out of view
#
# Rotation strategy
# ──────────────────
# A single FIXED, high-contrast set of spherical-harmonic "spot" coefficients
# (ACTIVITY_COEFFS) is drawn once, at full amplitude, and never changes.
# What changes from frame to frame is the map's rotation angle `theta`,
# stepped at a perfectly uniform angular speed:
#
#   theta(i) = 2π · i / N_FRAMES        for i = 0 .. N_FRAMES-1
#
# Because a full 2π rotation returns the map to its starting orientation,
# frame N_FRAMES would be pixel-identical to frame 0 — so omitting it and
# looping the GIF gives a perfectly seamless cycle with no jump. The surface
# itself is always fully active (no fading), so the animation reads as spots
# sweeping across the disc at constant speed rather than gently pulsing.
#
# Resolution
# ──────────
# Every frame is rendered at the full PNG resolution (SIZE_INCHES × DPI px).
# GIF supports at most 256 colours and no alpha channel, so before encoding:
#   1. Each RGBA frame is alpha-composited onto a black background.
#   2. The RGB result is quantised to 256 colours with Floyd–Steinberg
#      dithering, which distributes quantisation error across neighbours and
#      preserves smooth colour gradients far better than simple nearest-colour.
# ═════════════════════════════════════════════════════════════════════════════════
print('Rendering star_spots.gif ...')

np.random.seed(42)

# ── Animation parameters ──────────────────────────────────────────────────────
N_FRAMES  = 240    # total frames in one GIF loop  (↑ = smoother rotation + longer loop)
FPS       = 30     # playback speed  →  N_FRAMES / FPS seconds per loop  (8 s @ defaults)
ACTIVITY  = 1.0    # fixed amplitude multiplier for the spot coefficients (no fading)

# ── Fixed, high-contrast spot pattern (never changes — only theta does) ───────
# Because we re-seeded to 42 above, these are identical to the spots in
# star_spots.png — the GIF at theta=0 matches the static PNG exactly.
ACTIVITY_COEFFS = np.random.normal(0.5, 0.2, size=36)
frame_coeffs    = np.array([1.00, *(ACTIVITY_COEFFS * ACTIVITY)])
y_frame         = Ylm.from_dense(frame_coeffs)

surface_frame = Surface(
    inc=1.0, obl=0.2, period=27.0,
    u=u_star, y=y_frame,
)

# ── Per-frame rendering ───────────────────────────────────────────────────────
tmp_paths = []   # temporary PNG paths, removed after GIF is built

for i in range(N_FRAMES):

    # Uniform angular speed, 0 → 2π exclusive — the endpoint is skipped
    # because it would duplicate frame 0, which is what makes the loop seamless.
    theta = 2.0 * np.pi * i / N_FRAMES

    tmp_path = os.path.join(OUTPUT_DIR, f'_frame_{i:04d}.png')
    render_surface_to_png(surface_frame, tmp_path, theta=theta, verbose=False)
    tmp_paths.append(tmp_path)
    print(f'  Frame {i + 1:3d} / {N_FRAMES}', end='\r')

print()
assemble_gif(tmp_paths, os.path.join(OUTPUT_DIR, 'star_spots.gif'), FPS)

for p in tmp_paths:
    os.remove(p)


# ═════════════════════════════════════════════════════════════════════════════════
# GIF — Stellar surface pulsating (limb-darkening strength oscillating)
#
# Pulsation strategy
# ───────────────────
# The active-region spot pattern and viewing angle (theta=0) are held FIXED —
# identical to star_spots.png/star_spots.gif's starting frame. What changes
# from frame to frame is the quadratic limb-darkening coefficients `u`: both
# coefficients are scaled by a common factor that oscillates sinusoidally
# around 1.0, completing PULSE_CYCLES full breaths per loop:
#
#   scale(i) = 1 + PULSE_DEPTH · sin(2π · PULSE_CYCLES · i / N_FRAMES_PULSE)
#
# Higher u ⇒ stronger limb darkening (a brighter, sharper core and a darker
# rim); lower u ⇒ a flatter, more uniformly lit disc. Cycling u therefore
# reads as the star's core breathing brighter and dimmer. Since PULSE_CYCLES
# is an integer number of full sine periods, frame N_FRAMES_PULSE would still
# be pixel-identical to frame 0 — omitting it and looping gives a seamless
# cycle, the same trick used for the rotation GIF above.
# ═════════════════════════════════════════════════════════════════════════════════
print('Rendering star_pulse.gif ...')

N_FRAMES_PULSE = 120   # total frames in one GIF loop
FPS_PULSE      = 30    # playback speed → 4 s loop @ defaults
PULSE_CYCLES   = 3     # full brighten/dim breaths per loop → ~1.3 s per breath
PULSE_DEPTH    = 1.0   # ±100 % swing of each limb-darkening coefficient around its base value

tmp_paths = []

for i in range(N_FRAMES_PULSE):

    scale   = 1.0 + PULSE_DEPTH * np.sin(2.0 * np.pi * PULSE_CYCLES * i / N_FRAMES_PULSE)
    u_frame = tuple(c * scale for c in u_star)

    surface_pulse = Surface(inc=1.0, obl=0.2, period=27.0, u=u_frame, y=y_frame)

    tmp_path = os.path.join(OUTPUT_DIR, f'_pulse_{i:04d}.png')
    render_surface_to_png(surface_pulse, tmp_path, theta=0.0, verbose=False)
    tmp_paths.append(tmp_path)
    print(f'  Frame {i + 1:3d} / {N_FRAMES_PULSE}', end='\r')

print()
assemble_gif(tmp_paths, os.path.join(OUTPUT_DIR, 'star_pulse.gif'), FPS_PULSE)

for p in tmp_paths:
    os.remove(p)

print('\nDone — PNGs and GIFs written to images/')