import * as THREE from 'three';

// Texture procedurali disegnate su canvas (nessuna immagine esterna)

let seed = 1;
export const setSeed = (s: number) => {
	seed = s;
};
export const rnd = () => {
	seed = (seed * 16807) % 2147483647;
	return (seed - 1) / 2147483646;
};

type Ctx = CanvasRenderingContext2D;

const make = (w: number, h: number, draw: (c: Ctx, w: number, h: number) => void, srgb = true) => {
	const cv = document.createElement('canvas');
	cv.width = w;
	cv.height = h;
	const c = cv.getContext('2d')!;
	draw(c, w, h);
	const t = new THREE.CanvasTexture(cv);
	if (srgb) t.colorSpace = THREE.SRGBColorSpace;
	t.wrapS = THREE.RepeatWrapping;
	t.wrapT = THREE.RepeatWrapping;
	t.anisotropy = 4;
	return t;
};

const speckle = (c: Ctx, w: number, h: number, n: number, amp: number, size = 2) => {
	for (let i = 0; i < n; i++) {
		const v = (rnd() - 0.5) * amp;
		c.fillStyle = v > 0 ? `rgba(255,255,255,${v})` : `rgba(0,0,0,${-v})`;
		c.fillRect(rnd() * w, rnd() * h, size * (0.4 + rnd()), size * (0.4 + rnd()));
	}
};

