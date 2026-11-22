// Dati condivisi: edificio, cronologia, pianta dell'appartamento
import {Easing, interpolate} from 'remotion';

export const FPS = 30;
export const DURATION = 600;

export const BW = 30; // larghezza edificio (x)
export const BD = 10; // profondità (z), fronte su z = BD
export const H = 3.2;
export const SLAB = 0.3;
export const LEVELS = 10; // piano terra + 9
export const F = 5; // piano che si illumina
export const YF = F * H + SLAB; // quota pavimento finito del piano F
export const BAL = {x0: 0.8, x1: 8.4, z1: BD + 1.75};

// isolato del cantiere
export const LOT = {x0: -12, x1: 42, z0: -18, z1: 26};
export const PIT = {x0: -1, x1: BW + 1, z0: -1, z1: BD + 1, depth: 3};

export const T = {
	dig: [24, 62],
	pour: [62, 88],
	struct0: 88,
	structStep: 15,
	core: [88, 255],
	fac0: 140,
	facStep: 17,
	facDur: 16,
	roof: [300, 338],
	land: [300, 362],
	sun: [190, 430],
	lights: [330, 420],
	floorLit: [385, 412],
	lift: [440, 492],
	facOff: [446, 474],
	interior: 436,
	top: [470, 530],
	labels: [528, 572],
	fadeIn: [0, 14],
	fadeOut: [586, 599],
} as const;

const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const io = Easing.bezier(0.65, 0, 0.35, 1);
export const ease = (f: number, r: readonly [number, number] | number[], e = io) => interpolate(f, [r[0], r[1]], [0, 1], {...cl, easing: e});
export const lin = (f: number, r: readonly [number, number] | number[]) => interpolate(f, [r[0], r[1]], [0, 1], cl);
export const outC = Easing.out(Easing.cubic);
export const inC = Easing.in(Easing.cubic);

// ---------- pianta (coordinate di pianta: x → x, y → z) ----------
export type V2 = [number, number];
export type Room = {name: string; area: string; label: V2; rects: [number, number, number, number][]; floor: 'wood' | 'tiles'};
export const ROOMS: Room[] = [
	{name: 'Soggiorno · Cucina', area: '46,6 m²', label: [5.3, 8.9], floor: 'wood', rects: [[0, 4, 4.4, 10], [4.4, 5.4, 8.8, 10]]},
	{name: 'Camera', area: '17,6 m²', label: [2.9, 3.4], floor: 'wood', rects: [[0, 0, 4.4, 4]]},
	{name: 'Bagno', area: '6,8 m²', label: [5.7, 1.55], floor: 'tiles', rects: [[4.4, 0, 7, 2.6]]},
	{name: 'Rip.', area: '3,6 m²', label: [5.0, 3.0], floor: 'tiles', rects: [[4.4, 2.6, 7, 4]]},
	{name: 'Studio', area: '13,6 m²', label: [8.7, 1.9], floor: 'wood', rects: [[7, 0, 10.4, 4]]},
	{name: 'Matrimoniale', area: '19,4 m²', label: [12.4, 4.0], floor: 'wood', rects: [[10.4, 0, 14, 5.4]]},
	{name: 'Disimpegno', area: '8,4 m²', label: [7.6, 4.75], floor: 'wood', rects: [[4.4, 4, 10.4, 5.4]]},
	{name: 'Bagno', area: '6,6 m²', label: [9.9, 6.6], floor: 'tiles', rects: [[8.8, 5.4, 11, 8.4]]},
	{name: 'Lav.', area: '3,5 m²', label: [9.9, 8.9], floor: 'tiles', rects: [[8.8, 8.4, 11, 10]]},
	{name: 'Camera', area: '13,8 m²', label: [12.3, 9.2], floor: 'wood', rects: [[11, 5.4, 14, 10]]},
];

export const INNER: [V2, V2][] = [
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
export const DOORS: {h: V2; r: number; a1: number}[] = [
	{h: [4.1, 4], r: 0.9, a1: 1.5 * Math.PI},
	{h: [5.0, 4], r: 0.8, a1: -0.5 * Math.PI},
	{h: [6.1, 2.6], r: 0.9, a1: 1.5 * Math.PI},
	{h: [8.5, 4], r: 0.9, a1: 1.5 * Math.PI},
	{h: [10.4, 4.2], r: 0.9, a1: 0},
	{h: [9.2, 5.4], r: 0.8, a1: 0.5 * Math.PI},
	{h: [11, 8.6], r: 0.9, a1: 0},
];
// finestre sul perimetro dell'appartamento [lato, da, a]
export const WINDOWS: ['N' | 'S' | 'W' | 'E', number, number][] = [
	['S', 1, 3.5],
	['S', 4.5, 7.5],
	['S', 11.8, 13.2],
	['N', 1.2, 3.2],
	['N', 7.8, 9.6],
	['N', 11.4, 13],
	['W', 6, 8.5],
	['W', 1, 3],
];
