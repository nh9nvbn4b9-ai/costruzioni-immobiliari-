# Costruzioni Immobiliari S.r.l. – sito web

Sito one-page (Home, Chi siamo, Servizi, Preventivo, Contatti, Orari, Dove siamo).

- `site/` – il sito statico: apri `site/index.html` o pubblica la cartella su qualsiasi hosting.
- `video/` – progetto [Remotion](https://github.com/remotion-dev/remotion) che genera l'animazione della home.
  La versione usata dal sito è una scena 3D (`@remotion/three` + three.js) in `video/src/cantiere/`:
  un isolato di Milano, scavo e fondazioni, struttura in cemento armato che sale piano per piano,
  facciate e vetrate, tramonto, il 5° piano che si illumina e la pianta arredata vista dall'alto.

## Rigenerare i video

```bash
cd video
npm install
npx remotion studio src/index.ts            # anteprima interattiva
npx remotion render src/index.ts CantiereLandscape out/cantiere-landscape.mp4 --gl=swangle
npx remotion render src/index.ts CantierePortrait  out/cantiere-portrait.mp4  --gl=swangle
cp out/*.mp4 ../site/assets/
```

La versione verticale (1080×1920) viene usata automaticamente sui telefoni, così l'animazione copre tutto lo schermo.
