// Tropical sea: a physically lit (MeshStandardMaterial) water surface with Gerstner waves in the
// vertex shader, colour and transparency from the real water depth (island depth texture),
// shore foam and swash, crest foam, and two scrolling detail-normal layers. Sky reflections and
// sun glints come from three's own lighting (scene.environment + the sun light).
import * as THREE from 'three';

// [dirX, dirZ, wavelength m, steepness]. Swell rolls in toward the beach (−z).
const WAVES = [
  [-0.15, -1.0, 23, 0.22],
  [0.35, -0.94, 11, 0.2],
  [-0.55, -0.83, 6.2, 0.16],
  [0.2, -0.98, 3.1, 0.12],
];

// Tileable detail normals (and a foam-noise channel) from integer-frequency sine waves.
function detailNormalTexture(res = 256) {
  const h = new Float32Array(res * res);
  const rnd = (s) => { let x = Math.sin(s * 127.1) * 43758.5453; return x - Math.floor(x); };
  const waves = Array.from({ length: 24 }, (_, i) => ({
    fx: Math.round((rnd(i + 1) - 0.5) * 16), fy: Math.round((rnd(i + 40) - 0.5) * 16),
    ph: rnd(i + 80) * Math.PI * 2, a: 1 / (1 + i * 0.35),
  })).filter((w) => w.fx || w.fy);
  for (let y = 0; y < res; y++) for (let x = 0; x < res; x++) {
    let v = 0;
    for (const w of waves) v += w.a * Math.sin(((w.fx * x + w.fy * y) / res) * Math.PI * 2 + w.ph);
    h[y * res + x] = v;
  }
  const data = new Uint8Array(res * res * 4);
  let lo = Infinity, hi = -Infinity;
  for (const v of h) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  for (let y = 0; y < res; y++) for (let x = 0; x < res; x++) {
    const at = (i, j) => h[((j + res) % res) * res + ((i + res) % res)];
    const dx = (at(x + 1, y) - at(x - 1, y)) * 0.6, dy = (at(x, y + 1) - at(x, y - 1)) * 0.6;
    const n = new THREE.Vector3(-dx, -dy, 4).normalize();
    const k = (y * res + x) * 4;
    data[k] = (n.x * 0.5 + 0.5) * 255; data[k + 1] = (n.y * 0.5 + 0.5) * 255; data[k + 2] = (n.z * 0.5 + 0.5) * 255;
    data[k + 3] = ((h[y * res + x] - lo) / (hi - lo)) * 255;
  }
  const tex = new THREE.DataTexture(data, res, res, THREE.RGBAFormat);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.magFilter = THREE.LinearFilter;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.generateMipmaps = true;
  tex.needsUpdate = true;
  return tex;
}

