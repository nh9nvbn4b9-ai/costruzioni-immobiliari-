import React, {useEffect, useState} from 'react';
import {AbsoluteFill, OffthreadVideo, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import lab from './film/labels3d.json';

// Film della Home: facciata reale (costruzione, sera, piano acceso) -> plastico 3D animato -> tour 3D.
export const FILM2_FPS = 24;
export const FACADE_FRAMES = 370;
export const START3D = 356;
export const INT_FRAMES = 520;
export const FILM2_FRAMES = START3D + INT_FRAMES;
const BG = '#0b0d12';
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const outC = Easing.out(Easing.cubic);
const eio = (x: number) => {
	x = Math.min(Math.max(x, 0), 1);
	return x < 0.5 ? 4 * x ** 3 : 1 - (-2 * x + 2) ** 3 / 2;
};
const useFonts = () => {
	const [h] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(h));
	}, [h]);
};
const win = (f: number, a: number, b: number, d = 10) => Math.min(interpolate(f, [a, a + d], [0, 1], {...cl, easing: outC}), interpolate(f, [b - d, b], [1, 0], cl));

const CARDS: {r: [number, number]; k: string; t: string}[] = [
	{r: [268, 330], k: 'Soggiorno · 46,6 m²', t: 'Divano in tessuto e parete in pietra'},
	{r: [336, 392], k: 'Cucina con isola', t: 'Top in marmo e luci sospese'},
	{r: [396, 438], k: 'Zona pranzo', t: 'Tavolo in noce per sei'},
	{r: [482, 516], k: 'Camera matrimoniale · 19,4 m²', t: 'Testata imbottita e armadio a parete'},
];

export const Film2: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W, height: H} = useVideoConfig();
	const portrait = H > W;
	const s = Math.min(W, H) / 1080;
	const lf = f - START3D; // fotogramma del render 3D
	// inquadratura del render quadrato: intero (plastico) -> pieno schermo (dentro casa)
	const u = eio((lf - 200) / 62);
	const fitS = portrait ? W / 1200 : H / 1200;
	const fillS = portrait ? H / 1200 : W / 1200;
	const sc = fitS + (fillS - fitS) * u;
	const cx0 = portrait ? W / 2 : W * 0.62;
	const cy0 = portrait ? H * 0.45 : H / 2;
	const cx = cx0 + (W / 2 - cx0) * u;
	const cy = cy0 + (H / 2 - cy0) * u;
	const fade3d = interpolate(f, [START3D, FACADE_FRAMES], [0, 1], cl);
	const pos = lf >= 0 && lf < lab.pos.length ? (lab.pos[lf] as number[][]) : null;
	const labO = win(lf, 160, 206, 10);
	const end = interpolate(f, [FILM2_FRAMES - 14, FILM2_FRAMES - 1], [1, 0], cl);
	return (
		<AbsoluteFill style={{background: BG}}>
			<Sequence durationInFrames={FACADE_FRAMES}>
				<OffthreadVideo src={staticFile(portrait ? 'film/facade_portrait.mp4' : 'film/facade_landscape.mp4')} style={{width: '100%', height: '100%'}} muted />
			</Sequence>
			{lf >= 0 && (
				<AbsoluteFill style={{opacity: fade3d}}>
					<AbsoluteFill style={{background: BG}} />
					<Sequence from={START3D}>
						<OffthreadVideo
							src={staticFile('film/interior.mp4')}
							muted
							style={{position: 'absolute', width: 1200, height: 1200, left: cx - 600, top: cy - 600, transform: `scale(${sc})`, transformOrigin: '50% 50%'}}
						/>
					</Sequence>
					{u < 1 && (
						<AbsoluteFill
							style={{
								pointerEvents: 'none',
								background: `radial-gradient(${1200 * sc * 0.62}px ${1200 * sc * 0.62}px at ${cx}px ${cy}px, rgba(11,13,18,0) 70%, ${BG} 100%)`,
								opacity: 1 - u,
							}}
						/>
					)}
				</AbsoluteFill>
			)}
			{pos && labO > 0 && (
				<AbsoluteFill>
					{lab.rooms.map((r, j) => {
						const p = pos[j];
						const o = labO * interpolate(lf, [160 + j * 2, 170 + j * 2], [0, 1], {...cl, easing: outC});
						const small = r.name.length <= 5;
						return (
							<div
								key={j}
								style={{
									position: 'absolute',
									left: cx + (p[0] - 0.5) * 1200 * sc,
									top: cy + (p[1] - 0.5) * 1200 * sc,
									transform: `translate(-50%,-50%) translateY(${(1 - o) * 8}px)`,
									opacity: o,
									background: 'rgba(17,20,25,0.84)',
									color: '#fff',
									borderRadius: 6 * s,
									padding: `${3 * s}px ${8 * s}px`,
									textAlign: 'center',
									whiteSpace: 'nowrap',
									boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
								}}
							>
								<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: (small ? 11 : 12) * s, letterSpacing: '0.08em', textTransform: 'uppercase'}}>{r.name}</div>
								<div style={{fontFamily: 'IBM Plex Mono', fontWeight: 500, fontSize: 11 * s, color: '#ffd59a', marginTop: 1}}>{r.area}</div>
							</div>
						);
					})}
					<div style={{position: 'absolute', left: portrait ? 40 * s : cx - 520 * sc, top: portrait ? cy + 520 * sc : cy + 470 * sc, opacity: labO, color: '#fff'}}>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: 20 * s, letterSpacing: '0.1em'}}>PIANTA PIANO 3°</div>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: 12 * s, color: '#cfe6f6', marginTop: 4 * s}}>APPARTAMENTO TIPO · 140 m² · TERRAZZO VERDE</div>
					</div>
				</AbsoluteFill>
			)}
			{CARDS.map((c, i) => {
				const o = win(lf, c.r[0], c.r[1], 10);
				if (o <= 0) return null;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: portrait ? 40 * s : 72 * s,
							top: portrait ? 150 * s : undefined,
							bottom: portrait ? undefined : 80 * s,
							opacity: o,
							transform: `translateY(${(1 - o) * 14 * s}px)`,
							background: 'rgba(250,248,244,0.9)',
							borderRadius: 12 * s,
							padding: `${14 * s}px ${18 * s}px`,
							boxShadow: '0 18px 40px rgba(0,0,0,0.22)',
							color: '#16191e',
							maxWidth: 420 * s,
						}}
					>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: 13 * s, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#c4271f'}}>{c.k}</div>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: 24 * s, lineHeight: 1.12, marginTop: 6 * s}}>{c.t}</div>
					</div>
				);
			})}
			<AbsoluteFill style={{background: BG, opacity: 1 - end}} />
		</AbsoluteFill>
	);
};
