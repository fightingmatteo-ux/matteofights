import React from "react";
import { ReelComposition } from "../ReelComposition";
import { catalog } from "../../lib/catalog";

// CLIP SELECTION REASONING:
// Opening hook (0-150f / 0-5s): cinematic arrival clip sets moody gym world before the list starts
// Items 1-8 (150f each / 5s each): alternate training and atmosphere clips
//   - odd items: training clips (active energy matches doing something)
//   - even items: atmosphere clips (passive/mindset items)
// Closing (last 90f / 3s): hero shot — ends on Matteo for identity anchor
// Total: 1 arrival + 8 item clips + 1 hero = 10 clips × 150f (except hero 90f) = 1590 frames (~53s)
//
// Catalog is empty until generation runs — arrays will be populated after RunPod batch

const arrivalClips = catalog.filter((e) => e.shot_type === "arrival");
const trainingClips = catalog.filter((e) => e.shot_type === "training");
const atmosphereClips = catalog.filter((e) => e.shot_type === "atmosphere");
const heroClips = catalog.filter((e) => e.shot_type === "hero");

// Cycle through available clips for each item slot
function pick<T>(arr: T[], i: number): T {
  return arr[i % arr.length];
}

const FRAMES = 150; // 5s at 30fps

const clips = [
  { entry: arrivalClips[0] || trainingClips[0], durationInFrames: FRAMES },     // opening hook
  { entry: pick(trainingClips, 0), durationInFrames: FRAMES },                   // item 1
  { entry: pick(atmosphereClips, 0), durationInFrames: FRAMES },                 // item 2
  { entry: pick(trainingClips, 1), durationInFrames: FRAMES },                   // item 3
  { entry: pick(atmosphereClips, 1), durationInFrames: FRAMES },                 // item 4
  { entry: pick(trainingClips, 2), durationInFrames: FRAMES },                   // item 5
  { entry: pick(atmosphereClips, 2), durationInFrames: FRAMES },                 // item 6
  { entry: pick(trainingClips, 3), durationInFrames: FRAMES },                   // item 7
  { entry: pick(atmosphereClips, 3), durationInFrames: FRAMES },                 // item 8
  { entry: heroClips[0] || arrivalClips[0], durationInFrames: 90 },              // closing hero
].filter((c) => c.entry != null);

export const TrainingPartnerReel: React.FC = () => {
  if (clips.length === 0) {
    // Catalog empty — generate clips first using content-generation/generate.py
    return null;
  }

  return (
    <ReelComposition
      clips={clips}
      hookText={"8 WAYS TO GET DANGEROUS WITHOUT A TRAINING PARTNER"}
      overlayItems={[
        { text: "8 WAYS TO GET DANGEROUS WITHOUT A TRAINING PARTNER", startFrame: 10,   durationInFrames: 130, position: "top",    isHook: true },
        { text: "SHADOW ROUNDS BECOME REAL FIGHTS",                   startFrame: 160,  durationInFrames: 130, position: "bottom" },
        { text: "FILM STUDY FILLS THE REPS",                          startFrame: 310,  durationInFrames: 130, position: "bottom" },
        { text: "EVERY BAG ROUND HAS A PURPOSE",                      startFrame: 460,  durationInFrames: 130, position: "bottom" },
        { text: "FOOTWORK DRILLS REPLACE YOUR PARTNER",               startFrame: 610,  durationInFrames: 130, position: "bottom" },
        { text: "TRAIN HEAD MOVEMENT SOLO",                           startFrame: 760,  durationInFrames: 130, position: "bottom" },
        { text: "THE MIRROR SHOWS YOUR TELLS",                        startFrame: 910,  durationInFrames: 130, position: "bottom" },
        { text: "STACK MENTAL REPS BETWEEN SESSIONS",                 startFrame: 1060, durationInFrames: 130, position: "bottom" },
        { text: "SOLO DRILLING WIRES MUSCLE MEMORY",                  startFrame: 1210, durationInFrames: 130, position: "bottom" },
        { text: "READ DESCRIPTION ⬇️",                                startFrame: 1490, durationInFrames: 90,  position: "bottom" },
      ]}
    />
  );
};
