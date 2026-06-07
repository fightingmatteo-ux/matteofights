import React from "react";
import { interpolate, useCurrentFrame } from "remotion";

interface TextOverlayProps {
  text: string;
  position?: "top" | "center" | "bottom";
  isHook?: boolean;
}

export const TextOverlay: React.FC<TextOverlayProps> = ({
  text,
  position = "center",
  isHook = false,
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  const positionStyle: React.CSSProperties = {
    top: position === "top" ? 80 : position === "center" ? "40%" : undefined,
    bottom: position === "bottom" ? 120 : undefined,
  };

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        padding: "0 40px",
        textAlign: "center",
        opacity,
        ...positionStyle,
      }}
    >
      <span
        style={{
          fontFamily: "Arial Black, sans-serif",
          fontWeight: 900,
          fontSize: isHook ? 72 : 52,
          color: "#FFFFFF",
          textTransform: "uppercase",
          letterSpacing: 2,
          textShadow: "0 4px 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)",
          lineHeight: 1.1,
          display: "block",
        }}
      >
        {text}
      </span>
    </div>
  );
};