export const makeTextures = () => {
	setSeed(7);
	const concrete = make(512, 512, (c, w, h) => {
		c.fillStyle = '#b9b5ad';
		c.fillRect(0, 0, w, h);
		speckle(c, w, h, 9000, 0.12, 3);
		c.strokeStyle = 'rgba(0,0,0,0.06)';
		for (let y = 0; y < h; y += 128) {
			c.beginPath();
			c.moveTo(0, y + 0.5);
			c.lineTo(w, y + 0.5);
			c.stroke();
		}
		for (let x = 0; x < w; x += 256) {
			c.beginPath();
			c.moveTo(x + 0.5, 0);
			c.lineTo(x + 0.5, h);
			c.stroke();
		}
	});
	const dirt = make(512, 512, (c, w, h) => {
		c.fillStyle = '#7c5f44';
		c.fillRect(0, 0, w, h);
		speckle(c, w, h, 14000, 0.28, 4);
		for (let i = 0; i < 900; i++) {
			c.fillStyle = `rgba(${170 + rnd() * 50},${150 + rnd() * 40},${120 + rnd() * 30},0.7)`;
			c.beginPath();
			c.arc(rnd() * w, rnd() * h, 0.6 + rnd() * 1.6, 0, 7);
			c.fill();
		}
		// tracce di livellamento
		c.strokeStyle = 'rgba(0,0,0,0.07)';
		c.lineWidth = 6;
		for (let i = 0; i < 10; i++) {
			c.beginPath();
			const y = rnd() * h;
			c.moveTo(0, y);
			c.bezierCurveTo(w * 0.3, y + 20, w * 0.6, y - 20, w, y + 4);
			c.stroke();
		}
	});
	const asphalt = make(512, 512, (c, w, h) => {
		c.fillStyle = '#45484d';
		c.fillRect(0, 0, w, h);
		speckle(c, w, h, 20000, 0.16, 1.6);
	});
	const grass = make(512, 512, (c, w, h) => {
		c.fillStyle = '#5d7d3f';
		c.fillRect(0, 0, w, h);
		for (let i = 0; i < 16000; i++) {
			const g = 90 + rnd() * 70;
			c.strokeStyle = `rgba(${g * 0.6},${g},${g * 0.4},0.5)`;
			const x = rnd() * w;
			const y = rnd() * h;
			c.beginPath();
			c.moveTo(x, y);
			c.lineTo(x + (rnd() - 0.5) * 3, y - 3 - rnd() * 4);
			c.stroke();
		}
		// bande di taglio
		for (let x = 0; x < w; x += 128) {
			c.fillStyle = 'rgba(255,255,200,0.04)';
			c.fillRect(x, 0, 64, h);
		}
	});
	const paving = make(512, 512, (c, w, h) => {
		const n = 8;
		const s = w / n;
		for (let i = 0; i < n; i++)
			for (let j = 0; j < n; j++) {
				const v = 188 + rnd() * 18;
				c.fillStyle = `rgb(${v},${v - 5},${v - 12})`;
				c.fillRect(i * s, j * s, s, s);
			}
		speckle(c, w, h, 6000, 0.1, 2);
		c.strokeStyle = 'rgba(60,55,50,0.35)';
		c.lineWidth = 2;
		for (let i = 0; i <= n; i++) {
			c.beginPath();
			c.moveTo(i * s, 0);
			c.lineTo(i * s, h);
			c.moveTo(0, i * s);
			c.lineTo(w, i * s);
			c.stroke();
		}
	});
	const roofTiles = make(512, 512, (c, w, h) => {
		c.fillStyle = '#9c4f36';
		c.fillRect(0, 0, w, h);
		const rh = 16;
		for (let y = 0; y < h; y += rh) {
			const off = (y / rh) % 2 ? 10 : 0;
			for (let x = -20; x < w; x += 20) {
				const v = rnd() * 30 - 15;
				c.fillStyle = `rgb(${156 + v},${78 + v * 0.6},${52 + v * 0.4})`;
				c.fillRect(x + off, y, 19, rh - 3);
			}
			c.fillStyle = 'rgba(40,10,0,0.35)';
			c.fillRect(0, y + rh - 3, w, 3);
		}
		speckle(c, w, h, 5000, 0.12, 2);
	});
	const gravel = make(256, 256, (c, w, h) => {
		c.fillStyle = '#8e8b86';
		c.fillRect(0, 0, w, h);
		speckle(c, w, h, 9000, 0.3, 2);
	});

	// facciate milanesi: 4x4 moduli (12.8 m), finestre con persiane
	const facade = (wall: string, shutter: string, s: number) => {
		setSeed(s);
		const lit: boolean[] = [];
		const map = make(512, 512, (c, w, h) => {
			c.fillStyle = wall;
			c.fillRect(0, 0, w, h);
			speckle(c, w, h, 6000, 0.08, 3);
			const m = 128;
			for (let r = 0; r < 4; r++)
				for (let k = 0; k < 4; k++) {
					const x = k * m;
					const y = r * m;
					// marcapiano
					c.fillStyle = 'rgba(255,255,255,0.18)';
					c.fillRect(x, y + m - 7, m, 5);
					// finestra
					const wx = x + 42;
					const wy = y + 24;
					const ww = 44;
					const wh = 80;
					c.fillStyle = '#efe9df';
					c.fillRect(wx - 5, wy - 6, ww + 10, wh + 12);
					const gr = c.createLinearGradient(0, wy, 0, wy + wh);
					gr.addColorStop(0, '#5d6f7c');
					gr.addColorStop(1, '#1c242b');
					c.fillStyle = gr;
					c.fillRect(wx, wy, ww, wh);
					c.fillStyle = '#d8d1c4';
					c.fillRect(wx + ww / 2 - 1, wy, 2, wh);
					const closed = rnd() < 0.25;
					lit.push(rnd() < 0.42);
					c.fillStyle = shutter;
					if (closed) {
						c.fillRect(wx, wy, ww, wh);
						c.fillStyle = 'rgba(0,0,0,0.25)';
						for (let yy = wy + 4; yy < wy + wh; yy += 5) c.fillRect(wx, yy, ww, 1.5);
					} else {
						c.fillRect(wx - 26, wy, 21, wh);
						c.fillRect(wx + ww + 5, wy, 21, wh);
						c.fillStyle = 'rgba(0,0,0,0.25)';
						for (let yy = wy + 4; yy < wy + wh; yy += 5) {
							c.fillRect(wx - 26, yy, 21, 1.5);
							c.fillRect(wx + ww + 5, yy, 21, 1.5);
						}
					}
					// ringhierina
					if (r % 2 === 0 && k % 2 === 1) {
						c.fillStyle = 'rgba(30,30,30,0.85)';
						c.fillRect(wx - 10, wy + wh - 22, ww + 20, 2);
						for (let xx = wx - 10; xx < wx + ww + 10; xx += 4) c.fillRect(xx, wy + wh - 22, 1.2, 22);
					}
				}
		});
		setSeed(s);
		const em = make(512, 512, (c, w, h) => {
			c.fillStyle = '#000';
			c.fillRect(0, 0, w, h);
			let i = 0;
			for (let r = 0; r < 4; r++)
				for (let k = 0; k < 4; k++) {
					if (lit[i++]) {
						const v = 0.55 + ((i * 37) % 10) / 22;
						c.fillStyle = `rgba(255,${190 + ((i * 13) % 40)},${120 + ((i * 7) % 50)},${v})`;
						c.fillRect(k * 128 + 42, r * 128 + 24, 44, 80);
					}
				}
		});
		return {map, em};
	};
	const facades = [
		facade('#d7b27c', '#4a5a3c', 11), // ocra
		facade('#c9805f', '#5b3b2b', 23), // terracotta
		facade('#e7dcc6', '#3f5141', 37), // crema
		facade('#b8b3ab', '#43464a', 53), // grigio
	];

	const shop = make(512, 160, (c, w, h) => {
		c.fillStyle = '#7d756b';
		c.fillRect(0, 0, w, h);
		speckle(c, w, h, 3000, 0.1, 3);
		const colors = ['#6b2b25', '#2f4a3b', '#2f3f5c', '#5c4a2a', '#3d3d3d'];
		for (let x = 0; x < w; x += 128) {
			c.fillStyle = '#222a31';
			c.fillRect(x + 12, 30, 104, 120);
			c.fillStyle = 'rgba(255,255,255,0.12)';
			c.fillRect(x + 14, 32, 30, 116);
			c.fillStyle = colors[Math.floor(rnd() * colors.length)];
			c.fillRect(x + 8, 14, 112, 18);
			c.fillStyle = 'rgba(255,255,255,0.3)';
			for (let s = x + 8; s < x + 120; s += 14) c.fillRect(s, 14, 7, 18);
		}
	});
	const shopEm = make(512, 160, (c, w, h) => {
		c.fillStyle = '#000';
		c.fillRect(0, 0, w, h);
		for (let x = 0; x < w; x += 128) {
			if (rnd() < 0.7) {
				c.fillStyle = 'rgba(255,214,160,0.9)';
				c.fillRect(x + 12, 30, 104, 120);
			}
		}
	});
	const tower = make(256, 256, (c, w, h) => {
		c.fillStyle = '#5b6c7a';
		c.fillRect(0, 0, w, h);
		for (let y = 0; y < h; y += 16)
			for (let x = 0; x < w; x += 16) {
				const v = 70 + rnd() * 50;
				c.fillStyle = `rgb(${v},${v + 15},${v + 28})`;
				c.fillRect(x + 1, y + 1, 14, 14);
			}
	});
	const towerEm = make(256, 256, (c, w, h) => {
		c.fillStyle = '#000';
		c.fillRect(0, 0, w, h);
		for (let y = 0; y < h; y += 16)
			for (let x = 0; x < w; x += 16)
				if (rnd() < 0.35) {
					c.fillStyle = `rgba(255,${200 + rnd() * 40},150,${0.4 + rnd() * 0.5})`;
					c.fillRect(x + 1, y + 1, 14, 14);
				}
	});

	// ---------- interni ----------
	const wood = make(1024, 1024, (c, w, h) => {
		const pw = 92; // 0.18 m
		for (let y = 0; y < h; y += pw) {
			let x = -rnd() * 400;
			while (x < w) {
				const len = 260 + rnd() * 420;
				const v = rnd() * 26 - 13;
				c.fillStyle = `rgb(${178 + v},${136 + v * 0.8},${92 + v * 0.6})`;
				c.fillRect(x, y, len, pw);
				c.strokeStyle = `rgba(90,55,25,${0.12 + rnd() * 0.12})`;
				c.lineWidth = 1;
				for (let g = 0; g < 7; g++) {
					const gy = y + 6 + rnd() * (pw - 12);
					c.beginPath();
					c.moveTo(x, gy);
					c.bezierCurveTo(x + len * 0.3, gy + (rnd() - 0.5) * 10, x + len * 0.7, gy + (rnd() - 0.5) * 10, x + len, gy);
					c.stroke();
				}
				c.fillStyle = 'rgba(60,35,15,0.45)';
				c.fillRect(x, y, 2, pw);
				x += len;
			}
			c.fillStyle = 'rgba(60,35,15,0.4)';
			c.fillRect(0, y, w, 2);
		}
	});
	const tiles = make(512, 512, (c, w, h) => {
		const n = 3;
		const s = w / n;
		for (let i = 0; i < n; i++)
			for (let j = 0; j < n; j++) {
				const v = 214 + rnd() * 12;
				c.fillStyle = `rgb(${v},${v - 2},${v - 6})`;
				c.fillRect(i * s, j * s, s, s);
				c.strokeStyle = 'rgba(150,145,140,0.25)';
				c.lineWidth = 1.5;
				c.beginPath();
				c.moveTo(i * s + rnd() * s, j * s);
				c.bezierCurveTo(i * s + rnd() * s, j * s + s * 0.4, i * s + rnd() * s, j * s + s * 0.6, i * s + rnd() * s, j * s + s);
				c.stroke();
			}
		c.strokeStyle = '#a9a39b';
		c.lineWidth = 3;
		for (let i = 0; i <= n; i++) {
			c.beginPath();
			c.moveTo(i * s, 0);
			c.lineTo(i * s, h);
			c.moveTo(0, i * s);
			c.lineTo(w, i * s);
			c.stroke();
		}
	});
	const marble = make(512, 512, (c, w, h) => {
		c.fillStyle = '#f1efea';
		c.fillRect(0, 0, w, h);
		c.strokeStyle = 'rgba(120,120,125,0.35)';
		for (let i = 0; i < 14; i++) {
			c.lineWidth = 0.6 + rnd() * 1.6;
			c.beginPath();
			let x = rnd() * w;
			let y = 0;
			c.moveTo(x, y);
			while (y < h) {
				x += (rnd() - 0.5) * 40;
				y += 20 + rnd() * 30;
				c.lineTo(x, y);
			}
			c.stroke();
		}
	});
	const deck = make(512, 512, (c, w, h) => {
		const bw = 36;
		for (let x = 0; x < w; x += bw) {
			const v = rnd() * 20 - 10;
			c.fillStyle = `rgb(${126 + v},${98 + v},${74 + v})`;
			c.fillRect(x, 0, bw - 3, h);
			c.fillStyle = 'rgba(30,20,10,0.6)';
			c.fillRect(x + bw - 3, 0, 3, h);
		}
		speckle(c, w, h, 4000, 0.1, 2);
	});
	const rug = (a: string, b: string, kind: number) =>
		make(512, 512, (c, w, h) => {
			c.fillStyle = a;
			c.fillRect(0, 0, w, h);
			speckle(c, w, h, 12000, 0.08, 2);
			c.strokeStyle = b;
			if (kind === 0) {
				c.lineWidth = 6;
				c.strokeRect(24, 24, w - 48, h - 48);
				c.lineWidth = 3;
				for (let i = 0; i < 6; i++) {
					c.beginPath();
					c.moveTo(60, 80 + i * 70);
					for (let x = 60; x < w - 60; x += 40) c.lineTo(x + 20, 80 + i * 70 + (x % 80 ? 18 : -18));
					c.stroke();
				}
			} else {
				c.lineWidth = 10;
				for (let x = 40; x < w; x += 56) {
					c.beginPath();
					c.moveTo(x, 0);
					c.lineTo(x, h);
					c.stroke();
				}
			}
		});
	const rug1 = rug('#d9cdb8', '#3b3a37', 0);
	const rug2 = rug('#b9c2c4', '#7d6a55', 1);
	const hob = make(256, 256, (c, w, h) => {
		c.fillStyle = '#141516';
		c.fillRect(0, 0, w, h);
		c.strokeStyle = '#5c5f63';
		c.lineWidth = 4;
		[
			[70, 70, 44],
			[186, 70, 34],
			[70, 186, 34],
			[186, 186, 44],
		].forEach(([x, y, r]) => {
			c.beginPath();
			c.arc(x, y, r, 0, 7);
			c.stroke();
		});
	});
	const stairs = make(256, 512, (c, w, h) => {
		c.fillStyle = '#cfcac2';
		c.fillRect(0, 0, w, h);
		c.fillStyle = 'rgba(0,0,0,0.25)';
		for (let y = 0; y < h; y += 28) c.fillRect(0, y, w, 3);
		c.fillRect(w / 2 - 4, 0, 8, h);
	});
	return {concrete, dirt, asphalt, grass, paving, roofTiles, gravel, facades, shop, shopEm, tower, towerEm, wood, tiles, marble, deck, rug1, rug2, hob, stairs};
};
export type Textures = ReturnType<typeof makeTextures>;

