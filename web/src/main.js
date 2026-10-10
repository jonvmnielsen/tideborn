// Tideborn — browser/mobile. Phase 1 "Camp": wash ashore, gather, craft tools,
// build a home, survive day and night.
import './nozoom.js';
import * as THREE from 'three';
import { loadAssets } from './assets.js';
import { World } from './world/world.js';
import { Player } from './player.js';
import { OrbitCam } from './camera.js';
import { Chips } from './fx.js';
import { Input } from './input.js';
import { UI } from './ui.js';
import { Inventory } from './systems/inventory.js';
import { Gather } from './systems/gather.js';
import { Building } from './systems/building.js';
import { DayNight } from './systems/daynight.js';
import { Survival } from './systems/survival.js';
import { loadSave, writeSave, clearSave } from './save.js';
import { ITEMS, itemName } from './data/items.js';
import { PIECE } from './data/build.js';
import { TOOL_NAME } from './data/harvest.js';

const canvas = document.getElementById('game');
const loadFill = document.getElementById('loadFill');
const loadText = document.getElementById('loadText');
const loadingEl = document.getElementById('loading');
const params = new URLSearchParams(location.search);
if (params.has('reset')) clearSave();

const mobile = matchMedia('(pointer: coarse)').matches;
const renderer = new THREE.WebGLRenderer({ canvas, antialias: !mobile || devicePixelRatio < 2, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.6 : 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = mobile ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const VIEW = mobile ? 230 : 320; // fog end; chunks beyond it are culled
scene.fog = new THREE.Fog('#e9f2ee', VIEW * 0.3, VIEW);
const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.3, VIEW + 30);
const hemi = new THREE.HemisphereLight(0xdff1ff, 0x7c8f5a, 1.35);
scene.add(hemi);
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6);
sun.castShadow = true;
sun.shadow.mapSize.set(mobile ? 1024 : 2048, mobile ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -36, right: 36, top: 36, bottom: -36, near: 1, far: 160 });
sun.shadow.bias = -0.0005;
sun.shadow.normalBias = 0.05;
scene.add(sun, sun.target);

// A few point lights shared by the nearest fires and torches.
const lightPool = Array.from({ length: mobile ? 2 : 4 }, () => {
  const l = new THREE.PointLight(0xffa64a, 0, 16, 1.6);
  scene.add(l);
  return l;
});

function fail(err) {
  console.error(err);
  loadText.textContent = `Øen kunne ikke indlæses. Genindlæs siden for at prøve igen. (${err?.message ?? err})`;
  loadText.classList.add('error');
}

const OBJECTIVES = [
  { id: 'wood3', text: 'Saml træ: knæk grene af de døde træer på stranden', done: (g) => g.inv.count('wood') >= 3 || g.flags.axe },
  { id: 'mats', text: 'Saml løse sten og siv ved vandkanten', done: (g) => (g.inv.count('stone') >= 2 && g.inv.count('fiber') >= 2) || g.flags.axe },
  { id: 'axe', text: 'Åbn Rygsæk og lav en stenøkse', done: (g) => g.inv.has('stone_axe') },
  { id: 'fell', text: 'Fæld et træ med øksen', done: (g) => g.flags.felled },
  { id: 'found', text: 'Tryk Byg og læg et fundament', done: (g) => g.building.pieces.some((p) => p.id === 'foundation') },
  { id: 'walls', text: 'Byg vægge og en døråbning på fundamentet', done: (g) => g.building.pieces.filter((p) => p.edge).length >= 3 },
  { id: 'roof', text: 'Læg et tag over', done: (g) => g.building.pieces.some((p) => p.id === 'roof') },
  { id: 'fire', text: 'Byg et bål og en seng, så har du et hjem', done: (g) => g.building.pieces.some((p) => p.id === 'campfire') && g.building.pieces.some((p) => p.id === 'bed') },
  { id: 'pick', text: 'Lav en hakke og hak sten af de store klipper', done: (g) => g.inv.has('stone_pick') },
  { id: 'explore', text: 'Udforsk øen: Kæmpetræet i midten og tårnet på højderyggen mod nord', done: () => false },
];

