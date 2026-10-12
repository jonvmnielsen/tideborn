// Stylized low-poly look (D-013): the faceted ground material with glowing lava, the volcano's
// smoke plume, and how generated models are set up (shadows, wind, flat facets).
import * as THREE from 'three';

// Ground: flat per-face vertex colours; the "lava" attribute glows and pulses.
export function makeFacetGround() {
  const time = { value: 0 };
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.93, metalness: 0, flatShading: true });
  mat.name = 'ground-facets';
  mat.onBeforeCompile = (shader) => {
    shader.uniforms.uTime = time;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nattribute float lava;\nvarying float vLava;\nvarying vec2 vLavaP;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLava = lava;\nvLavaP = position.xz;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uTime;\nvarying float vLava;\nvarying vec2 vLavaP;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  // Lava: slow pulses running downhill, hotter in the middle of a run.
  float pulse = 0.75 + 0.25 * sin(uTime * 1.6 - length(vLavaP - vec2(30.0, -215.0)) * 0.12);
  totalEmissiveRadiance += vec3(1.0, 0.36, 0.08) * vLava * vLava * 6.0 * pulse;
}`);
  };
  mat.customProgramCacheKey = () => 'tideborn-ground-facets-v1';
  mat.userData.time = time;
  return mat;
}

// Every generated model: shadows on, and foliage materials marked for the wind patch.
export function prepareModel(scene) {
  scene.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = true;
    o.material.flatShading = true;
    // Flat steel facets mirror the whole sky: keep the blade grey, with a soft sheen.
    if (o.material.name === 'lowpoly_metal') Object.assign(o.material, { metalness: 0.3, roughness: 0.5, envMapIntensity: 0.35 });
    o.material.needsUpdate = true;
  });
}

// The plume: faceted puffs rising out of the crater, drifting downwind and swelling as they
// climb. One instanced mesh; colours darken toward the base where the lava lights them orange.
export class Plume {
  constructor(scene, { x, y, z }, { count = 46, mobile = false } = {}) {
    this.base = new THREE.Vector3(x, y, z);
    this.count = mobile ? Math.round(count * 0.6) : count;
    const geo = new THREE.IcosahedronGeometry(1, 1);
    const mat = new THREE.MeshLambertMaterial({ color: 0xffffff, flatShading: true });
    mat.name = 'smoke';
    this.mesh = new THREE.InstancedMesh(geo, mat, this.count);
    this.mesh.name = 'plume';
    this.mesh.frustumCulled = false;
    this.mesh.castShadow = false;
    this.seeds = Array.from({ length: this.count }, (_, i) => ({ t: i / this.count, a: Math.random() * 6.28, r: Math.random(), s: 0.7 + Math.random() * 0.6 }));
    this.m = new THREE.Matrix4();
    this.q = new THREE.Quaternion();
    this.c = new THREE.Color();
    for (let i = 0; i < this.count; i++) this.mesh.setColorAt(i, this.c.set(0xffffff));
    scene.add(this.mesh);
    this.update(0);
  }

  update(t) {
    const H = 170, wind = new THREE.Vector3(0.55, 0, 0.18);
    const dark = new THREE.Color('#3f3a38'), light = new THREE.Color('#b3aca4'), glow = new THREE.Color('#c0542a');
    for (let i = 0; i < this.count; i++) {
      const s = this.seeds[i];
      const u = (s.t + t * 0.012) % 1; // 0 at the crater → 1 at the top of the column
      const y = u * H;
      const spread = 6 + u * 38;
      const p = this.base.clone()
        .add(new THREE.Vector3(Math.cos(s.a + u * 2) * spread * s.r, y, Math.sin(s.a + u * 2) * spread * s.r))
        .addScaledVector(wind, y * y * 0.006);
      const size = (8 + u * 30) * s.s * Math.min(1, u * 8) * (1 - Math.pow(u, 6));
      this.q.setFromEuler(new THREE.Euler(s.a, s.a * 2 + u, 0));
      this.m.compose(p, this.q, new THREE.Vector3(size, size * 0.8, size));
      this.mesh.setMatrixAt(i, this.m);
      this.c.copy(dark).lerp(light, Math.min(1, u * 1.4)).lerp(glow, Math.max(0, 0.6 - u * 3));
      this.mesh.setColorAt(i, this.c);
    }
    this.mesh.instanceMatrix.needsUpdate = true;
    this.mesh.instanceColor.needsUpdate = true;
  }
}
