import React, {useMemo} from 'react';
import * as THREE from 'three';
import {RoundedBoxGeometry} from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import {Geo, Textures} from './tex';
import {BAL, BD, DOORS, INNER, ROOMS, WINDOWS} from './plan';

// Appartamento arredato, visto dall'alto. Coordinate di pianta: x → x, y → z (metri)

const WALL_H = 2.7;
type Mat = keyof ReturnType<typeof makeMats>;
// [x0, y0, x1, y1, quota base, altezza, materiale, raggio arrotondamento]
type Item = [number, number, number, number, number, number, Mat, number?];
// cilindri: [cx, cy, r, base, h, mat, scalaY?]
type Cyl = [number, number, number, number, number, Mat, number?];

const makeMats = (tx: Textures) => {
	const s = (o: THREE.MeshStandardMaterialParameters) => new THREE.MeshStandardMaterial(o);
	const rep = (t: THREE.Texture) => {
		const c = t.clone();
		c.needsUpdate = true;
		return c;
	};
	return {
		white: s({color: '#f1eee8', roughness: 0.55}),
		wallTop: s({color: '#fbfaf7', roughness: 0.7}),
		oak: s({color: '#c39a6b', roughness: 0.6}),
		walnut: s({color: '#6e4a31', roughness: 0.55}),
		teak: s({color: '#8a6446', roughness: 0.7}),
		fabricGrey: s({color: '#8d8f92', roughness: 0.95}),
		fabricLight: s({color: '#d9d4cb', roughness: 0.95}),
		fabricBeige: s({color: '#c8b49a', roughness: 0.95}),
		fabricBlue: s({color: '#3f5a78', roughness: 0.9}),
		leather: s({color: '#8b5a36', roughness: 0.6}),
		linen: s({color: '#f4f1ea', roughness: 0.9}),
		pillow: s({color: '#fbfaf6', roughness: 0.9}),
		pillowOchre: s({color: '#c99a3e', roughness: 0.9}),
		pillowTeal: s({color: '#3e6f6c', roughness: 0.9}),
		duvetSage: s({color: '#a9b59a', roughness: 0.92}),
		duvetCream: s({color: '#ebe2d2', roughness: 0.92}),
		duvetMustard: s({color: '#d2a43f', roughness: 0.92}),
		throwRust: s({color: '#a8573a', roughness: 0.95}),
		throwNavy: s({color: '#2f3c57', roughness: 0.95}),
		black: s({color: '#202124', roughness: 0.5}),
		steel: s({color: '#b8bcc2', metalness: 0.85, roughness: 0.25}),
		ceramic: s({color: '#fdfdfb', roughness: 0.18}),
		water: s({color: '#8fc3cf', roughness: 0.05, metalness: 0.1}),
		marble: s({map: tx.marble, roughness: 0.25}),
		darkStone: s({color: '#2e2d2b', roughness: 0.35}),
		hob: s({map: tx.hob, roughness: 0.15}),
		glassT: s({color: '#bcd8e4', transparent: true, opacity: 0.35, roughness: 0.05}),
		winGlass: s({color: '#9fcbe2', roughness: 0.1, metalness: 0.2}),
		lamp: s({color: '#fff3d6', emissive: new THREE.Color('#ffd79a'), emissiveIntensity: 1.6}),
		plant: s({color: '#4d7a3a', roughness: 0.85}),
		plant2: s({color: '#6b9a4a', roughness: 0.85}),
		pot: s({color: '#d6cfc4', roughness: 0.8}),
		potDark: s({color: '#3b3836', roughness: 0.8}),
		book: s({color: '#a23a2c', roughness: 0.8}),
		rug1: s({map: rep(tx.rug1), roughness: 1}),
		rug2: s({map: rep(tx.rug2), roughness: 1}),
		wood: s({map: tx.wood, roughness: 0.45}),
		tiles: s({map: tx.tiles, roughness: 0.3}),
		deck: s({map: tx.deck, roughness: 0.8}),
		stairs: s({map: tx.stairs, roughness: 0.8}),
		lift: s({color: '#7f8389', metalness: 0.6, roughness: 0.35}),
	};
};

