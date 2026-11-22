import React, {useMemo} from 'react';
import * as THREE from 'three';
import {mergeVertices} from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import {Geo, rnd, setSeed, Textures} from './tex';
import {LOT} from './plan';

// Quartiere milanese: isolati a corte, strade, binari del tram, alberi, skyline lontano

const PX = 68;
const PZ = 58;
const CX = (LOT.x0 + LOT.x1) / 2; // 15
const CZ = (LOT.z0 + LOT.z1) / 2; // 4
const HB = 27; // mezza larghezza isolato
const HD = 22; // mezza profondità isolato
const R = 3;

export type TreeInst = {x: number; z: number; h: number; r: number; c: number};

const buildCity = () => {
	setSeed(101);
	const facN = [0, 1, 2, 3].map(() => new Geo());
	const facF = [0, 1, 2, 3].map(() => new Geo());
	const shopN = new Geo();
	const shopF = new Geo();
	const tilesG = new Geo();
	const gravelG = new Geo();
	const trimG = new Geo();
	const pavingG = new Geo();
	const grassG = new Geo();
	const markG = new Geo();
	const steelG = new Geo();
	const towerG = new Geo();
	const trees: TreeInst[] = [];

	const segBuilding = (x0: number, z0: number, x1: number, z1: number, near: boolean, alongX: boolean) => {
		const floors = 5 + Math.floor(rnd() * 4);
		const h = 4 + floors * 3.2;
		const v = Math.floor(rnd() * 4);
		(near ? shopN : shopF).box(x0, 0.15, z0, x1, 4, z1, 12.8, 'XxZz', 4);
		(near ? facN : facF)[v].box(x0, 4, z0, x1, h, z1, 12.8, 'XxZz');
		trimG.box(x0 - 0.25, h, z0 - 0.25, x1 + 0.25, h + 0.45, z1 + 0.25, 4, 'XxZzY');
		if (rnd() < 0.78) {
			trimG.gable(x0, x1, z0, z1, h + 0.45, 2.4, alongX, tilesG, trimG);
		} else {
			gravelG.floor(x0, z0, x1, z1, h + 0.46, 6);
			const bx = x0 + 2 + rnd() * Math.max(1, x1 - x0 - 6);
			const bz = z0 + 2 + rnd() * Math.max(1, z1 - z0 - 6);
			trimG.box(bx, h + 0.45, bz, bx + 3, h + 3, bz + 3, 4);
		}
	};

	const side = (a0: number, a1: number, b0: number, b1: number, alongX: boolean, near: boolean) => {
		let a = a0;
		while (a < a1 - 0.1) {
			let l = 10 + rnd() * 10;
			if (a1 - (a + l) < 8) l = a1 - a;
			if (alongX) segBuilding(a, b0, a + l, b1, near, true);
			else segBuilding(b0, a, b1, a + l, near, false);
			a += l;
		}
	};

	for (let bx = -R; bx <= R; bx++)
		for (let bz = -R; bz <= R; bz++) {
			if (bx === 0 && bz === 0) continue;
			const cx = CX + bx * PX;
			const cz = CZ + bz * PZ;
			const x0 = cx - HB;
			const x1 = cx + HB;
			const z0 = cz - HD;
			const z1 = cz + HD;
			const near = Math.abs(bx) <= 1 && Math.abs(bz) <= 1;
			pavingG.box(x0, 0, z0, x1, 0.15, z1, 4, 'XxZzY');
			const park = (bx === 0 && bz === 1) || (bx === 1 && bz === 1) || (bx === -2 && bz === -1) || (bx === 2 && bz === -2);
			if (park) {
				grassG.floor(x0 + 3, z0 + 3, x1 - 3, z1 - 3, 0.16, 4);
				pavingG.floor(cx - 1.5, z0 + 3, cx + 1.5, z1 - 3, 0.17, 4);
				pavingG.floor(x0 + 3, cz - 1.5, x1 - 3, cz + 1.5, 0.17, 4);
				for (let i = 0; i < 60; i++) {
					const x = x0 + 6 + rnd() * (2 * HB - 12);
					const z = z0 + 6 + rnd() * (2 * HD - 12);
					if (Math.abs(x - cx) < 3 || Math.abs(z - cz) < 3) continue;
					trees.push({x, z, h: 7 + rnd() * 6, r: 3 + rnd() * 2, c: rnd()});
				}
				continue;
			}
			const e = 3.5;
			const dp = 12;
			side(x0 + e, x1 - e, z0 + e, z0 + e + dp, true, near);
			side(x0 + e, x1 - e, z1 - e - dp, z1 - e, true, near);
			side(z0 + e + dp, z1 - e - dp, x0 + e, x0 + e + dp, false, near);
			side(z0 + e + dp, z1 - e - dp, x1 - e - dp, x1 - e, false, near);
			grassG.floor(x0 + e + dp, z0 + e + dp, x1 - e - dp, z1 - e - dp, 0.16, 4);
			for (let i = 0; i < 3; i++)
				trees.push({x: cx + (rnd() - 0.5) * 18, z: cz + (rnd() - 0.5) * 8, h: 7 + rnd() * 4, r: 2.6 + rnd() * 1.4, c: rnd()});
		}

	// anello di edifici più lontani e skyline
	for (let i = 0; i < 90; i++) {
		const a = rnd() * Math.PI * 2;
		const d = 250 + rnd() * 120;
		const x = CX + Math.cos(a) * d;
		const z = CZ + Math.sin(a) * d;
		const w = 14 + rnd() * 20;
		const dd = 12 + rnd() * 12;
		const h = 16 + rnd() * 14;
		facF[Math.floor(rnd() * 4)].box(x, 0, z, x + w, h, z + dd, 12.8, 'XxZz');
		gravelG.floor(x, z, x + w, z + dd, h, 6);
	}
	for (let i = 0; i < 26; i++) {
		const a = -2.6 + rnd() * 2.2; // soprattutto verso nord-ovest, dietro il cantiere
		const d = 650 + rnd() * 500;
		const x = CX + Math.cos(a) * d;
		const z = CZ + Math.sin(a) * d;
		const w = 18 + rnd() * 18;
		const h = 45 + rnd() * 120;
		towerG.box(x, 0, z, x + w, h, z + w * (0.7 + rnd() * 0.5), 24, 'XxZzY');
	}

	// strade: mezzerie, strisce pedonali, binari del tram
	for (let k = -R - 1; k <= R; k++) {
		const sx = CX + k * PX + PX / 2;
		for (let z = CZ - (R + 0.5) * PZ; z < CZ + (R + 0.5) * PZ; z += 6) markG.floor(sx - 0.08, z, sx + 0.08, z + 3, 0.02, 4);
		const sz = CZ + k * PZ + PZ / 2;
		for (let x = CX - (R + 0.5) * PX; x < CX + (R + 0.5) * PX; x += 6) {
			if (Math.abs(sz - (LOT.z1 + 7)) < 1) continue; // la via del tram non ha mezzeria
			markG.floor(x, sz - 0.08, x + 3, sz + 0.08, 0.02, 4);
		}
	}
	// strisce pedonali attorno al cantiere
	const zebra = (x: number, z: number, alongX: boolean) => {
		for (let i = 0; i < 7; i++) {
			if (alongX) markG.floor(x + i * 1.0, z - 2, x + i * 1.0 + 0.5, z + 2, 0.021, 4);
			else markG.floor(x - 2, z + i * 1.0, x + 2, z + i * 1.0 + 0.5, 0.021, 4);
		}
	};
	[LOT.x0 - 7, LOT.x1 + 7].forEach((x) => {
		zebra(x - 3.5, LOT.z0 - 3, true);
		zebra(x - 3.5, LOT.z1 + 3, true);
	});
	[LOT.z0 - 7, LOT.z1 + 7].forEach((z) => {
		zebra(LOT.x0 - 3, z - 3.5, false);
		zebra(LOT.x1 + 3, z - 3.5, false);
	});
	const tramZ = LOT.z1 + 7;
	[tramZ - 1.6, tramZ + 1.6].forEach((c) =>
		[c - 0.72, c + 0.72].forEach((r) => steelG.box(CX - (R + 0.5) * PX, 0, r - 0.04, CX + (R + 0.5) * PX, 0.05, r + 0.04, 4)),
	);

	// alberi lungo le strade
	for (let k = -R - 1; k <= R; k++) {
		const sx = CX + k * PX + PX / 2;
		const sz = CZ + k * PZ + PZ / 2;
		for (const off of [-8.5, 8.5]) {
			for (let z = CZ - R * PZ; z < CZ + R * PZ; z += 10) {
				const dz = (((z - CZ - PZ / 2) % PZ) + PZ) % PZ;
				if (dz < 10 || dz > PZ - 10) continue;
				trees.push({x: sx + off, z: z + rnd() * 2, h: 8 + rnd() * 3, r: 2.6 + rnd() * 1.2, c: rnd()});
			}
			for (let x = CX - R * PX; x < CX + R * PX; x += 10) {
				const dx = (((x - CX - PX / 2) % PX) + PX) % PX;
				if (dx < 10 || dx > PX - 10) continue;
				if (Math.abs(sz - tramZ) < 1 && off < 0 && x > LOT.x0 - 2 && x < LOT.x1 + 2) continue; // fronte del cantiere libero
				trees.push({x: x + rnd() * 2, z: sz + off, h: 8 + rnd() * 3, r: 2.6 + rnd() * 1.2, c: rnd()});
			}
		}
	}

	const b = (g: Geo) => g.build();
	return {
		facN: facN.map(b),
		facF: facF.map(b),
		shopN: b(shopN),
		shopF: b(shopF),
		tiles: b(tilesG),
		gravel: b(gravelG),
		trim: b(trimG),
		paving: b(pavingG),
		grass: b(grassG),
		mark: b(markG),
		steel: b(steelG),
		tower: b(towerG),
		trees,
	};
};

