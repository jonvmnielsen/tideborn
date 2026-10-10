// Stylized ocean: shallow/deep tint from a distance-to-land field, rolling shore foam, sun glint.
import * as THREE from 'three';

const vertex = /* glsl */ `
  #include <fog_pars_vertex>
  varying vec3 vWorld;
  void main() {
    vec4 world = modelMatrix * vec4(position, 1.0);
    vWorld = world.xyz;
    vec4 mvPosition = viewMatrix * world;
    gl_Position = projectionMatrix * mvPosition;
    #include <fog_vertex>
  }
`;

const fragment = /* glsl */ `
  #include <common>
  #include <fog_pars_fragment>
  uniform float uTime;
  uniform sampler2D uDist;
  uniform vec4 uBounds;
  uniform float uMaxD;
  uniform vec3 uDeep;
  uniform vec3 uShallow;
  uniform vec3 uFoam;
  uniform vec3 uSunDir;
  uniform float uLight;
  varying vec3 vWorld;

  float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
  float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
  }

  void main() {
    vec2 uv = (vWorld.xz - uBounds.xy) / uBounds.zw;
    float inside = step(0.0, uv.x) * step(uv.x, 1.0) * step(0.0, uv.y) * step(uv.y, 1.0);
    float d = mix(1.0, texture2D(uDist, clamp(uv, 0.0, 1.0)).r, inside) * uMaxD;

    float n = vnoise(vWorld.xz * 0.35 + vec2(uTime * 0.12, -uTime * 0.08));
    float n2 = vnoise(vWorld.xz * 0.9 - vec2(uTime * 0.2, uTime * 0.15));

    float shallowT = 1.0 - smoothstep(0.0, 12.0, d + (n - 0.5) * 2.0);
    vec3 col = mix(uDeep, uShallow, shallowT * shallowT);

    float rip = (n - 0.5) * 0.06 + (n2 - 0.5) * 0.04;
    col += rip;

    // Foam hugging the shore, breathing in and out.
    float breathe = 0.9 + 0.35 * sin(uTime * 1.1 + vWorld.x * 0.08 + vWorld.z * 0.05);
    float band = 1.0 - smoothstep(0.1, breathe * 0.75, d + (n2 - 0.5) * 0.4);
    // Thin wave lines rolling toward the beach and fading out.
    float phase = d * 1.15 + uTime * 1.4 + n * 1.5;
    float wave = smoothstep(0.92, 0.99, sin(phase)) * (1.0 - smoothstep(1.2, 5.5, d)) * smoothstep(0.4, 0.9, d);
    float foam = clamp(band + wave * 0.65, 0.0, 1.0);
    col = mix(col, uFoam, foam * 0.9);
    col *= uLight;

    // Sun glint on the open water.
    vec3 V = normalize(cameraPosition - vWorld);
    vec3 N = normalize(vec3((n - 0.5) * 0.25, 1.0, (n2 - 0.5) * 0.25));
    vec3 H = normalize(V + uSunDir);
    float spec = pow(max(dot(N, H), 0.0), 140.0) * 0.55 * (1.0 - foam) * smoothstep(-0.05, 0.2, uSunDir.y);
    col += vec3(spec);

    gl_FragColor = vec4(col, 1.0);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
    #include <fog_fragment>
  }
`;

export function createOcean({ y, distTexture, bounds, maxDist, sunDir }) {
  const material = new THREE.ShaderMaterial({
    vertexShader: vertex,
    fragmentShader: fragment,
    fog: true,
    uniforms: THREE.UniformsUtils.merge([
      THREE.UniformsLib.fog,
      {
        uTime: { value: 0 },
        uDist: { value: null },
        uBounds: { value: new THREE.Vector4() },
        uMaxD: { value: maxDist },
        uDeep: { value: new THREE.Color('#1b4a5c') },
        uShallow: { value: new THREE.Color('#4f8f88') },
        uFoam: { value: new THREE.Color('#f4fbff') },
        uSunDir: { value: sunDir.clone().normalize() },
        uLight: { value: 1 },
      },
    ]),
  });
  material.uniforms.uDist.value = distTexture;
  material.uniforms.uBounds.value.set(bounds.minX, bounds.minZ, bounds.size, bounds.size);

  const geo = new THREE.PlaneGeometry(2600, 2600, 1, 1);
  geo.rotateX(-Math.PI / 2);
  const mesh = new THREE.Mesh(geo, material);
  mesh.position.y = y;
  mesh.receiveShadow = false;
  mesh.name = 'ocean';
  mesh.update = (t, light = 1, sun) => {
    material.uniforms.uTime.value = t;
    material.uniforms.uLight.value = light;
    if (sun) material.uniforms.uSunDir.value.copy(sun);
  };
  return mesh;
}

export function createSky(top = '#62b3ea', horizon = '#eaf3f0') {
  const material = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    uniforms: {
      uTop: { value: new THREE.Color(top) },
      uHorizon: { value: new THREE.Color(horizon) },
    },
    vertexShader: /* glsl */ `
      varying vec3 vDir;
      void main() {
        vDir = normalize(position);
        vec4 p = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_Position = p.xyww;
      }
    `,
    fragmentShader: /* glsl */ `
      uniform vec3 uTop;
      uniform vec3 uHorizon;
      varying vec3 vDir;
      void main() {
        float t = smoothstep(-0.05, 0.55, vDir.y);
        gl_FragColor = vec4(mix(uHorizon, uTop, t), 1.0);
        #include <colorspace_fragment>
      }
    `,
  });
  const sky = new THREE.Mesh(new THREE.SphereGeometry(900, 24, 12), material);
  sky.renderOrder = -1;
  sky.frustumCulled = false;
  sky.name = 'sky';
  return sky;
}
