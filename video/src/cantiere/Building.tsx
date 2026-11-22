import React, {useMemo} from 'react';
import * as THREE from 'three';
import {Geo, Textures} from './tex';
import {BAL, BD, BW, F, H, LEVELS, LOT, PIT, SLAB, T, ease, inC, lin, outC} from './plan';
import {Trees, TreeInst} from './City';

// Il cantiere: terreno, scavo, fondazioni, struttura in c.a., facciate, copertura, giardino

const COLS_X = [0.3, 5, 10, 13.8, 16.2, 20, 25, 29.7];
const COLS_Z = [0.3, 5, 9.7];
const LIT_LEVELS = [0.45, 0.0, 0.65, 0.3, 0.0, 1, 0.55, 0.0, 0.7, 0.35];

const buildGeos = () => {
	// ---- struttura ----
	const slab = new Geo().box(-0.25, 0, -0.25, BW + 0.25, SLAB, BD + 0.25, 3).build();
	const cant = new Geo()
		.box(BAL.x0, 0.08, BD + 0.25, BAL.x1, SLAB, BAL.z1, 3)
		.box(BW - BAL.x1, 0.08, BD + 0.25, BW - BAL.x0, SLAB, BAL.z1, 3)
		.build();
	const colG = new Geo();
	COLS_X.forEach((x) => COLS_Z.forEach((z) => colG.box(x - 0.2, 0, z - 0.2, x + 0.2, 1, z + 0.2, 3)));
	const cols = colG.build();
	const core = new Geo().box(13.6, 0, 2.4, 16.4, 1, 7.6, 3).build();

	// ---- facciate (per piano, altezza H - SLAB, base y = 0) ----
	const hF = H - SLAB;
	const glass = new Geo();
	const frame = new Geo();
	const wall = new Geo();
	const band = new Geo();
	const rail = new Geo();
	const railTop = new Geo();
	// fronte (z = BD): vetrate a tutta altezza negli alloggi, pannello pieno sul vano scala
	const front = (x0: number, x1: number) => {
		glass.quad([x0, 0, BD + 0.02], [x1 - x0, 0, 0], [0, hF, 0]);
		const n = Math.round((x1 - x0) / 1.45);
		for (let k = 0; k <= n; k++) {
			const x = x0 + ((x1 - x0) * k) / n;
			frame.box(x - 0.035, 0, BD, x + 0.035, hF, BD + 0.09);
		}
		frame.box(x0, 2.35, BD, x1, 2.41, BD + 0.08);
	};
	front(0.25, 13.6);
	front(16.4, BW - 0.25);
	wall.box(13.6, 0, BD - 0.05, 16.4, hF, BD + 0.06, 2);
	// retro e fianchi: muratura bianca con finestre a nastro
	wall.box(-0.06, 0, -0.06, BW + 0.06, hF, 0.05, 2, 'z');
	wall.box(-0.06, 0, -0.06, 0.05, hF, BD + 0.06, 2, 'x');
	wall.box(BW - 0.05, 0, -0.06, BW + 0.06, hF, BD + 0.06, 2, 'X');
	for (let x = 1; x < BW - 1; x += 3.2) {
		if (x > 13 && x < 16.5) continue;
		glass.quad([x + 1.7, 0.85, -0.08], [-1.7, 0, 0], [0, 1.6, 0]);
		frame.box(x - 0.04, 0.8, -0.12, x + 1.74, 0.85, -0.04);
	}
	[
		[1.2, 3.4],
		[6, 8.5],
	].forEach(([a, b]) => {
		glass.quad([-0.08, 0.85, a], [0, 0, b - a], [0, 1.6, 0]);
		glass.quad([BW + 0.08, 0.85, b], [0, 0, a - b], [0, 1.6, 0]);
	});
	// fascia marcapiano in pietra chiara
	band.box(-0.32, -0.04, -0.32, BW + 0.32, SLAB + 0.04, BD + 0.32, 2, 'XxZz');
	// parapetti in vetro dei balconi
	[
		[BAL.x0, BAL.x1],
		[BW - BAL.x1, BW - BAL.x0],
	].forEach(([a, b]) => {
		rail.box(a, 0, BAL.z1 - 0.05, b, 1.05, BAL.z1 - 0.02, 1);
		rail.box(a, 0, BD + 0.3, a + 0.03, 1.05, BAL.z1 - 0.02, 1);
		rail.box(b - 0.03, 0, BD + 0.3, b, 1.05, BAL.z1 - 0.02, 1);
		railTop.box(a, 1.05, BAL.z1 - 0.07, b, 1.1, BAL.z1, 1);
		band.box(a - 0.02, -0.26, BAL.z1 - 0.02, b + 0.02, 0.04, BAL.z1 + 0.04, 2, 'XxZ');
	});

	// piano terra: vetrina continua e ingresso
	const g0glass = new Geo().quad([0.25, 0, BD + 0.02], [BW - 0.5, 0, 0], [0, hF, 0]).build();
	const g0frame = new Geo();
	for (let x = 0.25; x <= BW - 0.2; x += 2.4) g0frame.box(x - 0.05, 0, BD, x + 0.05, hF, BD + 0.1);
	g0frame.box(0.25, 2.6, BD, BW - 0.25, 2.68, BD + 0.1);
	const g0stone = new Geo()
		.box(-0.08, 0, -0.08, BW + 0.08, hF, 0.06, 1.6, 'z')
		.box(-0.08, 0, -0.08, 0.06, hF, BD + 0.08, 1.6, 'x')
		.box(BW - 0.06, 0, -0.08, BW + 0.08, hF, BD + 0.08, 1.6, 'X')
		.box(-0.08, 0, BD - 0.1, 0.25, hF, BD + 0.1, 1.6)
		.box(BW - 0.25, 0, BD - 0.1, BW + 0.08, hF, BD + 0.1, 1.6)
		.build();
	const canopy = new Geo().box(12.4, 2.9, BD, 17.6, 3.12, BD + 2.6, 2).build();

	// copertura
	const parapet = new Geo()
		.box(-0.3, 0, -0.3, BW + 0.3, 1.1, 0, 2)
		.box(-0.3, 0, BD, BW + 0.3, 1.1, BD + 0.3, 2)
		.box(-0.3, 0, 0, 0, 1.1, BD, 2)
		.box(BW, 0, 0, BW + 0.3, 1.1, BD, 2)
		.build();
	const roofCore = new Geo().box(13.4, 0, 2.2, 16.6, 3.0, 7.8, 2).build();
	const roofBand = new Geo().box(13.38, 2.45, 2.18, 16.62, 3.0, 7.82, 2, 'XxZz').build();
	const pv = new Geo();
	for (const [x0, x1] of [
		[1.2, 12.4],
		[17.6, 28.8],
	])
		for (let z = 1.0; z < 8.6; z += 1.55) pv.quad([x0, 0.25, z + 1.1], [x1 - x0, 0, 0], [0, 0.5, -1.0], 1);
	const green = new Geo().floor(0.4, 0.4, 13.2, 9.6, 0.12, 3).floor(16.8, 0.4, BW - 0.4, 9.6, 0.12, 3).build();

	return {
		slab,
		cant,
		cols,
		core,
		glass: glass.build(),
		frame: frame.build(),
		wall: wall.build(),
		band: band.build(),
		rail: rail.build(),
		railTop: railTop.build(),
		g0glass,
		g0frame: g0frame.build(),
		g0stone,
		canopy,
		parapet,
		roofCore,
		roofBand,
		pv: pv.build(),
		green,
	};
};

