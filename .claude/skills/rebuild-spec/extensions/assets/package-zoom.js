/**
 * package-zoom.js — click-to-zoom viewer for the `--package` client bundle.
 *
 * Mermaid renders every diagram inline with its own `max-width`, so a large
 * flowchart or sequence diagram is scaled DOWN to the content column and its
 * labels become unreadable. `overflow-x: auto` on `pre.mermaid` never helps:
 * the SVG was shrunk, not clipped. This module makes each rendered diagram
 * openable in a full-screen overlay with wheel zoom, drag pan, and keyboard
 * controls.
 *
 * Constraints from the pass contract (references/pipeline-package.md): the
 * bundle opens from `file://` with no network and no build step, so this is a
 * classic IIFE — no `import`, no `export`, no `require`, no CDN, no
 * dependencies beyond plain DOM APIs.
 *
 * Kept as ONE file deliberately, against the repo's 200-line modularization
 * guidance: the bundle loads it through a plain relative `<script src>` with no
 * bundler, so splitting it would mean either a second vendored asset plus a
 * second global contract between the halves, or a build step the offline
 * contract forbids. The cost of the split is real; the benefit is not.
 *
 * Chrome strings come from the sidecar's `ui.zoom` block, handed to the page
 * as JSON in `<script type="application/json" id="pkg-zoom-i18n">`. That block
 * is OPTIONAL — a corpus whose sidecar predates it (or has no sidecar at all)
 * gets the English defaults below, the same precedent as
 * `FALLBACK_START_HERE_LABEL` in package-index-body.cjs.
 */
