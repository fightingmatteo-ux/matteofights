import React from "react";
import { Video, staticFile } from "remotion";
import type { AssetEntry } from "../lib/catalog";

interface VideoClipProps {
  entry: AssetEntry;
  startFrom?: number;
}

export const VideoClip: React.FC<VideoClipProps> = ({ entry, startFrom = 0 }) => {
  return (
    <Video
      src={staticFile(entry.file)}
      startFrom={startFrom}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  );
};
