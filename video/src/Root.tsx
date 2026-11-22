import React from 'react';
import {Composition} from 'remotion';
import {Palazzo, DURATION, FPS} from './Palazzo';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			{/* Desktop / tablet orizzontale */}
			<Composition
				id="PalazzoLandscape"
				component={Palazzo}
				durationInFrames={DURATION}
				fps={FPS}
				width={1920}
				height={1080}
			/>
			{/* Telefono verticale: riempie tutto lo schermo */}
			<Composition
				id="PalazzoPortrait"
				component={Palazzo}
				durationInFrames={DURATION}
				fps={FPS}
				width={1080}
				height={1920}
			/>
		</>
	);
};