export const Trees: React.FC<{list: TreeInst[]; scale?: number[]; cast?: boolean; night: number}> = ({list, scale, cast = true, night}) => {
	const {trunks, crowns, crowns2} = useMemo(() => {
		const tg = new THREE.CylinderGeometry(0.16, 0.28, 1, 7);
		tg.translate(0, 0.5, 0);
		// chioma irregolare: icosaedro con vertici spostati
		const ico = new THREE.IcosahedronGeometry(1, 3);
		ico.deleteAttribute('uv');
		ico.deleteAttribute('normal');
		const cg = mergeVertices(ico);
		const pa = cg.attributes.position;
		const v = new THREE.Vector3();
		for (let i = 0; i < pa.count; i++) {
			v.fromBufferAttribute(pa, i);
			const n = 1 + 0.14 * Math.sin(v.x * 7.1 + v.y * 3.3) * Math.cos(v.z * 6.7 - v.y * 2.1) + 0.07 * Math.sin(v.x * 17 + v.z * 13) + 0.05 * Math.sin(v.y * 23 + v.x * 5);
			v.multiplyScalar(n);
			pa.setXYZ(i, v.x, v.y, v.z);
		}
		cg.computeVertexNormals();
		const trunks = new THREE.InstancedMesh(tg, new THREE.MeshStandardMaterial({color: '#5a4636', roughness: 0.95}), list.length);
		const cm = new THREE.MeshStandardMaterial({color: '#ffffff', roughness: 0.95});
		const crowns = new THREE.InstancedMesh(cg, cm, list.length);
		const crowns2 = new THREE.InstancedMesh(cg, cm, list.length);
		[trunks, crowns, crowns2].forEach((m) => {
			m.castShadow = cast;
			m.receiveShadow = true;
		});
		return {trunks, crowns, crowns2};
	}, [list, cast]);
	const m = new THREE.Matrix4();
	const q = new THREE.Quaternion();
	const col = new THREE.Color();
	list.forEach((t, i) => {
		const s = scale ? scale[i] : 1;
		const hh = t.h * s;
		m.compose(new THREE.Vector3(t.x, 0.15, t.z), q, new THREE.Vector3(s, hh * 0.55, s));
		trunks.setMatrixAt(i, m);
		m.compose(new THREE.Vector3(t.x, 0.15 + hh * 0.62, t.z), q, new THREE.Vector3(t.r * s, t.r * 0.82 * s, t.r * s));
		crowns.setMatrixAt(i, m);
		m.compose(new THREE.Vector3(t.x + t.r * 0.35 * s, 0.15 + hh * 0.8, t.z - t.r * 0.25 * s), q, new THREE.Vector3(t.r * 0.68 * s, t.r * 0.6 * s, t.r * 0.68 * s));
		crowns2.setMatrixAt(i, m);
		const g = 0.2 + t.c * 0.08;
		col.setRGB((0.11 + t.c * 0.07) * (1 - night * 0.3), g * (1 - night * 0.3), (0.06 + t.c * 0.03) * (1 - night * 0.3));
		crowns.setColorAt(i, col);
		col.multiplyScalar(1.18);
		crowns2.setColorAt(i, col);
	});
	[trunks, crowns, crowns2].forEach((x) => {
		x.instanceMatrix.needsUpdate = true;
		if (x.instanceColor) x.instanceColor.needsUpdate = true;
	});
	return (
		<>
			<primitive object={trunks} />
			<primitive object={crowns} />
			<primitive object={crowns2} />
		</>
	);
};