// terreno del lotto attorno allo scavo + giardino finale
const buildLot = () => {
	const dirt = new Geo();
	const sidewalk = new Geo();
	const e = 4;
	const y = 0.15;
	// marciapiede perimetrale
	sidewalk.box(LOT.x0, 0, LOT.z0, LOT.x1, y, LOT.z0 + e, 4, 'XxZzY');
	sidewalk.box(LOT.x0, 0, LOT.z1 - e, LOT.x1, y, LOT.z1, 4, 'XxZzY');
	sidewalk.box(LOT.x0, 0, LOT.z0 + e, LOT.x0 + e, y, LOT.z1 - e, 4, 'XxZzY');
	sidewalk.box(LOT.x1 - e, 0, LOT.z0 + e, LOT.x1, y, LOT.z1 - e, 4, 'XxZzY');
	const ix0 = LOT.x0 + e;
	const ix1 = LOT.x1 - e;
	const iz0 = LOT.z0 + e;
	const iz1 = LOT.z1 - e;
	// terra attorno all'impronta dello scavo
	dirt.floor(ix0, iz0, ix1, PIT.z0, y, 6);
	dirt.floor(ix0, PIT.z1, ix1, iz1, y, 6);
	dirt.floor(ix0, PIT.z0, PIT.x0, PIT.z1, y, 6);
	dirt.floor(PIT.x1, PIT.z0, ix1, PIT.z1, y, 6);
	// prato a riquadri (comparirà a fine lavori)
	const lawns: [number, number, number, number][] = [
		[ix0, iz0, ix1, PIT.z0 - 0.6],
		[ix0, PIT.z0 - 0.6, PIT.x0 - 0.6, iz1],
		[PIT.x1 + 0.6, PIT.z0 - 0.6, ix1, iz1],
		[PIT.x0 - 0.6, PIT.z1 + 0.6, 12, iz1],
		[18, PIT.z1 + 0.6, PIT.x1 + 0.6, iz1],
	];
	const trees: TreeInst[] = [
		[-5, -10],
		[3, -11],
		[12, -10.5],
		[21, -11],
		[30, -10],
		[37, -9],
		[-5, 2],
		[36, 3],
		[-4, 16],
		[3.5, 18],
		[26.5, 18],
		[35, 16],
	].map(([x, z], i) => ({x, z, h: 6 + (i % 3), r: 2.2 + (i % 4) * 0.25, c: (i * 0.37) % 1}));
	return {dirt: dirt.build(), sidewalk: sidewalk.build(), lawns, trees};
};

