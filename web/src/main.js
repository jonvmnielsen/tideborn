// Tideborn — browser/mobile slice. Wash up in a cove, gather wood and stone.
import * as THREE from 'three';
import { loadAssets } from './assets.js';
import { World } from './world.js';
import { Player } from './player.js';
import { ResourceNodes } from './resources.js';
import { Chips } from './fx.js';
import { Input } from './input.js';
import { Hud } from './hud.js';
import { loadSave, writeSave, clearSave } from './save.js';
import { damp, clamp } from './util.js';

const canvas = document.getElementById('game');
const loadFill = document.getElementById('loadFill');
const loadText = document.getElementById('loadText');
const loadingEl = document.getElementById('loading');

if (new URLSearchParams(location.search).has('reset')) clearSave();

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const HORIZON = new THREE.Color('#eaf3f0');
scene.fog = new THREE.Fog(HORIZON, 70, 210);

const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 1.0, 900);

scene.add(new THREE.HemisphereLight(0xdff1ff, 0x7c8f5a, 1.35));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6);
sun.castShadow = true;
const mobile = matchMedia('(pointer: coarse)').matches;
sun.shadow.mapSize.set(mobile ? 1024 : 2048, mobile ? 1024 : 2048);
Object.assign(sun.shadow.camera, { left: -26, right: 26, top: 26, bottom: -26, near: 1, far: 120 });
sun.shadow.bias = -0.0006;
sun.shadow.normalBias = 0.04;
scene.add(sun, sun.target);

function fail(err) {
  console.error(err);
  loadText.textContent = 'Øen kunne ikke indlæses. Genindlæs siden for at prøve igen.';
  loadText.classList.add('error');
}