async function start() {
  const assets = await loadAssets((p) => { loadFill.style.width = `${Math.round(p * 70)}%`; });
  loadText.textContent = 'Bygger øen …';
  await new Promise((r) => setTimeout(r, 30));

  const world = new World(scene, assets);
  loadFill.style.width = '90%';
  const player = new Player(scene, assets.player, world);
  const chips = new Chips(scene);
  const gather = new Gather(world, chips);
  const building = new Building(world, assets);
  const inv = new Inventory();
  const survival = new Survival();
  const dayNight = new DayNight({ scene, sun, hemi, sky: world.sky, world });
  const cam = new OrbitCam(camera, world);
  const ui = new UI();
  const input = new Input({
    moveZone: document.getElementById('moveZone'),
    lookZone: document.getElementById('lookZone'),
    stick: document.getElementById('stick'),
    knob: document.getElementById('knob'),
  });

  const flags = { axe: false, felled: false, objective: 0 };
  let home = null; // bed spawn
  let gameTime = 0;
  let dirty = false;

  // --- Load save ---------------------------------------------------------------
  const save = loadSave();
  if (save) {
    try {
      for (const [id, n] of Object.entries(save.inv ?? {})) inv.add(id, n);
      survival.restore(save.surv);
      if (save.time) { dayNight.phase = save.time.p; dayNight.day = save.time.d; }
      Object.assign(flags, save.flags);
      building.restore(save.build);
      gather.restore(save.nodes, 0);
      player.restore(save.player);
      home = save.home ?? null;
    } catch (err) {
      // A save that does not fit this version must never block the game: start fresh.
      console.error('Save could not be restored', err);
      clearSave();
      location.replace(`${location.pathname}?reset`);
      return;
    }
  }

  if (camera.aspect < 0.8) { cam.dist = 12.5; cam.pitch = 0.5; }
  cam.snapBehind(player.facing);
  player.setTool(inv.hasTool('axe'));

  const persist = () => {
    writeSave({
      inv: inv.serialize(), surv: survival.serialize(), time: { p: +dayNight.phase.toFixed(4), d: dayNight.day },
      flags, build: building.serialize(), nodes: gather.serialize(gameTime), player: player.serialize(), home,
    });
    dirty = false;
  };
  setInterval(() => { if (dirty && player.state !== 'dead') persist(); }, 6000);
  document.addEventListener('visibilitychange', () => { if (document.hidden) persist(); });
  window.addEventListener('pagehide', persist);
  inv.onChange(() => { dirty = true; ui.renderSheet(); if (build.on) ui.renderPalette(build.piece, inv); player.setTool(inv.hasTool('axe')); });

  dayNight.on('dawn', () => {
    gather.tideIn();
    ui.toast('Tidevandet har skyllet nye forsyninger i land');
  });
  dayNight.on('dusk', () => ui.toast('Det bliver mørkt. Et bål giver lys og tryghed.'));

  // --- Build mode ------------------------------------------------------------------
  // In build mode the left stick moves a cursor (and the piece snapped to it) instead
  // of the player. The camera orbits the cursor; the player walks after it if it gets far.
  const build = { on: false, piece: 'foundation', remove: false, cursor: { x: 0, y: 0, z: 0 }, rot: 0, level: 0, lift: 0 };
  const cursorMark = new THREE.Mesh(
    new THREE.RingGeometry(0.28, 0.42, 24).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, depthTest: false }),
  );
  cursorMark.renderOrder = 10;
  cursorMark.visible = false;
  scene.add(cursorMark);
  const setBuild = (on) => {
    build.on = on;
    building.highlight(null);
    build.remove = false;
    ui.setBuildMode(on);
    ui.setRemoveMode(false);
    building.setGhost(on ? build.piece : null);
    cursorMark.visible = on;
    if (on) {
      build.cursor.x = player.pos.x + Math.sin(player.facing) * 4.5;
      build.cursor.z = player.pos.z + Math.cos(player.facing) * 4.5;
      build.level = building.levelAt(player.pos.x, player.pos.z, player.pos.y + 0.3);
      build.lift = 0;
      cam.pitch = Math.max(cam.pitch, 0.72);
      cam.dist = Math.max(cam.dist, 13);
      ui.renderPalette(build.piece, inv);
    }
    if (on && ui.sheetOpen) ui.closeSheet();
  };
  const levelText = () => (build.piece === 'foundation' && !build.remove
    ? `Højde ${build.lift >= 0 ? '+' : '−'}${Math.abs(build.lift * 0.5).toFixed(1).replace('.', ',')} m`
    : `Etage ${build.level + 1}`);
  const raise = (dir) => {
    if (!build.on) return;
    if (build.piece === 'foundation' && !build.remove) build.lift = Math.max(-2, Math.min(8, build.lift + dir));
    else build.level = Math.max(0, Math.min(4, build.level + dir));
  };
  const rotate = () => { build.rot = (build.rot + Math.PI / 4) % (Math.PI * 2); };
  ui.on('buildBtn', () => setBuild(!build.on));
  ui.on('pickPiece', (id) => { building.highlight(null); build.piece = id; build.remove = false; ui.setRemoveMode(false); building.setGhost(id); ui.renderPalette(id, inv); });
  ui.on('rotateBtn', rotate);
  ui.on('upBtn', () => raise(1));
  ui.on('downBtn', () => raise(-1));
  ui.on('removeBtn', () => { build.remove = !build.remove; building.highlight(null); ui.setRemoveMode(build.remove); building.setGhost(build.remove ? null : build.piece); });

  // --- Inventory / crafting --------------------------------------------------------
  const openInv = () => { if (build.on) setBuild(false); ui.openSheet(inv); };
  ui.on('invBtn', () => (ui.sheetOpen ? ui.closeSheet() : openInv()));
  ui.on('craft', (r) => {
    if (!inv.pay(r.cost)) return;
    for (const [id, n] of Object.entries(r.out)) inv.add(id, n);
    if (r.out.stone_axe) flags.axe = true;
    ui.toast(`Du lavede: ${itemName(Object.keys(r.out)[0])}`);
    ui.renderSheet();
  });
  const eat = () => {
    if (!inv.has('food') || player.busy) return;
    if (ui.sheetOpen) ui.closeSheet();
    player.perform('eat', null, () => { inv.remove('food'); survival.eat(ITEMS.food.food); dirty = true; });
  };
  ui.on('eat', eat);
  ui.on('eatBtn', eat);
  ui.on('changed', () => { dirty = true; });
  ui.on('sheetClosed', () => {});

  // --- Keys ----------------------------------------------------------------------------
  input.on('e', () => ui.press());
  input.on(' ', () => ui.press());
  input.on('e:up', () => ui.release());
  input.on(' :up', () => ui.release());
  input.on('b', () => setBuild(!build.on));
  input.on('i', () => (ui.sheetOpen ? ui.closeSheet() : openInv()));
  input.on('tab', () => (ui.sheetOpen ? ui.closeSheet() : openInv()));
  input.on('r', rotate);
  input.on('c', () => raise(1));
  input.on('z', () => raise(-1));
  input.on('pageup', () => raise(1));
  input.on('pagedown', () => raise(-1));
  input.on('x', () => build.on && ui.handlers.removeBtn());
  input.on('f', eat);
  input.on('escape', () => { if (ui.sheetOpen) ui.closeSheet(); else if (build.on) setBuild(false); });
  input.on('blur', () => ui.release());

  // --- Camera / resize ---------------------------------------------------------------
  const onResize = () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  };
  window.addEventListener('resize', onResize);
  onResize();

  // --- Context action (outside build mode) ------------------------------------------------
  let queued = false;
  function context() {
    if (player.state === 'dead' || player.state === 'sleep') return null;
    const piece = building.pieceInFront(player, ['chest', 'bed'], 2.6);
    if (piece?.id === 'chest') return { kind: 'chest', piece, label: 'Åbn kiste', icon: 'ui/b_chest.webp', enabled: true };
    if (piece?.id === 'bed') return { kind: 'bed', piece, label: dayNight.isNight ? 'Sov til morgen' : 'Gør til hjem', icon: 'ui/b_bed.webp', enabled: true };
    const node = gather.findTarget(player.pos.x, player.pos.z, player.facing);
    if (node) {
      const needs = node.def.tool && !inv.hasTool(node.def.tool);
      return { kind: 'node', node, needs, label: needs ? `Kræver ${ITEMS[node.def.tool === 'axe' ? 'stone_axe' : 'stone_pick'].name.toLowerCase()}` : node.def.label, icon: node.def.icon, enabled: true, style: needs ? 'locked' : '' };
    }
    return null;
  }

  function useContext(c) {
    if (!c) return;
    if (c.kind === 'chest') { ui.openSheet(inv, c.piece.storage); return; }
    if (c.kind === 'bed') {
      home = { x: c.piece.x, z: c.piece.z };
      dirty = true;
      if (!dayNight.isNight) { ui.toast('Sengen er nu dit hjem. Du vågner her, hvis du besvimer.'); return; }
      player.sleep(true);
      ui.overlay('Du sover …', true);
      setTimeout(() => {
        dayNight.skipToMorning();
        survival.eat(-10);
        player.sleep(false);
        ui.overlay(null, false);
        persist();
      }, 1600);
      return;
    }
    if (c.kind === 'node') {
      if (c.needs) { ui.toast(`Du skal bruge ${TOOL_NAME[c.node.def.tool]}. Lav den i Rygsækken.`); return; }
      const node = c.node;
      player.perform(node.def.anim, { x: node.x, z: node.z }, () => {
        const res = gather.hit(node, gameTime, player.pos.x, player.pos.z);
        if (!res) return;
        const got = inv.add(res.item, res.amount);
        if (res.item === 'food' && Math.random() < 0.5) inv.add('fiber', 2);
        ui.floater(new THREE.Vector3(node.x, node.y + 2, node.z), res.item, got || res.amount);
        if (res.spent && node.def.fall && node.def.tool === 'axe' && !flags.felled) { flags.felled = true; player.pendingCheer = true; }
      }, () => {
        if (player.pendingCheer) { player.pendingCheer = false; player.cheer(); return; }
        if (ui.actionHeld || queued) {
          queued = false;
          const next = context();
          if (next?.kind === 'node' && !next.needs) useContext(next);
        }
      });
    }
  }

  // --- Death / respawn -------------------------------------------------------------
  function handleDeath() {
    player.die();
    if (build.on) setBuild(false);
    ui.overlay('Du besvimede af sult …', true);
    setTimeout(() => {
      const at = home ?? world.spawn;
      player.revive(at.x + 1.5, at.z + 1.5, player.facing);
      survival.health = 60;
      survival.hunger = Math.max(survival.hunger, 45);
      ui.overlay(null, false);
      ui.toast(home ? 'Du vågnede i din seng' : 'Du vågnede på stranden ved vraget');
      cam.snapBehind(player.facing);
      persist();
    }, 3500);
  }

  // --- Loop ------------------------------------------------------------------------------
  const clock = new THREE.Clock();
  let t = 0, fpsT = performance.now(), fpsN = 0;
  const tmpV = new THREE.Vector3();

  function frame() {
    const dt = Math.min(clock.getDelta(), 0.05);
    t += dt;
    gameTime += dt;

    input.enabled = !ui.sheetOpen && player.state !== 'dead' && player.state !== 'sleep';
    input.update();
    const look = input.takeLook();
    const { fx, fz, rx, rz } = cam.basis();
    let mx = rx * input.move.x - fx * input.move.y;
    let mz = rz * input.move.x - fz * input.move.y;
    let moveMag = input.move.mag;
    let focus = null;

    if (build.on) {
      // Stick drives the cursor; the player stays put unless the cursor runs away.
      const c = build.cursor;
      const speed = 9 * (0.35 + 0.65 * moveMag);
      c.x += mx * speed * dt;
      c.z += mz * speed * dt;
      const dx = c.x - player.pos.x, dz = c.z - player.pos.z, d = Math.hypot(dx, dz);
      const MAXD = 24;
      if (d > MAXD) { c.x = player.pos.x + (dx / d) * MAXD; c.z = player.pos.z + (dz / d) * MAXD; }
      const base = building.baseTop(Math.round(c.x / 4), Math.round(c.z / 4));
      c.y = (base ?? world.terrain.heightAt(c.x, c.z)) + build.level * 4;
      if (d > 11 && player.state === 'free') { mx = dx / d; mz = dz / d; moveMag = d > 16 ? 1 : 0.5; }
      else { mx = 0; mz = 0; moveMag = 0; }
      focus = c;
      cursorMark.position.set(c.x, Math.max(c.y, world.groundAt(c.x, c.z, c.y + 0.3)) + 0.06, c.z);
      cursorMark.material.opacity = 0.55 + 0.3 * Math.sin(t * 5);
      ui.setLevelLabel(levelText());
    }
    const buildCtx = () => ({ x: build.cursor.x, z: build.cursor.z, vx: -Math.sin(cam.yaw), vz: -Math.cos(cam.yaw), rot: build.rot, level: build.level, lift: build.lift });

    // Actions
    const pressed = ui.consumePress();
    if (build.on) {
      if (build.remove) {
        const target = building.pieceNear(buildCtx());
        building.highlight(target);
        ui.setAction(target ? { label: `Fjern ${(PIECE[target.id]?.name ?? 'Etage').toLowerCase()}`, icon: PIECE[target.id]?.icon ?? 'ui/b_floor.webp', enabled: true, style: 'locked' } : { label: 'Peg på noget', icon: 'ui/b_wall.webp', enabled: false });
        ui.objective('Fjern: halvdelen af materialerne kommer tilbage');
        if (pressed && target) {
          const why = building.removalBlocker(target);
          if (why) ui.toast(why);
          else {
            building.remove(target);
            for (const [id, n] of Object.entries(PIECE[target.id]?.cost ?? { wood: 6 })) inv.add(id, Math.floor(n / 2));
            dirty = true;
          }
        }
      } else {
        const plan = building.updateGhost(buildCtx(), inv);
        const def = PIECE[build.piece];
        ui.setAction({ label: plan?.ok ? 'Placér' : 'Kan ikke', icon: def.icon, enabled: !!plan?.pos, style: plan?.ok ? 'build' : 'locked' });
        ui.objective(plan?.ok ? `${def.name}: ${Object.entries(def.cost).map(([id, n]) => `${n} ${itemName(id).toLowerCase()}`).join(', ')}` : plan?.reason ?? 'Gå tættere på');
        if (pressed && plan) {
          if (!plan.ok) ui.toast(plan.reason);
          else if (inv.pay(def.cost)) {
            building.place(build.piece, plan);
            player.perform('build', plan.pos, null, null);
            chips.burst(tmpV.set(plan.pos.x, plan.pos.y + 0.3, plan.pos.z), '#c8b48a', 8, 0.6);
            dirty = true;
            ui.renderPalette(build.piece, inv);
          }
        }
      }
    } else {
      const c = player.state === 'free' ? context() : null;
      if (player.state === 'free') ui.setAction(c);
      if (pressed) {
        if (player.state === 'action') queued = true;
        else useContext(c);
      } else if (ui.actionHeld && player.state === 'free' && c?.kind === 'node' && !c.needs && input.move.mag < 0.2) useContext(c);
      if (input.move.mag > 0.3) queued = false;
      // Objective line
      while (flags.objective < OBJECTIVES.length - 1 && OBJECTIVES[flags.objective].done({ inv, flags, building })) {
        flags.objective++;
        dirty = true;
        if (flags.objective > 0) ui.toast('Godt klaret!', 1400);
      }
      ui.objective(OBJECTIVES[flags.objective].text);
    }

    // Simulation
    const sleeping = player.state === 'sleep';
    survival.update(dt * (sleeping ? 0 : 1), sleeping);
    if (survival.dead && player.state !== 'dead') handleDeath();
    dayNight.update(dt);
    player.update(dt, mx, mz, moveMag);
    gather.update(dt, gameTime, player);
    building.update(dt, t);
    chips.update(dt, (x, z) => world.groundAt(x, z));
    cam.update(dt, player, look, input.takeZoom(), moveMag > 0.2, focus);
    world.update(dt, t, camera, dayNight.light, dayNight.sunDir);

    // Sun / shadows follow the player
    sun.position.copy(player.pos).addScaledVector(dayNight.sunDir, 70);
    sun.target.position.copy(player.pos);

    // Nearest fires get the point lights
    const night = dayNight.nightness ?? 0;
    const lights = building.lights.slice().sort((a, b) => (a.x - player.pos.x) ** 2 + (a.z - player.pos.z) ** 2 - ((b.x - player.pos.x) ** 2 + (b.z - player.pos.z) ** 2));
    lightPool.forEach((l, i) => {
      const s = lights[i];
      if (!s) { l.intensity = 0; return; }
      l.position.set(s.x, s.y, s.z);
      l.distance = s.range;
      l.intensity = s.power * (0.25 + 0.75 * night) * (1 + 0.08 * Math.sin(t * 11 + i));
    });

    ui.setMeters(survival.health, survival.hunger, inv.has('food'));
    ui.setClock(dayNight.day, dayNight.clock, dayNight.isNight);
    ui.update(dt, camera);
    if (player.state === 'free' && input.move.mag > 0.1) dirty = true;

    renderer.render(scene, camera);
    fpsN++;
    const now = performance.now();
    if (now - fpsT > 2000) {
      const fps = Math.round((fpsN * 1000) / (now - fpsT));
      window.__tideborn.fps = fps;
      // Step resolution down on slow devices, never below 1x.
      const pr = renderer.getPixelRatio();
      if (fps < 28 && pr > 1 && !params.has('fixedres')) renderer.setPixelRatio(Math.max(1, pr - 0.3));
      fpsT = now; fpsN = 0;
    }
    requestAnimationFrame(frame);
  }

  window.__tideborn = { fps: 0, world, player, gather, building, inv, survival, dayNight, cam, ui, input, scene, camera, renderer, flags, setBuild, build, persist };
  loadFill.style.width = '100%';
  ui.show();
  requestAnimationFrame(() => {
    loadingEl.classList.add('done');
    setTimeout(() => loadingEl.remove(), 500);
  });
  if (!save) ui.toast('Du er skyllet i land. Find materialer på stranden.', 4000);
  frame();
}

start().catch(fail);