const ITEMS: Item[] = [
	// cucina
	[0.15, 4.2, 0.78, 4.85, 0, 2.3, 'white'],
	[0.15, 4.85, 0.75, 7.6, 0, 0.88, 'white'],
	[0.12, 4.85, 0.78, 7.63, 0.88, 0.04, 'darkStone'],
	[0.3, 5.55, 0.62, 6.2, 0.9, 0.025, 'steel', 0.06],
	[0.24, 6.55, 0.7, 7.2, 0.92, 0.012, 'hob'],
	[1.9, 4.9, 3.6, 5.6, 0, 0.9, 'white', 0.03],
	[1.85, 4.85, 3.65, 5.65, 0.9, 0.04, 'marble', 0.02],
	// pranzo
	[5.15, 6.6, 7.45, 7.6, 0.72, 0.05, 'walnut', 0.03],
	// TV e soggiorno
	[0.1, 8.1, 0.5, 9.7, 0, 0.45, 'walnut'],
	[0.16, 8.35, 0.22, 9.45, 0.45, 0.68, 'black'],
	[1.0, 7.7, 3.05, 9.75, 0.005, 0.012, 'rug1'],
	[2.85, 7.45, 3.75, 9.88, 0, 0.42, 'fabricGrey', 0.08],
	[3.48, 7.45, 3.88, 9.88, 0, 0.82, 'fabricGrey', 0.08],
	[1.95, 9.0, 2.86, 9.88, 0, 0.42, 'fabricGrey', 0.08],
	[1.95, 9.52, 2.86, 9.9, 0, 0.82, 'fabricGrey', 0.08],
	[2.92, 7.55, 3.46, 8.4, 0.42, 0.14, 'fabricLight', 0.06],
	[2.92, 8.45, 3.46, 9.3, 0.42, 0.14, 'fabricLight', 0.06],
	[2.05, 9.05, 2.8, 9.5, 0.42, 0.14, 'fabricLight', 0.06],
	[3.22, 7.6, 3.46, 8.05, 0.5, 0.36, 'pillowOchre', 0.08],
	[2.2, 9.28, 2.65, 9.5, 0.5, 0.36, 'pillowTeal', 0.08],
	[1.7, 8.42, 2.1, 8.7, 0.38, 0.04, 'book'],
	// camera
	[0.05, 0.95, 0.16, 2.85, 0, 1.0, 'fabricBeige', 0.03],
	[0.12, 1.05, 2.2, 2.75, 0, 0.3, 'oak', 0.03],
	[0.17, 1.1, 2.15, 2.7, 0.3, 0.22, 'linen', 0.06],
	[0.8, 1.07, 2.18, 2.73, 0.45, 0.11, 'duvetSage', 0.05],
	[1.72, 1.05, 2.02, 2.75, 0.54, 0.04, 'throwRust', 0.02],
	[0.25, 1.2, 0.68, 1.86, 0.52, 0.15, 'pillow', 0.07],
	[0.25, 1.94, 0.68, 2.6, 0.52, 0.15, 'pillow', 0.07],
	[0.1, 0.48, 0.52, 0.95, 0, 0.5, 'oak', 0.02],
	[0.1, 2.85, 0.52, 3.32, 0, 0.5, 'oak', 0.02],
	[3.75, 0.2, 4.28, 2.8, 0, 2.3, 'white'],
	[2.35, 1.2, 3.5, 2.6, 0.005, 0.012, 'rug2'],
	// bagno
	[4.55, 0.15, 6.85, 0.92, 0, 0.58, 'ceramic', 0.14],
	[4.7, 0.28, 6.7, 0.79, 0.5, 0.06, 'water', 0.12],
	[4.48, 1.72, 4.66, 2.22, 0, 0.8, 'ceramic', 0.04],
	[6.4, 1.15, 6.92, 2.25, 0, 0.85, 'walnut'],
	[6.5, 1.42, 6.86, 1.98, 0.85, 0.12, 'ceramic', 0.05],
	// ripostiglio
	[5.9, 3.25, 6.55, 3.9, 0, 0.85, 'white', 0.03],
	[4.5, 3.4, 5.4, 3.92, 0, 1.8, 'oak'],
	// studio
	[7.3, 0.2, 9.1, 0.85, 0.72, 0.04, 'oak', 0.01],
	[7.9, 0.33, 8.35, 0.66, 0.76, 0.02, 'steel', 0.01],
	[9.98, 0.4, 10.33, 3.4, 0, 2.0, 'walnut'],
	[7.15, 2.1, 7.95, 3.8, 0, 0.45, 'fabricBeige', 0.08],
	[7.08, 2.1, 7.34, 3.8, 0, 0.82, 'fabricBeige', 0.08],
	[7.4, 2.25, 7.85, 2.75, 0.45, 0.3, 'pillowTeal', 0.08],
	// matrimoniale
	[10.45, 1.2, 10.6, 3.2, 0, 1.1, 'fabricGrey', 0.03],
	[10.55, 1.3, 12.6, 3.1, 0, 0.3, 'walnut', 0.03],
	[10.6, 1.35, 12.55, 3.05, 0.3, 0.22, 'linen', 0.06],
	[11.15, 1.33, 12.58, 3.07, 0.45, 0.11, 'duvetCream', 0.05],
	[12.12, 1.31, 12.45, 3.09, 0.54, 0.04, 'throwNavy', 0.02],
	[10.7, 1.45, 11.12, 2.15, 0.52, 0.15, 'pillow', 0.07],
	[10.7, 2.25, 11.12, 2.95, 0.52, 0.15, 'pillow', 0.07],
	[10.5, 0.7, 10.95, 1.15, 0, 0.5, 'walnut', 0.02],
	[10.5, 3.25, 10.95, 3.7, 0, 0.5, 'walnut', 0.02],
	[11.6, 4.7, 13.85, 5.25, 0, 2.3, 'oak'],
	[12.9, 0.3, 13.75, 1.15, 0, 0.42, 'leather', 0.1],
	[13.45, 0.3, 13.8, 1.15, 0, 0.8, 'leather', 0.08],
	[12.85, 1.5, 13.8, 3.1, 0.005, 0.012, 'rug1'],
	// disimpegno
	[6.0, 4.08, 7.4, 4.42, 0, 0.8, 'walnut'],
	// bagno 2
	[10.05, 7.45, 10.92, 8.32, 0, 0.05, 'ceramic'],
	[9.98, 7.4, 10.04, 8.32, 0, 2.0, 'glassT'],
	[8.85, 7.6, 9.03, 8.05, 0, 0.8, 'ceramic', 0.04],
	[8.85, 5.95, 9.35, 6.95, 0, 0.85, 'walnut'],
	[8.9, 6.2, 9.3, 6.7, 0.85, 0.12, 'ceramic', 0.05],
	// lavanderia
	[9.0, 9.2, 9.65, 9.85, 0, 0.85, 'white', 0.03],
	[9.7, 9.2, 10.35, 9.85, 0, 0.85, 'white', 0.03],
	[10.5, 8.55, 10.9, 9.85, 0, 1.8, 'oak'],
	// camera 2
	[12.9, 6.0, 13.88, 8.05, 0, 0.3, 'oak', 0.03],
	[12.95, 6.05, 13.83, 8.0, 0.3, 0.2, 'linen', 0.05],
	[12.93, 6.6, 13.85, 8.03, 0.42, 0.1, 'duvetMustard', 0.05],
	[13.05, 6.12, 13.75, 6.5, 0.48, 0.13, 'pillow', 0.06],
	[11.2, 5.55, 12.4, 6.05, 0.72, 0.04, 'white'],
	[11.1, 6.6, 11.65, 8.4, 0, 2.2, 'white'],
	[11.9, 7.0, 12.8, 8.6, 0.005, 0.012, 'rug2'],
	// terrazzo
	[1.2, 10.95, 3.1, 11.6, 0, 0.4, 'fabricLight', 0.08],
	[1.2, 11.35, 3.1, 11.62, 0, 0.75, 'fabricLight', 0.06],
	[5.0, 11.2, 8.2, 11.62, 0, 0.5, 'potDark'],
];
// sedie da pranzo
[5.6, 6.3, 7.0].forEach((x) => {
	ITEMS.push([x - 0.22, 6.18, x + 0.22, 6.58, 0.43, 0.06, 'fabricBeige', 0.03]);
	ITEMS.push([x - 0.22, 6.12, x + 0.22, 6.2, 0.43, 0.45, 'fabricBeige', 0.02]);
	ITEMS.push([x - 0.22, 7.62, x + 0.22, 8.02, 0.43, 0.06, 'fabricBeige', 0.03]);
	ITEMS.push([x - 0.22, 8.0, x + 0.22, 8.08, 0.43, 0.45, 'fabricBeige', 0.02]);
});

