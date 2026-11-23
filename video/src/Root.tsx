import React from 'react';
import {Composition} from 'remotion';
import {Palazzo, DURATION, FPS} from './Palazzo';
import {Cantiere} from './cantiere/Cantiere';
import {DURATION as D3} from './cantiere/plan';
import {Tour, TOUR_DURATION} from './cantiere/Tour';
import {HeroFinal, TourFinal, HERO_FRAMES, TOUR_FRAMES, FINAL_FPS} from './final/Final';

export const RemotionRoot: React.FC = () => {
	return (
		<>
			{/* Montaggio finale dei render fotorealistici Blender/Cycles (usato dal sito) */}
			<Composition id="HomeLandscape" component={HeroFinal} durationInFrames={HERO_FRAMES} fps={FINAL_FPS} width={1920} height={1080} />
			<Composition id="HomePortrait" component={HeroFinal} durationInFrames={HERO_FRAMES} fps={FINAL_FPS} width={1080} height={1920} />
			<Composition id="TourVideo" component={TourFinal} durationInFrames={TOUR_FRAMES} fps={FINAL_FPS} width={1280} height={720} />
			{/* Bozze three.js */}
			<Composition id="CantiereLandscape" component={Cantiere} durationInFrames={D3} fps={30} width={1920} height={1080} />
			<Composition id="CantierePortrait" component={Cantiere} durationInFrames={D3} fps={30} width={1080} height={1920} />
			{/* Tour dell'appartamento */}
			<Composition id="Tour" component={Tour} durationInFrames={TOUR_DURATION} fps={30} width={1920} height={1080} />
			{/* Versione isometrica precedente */}
			<Composition id="PalazzoLandscape" component={Palazzo} durationInFrames={DURATION} fps={FPS} width={1920} height={1080} />
			<Composition id="PalazzoPortrait" component={Palazzo} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
		</>
	);
};
