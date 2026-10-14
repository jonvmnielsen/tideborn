// Tideborn look test: a tropical volcano island in first person, stylized faceted low poly
// (D-013). Judges the look on phone and desktop before the game is rebuilt around it.
import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import '../nozoom.js';
import { loadAssets } from '../assets.js';
import { Island, VOLCANO } from './island.js';
import { makeFacetGround, Plume, prepareModel } from './facets.js';
import { Fauna } from './fauna.js';
import { Hands, ViewmodelPass, VIEW, VIEW_LAYER } from './hands.js';
import { Gather } from './gather.js';
import { Castaways } from './npc.js';
import { createOcean } from './ocean.js';
import { CoveSky } from './sky.js';
import { Flora } from './flora.js';
import { FirstPerson } from './fps.js';
import { startSound, initSfx, sfx } from './sound.js';

const params = new URLSearchParams(location.search);
const mobile = matchMedia('(pointer: coarse)').matches || params.has('mobile');
const canvas = document.getElementById('view');
const ui = {
  load: document.getElementById('load'), fill: document.getElementById('fill'), text: document.getElementById('loadText'),
  start: document.getElementById('start'), hint: document.getElementById('hint'), fps: document.getElementById('fps'),
  stick: document.getElementById('stick'), knob: document.getElementById('knob'),
};

// The picture goes through the bloom chain, so the canvas's own antialiasing is not used:
// the composer gets a multisampled target instead (sharp facet edges on phones too).
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, mobile ? 2 : 2));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
// Neutral tone mapping keeps the stylized colours saturated (ACES greys them out).
renderer.toneMapping = params.get('tm') === 'aces' ? THREE.ACESFilmicToneMapping : params.get('tm') === 'agx' ? THREE.AgXToneMapping : THREE.NeutralToneMapping;
renderer.toneMappingExposure = params.has('exp') ? +params.get('exp') : 0.45;
renderer.shadowMap.enabled = true;
renderer.info.autoReset = false; // the bloom passes render several times per frame
renderer.shadowMap.type = mobile ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0xb4cbdc, mobile ? 0.0014 : 0.0009);
const camera = new THREE.PerspectiveCamera(mobile ? 72 : 68, innerWidth / innerHeight, 0.08, 20000);
scene.add(camera);

const TIMES = { morgen: [12, 95], middag: [62, 160], eftermiddag: [30, 230], solnedgang: [4, 262] };

