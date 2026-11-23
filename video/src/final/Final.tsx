import React, {useEffect, useState} from 'react';
import {AbsoluteFill, OffthreadVideo, continueRender, delayRender, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import labels from './labels.json';

// Montaggio finale dei render Blender/Cycles (fotorealistici) con testi e dissolvenze

export const FINAL_FPS = 24;
export const HERO_FRAMES = 432;
export const TOUR_FRAMES = 432;
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const outC = Easing.out(Easing.cubic);
const BG = '#0c0f14';

const useFonts = () => {
	const [h] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(h));
	}, [h]);
};

const Grain: React.FC = () => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill
			style={{
				opacity: 0.06,
				mixBlendMode: 'overlay',
				backgroundImage:
					"url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
				backgroundPosition: `${(f * 37) % 220}px ${(f * 53) % 220}px`,
			}}
		/>
	);
};

// ---------- Home ----------
export const HeroFinal: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W, height: Hh} = useVideoConfig();
	const portrait = Hh > W;
	// il master è quadrato: lo posizioniamo in modo che il soggetto stia lontano dai testi del sito
	const S = portrait ? W * 1.25 : Hh * 1.15;
	const left = portrait ? (W - S) / 2 : W - S;
	const top = portrait ? 0 : (Hh - S) / 2;
	const px = (nx: number) => left + nx * S;
	const py = (ny: number) => top + ny * S;
	const lab = (j: number) => interpolate(f, [392 + j * 2, 404 + j * 2], [0, 1], {...cl, easing: outC});
	const fade = Math.min(interpolate(f, [0, 12], [0, 1], cl), interpolate(f, [HERO_FRAMES - 12, HERO_FRAMES - 1], [1, 0], cl));
	const fs = S * 0.0125;
	const d = labels.dims as Record<string, number[]>;
	const dimO = lab(labels.labels.length);
	return (
		<AbsoluteFill style={{background: BG}}>
			<div style={{position: 'absolute', left, top, width: S, height: S}}>
				<OffthreadVideo src={staticFile('blender/hero.mp4')} style={{width: '100%', height: '100%'}} muted />
			</div>
			{portrait ? (
				<AbsoluteFill style={{background: `linear-gradient(180deg, rgba(12,15,20,0) ${((S - 260) / Hh) * 100}%, ${BG} ${(S / Hh) * 100}%)`}} />
			) : (
				<AbsoluteFill style={{background: `linear-gradient(90deg, ${BG} ${(left / W) * 100}%, rgba(12,15,20,0) ${((left + 320) / W) * 100}%)`}} />
			)}
			{f >= 392 && (
				<AbsoluteFill>
					<svg width={W} height={Hh} style={{position: 'absolute', inset: 0}}>
						<g opacity={dimO} stroke="rgba(255,255,255,0.85)" strokeWidth={2} fill="#fff" fontFamily="IBM Plex Mono" fontSize={fs * 0.9}>
							<line x1={px(d.tl[0])} y1={py(d.tl[1]) - fs * 1.6} x2={px(d.tr[0])} y2={py(d.tr[1]) - fs * 1.6} />
							<text x={(px(d.tl[0]) + px(d.tr[0])) / 2} y={py(d.tl[1]) - fs * 2.1} textAnchor="middle" stroke="none" style={{textShadow: '0 1px 4px #000'}}>
								14,00 m
							</text>
							<line x1={px(d.tl[0]) - fs * 1.6} y1={py(d.tl[1])} x2={px(d.bl[0]) - fs * 1.6} y2={py(d.bl[1])} />
						</g>
					</svg>
					{labels.labels.map((r, j) => {
						const o = lab(j);
						const small = r.name.length <= 5;
						return (
							<div
								key={j}
								style={{
									position: 'absolute',
									left: px(r.x),
									top: py(r.y),
									transform: `translate(-50%,-50%) translateY(${(1 - o) * 8}px)`,
									opacity: o,
									background: 'rgba(17,20,25,0.8)',
									color: '#fff',
									borderRadius: 6,
									padding: `${fs * 0.25}px ${fs * 0.5}px`,
									textAlign: 'center',
									whiteSpace: 'nowrap',
									boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
								}}
							>
								<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: fs * (small ? 0.72 : 0.78), letterSpacing: '0.08em', textTransform: 'uppercase'}}>{r.name}</div>
								<div style={{fontFamily: 'IBM Plex Mono', fontWeight: 500, fontSize: fs * 0.75, color: '#ffd59a', marginTop: 2}}>{r.area}</div>
							</div>
						);
					})}
					<div style={{position: 'absolute', left: px(d.title[0]), top: py(d.title[1]), opacity: lab(labels.labels.length + 2), color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.8)'}}>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: fs * 1.15, letterSpacing: '0.1em'}}>PIANTA PIANO 5°</div>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: fs * 0.75, color: '#cfe6f6', marginTop: 4}}>APPARTAMENTO TIPO · 140 m² · TERRAZZO 13 m²</div>
					</div>
				</AbsoluteFill>
			)}
			<Grain />
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 60% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.4) 100%)'}} />
			<AbsoluteFill style={{background: BG, opacity: 1 - fade}} />
		</AbsoluteFill>
	);
};