const CYLS: Cyl[] = [
	[2.2, 5.95, 0.2, 0, 0.75, 'black'],
	[2.75, 5.95, 0.2, 0, 0.75, 'black'],
	[3.3, 5.95, 0.2, 0, 0.75, 'black'],
	[1.9, 8.6, 0.45, 0, 0.38, 'oak'],
	[5.8, 7.1, 0.22, 1.75, 0.08, 'lamp'],
	[6.8, 7.1, 0.22, 1.75, 0.08, 'lamp'],
	[0.31, 0.72, 0.13, 0.5, 0.32, 'lamp'],
	[0.31, 3.08, 0.13, 0.5, 0.32, 'lamp'],
	[10.72, 0.92, 0.13, 0.5, 0.32, 'lamp'],
	[10.72, 3.47, 0.13, 0.5, 0.32, 'lamp'],
	[4.95, 1.97, 0.22, 0, 0.42, 'ceramic', 1.35],
	[9.28, 7.82, 0.2, 0, 0.42, 'ceramic', 1.35],
	[8.2, 1.25, 0.28, 0, 0.5, 'black'],
	[11.8, 6.4, 0.24, 0, 0.45, 'fabricBlue'],
	[3.7, 10.95, 0.38, 0, 0.72, 'teak'],
	[4.3, 11.25, 0.22, 0, 0.45, 'teak'],
	[13.55, 9.6, 0.2, 1.4, 0.3, 'lamp'],
];
// piante [x, y, raggio chioma]
const PLANTS: [number, number, number][] = [
	[4.1, 9.55, 0.5],
	[8.4, 5.85, 0.42],
	[9.65, 3.6, 0.38],
	[13.6, 4.4, 0.35],
	[5.6, 11.4, 0.32],
	[6.6, 11.4, 0.36],
	[7.6, 11.4, 0.32],
	[0.5, 9.75, 0.35],
];