// ---------- costruttore di geometrie (UV in metri) ----------
type V3 = [number, number, number];
const sub = (a: V3, b: V3): V3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const add = (a: V3, b: V3): V3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const cross = (a: V3, b: V3): V3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a: V3) => Math.hypot(a[0], a[1], a[2]);
const dot = (a: V3, b: V3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a: V3): V3 => {
	const l = len(a) || 1;
	return [a[0] / l, a[1] / l, a[2] / l];
};

export class Geo {
	p: number[] = [];
	n: number[] = [];
	uv: number[] = [];
	idx: number[] = [];
	quad(o: V3, du: V3, dv: V3, mod = 1, modV = mod, world = true) {
		const nn = norm(cross(du, dv));
		const b = this.p.length / 3;
		const u0 = world ? dot(o, norm(du)) / mod : 0;
		const v0 = world ? dot(o, norm(dv)) / modV : 0;
		const ul = len(du) / mod;
		const vl = len(dv) / modV;
		const c = [o, add(o, du), add(add(o, du), dv), add(o, dv)];
		const uvs = [
			[u0, v0],
			[u0 + ul, v0],
			[u0 + ul, v0 + vl],
			[u0, v0 + vl],
		];
		for (let i = 0; i < 4; i++) {
			this.p.push(...c[i]);
			this.n.push(...nn);
			this.uv.push(uvs[i][0], uvs[i][1]);
		}
		this.idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
		return this;
	}
	box(x0: number, y0: number, z0: number, x1: number, y1: number, z1: number, mod = 1, faces = 'xXyYzZ', modV = mod) {
		const dx = x1 - x0;
		const dy = y1 - y0;
		const dz = z1 - z0;
		if (faces.includes('X')) this.quad([x1, y0, z1], [0, 0, -dz], [0, dy, 0], mod, modV);
		if (faces.includes('x')) this.quad([x0, y0, z0], [0, 0, dz], [0, dy, 0], mod, modV);
		if (faces.includes('Z')) this.quad([x0, y0, z1], [dx, 0, 0], [0, dy, 0], mod, modV);
		if (faces.includes('z')) this.quad([x1, y0, z0], [-dx, 0, 0], [0, dy, 0], mod, modV);
		if (faces.includes('Y')) this.quad([x0, y1, z1], [dx, 0, 0], [0, 0, -dz], mod, modV);
		if (faces.includes('y')) this.quad([x0, y0, z0], [dx, 0, 0], [0, 0, dz], mod, modV);
		return this;
	}
	tri(a: V3, b: V3, c: V3, mod = 1) {
		const nn = norm(cross(sub(b, a), sub(c, a)));
		const i = this.p.length / 3;
		[a, b, c].forEach((q) => {
			this.p.push(...q);
			this.n.push(...nn);
			this.uv.push((q[0] + q[2]) / mod, q[1] / mod);
		});
		this.idx.push(i, i + 1, i + 2);
		return this;
	}
	// tetto a due falde (colmo lungo x o lungo z)
	gable(x0: number, x1: number, z0: number, z1: number, y: number, r: number, alongX: boolean, roof: Geo, gableWall: Geo, mod = 4) {
		const dx = x1 - x0;
		const dz = z1 - z0;
		if (alongX) {
			const zm = (z0 + z1) / 2;
			roof.quad([x0, y, z1], [dx, 0, 0], [0, r, -(z1 - zm)], mod);
			roof.quad([x1, y, z0], [-dx, 0, 0], [0, r, zm - z0], mod);
			gableWall.tri([x0, y, z0], [x0, y, z1], [x0, y + r, zm], mod);
			gableWall.tri([x1, y, z1], [x1, y, z0], [x1, y + r, zm], mod);
		} else {
			const xm = (x0 + x1) / 2;
			roof.quad([x1, y, z1], [0, 0, -dz], [-(x1 - xm), r, 0], mod);
			roof.quad([x0, y, z0], [0, 0, dz], [xm - x0, r, 0], mod);
			gableWall.tri([x1, y, z0], [x0, y, z0], [xm, y + r, z0], mod);
			gableWall.tri([x0, y, z1], [x1, y, z1], [xm, y + r, z1], mod);
		}
		return this;
	}
	// piano orizzontale rivolto verso l'alto
	floor(x0: number, z0: number, x1: number, z1: number, y: number, mod = 1) {
		return this.quad([x0, y, z1], [x1 - x0, 0, 0], [0, 0, -(z1 - z0)], mod);
	}
	build() {
		const g = new THREE.BufferGeometry();
		g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
		g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
		g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
		g.setIndex(this.idx);
		return g;
	}
}
export {sub};