// ---------- Tour ----------
const SWITCH = 140;
const CARDS: {r: [number, number]; k: string; t: string; d: string}[] = [
	{r: [18, 112], k: 'Piano 5° · Appartamento tipo', t: '140 m² su un solo livello', d: '3 camere, 2 bagni, studio e terrazzo di 13 m².'},
	{r: [160, 222], k: 'Soggiorno · 46,6 m²', t: 'Rovere, bouclé e un tocco di colore', d: 'Vetrate a tutta altezza aperte sul tramonto.'},
	{r: [236, 282], k: 'Cucina', t: 'Isola in marmo, piano in pietra scura', d: 'Aperta sul soggiorno, con dispensa a colonna.'},
	{r: [288, 322], k: 'Zona pranzo', t: 'Una tavola per sei accanto al vetro', d: 'Luce naturale da due lati.'},
	{r: [322, 356], k: 'Terrazzo · 13 m²', t: 'Affacciato sul parco', d: 'Salotto esterno e fioriere in pietra.'},
	{r: [378, 426], k: 'Camera matrimoniale · 19,4 m²', t: 'Lino, legno di noce e luce calda', d: 'Armadio a tutta parete e angolo lettura.'},
];

export const TourFinal: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W} = useVideoConfig();
	const s = W / 1920;
	const flash = f < SWITCH ? interpolate(f, [SWITCH - 12, SWITCH], [0, 1], cl) : interpolate(f, [SWITCH, SWITCH + 12], [1, 0], cl);
	const fade = Math.min(interpolate(f, [0, 10], [0, 1], cl), interpolate(f, [TOUR_FRAMES - 12, TOUR_FRAMES - 1], [1, 0], cl));
	return (
		<AbsoluteFill style={{background: '#efece6'}}>
			<OffthreadVideo src={staticFile('blender/tour.mp4')} style={{width: '100%', height: '100%'}} muted />
			{CARDS.map((c, i) => {
				const o = Math.min(interpolate(f, [c.r[0], c.r[0] + 10], [0, 1], {...cl, easing: outC}), interpolate(f, [c.r[1] - 8, c.r[1]], [1, 0], cl));
				if (o <= 0) return null;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: 72 * s,
							bottom: 80 * s,
							width: 480 * s,
							opacity: o,
							transform: `translateY(${(1 - o) * 18 * s}px)`,
							background: 'rgba(250,248,244,0.9)',
							borderRadius: 14 * s,
							padding: `${22 * s}px ${26 * s}px`,
							boxShadow: '0 20px 50px rgba(0,0,0,0.2)',
							color: '#16191e',
						}}
					>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: 17 * s, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#c4271f'}}>{c.k}</div>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: 34 * s, lineHeight: 1.1, marginTop: 8 * s}}>{c.t}</div>
						<div style={{fontFamily: 'Archivo', fontWeight: 600, fontSize: 21 * s, color: '#585b60', marginTop: 8 * s}}>{c.d}</div>
					</div>
				);
			})}
			<Grain />
			<AbsoluteFill style={{background: '#ffffff', opacity: flash}} />
			<AbsoluteFill style={{background: '#efece6', opacity: 1 - fade}} />
		</AbsoluteFill>
	);
};
