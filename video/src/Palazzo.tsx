import React, {useEffect, useState} from 'react';
import {
	AbsoluteFill,
	Easing,
	continueRender,
	delayRender,
	interpolate,
	interpolateColors,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';

/*
 * Animazione hero "Costruzioni Immobiliari S.r.l."
 * 1. Griglia di cantiere + tracciato del palazzo (wireframe)
 * 2. Il palazzo si costruisce da solo, un piano alla volta
 * 3. Cala la sera, si illumina il 5° piano
 * 4. La camera si avvicina, i piani superiori si sollevano
 * 5. La vista ruota dall'assonometria alla pianta dell'appartamento
 * 6. Dissolvenza per il loop
 */

export const FPS = 30;
export const DURATION = 450;

type V3 = [number, number, number];
type V2 = [number, number];

const C = Math.cos(Math.PI / 6);
const W = 14; // larghezza (m)
const D = 10; // profondità (m)
const H = 3.2; // interpiano (m)
const SLAB = 0.35;
const LEVELS = 8;
const F = 5; // piano che si illumina
const OV = 0.12; // sbalzo solaio
const BAL = {x0: 0.8, x1: 8.4, depth: 1.4};

// Finestre in facciata, coerenti con la pianta
const WIN_FRONT: V2[] = [
	[1, 3.5],
	[4.5, 7.5],
	[11.8, 13.2],
]; // facciata y = D
const WIN_SIDE: V2[] = [
	[1.5, 3.5],
	[6.5, 8.5],
]; // facciata x = W

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const io = Easing.bezier(0.65, 0, 0.35, 1);
const outC = Easing.out(Easing.cubic);
const inC = Easing.in(Easing.cubic);
const mix = (a: number, b: number, t: number) => a + (b - a) * t;
const mix3 = (a: V3, b: V3, t: number): V3 => [mix(a[0], b[0], t), mix(a[1], b[1], t), mix(a[2], b[2], t)];
const lmix = (a: number, b: number, t: number) => Math.exp(mix(Math.log(a), Math.log(b), t));
const rnd = (n: number) => {
	const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};

// ---------- Pianta appartamento tipo (metri) ----------
type Room = {name: string; area: string; pts: V2[]; tone: 'wood' | 'tile'; label: V2};
const ROOMS: Room[] = [
	{name: 'SOGGIORNO · CUCINA', area: '46,6 m²', tone: 'wood', label: [2.5, 8.9], pts: [[0, 4], [4.4, 4], [4.4, 5.4], [8.8, 5.4], [8.8, 10], [0, 10]]},
	{name: 'CAMERA', area: '17,6 m²', tone: 'wood', label: [2.0, 3.15], pts: [[0, 0], [4.4, 0], [4.4, 4], [0, 4]]},
	{name: 'BAGNO', area: '6,8 m²', tone: 'tile', label: [5.7, 1.6], pts: [[4.4, 0], [7, 0], [7, 2.6], [4.4, 2.6]]},
	{name: 'RIP.', area: '3,6 m²', tone: 'tile', label: [5.7, 3.35], pts: [[4.4, 2.6], [7, 2.6], [7, 4], [4.4, 4]]},
	{name: 'STUDIO', area: '13,6 m²', tone: 'wood', label: [8.7, 2.2], pts: [[7, 0], [10.4, 0], [10.4, 4], [7, 4]]},
	{name: 'MATRIMONIALE', area: '19,4 m²', tone: 'wood', label: [12.2, 0.85], pts: [[10.4, 0], [14, 0], [14, 5.4], [10.4, 5.4]]},
	{name: 'DISIMPEGNO', area: '8,4 m²', tone: 'wood', label: [7.4, 4.75], pts: [[4.4, 4], [10.4, 4], [10.4, 5.4], [4.4, 5.4]]},
	{name: 'BAGNO', area: '6,6 m²', tone: 'tile', label: [9.9, 6.25], pts: [[8.8, 5.4], [11, 5.4], [11, 8.4], [8.8, 8.4]]},
	{name: 'LAV.', area: '3,5 m²', tone: 'tile', label: [9.9, 9.3], pts: [[8.8, 8.4], [11, 8.4], [11, 10], [8.8, 10]]},
	{name: 'CAMERA', area: '13,8 m²', tone: 'wood', label: [11.9, 9.35], pts: [[11, 5.4], [14, 5.4], [14, 10], [11, 10]]},
];
const TERRACE: V2[] = [[BAL.x0, D], [BAL.x1, D], [BAL.x1, D + BAL.depth], [BAL.x0, D + BAL.depth]];

const OUTER: [V2, V2][] = [
	[[0, 0], [14, 0]],
	[[14, 0], [14, 10]],
	[[14, 10], [0, 10]],
	[[0, 10], [0, 0]],
];
const INNER: [V2, V2][] = [
	[[0, 4], [3.2, 4]],
	[[4.4, 0], [4.4, 4]],
	[[7, 0], [7, 4]],
	[[4.4, 2.6], [5.2, 2.6]],
	[[6.1, 2.6], [7, 2.6]],
	[[4.1, 4], [5.0, 4]],
	[[5.8, 4], [7.6, 4]],
	[[8.5, 4], [10.4, 4]],
	[[10.4, 0], [10.4, 4.2]],
	[[10.4, 5.1], [10.4, 5.4]],
	[[8.8, 5.4], [9.2, 5.4]],
	[[10.0, 5.4], [14, 5.4]],
	[[8.8, 5.4], [8.8, 8.6]],
	[[8.8, 9.6], [8.8, 10]],
	[[8.8, 8.4], [11, 8.4]],
	[[11, 5.4], [11, 8.6]],
	[[11, 9.5], [11, 10]],
];
// porte: cerniera, raggio, angolo chiuso -> aperto
const DOORS: {h: V2; r: number; a0: number; a1: number}[] = [
	{h: [4.1, 4], r: 0.9, a0: Math.PI, a1: 1.5 * Math.PI},
	{h: [5.0, 4], r: 0.8, a0: 0, a1: -0.5 * Math.PI},
	{h: [6.1, 2.6], r: 0.9, a0: Math.PI, a1: 1.5 * Math.PI},
	{h: [8.5, 4], r: 0.9, a0: Math.PI, a1: 1.5 * Math.PI},
	{h: [10.4, 4.2], r: 0.9, a0: 0.5 * Math.PI, a1: 0},
	{h: [9.2, 5.4], r: 0.8, a0: 0, a1: 0.5 * Math.PI},
	{h: [11, 8.6], r: 0.9, a0: 0.5 * Math.PI, a1: 0},
	{h: [8.8, 9.6], r: 1.0, a0: -0.5 * Math.PI, a1: 0},
];
// finestre in pianta
const PLAN_WINDOWS: [V2, V2][] = [
	...WIN_FRONT.map(([a, b]) => [[a, D], [b, D]] as [V2, V2]),
	...WIN_SIDE.map(([a, b]) => [[W, a], [W, b]] as [V2, V2]),
	[[1.2, 0], [3.2, 0]],
	[[7.8, 0], [9.6, 0]],
	[[11.4, 0], [13, 0]],
	[[0, 6], [0, 8.5]],
	[[0, 1], [0, 3]],
];
// arredi (rettangoli e cerchi)
const FURN_RECT: [number, number, number, number][] = [
	[0.15, 4.25, 0.75, 7.6], // cucina
	[1.9, 4.8, 3.6, 5.4], // isola
	[1.0, 6.4, 3.4, 7.3], // divano
	[1.6, 7.6, 2.8, 8.2], // tavolino
	[5.2, 6.6, 7.4, 7.6], // tavolo
	[0.9, 0.35, 2.7, 2.35], // letto
	[3.75, 0.2, 4.3, 2.6], // armadio
	[4.55, 0.15, 6.85, 0.85], // vasca
	[7.25, 0.2, 9.1, 0.8], // scrivania
	[11.3, 1.55, 13.1, 3.55], // letto matrimoniale
	[11.6, 4.7, 13.85, 5.25], // armadio
	[10.1, 7.4, 10.9, 8.3], // doccia
	[12.85, 6.0, 13.85, 8.0], // letto singolo
	[11.2, 5.55, 12.4, 6.05], // scrivania
];
const FURN_CIRC: [number, number, number][] = [
	[6.4, 2.05, 0.22],
	[4.75, 2.05, 0.2],
	[8.15, 1.25, 0.25],
	[9.15, 6.0, 0.2],
	[9.15, 7.0, 0.22],
	[5.7, 6.35, 0.18],
	[6.9, 6.35, 0.18],
	[5.7, 7.85, 0.18],
	[6.9, 7.85, 0.18],
];

const useFonts = () => {
	const [handle] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(handle));
	}, [handle]);
};