export const Building: React.FC<{f: number; tx: Textures; night: number}> = ({f, tx, night}) => {
	const G = useMemo(buildGeos, []);
	const L = useMemo(buildLot, []);
	const M = useMemo(() => {
		const concrete = new THREE.MeshStandardMaterial({map: tx.concrete, roughness: 0.95});
		const white = new THREE.MeshStandardMaterial({color: '#eeeae3', roughness: 0.55});
		const stone = new THREE.MeshStandardMaterial({color: '#e3ddd2', roughness: 0.5});
		const darkStone = new THREE.MeshStandardMaterial({color: '#57524c', roughness: 0.6});
		const frame = new THREE.MeshStandardMaterial({color: '#2a2d31', metalness: 0.7, roughness: 0.35});
		const railGlass = new THREE.MeshStandardMaterial({color: '#a8c8d8', metalness: 0.3, roughness: 0.05, transparent: true, opacity: 0.32});
		const red = new THREE.MeshStandardMaterial({color: '#c4271f', roughness: 0.5});
		const pv = new THREE.MeshStandardMaterial({color: '#1d2c3f', metalness: 0.6, roughness: 0.2, side: THREE.DoubleSide});
		const green = new THREE.MeshStandardMaterial({map: tx.grass, roughness: 1});
		const dirt = new THREE.MeshStandardMaterial({map: tx.dirt, roughness: 1});
		const dirtWall = new THREE.MeshStandardMaterial({map: tx.dirt, roughness: 1, color: '#9a8574'});
		const paving = new THREE.MeshStandardMaterial({map: tx.paving, roughness: 0.9});
		const glasses = Array.from({length: LEVELS}, () =>
			new THREE.MeshStandardMaterial({color: '#6f8a99', metalness: 0.55, roughness: 0.07, envMapIntensity: 5, emissive: new THREE.Color('#ffcf8c'), emissiveIntensity: 0}),
		);
		return {concrete, white, stone, darkStone, frame, railGlass, red, pv, green, dirt, dirtWall, paving, glasses};
	}, [tx]);

	// ---- tempi ----
	const dig = ease(f, T.dig);
	const pour = ease(f, T.pour, outC);
	const pd = PIT.depth * dig;
	const coreH = Math.min(LEVELS * H + 3, lin(f, T.core) * (LEVELS * H + 3));
	const lift = ease(f, T.lift, inC);
	const facOff = ease(f, T.facOff);
	const fl = ease(f, T.floorLit);

	// luci delle finestre
	M.glasses.forEach((m, i) => {
		const base = LIT_LEVELS[i] * night * 0.55;
		m.emissiveIntensity = i === F ? Math.max(base, fl * 1.6) : base;
		if (i === F) m.emissive.set(fl > 0.5 ? '#ffd39a' : '#ffcf8c');
	});

	const levels: React.ReactNode[] = [];
	for (let i = 0; i <= LEVELS; i++) {
		const tS = f - (T.struct0 + i * T.structStep);
		if (tS < 0) continue;
		const slabS = ease(tS, [0, 9], outC);
		const colS = ease(tS, [6, 15], outC);
		const tF = f - (T.fac0 + i * T.facStep);
		const facS = ease(tF, [0, T.facDur], outC);
		let yOff = 0;
		let vis = true;
		if (i > F) {
			yOff = lift * (34 + (i - F) * 7);
			if (yOff > 70) vis = false;
		}
		const y = i * H + yOff;
		if (!vis) continue;
		const isRoof = i === LEVELS;
		const isF = i === F;
		const facScale = isF ? facS * (1 - facOff) : facS;
		const showCols = !isRoof && colS > 0 && !(isF && f > T.interior);
		levels.push(
			<group key={i} position={[0, y, 0]}>
				{/* solaio: getto che avanza da sinistra a destra */}
				<group position={[-0.25, 0, 0]} scale={[Math.max(0.001, slabS), 1, 1]}>
					<group position={[0.25, 0, 0]}>
						<mesh geometry={G.slab} material={M.concrete} castShadow receiveShadow />
						{i >= 1 && !isRoof && <mesh geometry={G.cant} material={M.concrete} castShadow receiveShadow />}
					</group>
				</group>
				{showCols && (
					<mesh geometry={G.cols} material={M.concrete} position={[0, SLAB, 0]} scale={[1, Math.max(0.001, colS * (H - SLAB)), 1]} castShadow receiveShadow />
				)}
				{!isRoof && facScale > 0.001 && (
					<group position={[0, SLAB, 0]} scale={[1, facScale, 1]}>
						{i === 0 ? (
							<>
								<mesh geometry={G.g0glass} material={M.glasses[0]} />
								<mesh geometry={G.g0frame} material={M.frame} castShadow />
								<mesh geometry={G.g0stone} material={M.darkStone} castShadow receiveShadow />
								<mesh geometry={G.canopy} material={M.red} position={[0, -SLAB, 0]} castShadow />
							</>
						) : (
							<>
								<mesh geometry={G.glass} material={M.glasses[i]} />
								<mesh geometry={G.frame} material={M.frame} castShadow />
								<mesh geometry={G.wall} material={M.white} castShadow receiveShadow />
								<mesh geometry={G.rail} material={M.railGlass} />
								<mesh geometry={G.railTop} material={M.frame} />
							</>
						)}
					</group>
				)}
				{facS > 0.001 && !(isF && facOff > 0.999) && <mesh geometry={G.band} material={M.stone} scale={[1, Math.max(0.001, facS), 1]} castShadow receiveShadow />}
				{isRoof && <Roof f={f} G={G} M={M} />}
			</group>,
		);
	}

	// vano scala/ascensore che anticipa la struttura
	const lawnS = ease(f, T.land, outC);
	const treeScale = L.trees.map((_, k) => ease(f, [T.land[0] + k * 3, T.land[0] + 40 + k * 3], outC));

	return (
		<group>
			{/* marciapiede e terreno */}
			<mesh geometry={L.sidewalk} material={M.paving} receiveShadow />
			<mesh geometry={L.dirt} material={M.dirt} receiveShadow />
			{/* scavo */}
			<group position={[0, 0.15, 0]}>
				{pd < 0.01 ? (
					<mesh rotation-x={-Math.PI / 2} position={[(PIT.x0 + PIT.x1) / 2, 0, (PIT.z0 + PIT.z1) / 2]} material={M.dirt} receiveShadow>
						<planeGeometry args={[PIT.x1 - PIT.x0, PIT.z1 - PIT.z0]} />
					</mesh>
				) : (
					<>
						<mesh rotation-x={-Math.PI / 2} position={[(PIT.x0 + PIT.x1) / 2, -pd, (PIT.z0 + PIT.z1) / 2]} material={M.dirt} receiveShadow>
							<planeGeometry args={[PIT.x1 - PIT.x0, PIT.z1 - PIT.z0]} />
						</mesh>
						{/* pareti dello scavo (rivolte verso l'interno) */}
						<mesh position={[(PIT.x0 + PIT.x1) / 2, -pd / 2, PIT.z0]} material={M.dirtWall} receiveShadow>
							<planeGeometry args={[PIT.x1 - PIT.x0, pd]} />
						</mesh>
						<mesh position={[(PIT.x0 + PIT.x1) / 2, -pd / 2, PIT.z1]} rotation-y={Math.PI} material={M.dirtWall} receiveShadow>
							<planeGeometry args={[PIT.x1 - PIT.x0, pd]} />
						</mesh>
						<mesh position={[PIT.x0, -pd / 2, (PIT.z0 + PIT.z1) / 2]} rotation-y={Math.PI / 2} material={M.dirtWall} receiveShadow>
							<planeGeometry args={[PIT.z1 - PIT.z0, pd]} />
						</mesh>
						<mesh position={[PIT.x1, -pd / 2, (PIT.z0 + PIT.z1) / 2]} rotation-y={-Math.PI / 2} material={M.dirtWall} receiveShadow>
							<planeGeometry args={[PIT.z1 - PIT.z0, pd]} />
						</mesh>
						{pour > 0 && (
							<mesh position={[(PIT.x0 + PIT.x1) / 2, -pd + (pd * pour) / 2 - 0.01, (PIT.z0 + PIT.z1) / 2]} material={M.concrete} receiveShadow>
								<boxGeometry args={[PIT.x1 - PIT.x0 - 0.02, Math.max(0.01, pd * pour), PIT.z1 - PIT.z0 - 0.02]} />
							</mesh>
						)}
					</>
				)}
			</group>
			{/* struttura e facciate */}
			<group position={[0, 0.15, 0]}>
				{coreH > 0.05 && f < T.interior + 4 + 1000 && (
					<mesh geometry={G.core} material={M.concrete} scale={[1, coreH, 1]} castShadow receiveShadow visible={!(f > T.lift[0] + 12)} />
				)}
				{levels}
			</group>
			{/* giardino e alberi del lotto */}
			{lawnS > 0 &&
				L.lawns.map(([x0, z0, x1, z1], k) => {
					const s = Math.max(0.001, ease(f, [T.land[0] + k * 5, T.land[0] + 30 + k * 5], outC));
					return (
						<mesh key={k} rotation-x={-Math.PI / 2} position={[(x0 + x1) / 2, 0.17, (z0 + z1) / 2]} scale={[s, s, 1]} material={M.green} receiveShadow>
							<planeGeometry args={[x1 - x0, z1 - z0]} />
						</mesh>
					);
				})}
			{lawnS > 0 && (
				<>
					<mesh rotation-x={-Math.PI / 2} position={[15, 0.175, (PIT.z1 + LOT.z1 - 4) / 2 + 0.3]} scale={[1, lawnS, 1]} material={M.paving} receiveShadow>
						<planeGeometry args={[6, LOT.z1 - 4 - PIT.z1 + 0.6]} />
					</mesh>
					<mesh rotation-x={-Math.PI / 2} position={[15, 0.172, 5]} scale={[lawnS, lawnS, 1]} material={M.paving} receiveShadow>
						<planeGeometry args={[BW + 3.2, BD + 3.2]} />
					</mesh>
				</>
			)}
			{lawnS > 0 && <Trees list={L.trees} scale={treeScale} night={night} />}
		</group>
	);
};

const Roof: React.FC<{f: number; G: ReturnType<typeof buildGeos>; M: Record<string, THREE.Material>}> = ({f, G, M}) => {
	const r = ease(f, T.roof, outC);
	if (r <= 0) return null;
	const s = Math.max(0.001, r);
	const pvS = Math.max(0.001, ease(f, [T.roof[0] + 15, T.roof[1] + 10], outC));
	return (
		<group position={[0, SLAB, 0]}>
			<mesh geometry={G.parapet} material={M.white} scale={[1, s, 1]} castShadow receiveShadow />
			<mesh geometry={G.green} material={M.green} receiveShadow scale={[1, s, 1]} />
			<mesh geometry={G.roofCore} material={M.white} scale={[1, s, 1]} castShadow receiveShadow />
			<mesh geometry={G.roofBand} material={M.red} scale={[1, s, 1]} />
			<mesh geometry={G.pv} material={M.pv} scale={[1, pvS, 1]} castShadow />
		</group>
	);
};
