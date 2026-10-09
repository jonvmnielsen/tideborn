// Item definitions. Recipes and build costs refer to these ids only.
export const ITEMS = {
  wood:  { name: 'Træ',   icon: 'ui/wood.webp',  stack: 99, tags: ['resource'] },
  stone: { name: 'Sten',  icon: 'ui/stone.webp', stack: 99, tags: ['resource'] },
  fiber: { name: 'Fibre', icon: 'ui/fiber.webp', stack: 99, tags: ['resource'] },
  food:  { name: 'Mad',   icon: 'ui/food.webp',  stack: 20, tags: ['food'], food: 35 },
  stone_axe:  { name: 'Stenøkse', icon: 'ui/axe.webp',  stack: 1, tags: ['tool'], tool: 'axe' },
  stone_pick: { name: 'Hakke',    icon: 'ui/pick.webp', stack: 1, tags: ['tool'], tool: 'pick' },
};

export const itemName = (id) => ITEMS[id]?.name ?? id;
export const itemIcon = (id) => ITEMS[id]?.icon ?? 'ui/crate.webp';
