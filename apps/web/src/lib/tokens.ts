/**
 * SteamScoop Design Tokens and Visualization Palettes.
 * Adheres to CODING_STANDARDS.md and modern web accessible color contrast.
 */

export const SENTIMENT_COLORS = {
  positive: "#10b981", // Emerald 500
  negative: "#f43f5e", // Rose 500
  neutral: "#94a3b8", // Slate 400
} as const;

export const ASPECT_COLORS: Record<string, string> = {
  gameplay: "#0ea5e9", // Sky 500
  graphics: "#a855f7", // Purple 500
  performance: "#f97316", // Orange 500
  story: "#ec4899", // Pink 500
  audio: "#06b6d4", // Cyan 500
  multiplayer: "#6366f1", // Indigo 500
  content: "#14b8a6", // Teal 500
  pricing: "#eab308", // Yellow 500
  controls: "#8b5cf6", // Violet 500
  technical: "#ef4444", // Red 500
  default: "#64748b", // Slate 500
};

export const COMPARISON_PALETTE = [
  "#38bdf8", // Sky 400
  "#34d399", // Emerald 400
  "#fbbf24", // Amber 400
  "#f472b6", // Pink 400
  "#a78bfa", // Violet 400
] as const;

export const ECHARTS_DARK_THEME = {
  backgroundColor: "transparent",
  textStyle: {
    fontFamily: "Inter, system-ui, sans-serif",
    color: "#94a3b8", // Slate 400
  },
  title: {
    textStyle: {
      color: "#f8fafc", // Slate 50
      fontWeight: 600,
    },
    subtextStyle: {
      color: "#64748b", // Slate 500
    },
  },
  tooltip: {
    backgroundColor: "#0f172a", // Slate 900
    borderColor: "#334155", // Slate 700
    borderWidth: 1,
    textStyle: {
      color: "#f1f5f9", // Slate 100
      fontSize: 12,
    },
    extraCssText: "box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5); border-radius: 8px;",
  },
  grid: {
    containLabel: true,
    top: 36,
    right: 20,
    bottom: 24,
    left: 20,
  },
};