export function createOcean({ depth, mobile = false }) {
  const uniforms = {
    uTime: { value: 0 },
    tDepth: { value: depth.tex },
    uDepthB: { value: new THREE.Vector3(depth.min, depth.min, depth.size) },
    uMaxDepth: { value: depth.maxDepth },
    uLandMax: { value: depth.landMax ?? 0 },
    tDetail: { value: detailNormalTexture() },
    uShallow: { value: new THREE.Color('#2fd3c6') },
    uMid: { value: new THREE.Color('#0e9db8') },
    uDeep: { value: new THREE.Color('#0b4a72') },
    uFoam: { value: new THREE.Color('#f4f8f6') },
    uCam: { value: new THREE.Vector3() },
  };
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.05, metalness: 0, transparent: true, envMapIntensity: 0.75 });
  mat.name = 'ocean';
  const waveCode = WAVES.map(([dx, dz, L, q], i) => {
    const d = new THREE.Vector2(dx, dz).normalize();
    const k = (2 * Math.PI) / L, c = Math.sqrt(9.8 / k), a = q / k;
    return `  { vec2 D = vec2(${d.x.toFixed(4)}, ${d.y.toFixed(4)}); float f = ${k.toFixed(5)} * dot(D, p0) - ${(c * k).toFixed(5)} * uTime + ${(i * 1.7).toFixed(2)};
    float A = ${a.toFixed(4)} * amp; float Q = ${q.toFixed(3)};
    disp += vec3(Q * A * D.x * cos(f), A * sin(f), Q * A * D.y * cos(f));
    nrm += vec3(-D.x * ${k.toFixed(5)} * A * cos(f), -Q * ${k.toFixed(5)} * A * sin(f), -D.y * ${k.toFixed(5)} * A * cos(f));
    crest += A * sin(f); }`;
  }).join('\n');

  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    const common = `#include <common>
uniform float uTime, uMaxDepth, uLandMax;
uniform sampler2D tDepth, tDetail;
uniform vec3 uDepthB, uCam, uShallow, uMid, uDeep, uFoam;
varying vec3 vWP;
varying float vDepth, vCrest;
float seaDepth(vec2 xz) {
  vec2 uv = (xz - uDepthB.xy) / uDepthB.z;
  if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return uMaxDepth;
  return texture2D(tDepth, uv).r * (uMaxDepth + uLandMax) - uLandMax;
}`;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', common)
      .replace('#include <beginnormal_vertex>', `
vec3 wp0 = (modelMatrix * vec4(position, 1.0)).xyz;
vec2 p0 = wp0.xz;
float depth0 = seaDepth(p0);
// Waves shrink in the shallows and far from the camera (no detail to see there anyway).
float amp = smoothstep(0.0, 3.0, max(depth0, 0.0) + 0.3) * (1.0 - smoothstep(140.0, 330.0, distance(p0, uCam.xz)));
vec3 disp = vec3(0.0);
vec3 nrm = vec3(0.0, 1.0, 0.0);
float crest = 0.0;
${waveCode}
// Swash: the water's edge runs up the sand and back.
disp.y += 0.13 * sin(uTime * 0.55) * (1.0 - smoothstep(0.0, 1.6, max(depth0, 0.0))) + 0.04 * sin(uTime * 1.3 + p0.x * 0.05);
vec3 objectNormal = normalize(nrm);
#ifdef USE_TANGENT
vec3 objectTangent = vec3(1.0, 0.0, 0.0);
#endif`)
      .replace('#include <begin_vertex>', `vec3 transformed = position + disp;
vWP = wp0 + disp;
vDepth = depth0;
vCrest = crest;`);

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', common)
      .replace('#include <map_fragment>', `
float wd = seaDepth(vWP.xz) + vWP.y;
float camDist = distance(vWP.xz, uCam.xz);
vec4 dA = texture2D(tDetail, vWP.xz * 0.045 + uTime * vec2(0.010, 0.016));
vec4 dB = texture2D(tDetail, vWP.xz * 0.13 - uTime * vec2(0.021, -0.008));
float fn = dA.a * 0.6 + dB.a * 0.4;
// Colour by depth: clear turquoise over sand, blue over the drop-off.
vec3 wcol = mix(uShallow, uMid, smoothstep(0.4, 4.5, wd));
wcol = mix(wcol, uDeep, smoothstep(5.0, 16.0, wd));
// Foam: a lacy line at the water's edge, and on steep crests.
float shore = (1.0 - smoothstep(0.02, 0.1 + 0.16 * fn, wd)) * smoothstep(-0.02, 0.03, wd);
float crestFoam = smoothstep(0.42, 0.7, vCrest + fn * 0.25) * smoothstep(1.5, 4.0, wd) * 0.6;
float foam = clamp(max(shore * smoothstep(0.25, 0.65, fn + shore * 0.4), crestFoam * smoothstep(0.55, 0.8, fn)), 0.0, 1.0);
diffuseColor.rgb = mix(wcol, uFoam, foam);
diffuseColor.a = mix(mix(0.55, 1.0, smoothstep(0.0, 4.5, wd)), 0.9, foam) * smoothstep(-0.01, 0.06, wd);
diffuseColor.a = max(diffuseColor.a, smoothstep(40.0, 160.0, camDist));`)
      .replace('#include <roughnessmap_fragment>', `float roughnessFactor = mix(0.04 + 0.05 * smoothstep(60.0, 400.0, camDist), 0.7, foam);`)
      .replace('#include <normal_fragment_maps>', `
{
  vec3 a = dA.xyz * 2.0 - 1.0, b = dB.xyz * 2.0 - 1.0;
  vec3 nt = normalize(vec3(a.xy + b.xy, a.z * b.z));
  nt.xy *= mix(0.55, 0.15, smoothstep(30.0, 300.0, camDist));
  nt = normalize(nt);
  vec3 gN = normalize((vec4(normal, 0.0) * viewMatrix).xyz); // view → world
  vec3 T = normalize(vec3(1.0, 0.0, 0.0) - gN * gN.x);
  vec3 B = cross(T, gN);
  vec3 wn = normalize(T * nt.x + B * nt.y + gN * nt.z);
  normal = normalize((viewMatrix * vec4(wn, 0.0)).xyz);
}`)
      .replace('vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;', `
// In the shallows you look through the water at the sand: keep sun glints, tone down the
// mirrored sky so the near water does not turn into a white sheet at low view angles.
vec3 outgoingLight = totalDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular * mix(0.3, 1.0, smoothstep(0.4, 4.0, wd)) + totalEmissiveRadiance;`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
// Light scattered inside the water: turquoise glow in the shallows and in wave crests.
totalEmissiveRadiance += uShallow * (0.05 + 0.1 * smoothstep(0.2, 0.6, vCrest)) * (1.0 - foam) * (1.0 - smoothstep(2.0, 10.0, wd));`);
  };
  mat.customProgramCacheKey = () => 'tideborn-ocean-v3';

  // Near grid with detail for waves; a coarse frame around it out to the horizon.
  const group = new THREE.Group();
  group.name = 'ocean';
  const NEAR = 760, seg = mobile ? 190 : 380;
  const near = new THREE.Mesh(new THREE.PlaneGeometry(NEAR, NEAR, seg, seg).rotateX(-Math.PI / 2), mat);
  near.position.set(0, 0, 120);
  near.receiveShadow = true;
  near.frustumCulled = false;
  group.add(near);
  const FAR = 16000, half = NEAR / 2;
  for (const [w, d, x, z] of [
    [FAR, (FAR - NEAR) / 2, 0, 120 + half + (FAR - NEAR) / 4],
    [FAR, (FAR - NEAR) / 2, 0, 120 - half - (FAR - NEAR) / 4],
    [(FAR - NEAR) / 2, NEAR, -half - (FAR - NEAR) / 4, 120],
    [(FAR - NEAR) / 2, NEAR, half + (FAR - NEAR) / 4, 120],
  ]) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d, 8, 8).rotateX(-Math.PI / 2), mat);
    m.position.set(x, 0, z);
    m.frustumCulled = false;
    group.add(m);
  }
  group.renderOrder = 1;
  group.userData.update = (t, camPos) => {
    uniforms.uTime.value = t;
    uniforms.uCam.value.copy(camPos);
  };
  return group;
}
