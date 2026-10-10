// Things in the world you can gather from. `tool` = required tool type (null = bare hands).
// Each hit gives `per`; after `hits` the node is spent and regrows after `regrow` seconds.
// `height` (metres, min–max) scales plant scans to a believable size.
export const HARVEST = {
  pine:     { label: 'Fæld træ',          icon: 'ui/tree.webp',  tool: 'axe',  item: 'wood',  per: 2, hits: 4, regrow: 240, radius: 0.6, anim: 'chop', fx: '#9a6332', fall: true, stump: true },
  cone:     { label: 'Fæld træ',          icon: 'ui/tree.webp',  tool: 'axe',  item: 'wood',  per: 2, hits: 3, regrow: 200, radius: 0.55, anim: 'chop', fx: '#9a6332', fall: true, stump: true },
  dead:     { label: 'Knæk grene',        icon: 'ui/wood.webp',  tool: null,   item: 'wood',  per: 1, hits: 2, regrow: 300, radius: 0.4, anim: 'chop', fx: '#8b7355', fall: true },
  drift:    { label: 'Saml drivtømmer',   icon: 'ui/wood.webp',  tool: null,   item: 'wood',  per: 1, hits: 2, regrow: 300, radius: 0.5, anim: 'pickup', fx: '#8b7355' },
  boulder:  { label: 'Hak sten',          icon: 'ui/rock.webp',  tool: 'pick', item: 'stone', per: 2, hits: 4, regrow: 360, radius: 1.3, anim: 'chop', fx: '#9aa2a6' },
  pebble:   { label: 'Saml sten',         icon: 'ui/stone.webp', tool: null,   item: 'stone', per: 1, hits: 1, regrow: 180, radius: 0.35, anim: 'pickup', fx: '#9aa2a6', walkable: true },
  reed:     { label: 'Pluk nælder',       icon: 'ui/fiber.webp', tool: null,   item: 'fiber', per: 2, hits: 1, regrow: 150, radius: 0.35, anim: 'pickup', fx: '#6f9a3a', walkable: true, height: [0.7, 1.1] },
  fern:     { label: 'Pluk bregner',      icon: 'ui/fiber.webp', tool: null,   item: 'fiber', per: 1, hits: 1, regrow: 150, radius: 0.4, anim: 'pickup', fx: '#5f8a34', walkable: true },
  supplies: { label: 'Åbn kasse',         icon: 'ui/crate.webp', tool: null,   item: 'food',  per: 3, hits: 1, regrow: 0,   radius: 0.6, anim: 'interact', fx: '#b98a4e', tide: true },
};

export const TOOL_NAME = { axe: 'en stenøkse', pick: 'en hakke' };