const buildStatic = () => {
	const wood = new Geo();
	const tiles = new Geo();
	const deck = new Geo();
	ROOMS.forEach((r) => r.rects.forEach(([x0, y0, x1, y1]) => (r.floor === 'wood' ? wood : tiles).floor(x0, y0, x1, y1, 0.004, 2)));
	deck.floor(BAL.x0, BD + 0.15, BAL.x1, BAL.z1 - 0.05, 0.004, 2);
	// muri interni
	const walls = new Geo();
	INNER.forEach(([a, b]) => {
		const t = 0.06;
		walls.box(Math.min(a[0], b[0]) - t, 0, Math.min(a[1], b[1]) - t, Math.max(a[0], b[0]) + t, WALL_H, Math.max(a[1], b[1]) + t, 2);
	});
	// muri perimetrali con aperture finestrate
	const win = new Geo();
	const t = 0.15;
	const side = (s: 'N' | 'S' | 'W' | 'E', from: number, to: number) => {
		const ws = WINDOWS.filter((w) => w[0] === s).map((w) => [w[1], w[2]]).sort((a, b) => a[0] - b[0]);
		let c = from;
		const seg = (a: number, b: number, g: Geo, hh: number, y0 = 0) => {
			if (b - a < 0.01) return;
			if (s === 'N') g.box(a, y0, -t, b, hh, t, 2);
			if (s === 'S') g.box(a, y0, BD - t, b, hh, BD + t, 2);
			if (s === 'W') g.box(-t, y0, a, t, hh, b, 2);
			if (s === 'E') g.box(14 - t, y0, a, 14 + t, hh, b, 2);
		};
		ws.forEach(([a, b]) => {
			seg(c, a, walls, WALL_H);
			if (s === 'N' || s === 'S') win.box(a, 0, (s === 'N' ? 0 : BD) - 0.04, b, WALL_H - 0.05, (s === 'N' ? 0 : BD) + 0.04, 2);
			else win.box(-0.04, 0, a, 0.04, WALL_H - 0.05, b, 2);
			c = b;
		});
		seg(c, to, walls, WALL_H);
	};
	side('N', -t, 14 + t);
	side('S', -t, 14 + t);
	side('W', 0, BD);
	side('E', 0, BD);
	// porte
	const doors = new Geo();
	const doorList = DOORS.map(({h, r, a1}) => ({h, r, a1}));
	return {wood: wood.build(), tiles: tiles.build(), deck: deck.build(), walls: walls.build(), win: win.build(), doors: doors.build(), doorList};
};

