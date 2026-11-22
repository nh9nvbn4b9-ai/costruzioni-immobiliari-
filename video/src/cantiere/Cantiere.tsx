import React, {useEffect, useMemo, useState} from 'react';
import * as THREE from 'three';
import {Sky} from 'three/examples/jsm/objects/Sky.js';
import {ThreeCanvas} from '@remotion/three';
import {useThree} from '@react-three/fiber';
import {AbsoluteFill, continueRender, delayRender, interpolate, interpolateColors, useCurrentFrame, useVideoConfig} from 'remotion';
import '@fontsource/archivo/600.css';
import '@fontsource/archivo/800.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import {makeTextures} from './tex';
import {City} from './City';
import {Building} from './Building';
import {Core, Interior} from './Interior';
import {BD, BW, F, LEVELS, H, ROOMS, T, YF, ease, io, lin, outC} from './plan';

const deg = Math.PI / 180;
type Cam = {pos: THREE.Vector3; target: THREE.Vector3; up: THREE.Vector3; fov: number; ppx: number; ppy: number};

// ---------- regia della camera (drone) ----------
type K = {f: number; t: [number, number, number]; th: number; ph: number; d: number};
const camAt = (f: number, portrait: boolean, W: number, Hh: number): Cam & {k: number; topDist: number} => {
	const fov = portrait ? 48 : 30;
	const topDist = portrait ? 35.5 : 34;
	const keys: K[] = [
		{f: 0, t: [15, 4, 5], th: 40, ph: 21, d: portrait ? 175 : 200},
		{f: 400, t: [15, 17, 5], th: 22, ph: 12, d: portrait ? 112 : 128},
		{f: 472, t: [7, YF + 1.5, BD + 0.5], th: 8, ph: 22, d: 30},
		{f: 532, t: [7, YF, 5.8], th: 0, ph: 90, d: topDist},
		{f: 600, t: [7, YF, 5.8], th: 0, ph: 90, d: topDist * 0.95},
	];
	let i = 0;
	while (i < keys.length - 2 && f > keys[i + 1].f) i++;
	const a = keys[i];
	const b = keys[i + 1];
	const u = interpolate(f, [a.f, b.f], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: i === 3 ? (x) => x : io});
	const m = (p: number, q: number) => p + (q - p) * u;
	const t = new THREE.Vector3(m(a.t[0], b.t[0]), m(a.t[1], b.t[1]), m(a.t[2], b.t[2]));
	const th = m(a.th, b.th) * deg;
	const ph = Math.min(89.95, m(a.ph, b.ph)) * deg;
	const d = Math.exp(m(Math.log(a.d), Math.log(b.d)));
	const pos = new THREE.Vector3(t.x + Math.sin(th) * Math.cos(ph) * d, t.y + Math.sin(ph) * d, t.z + Math.cos(th) * Math.cos(ph) * d);
	const k = interpolate(ph / deg, [55, 89.95], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const up = new THREE.Vector3(0, 1 - k, -k).normalize();
	const ppx = portrait ? W * 0.5 : W * interpolate(f, [0, 140], [0.5, 0.63], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: io});
	const ppy = portrait ? Hh * interpolate(f, [0, 140], [0.42, 0.34], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: io}) : Hh * 0.5;
	return {pos, target: t, up, fov, ppx, ppy, k, topDist: d};
};

const Rig: React.FC<{cam: Cam; W: number; H: number}> = ({cam, W, H: Hh}) => {
	const camera = useThree((s) => s.camera) as THREE.PerspectiveCamera;
	camera.fov = cam.fov;
	camera.near = 0.5;
	camera.far = 9000;
	camera.position.copy(cam.pos);
	camera.up.copy(cam.up);
	camera.lookAt(cam.target);
	camera.setViewOffset(W, Hh, -(cam.ppx - W / 2), -(cam.ppy - Hh / 2), W, Hh);
	camera.updateProjectionMatrix();
	camera.updateMatrixWorld();
	return null;
};

