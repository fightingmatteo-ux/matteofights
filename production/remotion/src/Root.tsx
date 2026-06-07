import React from "react";
import { Composition } from "remotion";
import { ReelComposition } from "./compositions/ReelComposition";
import { TrainingPartnerReel } from "./compositions/reels/TrainingPartnerReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Reel"
        component={ReelComposition}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          clips: [],
          overlayItems: [],
          hookText: "",
        }}
      />
      <Composition
        id="TrainingPartnerReel"
        component={TrainingPartnerReel}
        durationInFrames={1590}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{}}
      />
    </>
  );
};
