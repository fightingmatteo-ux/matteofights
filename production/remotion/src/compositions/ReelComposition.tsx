import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { VideoClip } from "../components/VideoClip";
import { TextOverlay } from "../components/TextOverlay";
import type { AssetEntry } from "../lib/catalog";

export interface ReelProps {
  clips: Array<{
    entry: AssetEntry;
    durationInFrames: number;
  }>;
  overlayItems: Array<{
    text: string;
    startFrame: number;
    durationInFrames: number;
    position: "top" | "center" | "bottom";
    isHook?: boolean;
  }>;
  hookText: string;
}

export const ReelComposition: React.FC<ReelProps> = ({
  clips,
  overlayItems,
}) => {
  let cursor = 0;
  const sequencedClips = clips.map((c) => {
    const start = cursor;
    cursor += c.durationInFrames;
    return { ...c, startFrame: start };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {sequencedClips.map((c, i) => (
        <Sequence
          key={i}
          from={c.startFrame}
          durationInFrames={c.durationInFrames}
        >
          <AbsoluteFill>
            <VideoClip entry={c.entry} />
          </AbsoluteFill>
        </Sequence>
      ))}
      {overlayItems.map((item, i) => (
        <Sequence
          key={`overlay-${i}`}
          from={item.startFrame}
          durationInFrames={item.durationInFrames}
        >
          <AbsoluteFill>
            <TextOverlay
              text={item.text}
              position={item.position}
              isHook={item.isHook}
            />
          </AbsoluteFill>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
