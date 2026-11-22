# Costruzioni Immobiliari S.r.l. – sito web

Sito one-page (Home, Chi siamo, Servizi, Preventivo, Contatti, Orari, Dove siamo).

- `site/` – il sito statico: apri `site/index.html` o pubblica la cartella su qualsiasi hosting.
- `video/` – progetto [Remotion](https://github.com/remotion-dev/remotion) che genera l'animazione della home
  (il palazzo si costruisce, si illumina il 5° piano, la camera si avvicina e mostra la pianta).

## Rigenerare i video

```bash
cd video
npm install
npx remotion studio src/index.ts            # anteprima interattiva
npx remotion render src/index.ts PalazzoLandscape out/palazzo-landscape.mp4
npx remotion render src/index.ts PalazzoPortrait  out/palazzo-portrait.mp4
cp out/*.mp4 ../site/assets/
```

La versione verticale (1080×1920) viene usata automaticamente sui telefoni, così l'animazione copre tutto lo schermo.
