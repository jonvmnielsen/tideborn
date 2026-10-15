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
  m.uniforms.uNight = { value: 0 };
  m.fragmentShader = 'uniform float uNight;\n' + m.fragmentShader.replace('gl_FragColor = vec4( retColor, 1.0 );', `
  float skyLum = dot(retColor, vec3(0.2126, 0.7152, 0.0722));
  vec3 graded = mix(vec3(skyLum), retColor, 1.9);
  float up = clamp(normalize(vWorldPosition - cameraPosition).y, 0.0, 1.0);
  graded *= mix(vec3(1.0), vec3(0.72, 0.86, 1.08), smoothstep(0.02, 0.6, up));
  // Keep the horizon a clear pale blue instead of a white glare band.
  graded *= mix(vec3(0.8, 0.9, 1.02), vec3(1.0), smoothstep(0.0, 0.18, up));
  // Night: a deep blue dome, a little lighter toward the horizon.
  vec3 nightCol = mix(vec3(0.018, 0.03, 0.06), vec3(0.006, 0.01, 0.026), smoothstep(0.0, 0.5, up));
  graded = mix(graded, nightCol, uNight);
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
    u.turbidity.value = 1.3;
    u.rayleigh.value = 3.0;
    u.mieCoefficient.value = 0.0015;
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
    const sm = mobile ? 2048 : 4096;
    this.sun.shadow.mapSize.set(sm, sm);
    const sb = mobile ? 30 : 45; // smaller box on phones: sharper shadows from the smaller map
    Object.assign(this.sun.shadow.camera, { left: -sb, right: sb, top: sb, bottom: -sb, near: 1, far: 260 });
    this.sun.shadow.bias = -0.0004;
    this.sun.shadow.normalBias = 0.04;
    scene.add(this.sun, this.sun.target);
    // Warm bounce from the sand below, cool sky above: keeps the stylized colours from going
    // olive under the blue sky light alone.
    this.hemi = new THREE.HemisphereLight(0xbcd6ff, 0xd8a25a, 0.6);
    scene.add(this.hemi);
    this.exposure = renderer.toneMappingExposure;

    // Stars: fade in as the sun goes down.
    const n = mobile ? 900 : 1600, pos = new Float32Array(n * 3);
    let seed = 7; const rnd = () => ((seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0) / 4294967296);
    for (let i = 0; i < n; i++) {
      const y = 0.04 + rnd() * 0.96, a = rnd() * Math.PI * 2, r = Math.sqrt(1 - y * y);
      pos.set([Math.cos(a) * r * 9000, y * 9000, Math.sin(a) * r * 9000], i * 3);
    }
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    this.stars = new THREE.Points(sg, new THREE.PointsMaterial({ color: 0xdfe8ff, size: mobile ? 1.6 : 1.3, sizeAttenuation: false, transparent: true, opacity: 0, depthWrite: false, fog: false }));
    this.stars.renderOrder = -2;
    this.stars.visible = false;
    scene.add(this.stars);
    this.night = 0;

    this.sunDir = new THREE.Vector3();
    this.lightDir = new THREE.Vector3();
    this.pmrem = new THREE.PMREMGenerator(renderer);
    this.envScene = new THREE.Scene();
    this.envSky = new Sky();
    this.envSky.scale.setScalar(1000);
    gradeSky(this.envSky);
    this.envScene.add(this.envSky);
    this.envRT = null;
  }

  // elevation/azimuth in degrees. Recomputes the sky light (a few ms; call on change only).
  // Below the horizon it becomes night: a cool moonlight from the other side of the sky, a dark
  // blue dome with stars, and fires and lava become the bright things.
  setSun(elevation, azimuth) {
    const S = THREE.MathUtils.smoothstep;
    const night = S(-elevation, -3, 12); // 0 by day, 1 once the sun is 12° under
    this.night = night;
    const phi = THREE.MathUtils.degToRad(90 - elevation), theta = THREE.MathUtils.degToRad(azimuth);
    this.sunDir.setFromSphericalCoords(1, phi, theta);
    for (const s of [this.sky, this.envSky]) {
      s.material.uniforms.sunPosition.value.copy(this.sunDir);
      s.material.uniforms.uNight.value = night;
      for (const k of ['turbidity', 'rayleigh', 'mieCoefficient', 'mieDirectionalG']) s.material.uniforms[k].value = this.sky.material.uniforms[k].value;
    }
    const low = S(elevation, 2, 25);
    const sunCol = new THREE.Color().setRGB(1, 0.62 + 0.33 * low, 0.38 + 0.52 * low);
    const moonCol = new THREE.Color().setRGB(0.55, 0.68, 1.0);
    // The light comes from the sun until it sets, then from the moon (high, opposite side).
    const moonDir = new THREE.Vector3().setFromSphericalCoords(1, THREE.MathUtils.degToRad(50), theta + Math.PI);
    const fromMoon = elevation < -1;
    this.lightDir.copy(fromMoon ? moonDir : this.sunDir);
    this.sun.color.copy(fromMoon ? moonCol : sunCol);
    this.sun.intensity = fromMoon ? 0.55 * S(-elevation, 1, 8) : 1.4 + 3.8 * S(elevation, -2, 30);
    const cu = this.clouds.material.uniforms;
    cu.uSunDir.value.copy(this.sunDir);
    cu.uSunCol.value.copy(sunCol).multiplyScalar(0.95 + 0.1 * low).lerp(new THREE.Color(0.1, 0.12, 0.18), night);
    cu.uSkyCol.value.setRGB(0.55 + 0.25 * low, 0.62 + 0.18 * low, 0.75).multiplyScalar(1 - 0.93 * night);
    if (this.envRT) this.envRT.dispose();
    this.envRT = this.pmrem.fromScene(this.envScene, 0, 0.1, 1000);
    this.scene.environment = this.envRT.texture;
    this.scene.environmentIntensity = (0.32 + 0.18 * low) * (1 - night) + 1.6 * night;
    this.hemi.intensity = (0.5 + 0.5 * low) * (1 - night) + 0.34 * night;
    this.hemi.color.setRGB(0.55 + 0.2 * low, 0.65 + 0.2 * low, 0.85 + 0.15 * low).lerp(new THREE.Color(0.35, 0.45, 0.8), night);
    this.hemi.groundColor.set(0xd8a25a).lerp(new THREE.Color(0.12, 0.12, 0.16), night);
    // Low sun: open the exposure up (like the eye adapting) so dawn and dusk stay readable.
    this.renderer.toneMappingExposure = this.exposure * ((1 + 0.9 * (1 - low)) * (1 - night) + 1.6 * night);
    if (this.scene.fog) this.scene.fog.color.setRGB(0.6 + 0.25 * (1 - low), 0.72 - 0.06 * (1 - low), 0.86 - 0.2 * (1 - low)).lerp(new THREE.Color(0.03, 0.045, 0.08), night);
    this.stars.visible = night > 0.02;
    this.stars.material.opacity = night;
  }

  update(t, focus) {
    this.clouds.material.uniforms.uTime.value = t;
    this.clouds.position.copy(focus);
    this.sky.position.copy(focus);
    this.stars.position.copy(focus);
    this.sun.position.copy(focus).addScaledVector(this.lightDir, 120);
    this.sun.target.position.copy(focus);
  }
}