async function start() {
  const assets = await loadAssets((p) => { ui.fill.style.width = `${Math.round(p * 85)}%`; }, 'cove');
  ui.text.textContent = 'Bygger øen …';
  await new Promise((r) => setTimeout(r, 30));

  const island = new Island({ cell: mobile ? 3.6 : 2.4 });
  const ground = makeFacetGround();
  scene.add(island.buildMesh(ground));
  const V = VOLCANO;
  const plume = new Plume(scene, { x: V.x, y: V.peak - 12, z: V.z }, { mobile });
  const depth = island.depthTexture();
  const ocean = createOcean({ depth, mobile });
  scene.add(ocean);
  const sky = new CoveSky(scene, renderer, { mobile });
  for (const l of [sky.sun, sky.hemi]) l.layers.enable(VIEW_LAYER); // the arms are lit like the world
  const flora = new Flora(scene, assets, island, { mobile });
  const fauna = new Fauna(scene, assets, island, { mobile });
  const castaways = new Castaways(scene, assets, island, flora.camp);

  const depthAt = (x, z) => -island.heightAt(x, z);
  const fp = new FirstPerson(camera, canvas, { ground: (x, z) => island.heightAt(x, z), blocked: (x, z, r) => flora.blocked(x, z, r), depthAt });
  fp.stick = (s) => {
    ui.stick.hidden = !s;
    if (!s) return;
    ui.stick.style.left = `${s.x0 - 55}px`; ui.stick.style.top = `${s.y0 - 55}px`;
    ui.knob.style.transform = `translate(${s.dx}px, ${s.dy}px)`;
  };
  // Start on the beach by the rowboat, looking up the sand toward the jungle and the volcano.
  const sx = -30;
  fp.place(sx, island.shoreZ(sx) - 7, params.has('yaw') ? +params.get('yaw') : 0.35);
  // The player's arms (hands.js) and the tools they can hold. userData.grip = the handle point.
  const tool = (key, grip, turn = 0) => {
    const m = assets[key].scene.clone(true);
    prepareModel(m);
    m.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.frustumCulled = false; } });
    const g = new THREE.Group();
    m.rotation.y = turn; // the axe head faces +x in its model; turn it so the edge leads
    g.add(m);
    g.userData.grip = grip;
    return g;
  };
  const tools = { machete: tool('props/machete', new THREE.Vector3(-0.004, 0.075, 0)), stone_axe: tool('props/stone_axe', new THREE.Vector3(0, 0.14, 0), Math.PI) };
  const hands = new Hands(camera, assets, { machete: tools.machete });
  initSfx(assets);
  initSfx({ 'sfx/treefall': { url: 'cove/audio/mw-lumberjack/tree_crack_fall.mp3' } });
  const gather = new Gather({ scene, camera, assets, flora, island, hands, mobile, tools });
  gather.ui.onToggle = (open) => { fp.enabled = !open && ui.start.hidden; };
  // Desktop: left click (with the mouse captured) cuts or picks up; E picks up; Tab / I opens
  // the bag; Q switches tool; Esc stops building.
  canvas.addEventListener('mousedown', (e) => { if (e.button === 0 && document.pointerLockElement === canvas) gather.act(); });
  addEventListener('keydown', (e) => {
    if (e.code === 'Tab' || e.code === 'KeyI') { e.preventDefault(); gather.ui.toggle(); if (!gather.ui.open && !mobile) canvas.requestPointerLock?.(); }
    if (!fp.enabled) return;
    if (e.code === 'KeyE') gather.interact();
    if (e.code === 'KeyQ' || e.code === 'Digit1' || e.code === 'Digit2') gather.cycleTool();
    if (e.code === 'Escape' && gather.placing) { gather.placing.ghost.removeFromParent(); gather.placing = null; }
  });

  let time = params.get('t') in TIMES ? params.get('t') : 'eftermiddag';
  const setTime = (name) => {
    time = name;
    sky.setSun(...TIMES[name]);
    for (const b of document.querySelectorAll('[data-time]')) b.classList.toggle('on', b.dataset.time === name);
  };
  setTime(time);
  for (const b of document.querySelectorAll('[data-time]')) b.addEventListener('click', (e) => { e.stopPropagation(); setTime(b.dataset.time); });

  // Bloom makes the lava, sun glints and foam glow a little (the stylized look leans on it).
  const rt = new THREE.WebGLRenderTarget(innerWidth * renderer.getPixelRatio(), innerHeight * renderer.getPixelRatio(), { type: THREE.HalfFloatType, samples: mobile ? 2 : 4 });
  const composer = new EffectComposer(renderer, rt);
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(new ViewmodelPass(hands, scene)); // arms and tool on top (D-019)
  const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight).multiplyScalar(mobile ? 0.35 : 0.5), 0.35, 0.3, 3.0); // only lava and hard glints are bright enough to bloom
  composer.addPass(bloom);
  composer.addPass(new OutputPass());
  const useBloom = !params.has('nobloom');

  addEventListener('resize', () => {
    composer.setSize(innerWidth, innerHeight);
    renderer.setSize(innerWidth, innerHeight);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  });

  // Start screen → pointer lock (desktop) / touch controls; sound needs a user gesture.
  ui.load.hidden = true;
  ui.start.hidden = false;
  const go = () => {
    ui.start.hidden = true;
    ui.hint.hidden = mobile; // the keyboard hint means nothing on a phone
    fp.enabled = true;
    if (!mobile) canvas.requestPointerLock?.();
    startSound('cove/audio');
  };
  ui.start.addEventListener('click', go);
  canvas.addEventListener('click', () => { if (!mobile && fp.enabled) canvas.requestPointerLock?.(); });

  const clock = new THREE.Clock();
  let t = 0, frames = 0, acc = 0, lastStep = 0;
  const loop = () => {
    const dt = Math.min(0.05, clock.getDelta());
    renderer.info.reset();
    t += dt;
    if (fp.enabled) fp.update(dt); else fp.update(0);
    camera.updateMatrixWorld();
    hands.update(dt, { speed: fp.speed, bob: fp.bob });
    gather.update(dt);
    // Footsteps on every other bob peak.
    const step = Math.floor(fp.bob / Math.PI);
    if (step !== lastStep && fp.speed > 0.5) sfx(['step1', 'step2', 'step3'], { vol: 0.12 + 0.06 * Math.min(1, fp.speed / 5) });
    lastStep = step;
    const p = camera.position;
    ocean.userData.update(t, p);
    ground.userData.time.value = t;
    sky.update(t, p);
    flora.update(p.x, p.z, t);
    plume.update(t);
    fauna.update(t, dt, p);
    castaways.update(dt);
    if (useBloom) composer.render(); else { renderer.render(scene, camera); hands.draw(renderer, scene); }
    frames++; acc += dt; window.__cove.frames++;
    if (acc > 1) { window.__cove.fps = Math.round(frames / acc); if (!ui.fps.hidden) ui.fps.textContent = `${window.__cove.fps} fps`; frames = 0; acc = 0; }
    requestAnimationFrame(loop);
  };
  ui.fps.hidden = !params.has('fps');
  window.__cove = { VIEW, fps: 0, frames: 0, scene, camera, renderer, fp, hands, gather, tools, castaways, island, flora, fauna, sky, plume, setTime, go };
  loop();
}

start().catch((err) => {
  console.error(err);
  ui.text.textContent = `Kunne ikke indlæse: ${err?.message ?? err}`;
});
