# Tideborn — browser/mobil

Spilbar version af Tideborn i browseren, bygget med three.js. Kører på telefon og computer uden installation.

**Spil:** https://jonvmnielsen.github.io/tideborn/
Start forfra med en tom gemning: https://jonvmnielsen.github.io/tideborn/?reset

## Sådan spiller du

| | Telefon | Computer |
|---|---|---|
| Gå | Træk med tommelfingeren i venstre side | WASD / piletaster |
| Løb | Træk joysticket helt ud | (altid løb med taster) |
| Saml | Tryk på den orange knap (hold for at blive ved) | E eller mellemrum |
| Zoom | – | Musehjul |

Træer giver træ (3 hug), sten giver sten (4 hug). De gror tilbage efter 1,5–2 minutter. Spillet gemmer automatisk i browseren på den enhed, du spiller på.

## Indhold i v0.1

- Ø af KayKit-hexfelter med automatisk tilpasset kystlinje og en bugt mod syd
- Hav med lavvandet farve og skum langs stranden (egen shader)
- Spiller (KayKit Barbarian) med gå, løb, hug og jubel
- Træer og sten at samle, med fældning, splinter og genvækst
- Joystick + kontekstknap på mobil, tastatur på computer
- Automatisk gemning lokalt

## Udvikling

```bash
cd web
npm install
npm run dev        # lokal udvikling
npm run build      # bygger til web/dist
```

Grafik kommer fra [game-assets](https://github.com/jonvmnielsen/game-assets). Listen over brugte modeller står i `assets.json`. Hent dem ind med (kræver game-assets klonet ved siden af tideborn):

```bash
npm run sync-assets
```

Hvert push til `main`, der ændrer `web/`, bygger og udgiver spillet automatisk via GitHub Actions (`.github/workflows/pages.yml`).

## Kode

| Fil | Ansvar |
|-----|--------|
| `src/main.js` | Opstart, kamera, lys, spil-loop, gemning |
| `src/world.js` | Øens form, kystfelter, højdeopslag, dekoration, kollisioner |
| `src/hex.js` | Hex-matematik og bagte højdekort pr. felt |
| `src/water.js` | Hav- og himmelshader |
| `src/player.js` | Spilleren: bevægelse, animationer, kollision |
| `src/resources.js` | Træer og sten: hug, fældning, genvækst |
| `src/input.js` | Joystick, knap og tastatur |
| `src/hud.js` | Inventar, knap-tekst, flydende "+1" |
| `src/fx.js` | Splinter-effekt |
| `src/save.js` | Gemning i localStorage |
