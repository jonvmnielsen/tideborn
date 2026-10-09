// 2D collision on the ground plane: circles (trees, rocks) and oriented boxes (walls),
// bucketed in a spatial grid. Also stores walkable surfaces (floors, stairs) with heights.
const CELL = 8;
export const STEP = 1.05; // how high the player can step up (onto a foundation, a stair)

export class SpatialGrid {
  constructor() {
    this.cells = new Map();
  }
  keysFor(minX, minZ, maxX, maxZ) {
    const out = [];
    for (let i = Math.floor(minX / CELL); i <= Math.floor(maxX / CELL); i++) {
      for (let j = Math.floor(minZ / CELL); j <= Math.floor(maxZ / CELL); j++) out.push(`${i},${j}`);
    }
    return out;
  }
  insert(item, minX, minZ, maxX, maxZ) {
    item._keys = this.keysFor(minX, minZ, maxX, maxZ);
    for (const k of item._keys) {
      let c = this.cells.get(k);
      if (!c) this.cells.set(k, (c = new Set()));
      c.add(item);
    }
  }
  remove(item) {
    for (const k of item._keys ?? []) this.cells.get(k)?.delete(item);
    item._keys = null;
  }
  query(minX, minZ, maxX, maxZ, out = new Set()) {
    for (const k of this.keysFor(minX, minZ, maxX, maxZ)) {
      const c = this.cells.get(k);
      if (c) for (const it of c) out.add(it);
    }
    return out;
  }
}

// Shapes: { kind: 'circle', x, z, r } | { kind: 'box', x, z, hw, hd, rot, top?, bottom? }
export class Colliders {
  constructor() {
    this.grid = new SpatialGrid();
  }
  addCircle(x, z, r, owner) {
    const s = { kind: 'circle', x, z, r, owner };
    this.grid.insert(s, x - r, z - r, x + r, z + r);
    return s;
  }
  addBox(x, z, hw, hd, rot, owner, extra = {}) {
    const s = { kind: 'box', x, z, hw, hd, rot, c: Math.cos(rot), s: Math.sin(rot), owner, ...extra };
    const R = Math.hypot(hw, hd);
    this.grid.insert(s, x - R, z - R, x + R, z + R);
    return s;
  }
  remove(s) {
    if (s) this.grid.remove(s);
  }

  // Penetration of a circle (x, z, r) into a shape: returns { nx, nz, depth } or null.
  static hit(s, x, z, r) {
    if (s.kind === 'circle') {
      const dx = x - s.x, dz = z - s.z, rr = r + s.r, d2 = dx * dx + dz * dz;
      if (d2 >= rr * rr) return null;
      const d = Math.sqrt(d2) || 1e-4;
      return { nx: dx / d, nz: dz / d, depth: rr - d };
    }
    // Box: work in box-local space.
    const dx = x - s.x, dz = z - s.z;
    const lx = dx * s.c - dz * s.s, lz = dx * s.s + dz * s.c;
    const cx = Math.max(-s.hw, Math.min(s.hw, lx)), cz = Math.max(-s.hd, Math.min(s.hd, lz));
    let ox = lx - cx, oz = lz - cz;
    let d = Math.hypot(ox, oz);
    if (d >= r) return null;
    if (d < 1e-5) {
      // Center inside the box: push out along the shallowest axis.
      const px = s.hw - Math.abs(lx), pz = s.hd - Math.abs(lz);
      if (px < pz) { ox = Math.sign(lx) || 1; oz = 0; d = 0; return worldNormal(s, ox, oz, px + r); }
      ox = 0; oz = Math.sign(lz) || 1;
      return worldNormal(s, ox, oz, pz + r);
    }
    return worldNormal(s, ox / d, oz / d, r - d);
  }

  near(x, z, r) {
    return this.grid.query(x - r - 1, z - r - 1, x + r + 1, z + r + 1);
  }

  blocked(x, z, r, y = null, ignore = null) {
    for (const s of this.near(x, z, r)) {
      if (s === ignore || s.owner?.noCollide) continue;
      if (y !== null && s.top !== undefined && y + STEP >= s.top) continue; // can step up onto it
      if (y !== null && s.bottom !== undefined && y + 1.8 <= s.bottom) continue;
      if (Colliders.hit(s, x, z, r)) return true;
    }
    return false;
  }

  // Push a circle out of everything it overlaps (a few iterations).
  resolve(x, z, r, y = null) {
    for (let it = 0; it < 3; it++) {
      let moved = false;
      for (const s of this.near(x, z, r)) {
        if (s.owner?.noCollide) continue;
        if (y !== null && s.top !== undefined && y + STEP >= s.top) continue;
        if (y !== null && s.bottom !== undefined && y + 1.8 <= s.bottom) continue;
        const h = Colliders.hit(s, x, z, r);
        if (h) { x += h.nx * h.depth; z += h.nz * h.depth; moved = true; }
      }
      if (!moved) break;
    }
    return { x, z };
  }
}

function worldNormal(s, lx, lz, depth) {
  // inverse rotation of local → world
  return { nx: lx * s.c + lz * s.s, nz: -lx * s.s + lz * s.c, depth };
}

// Walkable raised surfaces (foundation tops, stairs). Height function per surface.
export class Surfaces {
  constructor() {
    this.grid = new SpatialGrid();
  }
  // Axis box in local frame (x,z center, hw, hd, rot); height(lx, lz) gives y in local coords.
  add(x, z, hw, hd, rot, height, owner) {
    const s = { x, z, hw, hd, rot, c: Math.cos(rot), s: Math.sin(rot), height, owner };
    const R = Math.hypot(hw, hd);
    this.grid.insert(s, x - R, z - R, x + R, z + R);
    return s;
  }
  remove(s) {
    if (s) this.grid.remove(s);
  }
  // Highest surface at (x, z) that is at most `stepUp` above `fromY`.
  heightAt(x, z, fromY, stepUp = STEP) {
    let best = -Infinity;
    for (const s of this.grid.query(x, z, x, z)) {
      const dx = x - s.x, dz = z - s.z;
      const lx = dx * s.c - dz * s.s, lz = dx * s.s + dz * s.c;
      if (Math.abs(lx) > s.hw || Math.abs(lz) > s.hd) continue;
      const y = s.height(lx, lz);
      if (y <= fromY + stepUp && y > best) best = y;
    }
    return best;
  }
}
