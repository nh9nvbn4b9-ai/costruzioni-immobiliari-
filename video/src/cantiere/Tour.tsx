import React, {useEffect, useMemo, useState} from 'react';
import * as THREE from 'three';
import {Sky} from 'three/examples/jsm/objects/Sky.js';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import {AbsoluteFill, continueRender, delayRender, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import {makeTextures, Textures} from './tex';
import {City} from './City';
import {Interior} from './Interior';
import {BAL, BD, YF, io, outC} from './plan';

// Tour dell'appartamento: plastico che ruota, poi visita a altezza d'occhi

export const TOUR_DURATION = 660;
const deg = Math.PI / 180;
const cl = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const SWITCH = 236; // passaggio dal plastico all'interno
const FLOOR_Y = YF + 0.15; // quota del pavimento nella città
const EYE = 1.55;

// ---------- arredi aggiuntivi visibili solo nel tour ----------
const Decor: React.FC<{tx: Textures; inside: boolean}> = ({tx, inside}) => {
	const M = useMemo(() => {
		const s = (o: THREE.MeshStandardMaterialParameters) => new THREE.MeshStandardMaterial(o);
		return {
			ceiling: s({color: '#f4f2ee', roughness: 0.9}),
			walnut: s({color: '#6e4a31', roughness: 0.55}),
			white: s({color: '#f1eee8', roughness: 0.55}),
			art1: s({color: '#c8462a', roughness: 0.8}),
			art1b: s({color: '#e9a23b', roughness: 0.8}),
			art2: s({color: '#2f4c5c', roughness: 0.8}),
			frame: s({color: '#1f1f1f', roughness: 0.5}),
			spot: s({color: '#fff7e6', emissive: new THREE.Color('#fff1d6'), emissiveIntensity: 2.2}),
			cord: s({color: '#222', roughness: 0.6}),
			curtain: s({color: '#efe8dc', roughness: 1, transparent: true, opacity: 0.85}),
			railGlass: s({color: '#bcd8e4', transparent: true, opacity: 0.18, roughness: 0.05, metalness: 0.2}),
			rail: s({color: '#8a8d92', metalness: 0.7, roughness: 0.35}),
			slab: s({map: tx.concrete, roughness: 0.9, color: '#e8e4dd'}),
			books: ['#a23a2c', '#2f4c5c', '#d2a43f', '#efe8dc', '#3e6f6c', '#6b4a7a'].map((c) => s({color: c, roughness: 0.8})),
		};
	}, [tx]);
	const box = (x0: number, z0: number, x1: number, z1: number, y0: number, h: number, m: THREE.Material, k: string) => (
		<mesh key={k} position={[(x0 + x1) / 2, y0 + h / 2, (z0 + z1) / 2]} material={m} castShadow receiveShadow>
			<boxGeometry args={[x1 - x0, h, z1 - z0]} />
		</mesh>
	);
	const items: React.ReactNode[] = [];
	// soletta sotto l'appartamento (plastico e vista esterna)
	items.push(box(-0.3, -0.3, 14.3, BD + 0.3, -0.32, 0.32, M.slab, 'slab'));
	items.push(box(BAL.x0, BD + 0.3, BAL.x1, BAL.z1, -0.3, 0.3, M.slab, 'balslab'));
	// listelli in legno dietro la TV
	for (let z = 7.9; z < 9.95; z += 0.09) items.push(box(0.15, z, 0.2, z + 0.05, 0, 2.7, M.walnut, 'sl' + z));
	// pensili cucina
	items.push(box(0.15, 4.85, 0.5, 7.6, 1.55, 0.8, M.white, 'pensili'));
	// quadro arancio in soggiorno (parete y = 4, verso il soggiorno)
	items.push(box(1.35, 4.06, 2.95, 4.1, 1.15, 1.15, M.frame, 'q1f'));
	items.push(box(1.4, 4.1, 2.9, 4.11, 1.2, 1.05, M.art1, 'q1'));
	items.push(box(1.9, 4.11, 2.4, 4.115, 1.35, 0.6, M.art1b, 'q1b'));
	// quadro in camera matrimoniale sopra la testiera
	items.push(box(10.41, 1.55, 10.45, 2.85, 1.35, 0.75, M.frame, 'q2f'));
	items.push(box(10.45, 1.6, 10.46, 2.8, 1.4, 0.65, M.art2, 'q2'));
	// libri nella libreria dello studio
	for (let r = 0; r < 4; r++)
		for (let k = 0; k < 9; k++) {
			const z = 0.5 + k * 0.32 + ((r * 7 + k * 3) % 5) * 0.01;
			items.push(box(10.02, z, 10.3, z + 0.24, 0.35 + r * 0.45, 0.28 + ((k + r) % 3) * 0.04, M.books[(k + r * 2) % 6], `b${r}-${k}`));
		}
	// tende leggere ai lati delle vetrate
	[
		[0.9, 1.15],
		[3.35, 3.6],
		[4.4, 4.65],
		[7.35, 7.6],
	].forEach(([a, b], i) => items.push(box(a, BD - 0.32, b, BD - 0.2, 0.02, 2.62, M.curtain, 'c' + i)));
	// parapetto in vetro del terrazzo
	items.push(box(BAL.x0, BAL.z1 - 0.05, BAL.x1, BAL.z1 - 0.02, 0, 1.05, M.railGlass, 'rg'));
	items.push(box(BAL.x0, BAL.z1 - 0.05, BAL.x1, BAL.z1 - 0.01, 1.05, 0.03, M.rail, 'rt'));
	items.push(box(BAL.x1 - 0.03, BD + 0.2, BAL.x1, BAL.z1, 0, 1.05, M.railGlass, 'rs'));
	if (inside) {
		// soffitto (visibile solo da sotto) e faretti
		items.push(
			<mesh key="ceil" position={[7, 2.7 + 0.15, 5]} material={M.ceiling} castShadow receiveShadow>
				<boxGeometry args={[14.6, 0.3, 10.6]} />
			</mesh>,
		);
		[
			[1.5, 5.5],
			[3.5, 5.5],
			[1.5, 8.5],
			[3.5, 8.5],
			[6, 6.2],
			[7.5, 9],
			[5.5, 9],
			[7.5, 4.7],
			[5.5, 4.7],
			[2, 1.5],
			[12, 2],
			[12, 7.5],
			[8.7, 2],
		].forEach(([x, z], i) => (
			items.push(
				<mesh key={'s' + i} position={[x, 2.695, z]} rotation-x={Math.PI / 2} material={M.spot}>
					<circleGeometry args={[0.07, 16]} />
				</mesh>,
			)
		));
		// cavi delle lampade a sospensione
		[5.8, 6.8].forEach((x, i) => items.push(box(x - 0.005, 7.095, x + 0.005, 7.105, 1.83, 0.87, M.cord, 'cord' + i)));
	}
	return <group>{items}</group>;
};

// ---------- camera ----------
type Cam = {pos: THREE.Vector3; look: THREE.Vector3; fov: number};
const P = (x: number, z: number, y = EYE) => new THREE.Vector3(x, FLOOR_Y + y, z);
const tourKeys: {f: number; p: THREE.Vector3; l: THREE.Vector3}[] = [
	{f: 236, p: P(8.4, 4.75, 1.7), l: P(2.0, 9.8, 1.1)},
	{f: 320, p: P(6.8, 5.9), l: P(1.5, 10.6, 1.2)},
	{f: 392, p: P(5.0, 7.3), l: P(0.4, 5.3, 1.1)},
	{f: 452, p: P(4.1, 8.6), l: P(7.4, 7.0, 0.9)},
	{f: 505, p: P(5.4, 9.3), l: P(6.2, 13.5, 1.3)},
	{f: 565, p: P(8.0, 4.7), l: P(11.8, 4.55, 1.4)},
	{f: 622, p: P(11.75, 4.5), l: P(11.6, 2.0, 0.8)},
	{f: 660, p: P(12.6, 4.15), l: P(10.9, 1.7, 0.9)},
];
const pCurve = new THREE.CatmullRomCurve3(tourKeys.map((k) => k.p), false, 'centripetal');
const lCurve = new THREE.CatmullRomCurve3(tourKeys.map((k) => k.l), false, 'centripetal');

const camAt = (f: number): Cam => {
	if (f < SWITCH) {
		// plastico: orbita, poi tuffo verso il soggiorno
		const c = new THREE.Vector3(7, 0.4, 5.8);
		const th = interpolate(f, [0, 200], [-38, 28], {...cl, easing: io}) * deg;
		const dive = interpolate(f, [186, SWITCH], [0, 1], {...cl, easing: Easing2});
		const ph = (40 - 30 * dive) * deg;
		const d = interpolate(f, [0, 186], [27, 23], cl) * (1 - dive) + 2.2 * dive;
		const t = c.clone().lerp(new THREE.Vector3(4.2, 1.2, 8.0), dive);
		const pos = new THREE.Vector3(t.x + Math.sin(th) * Math.cos(ph) * d, t.y + Math.sin(ph) * d, t.z + Math.cos(th) * Math.cos(ph) * d);
		return {pos, look: t, fov: 32 + 20 * dive};
	}
	const n = tourKeys.length - 1;
	let i = 0;
	while (i < n - 1 && f > tourKeys[i + 1].f) i++;
	const a = tourKeys[i];
	const b = tourKeys[i + 1];
	const u = interpolate(f, [a.f, b.f], [0, 1], {...cl, easing: (x) => x * x * (3 - 2 * x) * 0.35 + x * 0.65});
	const t = (i + u) / n;
	return {pos: pCurve.getPoint(t), look: lCurve.getPoint(t), fov: 58};
};
function Easing2(x: number) {
	return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
}

const Rig: React.FC<{cam: Cam}> = ({cam}) => {
	const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
	camera.fov = cam.fov;
	camera.near = 0.05;
	camera.far = 9000;
	camera.position.copy(cam.pos);
	camera.up.set(0, 1, 0);
	camera.lookAt(cam.look);
	camera.updateProjectionMatrix();
	camera.updateMatrixWorld();
	return null;
};

// ---------- luci ----------
const ModelLights: React.FC = () => {
	const {gl, scene} = useThree();
	gl.toneMapping = THREE.ACESFilmicToneMapping;
	gl.toneMappingExposure = 0.95;
	scene.background = new THREE.Color('#f1efea');
	scene.fog = null;
	scene.environment = null;
	const key = useMemo(() => {
		const l = new THREE.DirectionalLight('#fffaf2', 2.2);
		l.castShadow = true;
		l.shadow.mapSize.set(4096, 4096);
		const c = l.shadow.camera as THREE.OrthographicCamera;
		c.left = -14;
		c.right = 14;
		c.top = 14;
		c.bottom = -14;
		c.near = 1;
		c.far = 80;
		c.updateProjectionMatrix();
		l.shadow.bias = -0.0004;
		l.shadow.normalBias = 0.02;
		l.shadow.radius = 5;
		l.position.set(-6, 30, 22);
		l.target.position.set(7, 0, 5.8);
		l.target.updateMatrixWorld();
		return l;
	}, []);
	return (
		<>
			<primitive object={key} />
			<primitive object={key.target} />
			<hemisphereLight args={['#ffffff', '#d9d3c8', 1.5]} />
			<mesh rotation-x={-Math.PI / 2} position={[7, -0.33, 5.8]} receiveShadow>
				<planeGeometry args={[200, 200]} />
				<meshStandardMaterial color="#efece6" roughness={1} />
			</mesh>
		</>
	);
};

const TourLights: React.FC = () => {
	const {gl, scene} = useThree();
	const el = 3.5 * deg;
	const az = 28 * deg;
	const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
	const sky = useMemo(() => {
		const k = new Sky();
		k.scale.setScalar(8000);
		return k;
	}, []);
	const env = useMemo(() => {
		const sc = new THREE.Scene();
		const k = new Sky();
		k.scale.setScalar(1000);
		sc.add(k);
		return {sc, k, pm: new THREE.PMREMGenerator(gl)};
	}, [gl]);
	[sky, env.k].forEach((k) => {
		const u = k.material.uniforms;
		u.turbidity.value = 10;
		u.rayleigh.value = 3.6;
		u.mieCoefficient.value = 0.009;
		u.mieDirectionalG.value = 0.82;
		u.sunPosition.value.copy(dir);
	});
	const rt = useMemo(() => env.pm.fromScene(env.sc, 0, 1, 2000), [env]);
	scene.environment = rt.texture;
	(scene as THREE.Scene & {environmentIntensity: number}).environmentIntensity = 0.45;
	scene.background = null;
	scene.fog = new THREE.Fog('#c79a7f', 300, 1500);
	gl.toneMapping = THREE.ACESFilmicToneMapping;
	gl.toneMappingExposure = 0.62;
	const sun = useMemo(() => {
		const l = new THREE.DirectionalLight('#ffb27a', 3.4);
		l.castShadow = true;
		l.shadow.mapSize.set(4096, 4096);
		const c = l.shadow.camera as THREE.OrthographicCamera;
		c.left = -16;
		c.right = 16;
		c.top = 16;
		c.bottom = -16;
		c.near = 1;
		c.far = 400;
		c.updateProjectionMatrix();
		l.shadow.bias = -0.0003;
		l.shadow.normalBias = 0.02;
		l.shadow.radius = 3;
		return l;
	}, []);
	const center = new THREE.Vector3(7, FLOOR_Y, 6);
	sun.position.copy(center.clone().add(dir.clone().multiplyScalar(150)));
	sun.target.position.copy(center);
	sun.target.updateMatrixWorld();
	return (
		<>
			<primitive object={sky} />
			<primitive object={sun} />
			<primitive object={sun.target} />
			<hemisphereLight args={['#f3d9c4', '#5a4a40', 0.9]} />
			<pointLight position={[3, FLOOR_Y + 2.4, 7]} intensity={9} distance={10} decay={2} color="#ffd9a8" />
			<pointLight position={[6.5, FLOOR_Y + 2.4, 5]} intensity={6} distance={9} decay={2} color="#ffd9a8" />
			<pointLight position={[12, FLOOR_Y + 2.4, 2.6]} intensity={7} distance={8} decay={2} color="#ffd9a8" />
		</>
	);
};

const useFonts = () => {
	const [h] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(h));
	}, [h]);
};

