// Local save in the browser (per device). Fails quietly if storage is unavailable.
// v2 = the large-island version. Older saves are from a different map and are dropped.
const KEY = 'tideborn.save.v2';
const OLD_KEYS = ['tideborn.save.v1'];

try {
  for (const k of OLD_KEYS) localStorage.removeItem(k);
} catch {
  /* storage unavailable */
}

export function loadSave() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    return data && data.v === 2 ? data : null;
  } catch {
    return null;
  }
}

export function writeSave(data) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ v: 2, savedAt: Date.now(), ...data }));
    return true;
  } catch {
    return false;
  }
}

export function clearSave() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
