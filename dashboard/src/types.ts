export type Archetype = "identity" | "tactical" | string;

export interface Profile {
  followers_count: number;
  follows_count: number;
  media_count: number;
  biography: string;
  website: string | null;
  dm_trigger_current: string;
}

export interface DailyPoint {
  date: string;
  reach: number;
  views: number;
  new_followers: number;
}

export interface TopMedia {
  date: string;
  type: string;
  archetype: Archetype;
  views: number;
  reach: number;
  saved: number;
  shares: number;
  likes: number;
  comments: number;
  avg_watch_ms: number;
  hook: string;
  cta: string;
  permalink: string;
}

export interface Snapshot {
  pulled_at: string;
  source: string;
  account: { username: string; id: string; windsor_account: string };
  note?: string;
  profile: Profile;
  daily_last_30d: DailyPoint[];
  top_media_by_views: TopMedia[];
  carousels?: { date: string; views: number; shares?: number; hook: string; note?: string }[];
  observed_dm_triggers?: string[];
}