export const Interior: React.FC<{tx: Textures; glow: number}> = ({tx, glow}) => {
	const M = useMemo(() => makeMats(tx), [tx]);
	const S = useMemo(buildStatic, []);
	const geos = useMemo(
		() =>
			ITEMS.map(([x0, y0, x1, y1, , h, , r]) => {
				const w = x1 - x0;
				const d = y1 - y0;
				const rr = r ? Math.min(r, w / 2 - 0.001, d / 2 - 0.001, h / 2 - 0.001) : 0;
				return rr > 0.005 ? new RoundedBoxGeometry(w, h, d, 3, rr) : new THREE.BoxGeometry(w, h, d);
			}),
		[],
	);
	const cylGeo = useMemo(() => new THREE.CylinderGeometry(1, 1, 1, 28), []);
	const leaf = useMemo(() => new THREE.IcosahedronGeometry(1, 1), []);
	M.lamp.emissiveIntensity = 1.6 * glow;
	return (
		<group>
			<mesh geometry={S.wood} material={M.wood} receiveShadow />
			<mesh geometry={S.tiles} material={M.tiles} receiveShadow />
			<mesh geometry={S.deck} material={M.deck} receiveShadow />
			<mesh geometry={S.walls} material={M.wallTop} castShadow receiveShadow />
			<mesh geometry={S.win} material={M.winGlass} />
			{S.doorList.map(({h, r, a1}, i) => (
				<mesh key={'d' + i} position={[h[0] + (Math.cos(a1) * r) / 2, 1.05, h[1] + (Math.sin(a1) * r) / 2]} rotation-y={-a1} material={M.oak} castShadow>
					<boxGeometry args={[r, 2.1, 0.04]} />
				</mesh>
			))}
			{ITEMS.map(([x0, y0, x1, y1, z0, h, m], i) => (
				<mesh key={i} geometry={geos[i]} material={M[m]} position={[(x0 + x1) / 2, z0 + h / 2, (y0 + y1) / 2]} castShadow receiveShadow />
			))}
			{CYLS.map(([cx, cy, r, z0, h, m, sy], i) => (
				<mesh key={'c' + i} geometry={cylGeo} material={M[m]} position={[cx, z0 + h / 2, cy]} scale={[r * (sy ?? 1), h, r]} castShadow receiveShadow />
			))}
			{PLANTS.map(([x, y, r], i) => (
				<group key={'p' + i} position={[x, 0, y]}>
					<mesh geometry={cylGeo} material={M.pot} position={[0, 0.22, 0]} scale={[r * 0.55, 0.44, r * 0.55]} castShadow />
					<mesh geometry={leaf} material={M.plant} position={[0, 0.75, 0]} scale={[r, r * 0.8, r]} castShadow />
					<mesh geometry={leaf} material={M.plant2} position={[r * 0.3, 0.95, -r * 0.2]} scale={[r * 0.6, r * 0.5, r * 0.6]} castShadow />
					<mesh geometry={leaf} material={M.plant2} position={[-r * 0.3, 0.9, r * 0.25]} scale={[r * 0.55, r * 0.5, r * 0.55]} castShadow />
				</group>
			))}
		</group>
	);
};

// vano scala tra i due alloggi
export const Core: React.FC<{tx: Textures}> = ({tx}) => {
	const M = useMemo(() => makeMats(tx), [tx]);
	return (
		<group>
			<mesh rotation-x={-Math.PI / 2} position={[15, 0.004, 3.6]} material={M.stairs} receiveShadow>
				<planeGeometry args={[2.4, 4.2]} />
			</mesh>
			<mesh rotation-x={-Math.PI / 2} position={[15, 0.004, 8.0]} material={M.tiles} receiveShadow>
				<planeGeometry args={[2.0, 4.0]} />
			</mesh>
			<mesh position={[15, 1.35, 6.3]} material={M.lift} castShadow>
				<boxGeometry args={[1.6, 2.7, 0.9]} />
			</mesh>
			<mesh position={[13.9, 1.35, 5]} material={M.wallTop}>
				<boxGeometry args={[0.2, 2.7, 10.3]} />
			</mesh>
			<mesh position={[16.1, 1.35, 5]} material={M.wallTop}>
				<boxGeometry args={[0.2, 2.7, 10.3]} />
			</mesh>
		</group>
	);
};