// ---------- cielo, sole, ambiente ----------
const Atmosphere: React.FC<{f: number}> = ({f}) => {
	const {gl, scene} = useThree();
	const s = lin(f, T.sun);
	const el = (32 - 30.5 * Math.pow(s, 0.9)) * deg;
	const az = (-30 - 115 * s) * deg;
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
		u.turbidity.value = 2.2 + 7 * s;
		u.rayleigh.value = 1.6 + 1.8 * s;
		u.mieCoefficient.value = 0.0018 + 0.0055 * s;
		u.mieDirectionalG.value = 0.8;
		u.sunPosition.value.copy(dir);
	});
	const rt = env.pm.fromScene(env.sc, 0, 1, 2000);
	if (scene.environment && scene.environment !== rt.texture) (scene.environment as THREE.Texture).dispose();
	scene.environment = rt.texture;
	(scene as THREE.Scene & {environmentIntensity: number}).environmentIntensity = interpolate(s, [0, 1], [0.32, 0.22]);
	gl.toneMapping = THREE.ACESFilmicToneMapping;
	gl.toneMappingExposure = interpolate(s, [0, 0.7, 1], [0.5, 0.48, 0.58]);
	const fogCol = interpolateColors(s, [0, 0.6, 0.85, 1], ['#a9bdd0', '#c4b4a2', '#b07b5e', '#4a4250']);
	scene.fog = new THREE.Fog(fogCol, 320, 1600);

	const sun = useMemo(() => {
		const l = new THREE.DirectionalLight('#ffffff', 3);
		l.castShadow = true;
		l.shadow.mapSize.set(4096, 4096);
		const c = l.shadow.camera as THREE.OrthographicCamera;
		c.left = -95;
		c.right = 95;
		c.top = 95;
		c.bottom = -95;
		c.near = 10;
		c.far = 700;
		c.updateProjectionMatrix();
		l.shadow.bias = -0.0004;
		l.shadow.normalBias = 0.06;
		return l;
	}, []);
	const center = new THREE.Vector3(15, 0, 5);
	sun.position.copy(center.clone().add(dir.clone().multiplyScalar(300)));
	sun.target.position.copy(center);
	sun.target.updateMatrixWorld();
	const top = ease(f, T.top);
	sun.intensity = interpolate(s, [0, 0.75, 1], [4.2, 3.0, 0.45]) * (1 - top * 0.85);
	sun.color.set(interpolateColors(s, [0, 0.6, 0.9, 1], ['#fff4e6', '#ffe0b8', '#ff9e5e', '#ff7a45']));
	const hemiI = interpolate(s, [0, 0.8, 1], [0.75, 0.6, 0.35]) * (1 - top * 0.5);
	const sky1 = interpolateColors(s, [0, 1], ['#cfe2f5', '#4a5a80']);
	const gr1 = interpolateColors(s, [0, 1], ['#6b6257', '#2a2523']);
	return (
		<>
			<primitive object={sky} />
			<primitive object={sun} />
			<primitive object={sun.target} />
			<hemisphereLight args={[sky1, gr1, hemiI]} />
		</>
	);
};

// luce d'ambiente per l'appartamento visto dall'alto
const InteriorLight: React.FC<{i: number}> = ({i}) => {
	const l = useMemo(() => {
		const d = new THREE.SpotLight('#fff0da', 0, 0, 0.72, 0.55, 0);
		d.castShadow = true;
		d.shadow.mapSize.set(2048, 2048);
		d.shadow.camera.near = 2;
		d.shadow.camera.far = 90;
		d.shadow.camera.updateProjectionMatrix();
		d.shadow.bias = -0.0004;
		d.shadow.normalBias = 0.02;
		d.shadow.radius = 4;
		return d;
	}, []);
	l.position.set(7 + 3, YF + 15, 5.8 + 4);
	l.target.position.set(7, YF, 5.8);
	l.target.updateMatrixWorld();
	l.intensity = 3.2 * i;
	return (
		<>
			<primitive object={l} />
			<primitive object={l.target} />
			<pointLight position={[6, YF + 2.5, 7]} intensity={14 * i} distance={14} decay={2} color="#ffd9a8" />
		</>
	);
};

const useFonts = () => {
	const [h] = useState(() => delayRender('fonts'));
	useEffect(() => {
		document.fonts.ready.then(() => continueRender(h));
	}, [h]);
};