export const Palazzo: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width, height} = useVideoConfig();
	const portrait = height > width;

	// ---------- fasi ----------
	const levelStart = (i: number) => 30 + i * 18;
	const roofStart = levelStart(LEVELS) - 4;
	const dusk = interpolate(f, [180, 225], [0, 1], {...clamp, easing: io});
	const k1 = interpolate(f, [235, 298], [0, 1], {...clamp, easing: io}); // avvicinamento
	const p = interpolate(f, [298, 352], [0, 1], {...clamp, easing: io}); // assonometria -> pianta
	const lift = interpolate(f, [240, 290], [0, 1], {...clamp, easing: inC});
	const facadeOut = interpolate(f, [262, 294], [0, 1], clamp);
	const interior = interpolate(f, [258, 296], [0, 1], {...clamp, easing: outC});
	const lowerOut = interpolate(f, [300, 336], [0, 1], clamp);
	const ctxOut = interpolate(f, [270, 320], [0, 1], clamp);
	const endFade = interpolate(f, [418, 449], [0, 1], {...clamp, easing: io});
	const gridIn = interpolate(f, [0, 24], [0, 1], clamp);

	// ---------- camera ----------
	const zF = F * H + SLAB;
	const bc: V3 = [W / 2, D / 2, (LEVELS * H) / 2 + 1.2];
	const fc: V3 = [W / 2, D / 2 + 0.6, zF];
	const pc: V3 = [6.7, 5.7, zF];
	const fw = mix3(mix3(bc, fc, k1), pc, p);

	const S0 = portrait ? Math.min((height * 0.46) / 39, (width * 0.8) / 22) : Math.min((height * 0.8) / 39, (width * 0.4) / 22);
	const S1 = portrait ? (width * 0.8) / 22 : Math.min((width * 0.5) / 22, (height * 0.7) / 15);
	const S2 = portrait ? (width * 0.84) / 16.2 : Math.min((width * 0.48) / 16.2, (height * 0.74) / 14.4);
	const push = interpolate(f, [0, 235], [1, 1.06], clamp);
	const S = lmix(lmix(S0 * push, S1, k1), S2, p) * (1 + 0.02 * interpolate(f, [352, 449], [0, 1], clamp));

	const a0: V2 = portrait ? [width * 0.5, height * 0.3] : [width * 0.68, height * 0.52];
	const a2: V2 = portrait ? [width * 0.5, height * 0.29] : [width * 0.65, height * 0.5];
	const ax = mix(a0[0], a2[0], k1);
	const ay = mix(a0[1], a2[1], k1);

	const isoP = (v: V3): V2 => [(v[0] - v[1]) * C, (v[0] + v[1]) * 0.5 - v[2]];
	const isoC = isoP([W / 2, D / 2, zF]);
	const proj = (v: V3): V2 => {
		const a = isoP(v);
		if (p <= 0) return a;
		const b: V2 = [v[0] - W / 2 + isoC[0], v[1] - D / 2 + isoC[1]];
		return [mix(a[0], b[0], p), mix(a[1], b[1], p)];
	};
	const focus = proj(fw);
	const sc = (v: V3): V2 => {
		const q = proj(v);
		return [ax + (q[0] - focus[0]) * S, ay + (q[1] - focus[1]) * S];
	};
	const pts = (vs: V3[]) => vs.map((v) => sc(v).map((n) => n.toFixed(1)).join(',')).join(' ');
	const line = (a: V3, b: V3) => {
		const A = sc(a);
		const B = sc(b);
		return `M${A[0].toFixed(1)},${A[1].toFixed(1)}L${B[0].toFixed(1)},${B[1].toFixed(1)}`;
	};

	// ---------- colori ----------
	const cLeft = interpolateColors(dusk, [0, 1], ['#dcd7cf', '#5f5c59']);
	const cRight = interpolateColors(dusk, [0, 1], ['#a7a29a', '#403e3c']);
	const cTop = interpolateColors(dusk, [0, 1], ['#ebe7e1', '#77736e']);
	const cSlabL = interpolateColors(dusk, [0, 1], ['#bdb7ae', '#4d4a47']);
	const cSlabR = interpolateColors(dusk, [0, 1], ['#8e8981', '#34322f']);
	const cGlass = interpolateColors(dusk, [0, 1], ['#4a6176', '#16202b']);
	const cGlass2 = interpolateColors(dusk, [0, 1], ['#3a4f62', '#111922']);
	const LIT = '#ffcf86';
	const RED = '#c4271f';
	const BP = 'rgba(160,196,230,'; // blueprint

	const elements: React.ReactNode[] = [];
	let key = 0;
	const add = (n: React.ReactNode) => elements.push(<React.Fragment key={key++}>{n}</React.Fragment>);

	const box = (x0: number, x1: number, y0: number, y1: number, z0: number, z1: number, top: string, left: string, right: string, op = 1) => {
		add(
			<g opacity={op}>
				<polygon points={pts([[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])} fill={top} />
				<polygon points={pts([[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]])} fill={left} />
				<polygon points={pts([[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]])} fill={right} />
			</g>,
		);
	};

	// ---------- griglia a terra ----------
	const grid: string[] = [];
	for (let g = -24; g <= 38; g += 2) {
		grid.push(line([g, -20, 0], [g, 30, 0]));
	}
	for (let g = -20; g <= 30; g += 2) {
		grid.push(line([-24, g, 0], [38, g, 0]));
	}
	const groundOp = gridIn * (1 - lowerOut) * (1 - endFade);

	// ---------- edifici di contesto (wireframe) ----------
	const NEIGH: [number, number, number, number, number][] = [
		[-15, -3, 9, 8, 15],
		[19, -1, 8, 9, 21],
		[-5, 15, 11, 6, 9],
		[20, 14, 9, 7, 13],
		[3, -17, 12, 8, 27],
		[-17, 12, 8, 8, 18],
	];
	const wire = (x: number, y: number, w: number, d: number, h: number) => {
		const c: V3[] = [
			[x, y, 0], [x + w, y, 0], [x + w, y + d, 0], [x, y + d, 0],
			[x, y, h], [x + w, y, h], [x + w, y + d, h], [x, y + d, h],
		];
		const e = [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]];
		return e.map(([a, b]) => line(c[a], c[b])).join('');
	};
	const neighIn = interpolate(f, [8, 40], [0, 1], clamp);

	// ---------- tracciato fantasma ----------
	const TOPZ = LEVELS * H + SLAB;
	const ghostDraw = interpolate(f, [4, 34], [0, 1], {...clamp, easing: outC});
	const ghostOp = interpolate(f, [4, 14], [0, 1], clamp) * (1 - interpolate(f, [170, 215], [0, 1], clamp));
	const ghostEdges: string[] = [];
	{
		const c: V3[] = [
			[0, 0, 0], [W, 0, 0], [W, D, 0], [0, D, 0],
			[0, 0, TOPZ], [W, 0, TOPZ], [W, D, TOPZ], [0, D, TOPZ],
		];
		[[0, 1], [1, 2], [2, 3], [3, 0], [0, 4], [1, 5], [2, 6], [3, 7], [4, 5], [5, 6], [6, 7], [7, 4]].forEach(([a, b]) =>
			ghostEdges.push(line(c[a], c[b])),
		);
		for (let i = 1; i < LEVELS; i++) {
			const z = i * H;
			ghostEdges.push(line([0, D, z], [W, D, z]) + line([W, D, z], [W, 0, z]));
		}
	}

	add(
		<g opacity={(1 - ctxOut) * neighIn * 0.55}>
			<path d={NEIGH.map((n) => wire(...n)).join('')} stroke={BP + '0.28)'} strokeWidth={1} fill="none" />
		</g>,
	);
	add(
		<g opacity={groundOp}>
			<path d={grid.join('')} stroke={BP + '0.09)'} strokeWidth={1} fill="none" mask="url(#gridMask)" />
			<polygon
				points={pts([[-0.6, -0.6, 0], [W + 0.6, -0.6, 0], [W + 0.6, D + 2, 0], [-0.6, D + 2, 0]])}
				fill={BP + '0.05)'}
				stroke={BP + '0.45)'}
				strokeWidth={1}
				strokeDasharray="6 6"
			/>
		</g>,
	);
	add(
		<path
			d={ghostEdges.join('')}
			stroke={BP + '0.55)'}
			strokeWidth={1.2}
			fill="none"
			opacity={ghostOp}
			pathLength={1}
			strokeDasharray={`${ghostDraw} 1`}
		/>,
	);

	// ---------- piani ----------
	const litFor = (j: number) => interpolate(f, [200 + j * 5, 214 + j * 5], [0, 1], {...clamp, easing: outC});
	let laser: React.ReactNode = null;

	for (let i = 0; i <= LEVELS; i++) {
		const t = f - (i === LEVELS ? roofStart : levelStart(i));
		if (t < 0) continue;
		const isF = i === F;
		let zOff = interpolate(t, [0, 12], [5, 0], {...clamp, easing: outC});
		let op = interpolate(t, [0, 6], [0, 1], clamp);
		if (i > F) {
			zOff += lift * (5 + (i - F) * 4);
			op *= 1 - interpolate(f, [244, 284], [0, 1], clamp);
		}
		if (i < F) op *= 1 - lowerOut;
		op *= 1 - endFade;
		if (op <= 0.001) continue;
		const z0 = i * H + zOff;
		const zb = z0 + SLAB;

		if (i === LEVELS) {
			// copertura
			const top = zb;
			box(-OV, W + OV, -OV, D + OV, z0, top, cTop, cSlabL, cSlabR, op);
			const coreT = interpolate(t, [6, 18], [0, 1], {...clamp, easing: outC});
			const ch = 2.6 * coreT;
			if (ch > 0.01) {
				box(4.5, 9.5, 1.2, 4.6, top, top + ch, cTop, cLeft, cRight, op);
				const band = Math.min(0.45, ch);
				add(
					<g opacity={op}>
						<polygon points={pts([[4.5, 4.6, top + ch - band], [9.5, 4.6, top + ch - band], [9.5, 4.6, top + ch], [4.5, 4.6, top + ch]])} fill={RED} />
						<polygon points={pts([[9.5, 1.2, top + ch - band], [9.5, 4.6, top + ch - band], [9.5, 4.6, top + ch], [9.5, 1.2, top + ch]])} fill="#8f1b15" />
					</g>,
				);
			}
			const ph = 0.8 * interpolate(t, [4, 14], [0, 1], clamp);
			if (ph > 0.01) {
				add(
					<g opacity={op}>
						<polygon points={pts([[-OV, D + OV, top], [W + OV, D + OV, top], [W + OV, D + OV, top + ph], [-OV, D + OV, top + ph]])} fill={cLeft} />
						<polygon points={pts([[W + OV, -OV, top], [W + OV, D + OV, top], [W + OV, D + OV, top + ph], [W + OV, -OV, top + ph]])} fill={cRight} />
						<path d={line([-OV, D + OV, top + ph], [W + OV, D + OV, top + ph]) + line([W + OV, D + OV, top + ph], [W + OV, -OV, top + ph])} stroke={cTop} strokeWidth={2} />
					</g>,
				);
			}
			continue;
		}

		// solaio
		box(-OV, W + OV, -OV, D + OV, z0, zb, isF && interior > 0 ? interpolateColors(interior, [0, 1], [cTop, '#2a2622']) : cTop, cSlabL, cSlabR, op);

		const wallT = interpolate(t, [7, 19], [0, 1], {...clamp, easing: outC});
		const winT = interpolate(t, [13, 22], [0, 1], clamp);
		const zt = zb + (H - SLAB) * wallT;

		// interno del piano illuminato (prima della facciata)
		if (isF && interior > 0) {
			add(renderPlan(zb));
		}

		const fop = op * (isF ? 1 - facadeOut : 1);
		if (wallT > 0 && fop > 0.001) {
			const sill = i === 0 ? 0.25 : 0.55;
			const head = i === 0 ? 2.6 : 2.45;
			const nodes: React.ReactNode[] = [];
			nodes.push(<polygon key="r" points={pts([[W, 0, zb], [W, D, zb], [W, D, zt], [W, 0, zt]])} fill={cRight} />);
			nodes.push(<polygon key="l" points={pts([[0, D, zb], [W, D, zb], [W, D, zt], [0, D, zt]])} fill={cLeft} />);
			const wz0 = zb + sill;
			const wz1 = Math.min(zt, zb + head);
			if (wz1 > wz0 && winT > 0) {
				WIN_FRONT.forEach(([a, b], j) => {
					const lit = isF ? litFor(j) : 0;
					const g = interpolateColors(lit, [0, 1], [cGlass, LIT]);
					nodes.push(
						<g key={'wf' + j} opacity={winT * (0.85 + 0.15 * rnd(i * 10 + j))}>
							<polygon points={pts([[a, D + 0.01, wz0], [b, D + 0.01, wz0], [b, D + 0.01, wz1], [a, D + 0.01, wz1]])} fill={g} />
							<path d={line([(a + b) / 2, D + 0.01, wz0], [(a + b) / 2, D + 0.01, wz1])} stroke={interpolateColors(dusk, [0, 1], ['#2b3946', '#0c1117'])} strokeWidth={1.2} />
						</g>,
					);
				});
				WIN_SIDE.forEach(([a, b], j) => {
					const lit = isF ? litFor(j + 3) : 0;
					const g = interpolateColors(lit, [0, 1], [cGlass2, '#f3b866']);
					nodes.push(
						<g key={'ws' + j} opacity={winT * (0.85 + 0.15 * rnd(i * 20 + j))}>
							<polygon points={pts([[W + 0.01, a, wz0], [W + 0.01, b, wz0], [W + 0.01, b, wz1], [W + 0.01, a, wz1]])} fill={g} />
							<path d={line([W + 0.01, (a + b) / 2, wz0], [W + 0.01, (a + b) / 2, wz1])} stroke={interpolateColors(dusk, [0, 1], ['#26323d', '#0a0e13'])} strokeWidth={1.2} />
						</g>,
					);
				});
			}
			add(<g opacity={fop}>{nodes}</g>);

			// alone del piano illuminato
			if (isF) {
				const glow = litFor(2) * (1 - facadeOut * 0.4);
				if (glow > 0) {
					add(
						<g opacity={glow * op * 0.9} filter="url(#glow)">
							{WIN_FRONT.map(([a, b], j) => (
								<polygon key={j} points={pts([[a, D + 0.3, wz0], [b, D + 0.3, wz0], [b, D + 0.3, zb + 2.45], [a, D + 0.3, zb + 2.45]])} fill={LIT} />
							))}
							{WIN_SIDE.map(([a, b], j) => (
								<polygon key={'s' + j} points={pts([[W + 0.3, a, wz0], [W + 0.3, b, wz0], [W + 0.3, b, zb + 2.45], [W + 0.3, a, zb + 2.45]])} fill={LIT} />
							))}
						</g>,
					);
				}
			}
		}

		// balcone
		if (i >= 1 && wallT > 0) {
			const bt = zb;
			const bz0 = bt - 0.25;
			const y1 = D + BAL.depth * wallT;
			const rail = 1.0 * winT;
			const bop = op * (isF ? 1 - facadeOut * 0.85 : 1);
			add(
				<g opacity={bop}>
					<polygon points={pts([[BAL.x0, D, bt], [BAL.x1, D, bt], [BAL.x1, y1, bt], [BAL.x0, y1, bt]])} fill={isF && interior > 0 ? interpolateColors(interior, [0, 1], [cTop, '#3b342d']) : cTop} />
					<polygon points={pts([[BAL.x0, y1, bz0], [BAL.x1, y1, bz0], [BAL.x1, y1, bt], [BAL.x0, y1, bt]])} fill={cSlabL} />
					<polygon points={pts([[BAL.x1, D, bz0], [BAL.x1, y1, bz0], [BAL.x1, y1, bt], [BAL.x1, D, bt]])} fill={cSlabR} />
					{rail > 0 && (
						<>
							<polygon points={pts([[BAL.x0, y1, bt], [BAL.x1, y1, bt], [BAL.x1, y1, bt + rail], [BAL.x0, y1, bt + rail]])} fill="rgba(170,205,230,0.18)" />
							<polygon points={pts([[BAL.x1, D, bt], [BAL.x1, y1, bt], [BAL.x1, y1, bt + rail], [BAL.x1, D, bt + rail]])} fill="rgba(170,205,230,0.12)" />
							<path d={line([BAL.x0, y1, bt + rail], [BAL.x1, y1, bt + rail]) + line([BAL.x1, y1, bt + rail], [BAL.x1, D, bt + rail])} stroke={interpolateColors(dusk, [0, 1], ['#f2efe9', '#8d8984'])} strokeWidth={1.6} />
						</>
					)}
				</g>,
			);
		}

		// laser di livellamento durante la costruzione
		if (wallT > 0 && wallT < 1) {
			const lo = Math.sin(wallT * Math.PI);
			laser = (
				<g opacity={lo * 0.9}>
					<polygon
						points={pts([[-0.5, -0.5, zt], [W + 0.5, -0.5, zt], [W + 0.5, D + 0.5, zt], [-0.5, D + 0.5, zt]])}
						fill="rgba(120,200,255,0.06)"
						stroke="rgba(150,215,255,0.9)"
						strokeWidth={1.4}
					/>
				</g>
			);
		}
	}
	if (laser) add(laser);

	// ---------- pianta ----------
	function renderPlan(zb: number) {
		const z = zb + 0.005;
		const wallH = 1.15 * interior;
		const furn = interpolate(f, [318, 350], [0, 1], clamp);
		const fill = interior;
		const out: React.ReactNode[] = [];
		const toneCol = (t: Room['tone']) => (t === 'wood' ? '#a67c52' : '#7f97a3');
		out.push(
			<g key="rooms" opacity={fill}>
				{ROOMS.map((r, j) => (
					<polygon key={j} points={pts(r.pts.map(([x, y]) => [x, y, z] as V3))} fill={toneCol(r.tone)} opacity={0.62} />
				))}
				<polygon points={pts(TERRACE.map(([x, y]) => [x, y, z] as V3))} fill="#5b544c" opacity={0.7} />
				{/* luce calda */}
				<polygon points={pts([[0, 0, z], [W, 0, z], [W, D, z], [0, D, z]])} fill="url(#warm)" opacity={0.55 * (1 - p * 0.6)} />
			</g>,
		);
		// arredi
		if (furn > 0) {
			out.push(
				<g key="furn" opacity={furn * 0.9} stroke="rgba(255,248,238,0.55)" strokeWidth={Math.max(1, S * 0.025)} fill="rgba(255,248,238,0.10)">
					{FURN_RECT.map(([x0, y0, x1, y1], j) => (
						<polygon key={j} points={pts([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]])} />
					))}
					{FURN_CIRC.map(([cx, cy, r], j) => {
						const P = sc([cx, cy, z]);
						return <circle key={'c' + j} cx={P[0]} cy={P[1]} r={r * S} />;
					})}
				</g>,
			);
		}
		// muri: facce laterali + sommità
		const seg = (list: [V2, V2][], th: number, side: string, topc: string, k: string) => {
			const sides = list.map(([a, b], j) => (
				<polygon key={k + 's' + j} points={pts([[a[0], a[1], z], [b[0], b[1], z], [b[0], b[1], z + wallH], [a[0], a[1], z + wallH]])} fill={side} />
			));
			const tops = (
				<path
					key={k + 't'}
					d={list.map(([a, b]) => line([a[0], a[1], z + wallH], [b[0], b[1], z + wallH])).join('')}
					stroke={topc}
					strokeWidth={th * S}
					strokeLinecap="square"
					fill="none"
				/>
			);
			return [...sides, tops];
		};
		out.push(<g key="walls">{[...seg(OUTER, 0.3, '#b9b1a5', '#f6f2ec', 'o'), ...seg(INNER, 0.12, '#cfc7bb', '#f6f2ec', 'i')]}</g>);
		// finestre in pianta
		out.push(
			<path
				key="pw"
				d={PLAN_WINDOWS.map(([a, b]) => line([a[0], a[1], z + wallH], [b[0], b[1], z + wallH])).join('')}
				stroke="#8fc4e8"
				strokeWidth={0.16 * S}
				opacity={interior}
			/>,
		);
		// porte
		const doorOp = interpolate(f, [330, 356], [0, 1], clamp);
		if (doorOp > 0) {
			const d = DOORS.map(({h, r, a0, a1}) => {
				const steps = 12;
				let s = '';
				for (let k = 0; k <= steps; k++) {
					const a = mix(a0, a1, k / steps);
					const P = sc([h[0] + r * Math.cos(a), h[1] + r * Math.sin(a), z]);
					s += (k === 0 ? 'M' : 'L') + P[0].toFixed(1) + ',' + P[1].toFixed(1);
				}
				const H0 = sc([h[0], h[1], z]);
				const E = sc([h[0] + r * Math.cos(a1), h[1] + r * Math.sin(a1), z]);
				return s + `M${H0[0].toFixed(1)},${H0[1].toFixed(1)}L${E[0].toFixed(1)},${E[1].toFixed(1)}`;
			}).join('');
			out.push(<path key="doors" d={d} stroke="rgba(255,248,238,0.75)" strokeWidth={Math.max(1, S * 0.03)} fill="none" opacity={doorOp} />);
		}
		// ringhiera terrazzo
		out.push(
			<path
				key="ter"
				d={line([BAL.x0, D + BAL.depth, z], [BAL.x1, D + BAL.depth, z]) + line([BAL.x1, D + BAL.depth, z], [BAL.x1, D, z]) + line([BAL.x0, D + BAL.depth, z], [BAL.x0, D, z])}
				stroke="#8fc4e8"
				strokeWidth={0.08 * S}
				opacity={interior}
			/>,
		);

		// etichette, quote, cartiglio (solo in pianta)
		const lab = (j: number) => interpolate(f, [338 + j * 3, 356 + j * 3], [0, 1], {...clamp, easing: outC});
		const fs = 0.3 * S;
		ROOMS.forEach((r, j) => {
			const o = lab(j) * p;
			if (o <= 0) return;
			const P = sc([r.label[0], r.label[1], z]);
			const small = r.name.length <= 5;
			out.push(
				<g key={'lab' + j} opacity={o} transform={`translate(${P[0]},${P[1] + (1 - o) * 8})`}>
					<text textAnchor="middle" fontFamily="Archivo" fontWeight={800} fontSize={fs * (small ? 0.78 : 0.82)} letterSpacing={fs * 0.08} fill="#fffaf2" style={{paintOrder: 'stroke'}} stroke="rgba(20,16,12,0.55)" strokeWidth={fs * 0.18}>
						{r.name}
					</text>
					<text y={fs * 1.15} textAnchor="middle" fontFamily="IBM Plex Mono" fontWeight={500} fontSize={fs * 0.82} fill="#ffd9a0" style={{paintOrder: 'stroke'}} stroke="rgba(20,16,12,0.55)" strokeWidth={fs * 0.18}>
						{r.area}
					</text>
				</g>,
			);
		});
		{
			const o = lab(ROOMS.length) * p;
			if (o > 0) {
				const P = sc([4.6, D + 0.82, z]);
				out.push(
					<text key="terlab" x={P[0]} y={P[1]} opacity={o} textAnchor="middle" fontFamily="IBM Plex Mono" fontWeight={500} fontSize={fs * 0.74} letterSpacing={fs * 0.06} fill="#cfe6f6">
						TERRAZZO · 10,6 m²
					</text>,
				);
			}
		}
		const dimO = interpolate(f, [352, 380], [0, 1], clamp) * p;
		if (dimO > 0) {
			const tk = 0.22;
			const dd =
				line([0, -0.9, z], [W, -0.9, z]) +
				line([0, -0.9 - tk, z], [0, -0.9 + tk, z]) +
				line([W, -0.9 - tk, z], [W, -0.9 + tk, z]) +
				line([-0.9, 0, z], [-0.9, D, z]) +
				line([-0.9 - tk, 0, z], [-0.9 + tk, 0, z]) +
				line([-0.9 - tk, D, z], [-0.9 + tk, D, z]);
			const T1 = sc([W / 2, -1.15, z]);
			const T2 = sc([-1.15, D / 2, z]);
			out.push(
				<g key="dims" opacity={dimO}>
					<path d={dd} stroke={BP + '0.8)'} strokeWidth={1.3} fill="none" />
					<text x={T1[0]} y={T1[1]} textAnchor="middle" fontFamily="IBM Plex Mono" fontSize={fs * 0.8} fill={BP + '0.95)'}>
						14,00
					</text>
					<text x={T2[0]} y={T2[1]} textAnchor="middle" fontFamily="IBM Plex Mono" fontSize={fs * 0.8} fill={BP + '0.95)'} transform={`rotate(-90 ${T2[0]} ${T2[1]})`}>
						10,00
					</text>
				</g>,
			);
		}
		const tbO = interpolate(f, [364, 392], [0, 1], clamp) * p;
		if (tbO > 0) {
			const P = sc([0, D + 2.35, z]);
			const N = sc([13.3, D + 2.0, z]);
			out.push(
				<g key="tb" opacity={tbO}>
					<text x={P[0]} y={P[1]} fontFamily="Archivo" fontWeight={800} fontSize={fs * 0.95} letterSpacing={fs * 0.1} fill="#fffaf2">
						PIANTA PIANO 5°
					</text>
					<text x={P[0]} y={P[1] + fs * 1.25} fontFamily="IBM Plex Mono" fontSize={fs * 0.72} letterSpacing={fs * 0.04} fill={BP + '0.95)'}>
						APPARTAMENTO TIPO · SUP. 140 m² · SCALA 1:100
					</text>
					<g transform={`translate(${N[0]},${N[1]})`}>
						<circle r={fs * 1.1} fill="none" stroke={BP + '0.8)'} strokeWidth={1.3} />
						<polygon points={`0,${-fs * 0.95} ${fs * 0.38},${fs * 0.5} 0,${fs * 0.2} ${-fs * 0.38},${fs * 0.5}`} fill="#fffaf2" />
						<text y={-fs * 1.35} textAnchor="middle" fontFamily="IBM Plex Mono" fontWeight={500} fontSize={fs * 0.75} fill="#fffaf2">
							N
						</text>
					</g>
				</g>,
			);
		}
		return <g opacity={1 - endFade}>{out}</g>;
	}

	// ---------- sfondo ----------
	const bgTop = interpolateColors(dusk, [0, 1], ['#1d2a3a', '#0b1018']);
	const bgBot = interpolateColors(dusk, [0, 1], ['#0f151e', '#06080c']);
	const halo = interpolateColors(dusk, [0, 1], ['rgba(120,160,200,0.22)', 'rgba(255,190,110,0.10)']);

	return (
		<AbsoluteFill style={{background: `linear-gradient(180deg, ${bgTop} 0%, ${bgBot} 100%)`}}>
			<svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
				<defs>
					<radialGradient id="halo" cx="50%" cy="50%" r="50%">
						<stop offset="0%" stopColor={halo} />
						<stop offset="100%" stopColor="rgba(0,0,0,0)" />
					</radialGradient>
					<radialGradient id="gridFade" cx="50%" cy="45%" r="55%">
						<stop offset="0%" stopColor="#fff" stopOpacity={1} />
						<stop offset="100%" stopColor="#fff" stopOpacity={0} />
					</radialGradient>
					<mask id="gridMask" maskUnits="userSpaceOnUse" x={0} y={0} width={width} height={height}>
						<rect width={width} height={height} fill="url(#gridFade)" />
					</mask>
					<radialGradient id="warm" cx="50%" cy="60%" r="70%">
						<stop offset="0%" stopColor="#ffd08a" stopOpacity={0.9} />
						<stop offset="100%" stopColor="#ffb25e" stopOpacity={0.15} />
					</radialGradient>
					<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
						<feGaussianBlur stdDeviation={18} />
					</filter>
				</defs>
				<ellipse cx={ax} cy={ay} rx={Math.max(width, height) * 0.55} ry={Math.max(width, height) * 0.45} fill="url(#halo)" />
				{elements}
			</svg>
			{/* vignettatura */}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 60% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 100%)'}} />
		</AbsoluteFill>
	);
};
