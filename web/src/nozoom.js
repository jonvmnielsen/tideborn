// iOS Safari ignores user-scalable=no, so a double tap or pinch can zoom the page.
// Because the game captures all touches, the player then cannot pinch back out.
// This blocks page zoom and snaps back to 100 % if the page is ever zoomed anyway
// (iOS can even keep the zoom across a reload).

const meta = document.querySelector('meta[name="viewport"]');
const BASE = 'width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';

const isButton = (t) => t instanceof Element && !!t.closest('button, input, select, textarea, a');

// Pinch (iOS-only gesture events).
for (const type of ['gesturestart', 'gesturechange', 'gestureend']) {
  document.addEventListener(type, (e) => e.preventDefault(), { passive: false });
}

// Two-finger moves are camera + joystick in the game; never let them zoom the page.
document.addEventListener('touchmove', (e) => {
  if (e.touches.length > 1 || (e.scale !== undefined && e.scale !== 1)) e.preventDefault();
}, { passive: false });

// Double tap on anything that is not a button (buttons already use touch-action: manipulation).
let lastTap = 0;
document.addEventListener('touchend', (e) => {
  const now = performance.now();
  if (now - lastTap < 350 && !isButton(e.target)) e.preventDefault();
  lastTap = now;
}, { passive: false });
document.addEventListener('dblclick', (e) => e.preventDefault(), { passive: false });

// If the page is zoomed (now, or remembered from before), force it back to 1.
let resetting = false;
function resetZoom() {
  const vv = window.visualViewport;
  if (!vv || vv.scale <= 1.01 || resetting || !meta) return;
  resetting = true;
  // Rewriting the viewport tag makes Safari re-apply maximum-scale=1.
  meta.setAttribute('content', `${BASE}, height=device-height`);
  requestAnimationFrame(() => {
    meta.setAttribute('content', BASE);
    window.scrollTo(0, 0);
    resetting = false;
  });
}

if (meta) meta.setAttribute('content', BASE);
window.visualViewport?.addEventListener('resize', resetZoom);
window.addEventListener('orientationchange', () => setTimeout(resetZoom, 300));
document.addEventListener('visibilitychange', () => { if (!document.hidden) resetZoom(); });
window.addEventListener('pageshow', resetZoom);
resetZoom();
setInterval(resetZoom, 1500);