async function start() {
  const assets = await loadAssets((p) => {
    loadFill.style.width = `${Math.round(p * 85)}%`;
  });
  loadText.textContent = 'Bygger øen …';
  await new Promise((r) => requestAnimationFrame(r));

  const world = new World(scene, assets);
  loadFill.style.width = '95%';
  const player = new Player(scene, assets.player, world);
  const nodes = new ResourceNodes(scene, assets, world);
  const chips = new Chips(scene);
  const hud = new Hud();
  const input = new Input({
    zone: document.getElementById('touchZone'),
    stick: document.getElementById('stick'),
    knob: document.getElementById('knob'),
    action: document.getElementById('action'),
  });

  // --- State + save -----------------------------------------------------
  const inv = { wood: 0, stone: 0 };
  const progress = { moved: false, gathered: false, firstTree: false };
  let gameTime = 0;
  let dirty = false;
  const save = loadSave();
  if (save) {
    Object.assign(inv, save.inv);
    Object.assign(progress, save.progress);
    player.restore(save.player);
    nodes.restore(save.nodes, 0);
  }
  hud.setInventory(inv);
  const persist = (flash) => {
    const ok = writeSave({ inv, progress, player: player.serialize(), nodes: nodes.serialize(gameTime) });
    dirty = false;
    if (ok && flash) hud.flashSaved();
  };
  setInterval(() => { if (dirty) persist(true); }, 5000);
  document.addEventListener('visibilitychange', () => { if (document.hidden) persist(false); });
  window.addEventListener('pagehide', () => persist(false));

  // --- Camera ------------------------------------------------------------
  const camTarget = new THREE.Vector3().copy(player.pos);
  let zoom = 1;
  const camDistance = () => (camera.aspect < 0.8 ? 32 : camera.aspect < 1.2 ? 28 : 24) * zoom;
  const PITCH = THREE.MathUtils.degToRad(47);
  const placeCamera = (dt) => {
    const k = dt ? 1 - Math.exp(-6 * dt) : 1;
    camTarget.lerp(new THREE.Vector3(player.pos.x, player.pos.y + 1.0, player.pos.z), k);
    const d = camDistance();
    camera.position.set(camTarget.x, camTarget.y + Math.sin(PITCH) * d, camTarget.z + Math.cos(PITCH) * d);
    camera.lookAt(camTarget);
    sun.position.copy(camTarget).addScaledVector(world.sunDir, 50);
    sun.target.position.copy(camTarget);
  };
  window.addEventListener('wheel', (e) => { zoom = clamp(zoom * (1 + Math.sign(e.deltaY) * 0.1), 0.65, 1.6); }, { passive: true });
  const onResize = () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  };
  window.addEventListener('resize', onResize);
  onResize();
  placeCamera(0);

  // --- Gathering -----------------------------------------------------------
  let queuedPress = false; // a tap during a swing chains the next swing
  const startSwing = (target) => {
    player.swing(
      target,
      () => {
        const res = nodes.hit(target, gameTime, player.pos.x, player.pos.z, chips);
        if (!res) return;
        inv[res.item] += res.amount;
        hud.setInventory(inv, res.item);
        hud.floater(new THREE.Vector3(target.x, target.y + target.k.impactY + 1.2, target.z), res.item, res.amount);
        progress.gathered = true;
        dirty = true;
        if (res.depleted && target.kind === 'tree' && !progress.firstTree) {
          progress.firstTree = true;
          player.pendingCheer = true;
        }
      },
      () => {
        if (player.pendingCheer) {
          player.pendingCheer = false;
          player.cheer();
          return;
        }
        if (input.actionHeld || queuedPress) {
          queuedPress = false;
          const next = nodes.findTarget(player.pos.x, player.pos.z, player.facing);
          if (next) startSwing(next);
        }
      },
    );
  };

  // --- Hints ----------------------------------------------------------------
  const touchFirst = matchMedia('(pointer: coarse)').matches;
  const hintFor = () => {
    if (!progress.moved) return touchFirst ? 'Træk med tommelfingeren i venstre side for at gå' : 'Gå med WASD eller piletasterne';
    if (!progress.gathered) return touchFirst ? 'Gå hen til et træ og tryk på knappen' : 'Gå hen til et træ og tryk E';
    return '';
  };

  // --- Loop -------------------------------------------------------------------
  const clock = new THREE.Clock();
  let t = 0;
  function frame() {
    const dt = Math.min(clock.getDelta(), 0.05);
    t += dt;
    gameTime += dt;

    input.update();
    if (input.move.mag > 0.3 && !progress.moved) { progress.moved = true; dirty = true; }

    const target = player.busy ? null : nodes.findTarget(player.pos.x, player.pos.z, player.facing);
    hud.setAction(target ?? (player.state === 'swing' ? player.swingTarget : null), player.state === 'swing');
    const pressed = input.consumePress();
    if (pressed && player.state === 'swing') queuedPress = true;
    else if (pressed && target && !player.busy) startSwing(target);
    else if (input.actionHeld && target && !player.busy && input.move.mag < 0.2) startSwing(target);
    if (input.move.mag > 0.3) queuedPress = false;

    player.update(dt, input.move);
    nodes.update(dt, gameTime, player);
    chips.update(dt, (x, z) => world.heightAt(x, z));
    world.update(dt, t, camera);
    placeCamera(dt);
    hud.update(dt, camera);
    hud.hint(hintFor());
    if (player.state === 'free' && input.move.mag > 0.1) dirty = true;

    renderer.render(scene, camera);
    fpsT += dt; fpsN++;
    if (fpsT > 1) { window.__tideborn.fps = Math.round(fpsN / fpsT); fpsT = 0; fpsN = 0; }
    requestAnimationFrame(frame);
  }

  let fpsT = 0, fpsN = 0;
  window.__tideborn = { fps: 0, world, player, nodes, input, inv, scene, camera, renderer, setZoom: (z) => { zoom = z; placeCamera(0); } };
  loadFill.style.width = '100%';
  hud.show();
  requestAnimationFrame(() => {
    loadingEl.classList.add('done');
    setTimeout(() => loadingEl.remove(), 500);
  });
  frame();
}

start().catch(fail);
