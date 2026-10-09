# Tideborn — browser/mobil

Tideborn i browseren, bygget med three.js efter designet i `../Docs/`. Kører på telefon og computer uden installation.

**Spil:** https://jonvmnielsen.github.io/tideborn/
Start forfra med en tom gemning: https://jonvmnielsen.github.io/tideborn/?reset

## Sådan spiller du

| | Telefon | Computer |
|---|---|---|
| Gå / løb | Venstre tommelfinger (træk helt ud for at løbe) | WASD / piletaster (Shift = gå) |
| Drej kameraet | Træk med højre tommelfinger | Træk med musen |
| Zoom | – | Musehjul |
| Handling (saml, fæld, åbn, sov) | Den runde knap (hold for at blive ved) | E eller mellemrum |
| Rygsæk og crafting | Rygsæk-knappen | I eller Tab |
| Byg | Byg-knappen, vælg en del, tryk Placér | B, vælg del, E for at placere, R for at dreje, X for at fjerne |
| Spis | Spis-knappen ved måleren | F |

## Spilløkken (Phase 1 — Camp)

1. Knæk grene af døde træer, saml løse sten og plukker siv ved vandet.
2. Lav en **stenøkse** i Rygsækken. Nu kan du fælde alle træer, også i skovene.
3. Lav en **hakke** og hak sten af de store klipper.
4. **Byg**: fundament → vægge, døråbning, vinduer → tag. Etage og trappe giver 2. sal. Bål og fakler lyser om natten, kisten gemmer ting, sengen bliver dit hjem.
5. Sult tæres langsomt. Forsyningskasser skyller i land på stranden hver morgen.
6. Udforsk: kæmpetræet midt på øen og udsigtstårnet på højderyggen mod nord.

Spillet gemmer automatisk i browseren på den enhed, du spiller på.

## Udvikling

```bash
cd web
npm install
npm run dev        # lokal udvikling
npm run build      # bygger til web/dist
npm run sync-assets   # henter modellerne i assets.json fra ../../game-assets
```

Hvert push til `main`, der ændrer `web/`, bygger og udgiver spillet automatisk via GitHub Actions.

## Kode

| Mappe/fil | Ansvar |
|-----|--------|
| `src/main.js` | Opstart, spil-loop, handlinger, mål, gemning |
| `src/world/terrain.js` | Øens højdekort, bælter, farver, afstandsfelt til havet |
| `src/world/world.js` | Samler øen: landemærker, flora, kollision, himmel og hav |
| `src/world/scatter.js` | Instansering pr. 64 m chunk; hvert træ kan skjules/vises |
| `src/world/collide.js` | Cirkler og bokse til kollision, gangbare flader (gulve, trapper) |
| `src/systems/gather.js` | Fæld, hak, saml; fald-animation; genvækst; tidevand |
| `src/systems/building.js` | Byggesystem: ghost, snap, regler, placering, fjern, gem |
| `src/systems/daynight.js` | Døgnrytme og lys |
| `src/systems/survival.js` | Sult og liv |
| `src/systems/inventory.js` | Ting i rygsæk og kister |
| `src/data/*.js` | Ting, opskrifter, byggedele og indsamling som data |
| `src/player.js`, `src/camera.js`, `src/input.js`, `src/ui.js` | Spiller, tredjepersonskamera, styring, skærmlag |
