// Sky for the cove: three's physical sky (Preetham), a drifting cumulus layer, the sun light,
// and image-based light rendered from that same sky so everything is lit consistently.
import * as THREE from 'three';
import { Sky } from 'three/addons/objects/Sky.js';

const CLOUD_FRAG = `
uniform float uTime, uCover;
uniform vec3 uSunDir, uSunCol, uSkyCol;
varying vec3 vDir;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { float v = 0.0, a = 0.5; for (int i = 0; i < 6; i++) { v += a * n(p); p = p * 2.03 + 11.7; a *= 0.5; } return v; }
void main() {
  vec3 d = normalize(vDir);
  if (d.y < 0.005) discard;
  // Project onto a cloud deck ~1.2 km up.
  vec2 p = d.xz / d.y * 1.2 + vec2(uTime * 0.004, uTime * 0.0015);
  float c = fbm(p * 1.6);
  float dens = smoothstep(uCover, uCover + 0.14, c);
  // Puffy tops lit by the sun, darker grey bellies.
  float shade = clamp(fbm(p * 1.6 + uSunDir.xz * 0.06) - c + 0.55, 0.0, 1.0);
  vec3 col = mix(uSkyCol * 0.75 + vec3(0.12), uSunCol, shade);
  float horizon = smoothstep(0.01, 0.16, d.y);
  gl_FragColor = vec4(col, dens * horizon * 0.95);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

// The physical sky comes out washed-out under ACES at game exposure; grade it toward a clear
// tropical blue (more saturation, deeper zenith) before tone mapping.
function gradeSky(sky) {
  const m = sky.material;
  m.fragmentShader = m.fragmentShader.replace('gl_FragColor = vec4( retColor, 1.0 );', `
  float skyLum = dot(retColor, vec3(0.2126, 0.7152, 0.0722));
  vec3 graded = mix(vec3(skyLum), retColor, 1.9);
  float up = clamp(normalize(vWorldPosition - cameraPosition).y, 0.0, 1.0);
  graded *= mix(vec3(1.0), vec3(0.72, 0.86, 1.08), smoothstep(0.02, 0.6, up));
  gl_FragColor = vec4(max(graded, 0.0), 1.0);`);
  m.needsUpdate = true;
}

export class CoveSky {
  constructor(scene, renderer, { mobile = false } = {}) {
    this.scene = scene;
    this.renderer = renderer;
    this.sky = new Sky();
    this.sky.scale.setScalar(20000);
    gradeSky(this.sky);
    scene.add(this.sky);
    const u = this.sky.material.uniforms;
    u.turbidity.value = 1.6;
    u.rayleigh.value = 3.0;
    u.mieCoefficient.value = 0.0025;
    u.mieDirectionalG.value = 0.82;

    this.clouds = new THREE.Mesh(
      new THREE.SphereGeometry(15000, 32, 16),
      new THREE.ShaderMaterial({
        uniforms: { uTime: { value: 0 }, uCover: { value: 0.66 }, uSunDir: { value: new THREE.Vector3() }, uSunCol: { value: new THREE.Color() }, uSkyCol: { value: new THREE.Color() } },
        vertexShader: 'varying vec3 vDir; void main() { vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
        fragmentShader: CLOUD_FRAG,
        side: THREE.BackSide, transparent: true, depthWrite: false, fog: false,
      }),
    );
    this.clouds.renderOrder = -1;
    scene.add(this.clouds);

    this.sun = new THREE.DirectionalLight(0xffffff, 3);
    this.sun.castShadow = true;
    const sm = mobile ? 1024 : 2048;
    this.sun.shadow.mapSize.set(sm, sm);
    Object.assign(this.sun.shadow.camera, { left: -45, right: 45, top: 45, bottom: -45, near: 1, far: 260 });
    this.sun.shadow.bias = -0.0004;
    this.sun.shadow.normalBias = 0.04;
    scene.add(this.sun, this.sun.target);

    this.sunDir = new THREE.Vector3();
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.envScene = new THREE.Scene();
    this.envSky = new Sky();
    this.envSky.scale.setScalar(1000);
    gradeSky(this.envSky);
    this.envScene.add(this.envSky);
    this.envRT = null;
  }

  // elevation/azimuth in degrees. Recomputes the sky light (a few ms; call on change only).
  setSun(elevation, azimuth) {
    const phi = THREE.MathUtils.degToRad(90 - elevation), theta = THREE.MathUtils.degToRad(azimuth);
    this.sunDir.setFromSphericalCoords(1, phi, theta);
    for (const s of [this.sky, this.envSky]) {
      s.material.uniforms.sunPosition.value.copy(this.sunDir);
      for (const k of ['turbidity', 'rayleigh', 'mieCoefficient', 'mieDirectionalG']) s.material.uniforms[k].value = this.sky.material.uniforms[k].value;
    }
    const low = THREE.MathUtils.smoothstep(elevation, 2, 25);
    const sunCol = new THREE.Color().setRGB(1, 0.62 + 0.33 * low, 0.38 + 0.52 * low);
    this.sun.color.copy(sunCol);
    this.sun.intensity = 0.6 + 4.6 * THREE.MathUtils.smoothstep(elevation, -2, 30);
    const cu = this.clouds.material.uniforms;
    cu.uSunDir.value.copy(this.sunDir);
    cu.uSunCol.value.copy(sunCol).multiplyScalar(0.95 + 0.1 * low);
    cu.uSkyCol.value.setRGB(0.55 + 0.25 * low, 0.62 + 0.18 * low, 0.75);
    if (this.envRT) this.envRT.dispose();
    this.envRT = this.pmrem.fromScene(this.envScene, 0, 0.1, 1000);
    this.scene.environment = this.envRT.texture;
    this.scene.environmentIntensity = 0.55 + 0.2 * low;
    if (this.scene.fog) this.scene.fog.color.setRGB(0.6 + 0.25 * (1 - low), 0.72 - 0.06 * (1 - low), 0.86 - 0.2 * (1 - low));
  }

  update(t, focus) {
    this.clouds.material.uniforms.uTime.value = t;
    this.clouds.position.copy(focus);
    this.sky.position.copy(focus);
    this.sun.position.copy(focus).addScaledVector(this.sunDir, 120);
    this.sun.target.position.copy(focus);
  }
}
