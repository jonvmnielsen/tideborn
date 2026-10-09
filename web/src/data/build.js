// Modular building pieces on a 4 m grid. Foundations define the grid; walls snap to
// foundation edges, roofs sit on top of walls, furniture goes on floors or ground.
//
// snap:
//   'foundation' — 4×4 cell; first one is free, the rest snap next to existing ones
//   'edge'       — on a foundation edge (walls, doorway, window, fence on ground edge)
//   'roof'       — over a foundation cell, at wall height
//   'free'       — anywhere on ground or floor, small grid
export const GRID = 4;
export const WALL_H = 4;
export const FLOOR_H = 0.6; // foundation top above its lowest ground point

export const PIECES = [
  { id: 'foundation', name: 'Fundament', icon: 'ui/b_footing.webp',   cost: { wood: 4, stone: 4 }, snap: 'foundation' },
  { id: 'wall',       name: 'Væg',       icon: 'ui/b_wall.webp',    cost: { wood: 3, stone: 2 }, snap: 'edge' },
  { id: 'doorway',    name: 'Døråbning', icon: 'ui/b_doorway.webp', cost: { wood: 4, stone: 1 }, snap: 'edge', passable: true },
  { id: 'window',     name: 'Vindue',    icon: 'ui/b_window.webp',  cost: { wood: 3, stone: 1, fiber: 1 }, snap: 'edge' },
  { id: 'loft',       name: 'Etage',     icon: 'ui/b_floor.webp',   cost: { wood: 6 }, snap: 'level' },
  { id: 'roof',       name: 'Tag',       icon: 'ui/b_gable.webp',   cost: { wood: 4, fiber: 3 }, snap: 'roof' },
  { id: 'stairs',     name: 'Trappe',    icon: 'ui/b_stairs.webp',  cost: { wood: 5 }, snap: 'free', size: [3.3, 6], step: 0.5 },
  { id: 'fence',      name: 'Hegn',      icon: 'ui/b_fence.webp',   cost: { wood: 2 }, snap: 'free', size: [4.6, 0.4], step: 0.5 },
  { id: 'campfire',   name: 'Bål',       icon: 'ui/b_torch.webp',   cost: { wood: 3, stone: 4 }, snap: 'free', size: [1.6, 1.6], step: 0.25, light: true },
  { id: 'torch',      name: 'Fakkel',    icon: 'ui/b_torch.webp',   cost: { wood: 1, fiber: 1 }, snap: 'free', size: [0.5, 0.5], step: 0.25, light: true },
  { id: 'chest',      name: 'Kiste',     icon: 'ui/b_chest.webp',   cost: { wood: 6 }, snap: 'free', size: [1.7, 1.9], step: 0.25, storage: 24 },
  { id: 'bed',        name: 'Seng',      icon: 'ui/b_bed.webp',     cost: { wood: 5, fiber: 6 }, snap: 'free', size: [1.6, 3.0], step: 0.25, spawn: true },
];

export const PIECE = Object.fromEntries(PIECES.map((p) => [p.id, p]));
