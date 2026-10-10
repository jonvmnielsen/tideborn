// Ground material for the island: four Poly Haven texture sets (sand, grass, forest floor,
// rock) blended per vertex by the "splat" weights the terrain computes from height, slope
// and biome. Textures are projected from above in world space (no UVs needed); rock also
// projects from the side on cliffs so it doesn't smear. Each layer's own brightness acts as
// a height map so the layers meet in irregular, natural edges instead of soft fades.
import * as THREE from 'three';

export const GROUND_LAYERS = ['ground/sand', 'ground/grass', 'ground/forest', 'ground/rock'];
const TILE = new THREE.Vector4(5, 4.5, 5.5, 8);        // metres per texture repeat
const ROUGH = new THREE.Vector4(0.92, 0.97, 0.95, 0.86);
// Colour grading per layer so the scans sit together (the grass scan is a dry, pale field).
const TINT = [new THREE.Color(0.92, 0.88, 0.8), new THREE.Color(0.48, 0.64, 0.3), new THREE.Color(0.85, 0.85, 0.78), new THREE.Color(0.92, 0.9, 0.86)];

export function makeGroundMaterial(assets, renderer) {
  const aniso = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const tex = GROUND_LAYERS.map((k) => {
    const set = assets[k];
    for (const t of Object.values(set)) t.anisotropy = aniso;
    return set;
  });
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  mat.name = 'ground';
  mat.onBeforeCompile = (shader) => {
    tex.forEach((set, i) => {
      shader.uniforms[`tDiff${i}`] = { value: set.diff };
      shader.uniforms[`tNor${i}`] = { value: set.nor };
    });
    shader.uniforms.uTile = { value: TILE };
    shader.uniforms.uRough = { value: ROUGH };
    TINT.forEach((c, i) => { shader.uniforms[`uTint${i}`] = { value: c }; });

    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
attribute vec4 splat;
varying vec4 vSplat;
varying vec3 vWPos;
varying vec3 vWNrm;`)
      .replace('#include <project_vertex>', `#include <project_vertex>
vSplat = splat;
vWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;
vWNrm = normalize(mat3(modelMatrix) * objectNormal);`);

    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
uniform sampler2D tDiff0, tDiff1, tDiff2, tDiff3, tNor0, tNor1, tNor2, tNor3;
uniform vec4 uTile, uRough;
uniform vec3 uTint0, uTint1, uTint2, uTint3;
varying vec4 vSplat;
varying vec3 vWPos;
varying vec3 vWNrm;
float gLum(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }
// Second, larger and offset sample hides the repeat of a tiling texture.
vec3 gTwoScale(sampler2D t, vec2 p, float tile) {
  vec3 a = texture2D(t, p / tile).rgb;
  vec3 b = texture2D(t, p / (tile * 4.3) + vec2(0.37, 0.71)).rgb;
  return mix(a, b, 0.42) * (0.82 + 0.36 * gLum(b));
}`)
      .replace('#include <map_fragment>', `
vec2 gUv = vWPos.xz;
vec3 gN = normalize(vWNrm);
vec2 gUvSide = abs(gN.x) > abs(gN.z) ? vWPos.zy : vWPos.xy;
float gSteep = smoothstep(0.45, 0.8, 1.0 - abs(gN.y));
vec3 gC0 = gTwoScale(tDiff0, gUv, uTile.x);
vec3 gC1 = gTwoScale(tDiff1, gUv, uTile.y);
vec3 gC2 = gTwoScale(tDiff2, gUv, uTile.z);
vec3 gC3 = mix(gTwoScale(tDiff3, gUv, uTile.w), texture2D(tDiff3, gUvSide / uTile.w).rgb, gSteep);
vec4 gW = vSplat * (vec4(gLum(gC0), gLum(gC1), gLum(gC2), gLum(gC3)) * 0.9 + 0.35);
gW = gW * gW * gW * gW;
gW /= dot(gW, vec4(1.0)) + 1e-6;
vec3 gCol = gC0 * uTint0 * gW.x + gC1 * uTint1 * gW.y + gC2 * uTint2 * gW.z + gC3 * uTint3 * gW.w;
// Wet sand darkens towards the waterline.
gCol *= mix(0.6, 1.0, smoothstep(-0.4, 0.9, vWPos.y));
diffuseColor.rgb *= gCol;`)
      .replace('#include <roughnessmap_fragment>', `float roughnessFactor = dot(gW, uRough) * mix(0.7, 1.0, smoothstep(-0.3, 0.6, vWPos.y));`)
      .replace('#include <normal_fragment_maps>', `
{
  vec3 n0 = texture2D(tNor0, gUv / uTile.x).xyz * 2.0 - 1.0;
  vec3 n1 = texture2D(tNor1, gUv / uTile.y).xyz * 2.0 - 1.0;
  vec3 n2 = texture2D(tNor2, gUv / uTile.z).xyz * 2.0 - 1.0;
  vec3 n3 = texture2D(tNor3, mix(gUv, gUvSide, step(0.5, gSteep)) / uTile.w).xyz * 2.0 - 1.0;
  vec3 nt = normalize(n0 * gW.x + n1 * gW.y + n2 * gW.z + n3 * gW.w);
  vec3 T = normalize(vec3(1.0, 0.0, 0.0) - gN * gN.x);
  vec3 B = cross(T, gN);
  vec3 wn = normalize(T * nt.x + B * nt.y + gN * nt.z);
  normal = normalize((viewMatrix * vec4(wn, 0.0)).xyz);
}`);
  };
  mat.customProgramCacheKey = () => 'tideborn-ground-v2';
  return mat;
}
