/* ============================================================
   RESEARCH TAB — Star System Interactivity  (hardened version)
============================================================ */

(function () {
  'use strict';

  /* ── SAFETY NET: log every step so the console tells you what fails ── */
  console.log('[research.js] Script started.');

  /* ── 1. RESEARCH CONTENT ──────────────────────────────── */
  const RESEARCH_DATA = {
    'limb': {
      emoji : '🌟',
      title : 'Limb Darkening',
      body  : 'Stars appear darker at their edges (limbs) than at their ' +
              'centre. This happens because we look into deeper, hotter ' +
              'stellar layers at disc centre, while at the limb only cooler ' +
              'outer layers are visible. I develop precise limb-darkening ' +
              'models and study how this effect shapes the light curves of ' +
              'transiting exoplanets, directly affecting the accuracy of ' +
              'derived planetary radii and other parameters.',
      tags  : ['Stellar Atmospheres', 'Transit Photometry', 'Light Curves', 'TESS', 'JWST']
    },
    'active-regions': {
      emoji : '☀️',
      title : 'Stellar Active Regions',
      body  : 'The surfaces of Sun-like stars are covered with dark spots ' +
              'and bright faculae — magnetically driven active regions. ' +
              'When a transiting planet crosses one, it can distort the ' +
              'observed transit signal and bias planetary parameters. I ' +
              'characterise these features and develop methods to disentangle ' +
              'their signatures from genuine planetary signals.',
      tags  : ['Starspots', 'Faculae', 'Stellar Activity', 'Magnetic Fields', 'Transit Contamination']
    },
    'orbit': {
      emoji : '🔄',
      title : 'Rossiter–McLaughlin Effect',
      body  : 'As a planet transits a rotating star it blocks the approaching ' +
              'and receding limbs in turn, inducing a characteristic ' +
              'radial-velocity anomaly known as the Rossiter–McLaughlin effect. ' +
              'By modelling this signal I measure the sky-projected spin–orbit ' +
              'angle — the misalignment between stellar spin and planetary orbit — ' +
              'providing key constraints on the dynamical history of planetary systems.',
      tags  : ['Radial Velocity', 'Spin–Orbit Alignment', 'System Dynamics', 'Hot Jupiters']
    },
    'atmosphere': {
      emoji : '🌍',
      title : 'Exoplanet Atmospheres',
      body  : 'During transit, starlight filters through the planet\'s ' +
              'atmosphere, imprinting absorption features of molecules ' +
              '(H₂O, CO₂, CH₄, Na, K…) at specific wavelengths. ' +
              'I use transmission and emission spectroscopy with JWST and ' +
              'HST to probe atmospheric composition, temperature–pressure ' +
              'profiles, and cloud structures on worlds beyond our Solar System.',
      tags  : ['Transmission Spectroscopy', 'Emission Spectroscopy', 'JWST', 'HST', 'Climate']
    },
    'lava': {
      emoji : '🌋',
      title : 'Lava Planets',
      body  : 'Lava planets are ultra-short-period rocky worlds so intensely ' +
              'irradiated that their surfaces are partially or entirely molten. ' +
              'The magma ocean can drive a thin silicate-vapour atmosphere ' +
              'detectable in thermal emission and phase curves. I study the ' +
              'surface–atmosphere coupling, mineral composition, and thermal ' +
              'structure of these extreme laboratories for planetary physics.',
      tags  : ['Extreme Irradiation', 'Rocky Planets', 'Thermal Emission', 'Phase Curves', 'Interiors']
    },
    'oblateness': {
      emoji : '🪐',
      title : 'Planetary Oblateness',
      body  : 'A rapidly rotating planet bulges at its equator, making it ' +
              'oblate. This departure from spherical symmetry produces subtle ' +
              'asymmetries in transit light curves — ingress and egress have ' +
              'slightly different shapes. By detecting this signal in high-' +
              'precision photometry (TESS, JWST, Cheops), I constrain exoplanet ' +
              'rotation rates and internal density distributions.',
      tags  : ['Planet Shape', 'Rotation Rate', 'Interior Structure', 'TESS', 'Photometry']
    }
  };

  /* The top-right hotspot is a second entry point into the same Limb Darkening
     topic (it visualises the effect via a pulsating GIF instead of a tint) —
     reuse the 'limb' content rather than duplicating it. */
  RESEARCH_DATA['limb-pulse'] = RESEARCH_DATA['limb'];

  /* ── 2. DOM REFERENCES — each one checked individually ── */
  var svg = document.getElementById('rs-svg');
  if (!svg) {
    console.error('[research.js] STOP: #rs-svg not found. Check that the SVG is in index.html.');
    return;
  }
  console.log('[research.js] SVG found:', svg);

  var wrapper = document.querySelector('.rs-wrapper');
  if (!wrapper) { console.warn('[research.js] .rs-wrapper not found.'); }

  var tip = document.getElementById('rs-tip');
  if (!tip) { console.warn('[research.js] #rs-tip not found — tooltips disabled.'); }

  var modal = document.getElementById('rs-modal');
  if (!modal) {
    console.error('[research.js] STOP: #rs-modal not found. ' +
                  'Make sure the modal <div> is placed just before </body> ' +
                  'and INSIDE the <body> tag.');
    return;
  }
  console.log('[research.js] Modal found:', modal);

  var modalBox   = modal.querySelector('.rs-modal-box');
  var modalClose = document.getElementById('rs-modal-x');
  var modalEmoji = document.getElementById('rs-modal-emoji');
  var modalTitle = document.getElementById('rs-modal-title');
  var modalBody  = document.getElementById('rs-modal-body');
  var modalTags  = document.getElementById('rs-modal-tags');

  var regions    = svg.querySelectorAll('.rs-region');
  var legendBtns = document.querySelectorAll('.rs-legend .rs-lb');

  console.log('[research.js] Interactive regions found:', regions.length,
              '(expected 6)');
  console.log('[research.js] Legend buttons found:', legendBtns.length,
              '(expected 6)');

  /* ── 3. HOVER EFFECTS ────────────────────────────────── */
  var hoverHandlers = {
    'active-regions': {
      enter: function () {
        document.getElementById('rs-star-img').setAttribute('href', 'images/star_spots.gif');
      },
      leave: function () {
        document.getElementById('rs-star-img').setAttribute('href', 'images/star_spots.png');
      }
    },
    'limb-pulse': {
      enter: function () {
        document.getElementById('rs-star-img').setAttribute('href', 'images/star_pulse.gif');
      },
      leave: function () {
        document.getElementById('rs-star-img').setAttribute('href', 'images/star_spots.png');
      }
    },
    'orbit': {
      enter: function () {
        document.getElementById('rs-orbit-hl').setAttribute('stroke-opacity', '0.75');
      },
      leave: function () {
        document.getElementById('rs-orbit-hl').setAttribute('stroke-opacity', '0');
      }
    },
    'atmosphere': {
      enter: function () {
        var h = document.getElementById('rs-atmo-vis');
        h.setAttribute('fill',   'rgba(70,150,255,0.24)');
        h.setAttribute('stroke', 'rgba(130,200,255,0.75)');
        h.setAttribute('filter', 'url(#fGlow)');
      },
      leave: function () {
        var h = document.getElementById('rs-atmo-vis');
        h.setAttribute('fill',   'rgba(70,150,255,0.10)');
        h.setAttribute('stroke', 'rgba(100,185,255,0.38)');
        h.removeAttribute('filter');
      }
    },
    'lava': {
      enter: function () {
        document.getElementById('rs-lava-vis').setAttribute('filter', 'url(#fGlow)');
        document.getElementById('rs-lava-hl').setAttribute('opacity', '1');
      },
      leave: function () {
        document.getElementById('rs-lava-vis').removeAttribute('filter');
        document.getElementById('rs-lava-hl').setAttribute('opacity', '0');
      }
    },
    'oblateness': {
      enter: function () {
        var t = 'translate(850,280) scale(1.20,0.84) translate(-850,-280)';
        document.getElementById('rs-p1-vis').setAttribute('transform', t);
        document.getElementById('rs-core-vis').setAttribute('transform', t);
        document.getElementById('rs-core-vis').setAttribute('opacity', '0.90');
      },
      leave: function () {
        document.getElementById('rs-p1-vis').removeAttribute('transform');
        document.getElementById('rs-core-vis').removeAttribute('transform');
        document.getElementById('rs-core-vis').setAttribute('opacity', '0.50');
      }
    }
  };

  /* ── 4. TOOLTIP ──────────────────────────────────────── */
  function showTip(key, cx, cy) {
    if (!tip) return;
    tip.textContent = RESEARCH_DATA[key].title;
    tip.classList.add('visible');
    moveTip(cx, cy);
  }
  function moveTip(cx, cy) {
    if (!tip || !wrapper) return;
    var r = wrapper.getBoundingClientRect();
    var x = cx - r.left + 18;
    var y = cy - r.top  - 12;
    if (x + tip.offsetWidth > wrapper.offsetWidth - 8)
      x = cx - r.left - tip.offsetWidth - 18;
    tip.style.left = x + 'px';
    tip.style.top  = y + 'px';
  }
  function hideTip() {
    if (tip) tip.classList.remove('visible');
  }

  /* ── 5. REGION EVENT LISTENERS ──────────────────────── */
  regions.forEach(function (el) {
    var key = el.dataset.key;
    var h   = hoverHandlers[key];

    el.addEventListener('mouseenter', function (e) {
      if (h) h.enter();
      showTip(key, e.clientX, e.clientY);
    });
    el.addEventListener('mousemove', function (e) {
      moveTip(e.clientX, e.clientY);
    });
    el.addEventListener('mouseleave', function () {
      if (h) h.leave();
      hideTip();
    });
    el.addEventListener('click', function (e) {
      e.stopPropagation();   /* ← prevents template from catching and closing the panel */
      console.log('[research.js] Region clicked:', key);
      openModal(key);
    });
    el.addEventListener('touchend', function (e) {
      e.preventDefault();
      openModal(key);
    });
  });

  /* ── 6. LEGEND BUTTON LISTENERS ────────────────────── */
  legendBtns.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      console.log('[research.js] Legend button clicked:', btn.dataset.key);
      openModal(btn.dataset.key);
    });
  });

  /* ── 7. MODAL ───────────────────────────────────────── */
  function openModal(key) {
    var d = RESEARCH_DATA[key];
    if (!d) {
      console.warn('[research.js] No data found for key:', key);
      return;
    }
    console.log('[research.js] Opening modal for:', key);

    modalEmoji.textContent = d.emoji;
    modalTitle.textContent = d.title;
    modalBody.textContent  = d.body;

    modalTags.innerHTML = '';
    d.tags.forEach(function (tag) {
      var s = document.createElement('span');
      s.className   = 'rs-tag';
      s.textContent = tag;
      modalTags.appendChild(s);
    });

    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    setTimeout(function () { if (modalBox) modalBox.focus(); }, 60);
  }

  function closeModal() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  if (modalClose) modalClose.addEventListener('click', closeModal);

  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modal.classList.contains('open')) closeModal();
  });

  console.log('[research.js] All event listeners attached successfully.');

})();