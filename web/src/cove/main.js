// Tideborn look test: a tropical cove in first person. Judges the look (sea, light, palms,
// jungle, rocks) on phone and desktop before the game is rebuilt around it.
import * as THREE from 'three';
import '../nozoom.js';
import { loadAssets } from '../assets.js';
import { makeGroundMaterial } from '../world/ground.js';
import { Island } from './island.js';
import { createOcean } from './ocean.js';
import { CoveSky } from './sky.js';
import { Flora } from './flora.js';
import { FirstPerson } from './fps.js';
import { startSound } from './sound.js';

const params = new URLSearchParams(location.search);
const mobile = matchMedia('(pointer: coarse)').matches || params.has('mobile');
const canvas = document.getElementById('view');
const ui = {
  load: document.getElementById('load'), fill: document.getElementById('fill'), text: document.getElementById('loadText'),
  start: document.getElementById('start'), hint: document.getElementById('hint'), fps: document.getElementById('fps'),
  stick: document.getElementById('stick'), knob: document.getElementById('knob'),
};

const renderer = new THREE.WebGLRenderer({ canvas, antialias: !mobile, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(devicePixelRatio, mobile ? 1.3 : 1.75));
renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.56;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = mobile ? THREE.PCFShadowMap : THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0xb4cbdc, mobile ? 0.0024 : 0.0013);
const camera = new THREE.PerspectiveCamera(mobile ? 72 : 68, innerWidth / innerHeight, 0.08, 20000);
scene.add(camera);

const TIMES = { morgen: [12, 95], middag: [62, 160], eftermiddag: [30, 230], solnedgang: [4, 262] };

async function start() {
  const assets = await loadAssets((p) => { ui.fill.style.width = `${Math.round(p * 85)}%`; }, 'cove');
  ui.text.textContent = 'Bygger bugten …';
  await new Promise((r) => setTimeout(r, 30));

  const island = new Island({ cell: mobile ? 3.2 : 1.9 });
  const ground = makeGroundMaterial(assets, renderer, {
    layers: ['ground/sand', 'ground/grass', 'ground/forest', 'ground/rock'],
    tint: [new THREE.Color(1.32, 1.1, 0.78), new THREE.Color(0.55, 0.78, 0.36), new THREE.Color(0.78, 0.82, 0.62), new THREE.Color(0.9, 0.88, 0.84)],
    tile: new THREE.Vector4(6, 4.5, 5.5, 9),
    caustics: true,
  });
  scene.add(island.buildMesh(ground));
  const depth = island.depthTexture();
  const ocean = createOcean({ depth, mobile });
  scene.add(ocean);
  const sky = new CoveSky(scene, renderer, { mobile });
  const flora = new Flora(scene, assets, island, { mobile });

  const depthAt = (x, z) => -island.heightAt(x, z);
  const fp = new FirstPerson(camera, canvas, { ground: (x, z) => island.heightAt(x, z), blocked: (x, z, r) => flora.blocked(x, z, r), depthAt });
  fp.stick = (s) => {
    ui.stick.hidden = !s;
    if (!s) return;
    ui.stick.style.left = `${s.x0 - 55}px`; ui.stick.style.top = `${s.y0 - 55}px`;
    ui.knob.style.transform = `translate(${s.dx}px, ${s.dy}px)`;
  };
  // Start on the beach, looking along the sand toward the wreck and the sea.
  const sx = -20;
  fp.place(sx, island.shoreZ(sx) - 16, 0.5);
  // The machete in hand.
  const machete = assets['props/machete'].scene.clone(true);
  machete.rotation.set(-1.05, 0.35, 0.55);
  machete.traverse((o) => { if (o.isMesh) { o.castShadow = false; o.frustumCulled = false; } });
  fp.hold(machete);

  let time = params.get('t') in TIMES ? params.get('t') : 'eftermiddag';
  const setTime = (name) => {
    time = name;
    sky.setSun(...TIMES[name]);
    for (const b of document.querySelectorAll('[data-time]')) b.classList.toggle('on', b.dataset.time === name);
  };
  setTime(time);
  for (const b of document.querySelectorAll('[data-time]')) b.addEventListener('click', (e) => { e.stopPropagation(); setTime(b.dataset.time); });

  addEventListener('resize', () => {
    renderer.setSize(innerWidth, innerHeight);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  });

  // Start screen → pointer lock (desktop) / touch controls; sound needs a user gesture.
  ui.load.hidden = true;
  ui.start.hidden = false;
  const go = () => {
    ui.start.hidden = true;
    ui.hint.hidden = false;
    fp.enabled = true;
    if (!mobile) canvas.requestPointerLock?.();
    startSound('cove/audio');
  };
  ui.start.addEventListener('click', go);
  canvas.addEventListener('click', () => { if (!mobile && fp.enabled) canvas.requestPointerLock?.(); });

  const clock = new THREE.Clock();
  let t = 0, frames = 0, acc = 0;
  const loop = () => {
    const dt = Math.min(0.05, clock.getDelta());
    t += dt;
    if (fp.enabled) fp.update(dt); else fp.update(0);
    const p = camera.position;
    ocean.userData.update(t, p);
    ground.userData.time.value = t;
    sky.update(t, p);
    flora.update(p.x, p.z, t);
    renderer.render(scene, camera);
    frames++; acc += dt;
    if (acc > 1) { window.__cove.fps = Math.round(frames / acc); if (!ui.fps.hidden) ui.fps.textContent = `${window.__cove.fps} fps`; frames = 0; acc = 0; }
    requestAnimationFrame(loop);
  };
  ui.fps.hidden = !params.has('fps');
  window.__cove = { fps: 0, scene, camera, renderer, fp, island, flora, sky, setTime, go };
  loop();
}

start().catch((err) => {
  console.error(err);
  ui.text.textContent = `Kunne ikke indlæse: ${err?.message ?? err}`;
});