export const City: React.FC<{tx: Textures; night: number; lamps: number}> = ({tx, night, lamps}) => {
	const g = useMemo(buildCity, []);
	const mats = useMemo(() => {
		const fac = tx.facades.map(
			(fa) => new THREE.MeshStandardMaterial({map: fa.map, emissiveMap: fa.em, emissive: new THREE.Color('#ffcf94'), emissiveIntensity: 0, roughness: 0.92}),
		);
		const shop = new THREE.MeshStandardMaterial({map: tx.shop, emissiveMap: tx.shopEm, emissive: new THREE.Color('#ffd7a8'), emissiveIntensity: 0, roughness: 0.8});
		const tiles = new THREE.MeshStandardMaterial({map: tx.roofTiles, roughness: 0.85});
		const gravel = new THREE.MeshStandardMaterial({map: tx.gravel, roughness: 0.95});
		const trim = new THREE.MeshStandardMaterial({color: '#e7dfd1', roughness: 0.8});
		const paving = new THREE.MeshStandardMaterial({map: tx.paving, roughness: 0.9});
		const grass = new THREE.MeshStandardMaterial({map: tx.grass, roughness: 1});
		const mark = new THREE.MeshStandardMaterial({color: '#dedbd3', roughness: 0.7});
		const steel = new THREE.MeshStandardMaterial({color: '#a3a7ad', metalness: 0.85, roughness: 0.3});
		const tower = new THREE.MeshStandardMaterial({map: tx.tower, emissiveMap: tx.towerEm, emissive: new THREE.Color('#ffe2b0'), emissiveIntensity: 0, metalness: 0.55, roughness: 0.25});
		const asphalt = new THREE.MeshStandardMaterial({map: tx.asphalt, roughness: 0.95});
		const t2 = tx.asphalt.clone();
		t2.repeat.set(400, 400);
		t2.needsUpdate = true;
		asphalt.map = t2;
		return {fac, shop, tiles, gravel, trim, paving, grass, mark, steel, tower, asphalt};
	}, [tx]);
	mats.fac.forEach((m) => (m.emissiveIntensity = night * 1.25));
	mats.shop.emissiveIntensity = night * 1.1;
	mats.tower.emissiveIntensity = night * 1.0;

	const lampData = useMemo(() => {
		const pts: [number, number][] = [];
		for (let x = LOT.x0 - 60; x < LOT.x1 + 70; x += 16) {
			pts.push([x, LOT.z1 + 0.8]);
			pts.push([x + 8, LOT.z1 + 13.2]);
		}
		for (let z = LOT.z0 - 40; z < LOT.z1 + 40; z += 16) {
			pts.push([LOT.x1 + 0.8, z]);
			pts.push([LOT.x0 - 0.8, z + 8]);
		}
		const pole = new THREE.CylinderGeometry(0.07, 0.1, 7, 6);
		pole.translate(0, 3.5, 0);
		const head = new THREE.BoxGeometry(0.5, 0.18, 1.0);
		const poles = new THREE.InstancedMesh(pole, new THREE.MeshStandardMaterial({color: '#2d3034', metalness: 0.6, roughness: 0.5}), pts.length);
		const hm = new THREE.MeshStandardMaterial({color: '#3a3d40', emissive: new THREE.Color('#ffe0a8'), emissiveIntensity: 0});
		const heads = new THREE.InstancedMesh(head, hm, pts.length);
		const m = new THREE.Matrix4();
		pts.forEach(([x, z], i) => {
			m.makeTranslation(x, 0.15, z);
			poles.setMatrixAt(i, m);
			m.makeTranslation(x, 7.05, z);
			heads.setMatrixAt(i, m);
		});
		poles.castShadow = true;
		return {poles, heads, hm};
	}, []);
	lampData.hm.emissiveIntensity = lamps * 4;

	return (
		<group>
			<mesh rotation-x={-Math.PI / 2} position={[CX, 0, CZ]} receiveShadow material={mats.asphalt}>
				<planeGeometry args={[2400, 2400]} />
			</mesh>
			<mesh geometry={g.paving} material={mats.paving} receiveShadow />
			<mesh geometry={g.grass} material={mats.grass} receiveShadow />
			<mesh geometry={g.mark} material={mats.mark} receiveShadow />
			<mesh geometry={g.steel} material={mats.steel} />
			{g.facN.map((geo, i) => (
				<mesh key={'n' + i} geometry={geo} material={mats.fac[i]} castShadow receiveShadow />
			))}
			{g.facF.map((geo, i) => (
				<mesh key={'f' + i} geometry={geo} material={mats.fac[i]} receiveShadow />
			))}
			<mesh geometry={g.shopN} material={mats.shop} castShadow receiveShadow />
			<mesh geometry={g.shopF} material={mats.shop} receiveShadow />
			<mesh geometry={g.tiles} material={mats.tiles} castShadow receiveShadow />
			<mesh geometry={g.gravel} material={mats.gravel} receiveShadow />
			<mesh geometry={g.trim} material={mats.trim} castShadow receiveShadow />
			<mesh geometry={g.tower} material={mats.tower} />
			<Trees list={g.trees} night={night} />
			<primitive object={lampData.poles} />
			<primitive object={lampData.heads} />
		</group>
	);
};