(function () {
  'use strict';

  var DEFAULT_STRINGS = {
    title: 'Diagram viewer',
    open: 'Open this diagram in the zoom viewer',
    close: 'Close',
    zoom_in: 'Zoom in',
    zoom_out: 'Zoom out',
    fit: 'Fit to screen',
    actual_size: 'Actual size',
    hint: 'Scroll to zoom · drag to pan · Esc to close'
  };

  var MIN_SCALE = 0.1;
  var MAX_SCALE = 8;
  // Floor for the scale a diagram OPENS at. True fit is the honest overview,
  // but a real corpus holds flowcharts ~10000px wide, and fitting one of those
  // to a laptop stage lands at 12% — a hairline, which is the very complaint
  // this viewer exists to answer. Below this floor the viewer opens partly
  // zoomed and anchored top-left so the reader starts on legible content and
  // pans; the ⤢ button still gives the true whole-diagram fit in one click.
  var MIN_OPEN_SCALE = 0.5;
  var STAGE_PADDING = 24;
  var WHEEL_FACTOR = 1.15;
  var PAN_STEP = 60;
  var DRAG_SLOP = 3; // px of travel before a press counts as a pan, not a click

  var strings = readStrings();
  var overlay = null; // built lazily on first open, then reused
  var refs = null; // {stage, canvas, level}
  var view = { scale: 1, x: 0, y: 0, fitScale: 1 };
  var drag = null; // {pointerId, startX, startY, originX, originY}
  var dragMoved = false; // a real pan happened — swallow the click it synthesizes
  var opener = null; // element focus returns to on close

  function readStrings() {
    var out = {};
    for (var k in DEFAULT_STRINGS) {
      if (Object.prototype.hasOwnProperty.call(DEFAULT_STRINGS, k)) out[k] = DEFAULT_STRINGS[k];
    }
    var tag = document.getElementById('pkg-zoom-i18n');
    if (!tag) return out;
    try {
      var parsed = JSON.parse(tag.textContent || '{}');
      for (var key in out) {
        if (Object.prototype.hasOwnProperty.call(out, key) && typeof parsed[key] === 'string' && parsed[key]) {
          out[key] = parsed[key];
        }
      }
    } catch (err) {
      /* malformed block: keep the defaults rather than lose the viewer entirely */
    }
    return out;
  }

  /** Intrinsic px size of a rendered mermaid SVG, from its viewBox where possible. */
  function intrinsicSize(svg) {
    var box = svg.viewBox && svg.viewBox.baseVal;
    if (box && box.width > 0 && box.height > 0) return { w: box.width, h: box.height };
    var rect = svg.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) return { w: rect.width, h: rect.height };
    return { w: 800, h: 600 };
  }

  function button(action, label, glyph) {
    var el = document.createElement('button');
    el.type = 'button';
    el.className = 'pkg-zoom-btn';
    el.setAttribute('data-act', action);
    el.setAttribute('aria-label', label);
    el.setAttribute('title', label);
    el.textContent = glyph;
    return el;
  }

  function buildOverlay() {
    var root = document.createElement('div');
    root.className = 'pkg-zoom-overlay';
    root.setAttribute('role', 'dialog');
    root.setAttribute('aria-modal', 'true');
    root.setAttribute('aria-label', strings.title);
    root.hidden = true;

    var bar = document.createElement('div');
    bar.className = 'pkg-zoom-toolbar';
    var level = document.createElement('span');
    level.className = 'pkg-zoom-level';
    level.textContent = '100%';
    bar.appendChild(button('out', strings.zoom_out, '−'));
    bar.appendChild(level);
    bar.appendChild(button('in', strings.zoom_in, '+'));
    bar.appendChild(button('fit', strings.fit, '⤢'));
    bar.appendChild(button('actual', strings.actual_size, '1:1'));
    bar.appendChild(button('close', strings.close, '✕'));

    var stage = document.createElement('div');
    stage.className = 'pkg-zoom-stage';
    var canvas = document.createElement('div');
    canvas.className = 'pkg-zoom-canvas';
    stage.appendChild(canvas);

    var hint = document.createElement('p');
    hint.className = 'pkg-zoom-hint';
    hint.textContent = strings.hint;

    root.appendChild(bar);
    root.appendChild(stage);
    root.appendChild(hint);
    document.body.appendChild(root);

    refs = { stage: stage, canvas: canvas, level: level };

    bar.addEventListener('click', function (ev) {
      var btn = ev.target.closest ? ev.target.closest('[data-act]') : null;
      if (!btn) return;
      var act = btn.getAttribute('data-act');
      if (act === 'close') close();
      else if (act === 'in') zoomBy(WHEEL_FACTOR, null);
      else if (act === 'out') zoomBy(1 / WHEEL_FACTOR, null);
      else if (act === 'fit') applyFit();
      else if (act === 'actual') setView(1, 0, 0);
    });

    // Backdrop only — a click that started on the toolbar or the diagram must
    // not close. A press/release pair still synthesizes a `click` on the nearest
    // common ancestor no matter how far the pointer travelled between them, so a
    // pan that starts or ends on the backdrop lands here too: verified in Chrome,
    // dragging from the backdrop panned the diagram and then immediately closed
    // the viewer. `dragMoved` distinguishes a pan from a real dismiss click.
    root.addEventListener('click', function (ev) {
      if (dragMoved) {
        dragMoved = false;
        return;
      }
      if (ev.target === root || ev.target === stage) close();
    });
    stage.addEventListener('dblclick', function () {
      if (Math.abs(view.scale - view.fitScale) < 0.01) setView(1, 0, 0);
      else applyFit();
    });
    stage.addEventListener('wheel', onWheel, { passive: false });
    stage.addEventListener('pointerdown', onPointerDown);
    // A drag tracks on `window`, not on the stage. A pan routinely carries the
    // cursor off the stage — past the toolbar, past the window edge — and
    // stage-bound move/up listeners simply stop firing there, stranding the
    // gesture mid-drag with `drag` still armed. `setPointerCapture` is the other
    // way to solve this, but it is the heavier instrument: it retargets an input
    // stream globally for the duration, and an early build of this viewer showed
    // wheel events resolving to the wrong element after a captured drag.
    // Window-level tracking gets the same reach with none of that reach.
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);

    return root;
  }

  function setView(scale, x, y) {
    view.scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale));
    view.x = x;
    view.y = y;
    refs.canvas.style.transform = 'translate(' + view.x + 'px, ' + view.y + 'px) scale(' + view.scale + ')';
    refs.level.textContent = Math.round(view.scale * 100) + '%';
  }

  /** Zoom about a stage-relative point, keeping that point visually anchored. */
  function zoomBy(factor, point) {
    var next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, view.scale * factor));
    var applied = next / view.scale;
    if (applied === 1) return;
    var rect = refs.stage.getBoundingClientRect();
    var px = point ? point.x - rect.left - rect.width / 2 : 0;
    var py = point ? point.y - rect.top - rect.height / 2 : 0;
    setView(next, px - (px - view.x) * applied, py - (py - view.y) * applied);
  }

  function applyFit() {
    setView(view.fitScale, 0, 0);
  }

  /**
   * Translation that brings the diagram's top-left corner into view, for a
   * scale at which it overflows the stage. The canvas is centred by flexbox and
   * scales about its own centre, so its left edge sits at
   * `stageW/2 - w*s/2 + x` — solve that for the padding offset. An axis that
   * still fits stays centred (0).
   */
  function topLeftOffset(size, scale) {
    var rect = refs.stage.getBoundingClientRect();
    var w = size.w * scale;
    var h = size.h * scale;
    return {
      x: w > rect.width ? STAGE_PADDING - rect.width / 2 + w / 2 : 0,
      y: h > rect.height ? STAGE_PADDING - rect.height / 2 + h / 2 : 0,
    };
  }

  function onWheel(ev) {
    ev.preventDefault();
    zoomBy(ev.deltaY < 0 ? WHEEL_FACTOR : 1 / WHEEL_FACTOR, { x: ev.clientX, y: ev.clientY });
  }

  function onPointerDown(ev) {
    if (ev.button !== 0 && ev.pointerType === 'mouse') return;
    drag = { pointerId: ev.pointerId, startX: ev.clientX, startY: ev.clientY, originX: view.x, originY: view.y };
    dragMoved = false;
    refs.stage.classList.add('is-panning');
  }

  function onPointerMove(ev) {
    if (!drag || ev.pointerId !== drag.pointerId) return;
    ev.preventDefault();
    var dx = ev.clientX - drag.startX;
    var dy = ev.clientY - drag.startY;
    if (Math.abs(dx) > DRAG_SLOP || Math.abs(dy) > DRAG_SLOP) dragMoved = true;
    setView(view.scale, drag.originX + dx, drag.originY + dy);
  }

  /** Ends a pan. Bound on `window`, so a release anywhere on the page counts. */
  function onPointerUp(ev) {
    if (!drag || ev.pointerId !== drag.pointerId) return;
    drag = null;
    refs.stage.classList.remove('is-panning');
  }

  function onKeyDown(ev) {
    if (!overlay || overlay.hidden) return;
    var key = ev.key;
    if (key === 'Escape') close();
    else if (key === '+' || key === '=') zoomBy(WHEEL_FACTOR, null);
    else if (key === '-' || key === '_') zoomBy(1 / WHEEL_FACTOR, null);
    else if (key === '0') applyFit();
    else if (key === '1') setView(1, 0, 0);
    else if (key === 'ArrowLeft') setView(view.scale, view.x + PAN_STEP, view.y);
    else if (key === 'ArrowRight') setView(view.scale, view.x - PAN_STEP, view.y);
    else if (key === 'ArrowUp') setView(view.scale, view.x, view.y + PAN_STEP);
    else if (key === 'ArrowDown') setView(view.scale, view.x, view.y - PAN_STEP);
    else return;
    ev.preventDefault();
  }

  /**
   * Give the clone its own root id and repoint its stylesheet at it.
   *
   * Mermaid emits every rule in its inline `<style>` scoped to the SVG's own id
   * (`#mermaid-1787795211799 .node rect { ... }`). Simply dropping the id to
   * avoid a duplicate silently unstyles the whole clone — flowchart nodes lost
   * their fills and rendered as solid black boxes. Renaming keeps the rules
   * matching while leaving exactly one element per id in the document.
   *
   * Ids nested inside `<defs>` (markers, gradients) are deliberately left alone:
   * the two subtrees are byte-identical, so a `url(#id)` reference resolves to
   * an equivalent node either way, and rewriting them would mean parsing every
   * attribute that can carry a functional IRI.
   */
  function rescopeCloneId(svg, clone) {
    var oldId = svg.getAttribute('id');
    if (!oldId) return;
    var newId = oldId + '-pkgzoom';
    clone.setAttribute('id', newId);
    var styles = clone.querySelectorAll('style');
    for (var i = 0; i < styles.length; i++) {
      styles[i].textContent = styles[i].textContent.split('#' + oldId).join('#' + newId);
    }
  }

  /** Take the page behind the viewer out of the tab order (and back). */
  function setShellInert(on) {
    var shell = document.querySelector('.pkg-shell');
    if (shell) shell.inert = on;
  }

  function open(svg, host) {
    if (!overlay) overlay = buildOverlay();
    opener = host;

    var size = intrinsicSize(svg);
    var clone = svg.cloneNode(true);
    // Mermaid stamps `max-width: NNNpx` on the live SVG to fit the content
    // column. Inside the overlay that cap is exactly what we are escaping, so
    // the clone is re-sized to its intrinsic dimensions and scaled by transform.
    clone.removeAttribute('style');
    rescopeCloneId(svg, clone);
    clone.setAttribute('width', String(size.w));
    clone.setAttribute('height', String(size.h));
    clone.style.maxWidth = 'none';
    clone.style.width = size.w + 'px';
    clone.style.height = size.h + 'px';

    refs.canvas.innerHTML = '';
    refs.canvas.appendChild(clone);
    refs.canvas.style.width = size.w + 'px';
    refs.canvas.style.height = size.h + 'px';

    overlay.hidden = false;
    document.documentElement.classList.add('pkg-zoom-open');
    // `aria-modal` is a promise that focus stays in the dialog. The page behind
    // is only visually covered — its sidebar links, <details> toggles and other
    // diagram hosts keep their place in the tab order — so mark the shell inert
    // for as long as the viewer is up. `inert` degrades silently where it isn't
    // supported, which is no worse than not setting it.
    setShellInert(true);

    var rect = refs.stage.getBoundingClientRect();
    var fit = Math.min(
      (rect.width - STAGE_PADDING * 2) / size.w,
      (rect.height - STAGE_PADDING * 2) / size.h
    );
    // Never enlarge a diagram that already fits, and never fit below the floor.
    view.fitScale = Math.min(1, Math.max(MIN_SCALE, fit));
    var openScale = Math.max(view.fitScale, MIN_OPEN_SCALE);
    var offset = topLeftOffset(size, openScale);
    setView(openScale, offset.x, offset.y);

    var closeBtn = overlay.querySelector('[data-act="close"]');
    if (closeBtn) closeBtn.focus();
  }

  function close() {
    if (!overlay || overlay.hidden) return;
    overlay.hidden = true;
    document.documentElement.classList.remove('pkg-zoom-open');
    setShellInert(false);
    refs.canvas.innerHTML = ''; // drop the clone so a big diagram isn't held in memory
    if (opener && opener.focus) opener.focus();
    opener = null;
  }

  /**
   * Mark every rendered diagram on the page as openable. Idempotent — safe to
   * call again after mermaid renders more content. A `pre.mermaid` that mermaid
   * failed to render holds raw text, not an `<svg>`, and is deliberately left
   * alone: there is nothing to zoom.
   */
  function attach() {
    var hosts = document.querySelectorAll('pre.mermaid');
    for (var i = 0; i < hosts.length; i++) {
      var host = hosts[i];
      if (host.classList.contains('pkg-zoomable')) continue;
      var svg = host.querySelector('svg');
      if (!svg) continue;
      host.classList.add('pkg-zoomable');
      host.setAttribute('role', 'button');
      host.setAttribute('tabindex', '0');
      host.setAttribute('aria-label', strings.open);
      host.setAttribute('title', strings.open);
      host.addEventListener('click', onHostActivate);
      host.addEventListener('keydown', onHostKey);
    }
  }

  function onHostActivate(ev) {
    var host = ev.currentTarget;
    var svg = host.querySelector('svg');
    if (svg) open(svg, host);
  }

  function onHostKey(ev) {
    if (ev.key !== 'Enter' && ev.key !== ' ' && ev.key !== 'Spacebar') return;
    ev.preventDefault();
    onHostActivate(ev);
  }

  document.addEventListener('keydown', onKeyDown);
  // A button released entirely outside the browser window may never deliver a
  // pointerup, which would leave `drag` armed and make the next hover pan.
  window.addEventListener('blur', function () {
    if (!drag) return;
    drag = null;
    dragMoved = false;
    refs.stage.classList.remove('is-panning');
  });

  window.pkgZoom = { attach: attach, close: close };
})();
