import catalogData from "../../../content-bank/catalog.json";

export interface AssetEntry {
  id: string;
  file: string;
  source: "ai" | "real";
  shot_type: "arrival" | "training" | "atmosphere" | "outdoor" | "lifestyle" | "hero";
  style_preset: "gym" | "outdoor" | "lifestyle";
  mood: string;
  likeness: boolean;
  tags: string[];
  duration_sec: number;
  prompt?: string;
  generated_at?: string;
}

export const catalog: AssetEntry[] = catalogData as AssetEntry[];

export function queryByType(shot_type: string): AssetEntry[] {
  return catalog.filter((e) => e.shot_type === shot_type);
}

export function queryByTags(tags: string[]): AssetEntry[] {
  return catalog.filter((e) => tags.every((t) => e.tags.includes(t)));
}
