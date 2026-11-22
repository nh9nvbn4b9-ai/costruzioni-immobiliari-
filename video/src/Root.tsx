import React from 'react';
import {Composition} from 'remotion';
import {Palazzo, DURATION, FPS} from './Palazzo';
import {Cantiere} from './cantiere/Cantiere';
import {DURATION as D3} from './cantiere/plan';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			{/* Animazione 3D realistica (usata dal sito) */}
			<Composition id="CantiereLandscape" component={Cantiere} durationInFrames={D3} fps={30} width={1920} height={1080} />
			<Composition id="CantierePortrait" component={Cantiere} durationInFrames={D3} fps={30} width={1080} height={1920} />
			{/* Versione isometrica precedente */}
			<Composition id="PalazzoLandscape" component={Palazzo} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
			<Composition id="PalazzoPortrait" component={Palazzo} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
		</>
	);
};
