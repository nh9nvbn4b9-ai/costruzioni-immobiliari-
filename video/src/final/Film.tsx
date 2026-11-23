import React, {useEffect, useState} from 'react';
import {AbsoluteFill, OffthreadVideo, continueRender, delayRender, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import planLabels from './film/plan.json';
import metaP from './film/base_portrait.json';
import metaL from './film/base_landscape.json';

// Film della Home: costruzione dalla foto reale, sera, pianta, tour nelle stanze reali.
export const FILM_FPS = 24;
export const FILM_FRAMES = 804;
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const outC = Easing.out(Easing.cubic);

const useFonts = () => {
	const [h] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(h));
	}, [h]);
};

const fadeWin = (f: number, a: number, b: number, d = 8) => Math.min(interpolate(f, [a, a + d], [0, 1], {...cl, easing: outC}), interpolate(f, [b - d, b], [1, 0], cl));

const ROOM_CARDS: {r: [number, number]; k: string; t: string}[] = [
	{r: [500, 618], k: 'Soggiorno · 46,6 m²', t: 'Pietra naturale, rovere e luce diffusa'},
	{r: [650, 785], k: 'Bagno padronale', t: 'Vasca freestanding su pedana in pietra'},
];

export const FilmHome: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W, height: H} = useVideoConfig();
	const portrait = H > W;
	const meta = (portrait ? metaP : metaL) as {plan: (number[] | null)[]};
	const s = Math.min(W, H) / 1080;
	const rect = meta.plan[Math.min(f, meta.plan.length - 1)];
	const labO = fadeWin(f, 392, 446, 10);
	return (
		<AbsoluteFill style={{background: '#0c0f14'}}>
			<OffthreadVideo src={staticFile(portrait ? 'film/base_portrait.mp4' : 'film/base_landscape.mp4')} style={{width: '100%', height: '100%'}} muted />
			{rect && labO > 0 && (
				<AbsoluteFill>
					{planLabels.labels.map((l, j) => {
						const o = labO * interpolate(f, [392 + j * 2, 402 + j * 2], [0, 1], {...cl, easing: outC});
						const small = l.name.length <= 5;
						return (
							<div
								key={j}
								style={{
									position: 'absolute',
									left: rect[0] + l.x * rect[2],
									top: rect[1] + l.y * rect[3],
									transform: `translate(-50%,-50%) translateY(${(1 - o) * 8}px)`,
									opacity: o,
									background: 'rgba(17,20,25,0.82)',
									color: '#fff',
									borderRadius: 6 * s,
									padding: `${3 * s}px ${8 * s}px`,
									textAlign: 'center',
									whiteSpace: 'nowrap',
									boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
								}}
							>
								<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: (small ? 11 : 12) * s, letterSpacing: '0.08em', textTransform: 'uppercase'}}>{l.name}</div>
								<div style={{fontFamily: 'IBM Plex Mono', fontWeight: 500, fontSize: 11 * s, color: '#ffd59a', marginTop: 1}}>{l.area}</div>
							</div>
						);
					})}
					<div style={{position: 'absolute', left: rect[0], top: rect[1] + rect[3] + 18 * s, opacity: labO, color: '#fff'}}>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: 18 * s, letterSpacing: '0.1em'}}>PIANTA PIANO 3°</div>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: 12 * s, color: '#cfe6f6', marginTop: 4 * s}}>APPARTAMENTO TIPO · 140 m² · TERRAZZO VERDE</div>
					</div>
				</AbsoluteFill>
			)}
			{ROOM_CARDS.map((c, i) => {
				const o = fadeWin(f, c.r[0], c.r[1], 12);
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
		</AbsoluteFill>
	);
};
