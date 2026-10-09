// Crafting recipes (hand-crafted from the inventory panel).
export const RECIPES = [
  {
    id: 'stone_axe',
    out: { stone_axe: 1 },
    cost: { wood: 3, stone: 2, fiber: 2 },
    text: 'Fælder træer. Uden økse kan du kun samle døde grene.',
  },
  {
    id: 'stone_pick',
    out: { stone_pick: 1 },
    cost: { wood: 4, stone: 4, fiber: 3 },
    needs: 'stone_axe',
    text: 'Hakker store klipper til sten. Giver langt mere end løse sten.',
  },
];