// schede descrittive
const CARDS: {r: [number, number]; k: string; t: string; d: string}[] = [
	{r: [30, 190], k: 'Piano 5° · Appartamento tipo', t: '140 m² su un solo livello', d: '3 camere, 2 bagni, studio e terrazzo di 13 m².'},
	{r: [262, 345], k: 'Soggiorno · 46,6 m²', t: 'Rovere, bouclé e un tocco di colore', d: 'Vetrate a tutta altezza aperte sul tramonto.'},
	{r: [372, 440], k: 'Cucina', t: 'Isola in marmo, piano in pietra scura', d: 'Aperta sul soggiorno, con dispensa a colonna.'},
	{r: [450, 500], k: 'Zona pranzo', t: 'Una tavola per sei accanto al vetro', d: 'Luce naturale da due lati.'},
	{r: [500, 548], k: 'Terrazzo · 13 m²', t: 'Affacciato sul parco', d: 'Salotto esterno e fioriere in pietra.'},
	{r: [590, 648], k: 'Camera matrimoniale · 19,4 m²', t: 'Lino, legno di noce e luce calda', d: 'Armadio a tutta parete e angolo lettura.'},
];

export const Tour: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W, height: Hh} = useVideoConfig();
	const tx = useMemo(makeTextures, []);
	const cam = camAt(f);
	const inside = f >= SWITCH;
	const flash = f < SWITCH ? interpolate(f, [SWITCH - 14, SWITCH], [0, 1], cl) : interpolate(f, [SWITCH, SWITCH + 16], [1, 0], cl);
	const fade = Math.min(interpolate(f, [0, 12], [0, 1], cl), interpolate(f, [TOUR_DURATION - 16, TOUR_DURATION - 1], [1, 0], cl));
	const s = W / 1920;

	return (
		<AbsoluteFill style={{background: '#f1efea'}}>
			<ThreeCanvas width={W} height={Hh} shadows gl={{antialias: true, preserveDrawingBuffer: true}} camera={{fov: 40, near: 0.05, far: 9000}}>
				<Rig cam={cam} />
				{inside ? (
					<>
						<TourLights />
						<City tx={tx} night={0.25} lamps={0.3} />
						<group position={[0, FLOOR_Y, 0]}>
							<Interior tx={tx} glow={0.8} glass="clear" hideDoors={[4]} />
							<Decor tx={tx} inside />
						</group>
					</>
				) : (
					<>
						<ModelLights />
						<group position={[0, 0, 0]}>
							<Interior tx={tx} glow={0.4} glass="clear" />
							<Decor tx={tx} inside={false} />
						</group>
					</>
				)}
			</ThreeCanvas>
			{CARDS.map((c, i) => {
				const o = Math.min(interpolate(f, [c.r[0], c.r[0] + 12], [0, 1], {...cl, easing: outC}), interpolate(f, [c.r[1] - 10, c.r[1]], [1, 0], cl));
				if (o <= 0) return null;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: 72 * s,
							bottom: 80 * s,
							width: 470 * s,
							opacity: o,
							transform: `translateY(${(1 - o) * 18 * s}px)`,
							background: 'rgba(250,248,244,0.9)',
							borderRadius: 14 * s,
							padding: `${22 * s}px ${26 * s}px`,
							boxShadow: '0 20px 50px rgba(0,0,0,0.18)',
							color: '#16191e',
						}}
					>
						<div style={{fontFamily: 'IBM Plex Mono', fontSize: 17 * s, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#c4271f'}}>{c.k}</div>
						<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: 34 * s, lineHeight: 1.1, marginTop: 8 * s}}>{c.t}</div>
						<div style={{fontFamily: 'Archivo', fontWeight: 600, fontSize: 21 * s, color: '#585b60', marginTop: 8 * s}}>{c.d}</div>
					</div>
				);
			})}
			<AbsoluteFill style={{background: '#ffffff', opacity: flash}} />
			<AbsoluteFill style={{background: '#f1efea', opacity: 1 - fade}} />
		</AbsoluteFill>
	);
};

export {io};