export const Cantiere: React.FC = () => {
	useFonts();
	const f = useCurrentFrame();
	const {width: W, height: Hh} = useVideoConfig();
	const portrait = Hh > W;
	const tx = useMemo(makeTextures, []);
	const cam = camAt(f, portrait, W, Hh);
	const night = ease(f, T.lights);
	const lamps = ease(f, [T.lights[0] - 20, T.lights[0] + 30]);
	const showInterior = f >= T.interior;
	const intLight = ease(f, [T.interior + 10, T.top[1]]);

	// ---------- etichette della pianta (proiezione della camera zenitale) ----------
	const labO = (j: number) => interpolate(f, [T.labels[0] + j * 3, T.labels[0] + 16 + j * 3], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: outC});
	const kpx = Hh / 2 / ((cam.pos.y - YF) * Math.tan((cam.fov * deg) / 2));
	const sp = (x: number, z: number): [number, number] => [cam.ppx + (x - cam.target.x) * kpx, cam.ppy + (z - cam.target.z) * kpx];
	const showLabels = f >= T.labels[0] && cam.k > 0.999;
	const fade = Math.min(lin(f, T.fadeIn), 1 - lin(f, T.fadeOut));
	const fs = Math.max(14, kpx * 0.34);

	return (
		<AbsoluteFill style={{background: '#0c0f14'}}>
			<ThreeCanvas width={W} height={Hh} shadows gl={{antialias: true, preserveDrawingBuffer: true}} camera={{fov: cam.fov, near: 0.5, far: 9000}}>
				<Rig cam={cam} W={W} H={Hh} />
				<Atmosphere f={f} />
				<City tx={tx} night={night} lamps={lamps} />
				<Building f={f} tx={tx} night={night} />
				{showInterior && (
					<group position={[0, 0.15 + YF, 0]}>
						<Interior tx={tx} glow={intLight} />
						<group position={[BW, 0, 0]} scale={[-1, 1, 1]}>
							<Interior tx={tx} glow={intLight} />
						</group>
						<Core tx={tx} />
					</group>
				)}
				{showInterior && <InteriorLight i={intLight} />}
			</ThreeCanvas>

			{showLabels && (
				<AbsoluteFill>
					<svg width={W} height={Hh} style={{position: 'absolute', inset: 0}}>
						{(() => {
							const o = labO(ROOMS.length + 1);
							const [ax, ay] = sp(0, -0.9);
							const [bx] = sp(14, -0.9);
							const [cx, cy] = sp(-0.9, 0);
							const [, dy] = sp(-0.9, BD);
							const st = {stroke: 'rgba(255,255,255,0.85)', strokeWidth: 2};
							return (
								<g opacity={o} fontFamily="IBM Plex Mono" fontSize={fs * 0.85} fill="#fff">
									<line x1={ax} y1={ay} x2={bx} y2={ay} {...st} />
									<line x1={ax} y1={ay - 8} x2={ax} y2={ay + 8} {...st} />
									<line x1={bx} y1={ay - 8} x2={bx} y2={ay + 8} {...st} />
									<text x={(ax + bx) / 2} y={ay - 10} textAnchor="middle" style={{paintOrder: 'stroke'}} stroke="rgba(0,0,0,0.6)" strokeWidth={4}>
										14,00
									</text>
									<line x1={cx} y1={cy} x2={cx} y2={dy} {...st} />
									<line x1={cx - 8} y1={cy} x2={cx + 8} y2={cy} {...st} />
									<line x1={cx - 8} y1={dy} x2={cx + 8} y2={dy} {...st} />
									<text x={cx - 12} y={(cy + dy) / 2} textAnchor="middle" transform={`rotate(-90 ${cx - 12} ${(cy + dy) / 2})`} style={{paintOrder: 'stroke'}} stroke="rgba(0,0,0,0.6)" strokeWidth={4}>
										10,00
									</text>
								</g>
							);
						})()}
					</svg>
					{ROOMS.map((r, j) => {
						const o = labO(j);
						const [x, y] = sp(r.label[0], r.label[1]);
						const small = r.name.length <= 5;
						return (
							<div
								key={j}
								style={{
									position: 'absolute',
									left: x,
									top: y,
									transform: `translate(-50%,-50%) translateY(${(1 - o) * 10}px)`,
									opacity: o,
									background: 'rgba(17,20,25,0.78)',
									color: '#fff',
									borderRadius: 6,
									padding: `${fs * 0.22}px ${fs * 0.45}px`,
									textAlign: 'center',
									whiteSpace: 'nowrap',
									boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
									backdropFilter: 'blur(2px)',
								}}
							>
								<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: fs * (small ? 0.62 : 0.68), letterSpacing: '0.08em', textTransform: 'uppercase'}}>{r.name}</div>
								<div style={{fontFamily: 'IBM Plex Mono', fontWeight: 500, fontSize: fs * 0.66, color: '#ffd59a', marginTop: 2}}>{r.area}</div>
							</div>
						);
					})}
					{(() => {
						const o = labO(ROOMS.length + 3);
						const [x, y] = sp(0, BD + 2.3);
						return (
							<div style={{position: 'absolute', left: x, top: y, opacity: o, color: '#fff', textShadow: '0 2px 10px rgba(0,0,0,0.7)'}}>
								<div style={{fontFamily: 'Archivo', fontWeight: 800, fontSize: fs * 0.95, letterSpacing: '0.1em'}}>PIANTA PIANO {F}°</div>
								<div style={{fontFamily: 'IBM Plex Mono', fontSize: fs * 0.62, letterSpacing: '0.05em', color: '#cfe6f6', marginTop: 4}}>APPARTAMENTO TIPO · SUP. 140 m² · TERRAZZO 13 m²</div>
							</div>
						);
					})()}
				</AbsoluteFill>
			)}
			<AbsoluteFill style={{background: 'radial-gradient(ellipse at 55% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)'}} />
			<AbsoluteFill style={{background: '#0c0f14', opacity: 1 - fade}} />
		</AbsoluteFill>
	);
};

export {LEVELS, H};
