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

/**
 * A post as the Graph API returns it on the current token. Everything here is live —
 * likes, comments, caption and permalink only need instagram_basic. Reach, views, saves
 * and watch time are deliberately absent: those need instagram_manage_insights, and an
 * absent field is better than a months-old one wearing a live label.
 */
export interface RecentMedia {
  id: string;
  date: string | null;
  timestamp: string | null;
  /** REELS | FEED | STORY | CAROUSEL_ALBUM ... */
  type: string;
  likes: number;
  comments: number;
  engagement: number;
  hook: string;
  caption: string;
  permalink: string | null;
  thumbnail: string | null;
}

/** What the token could actually see on the run that produced this snapshot. */
export interface Capabilities {
  profile: boolean;
  media: boolean;
  insights: boolean;
}

export interface Snapshot {
  pulled_at: string;
  /** Full ISO timestamp — lets the UI say "42s ago" instead of only "today". */
  pulled_at_iso?: string;
  source: string;
  account: { username: string; id: string; windsor_account: string };
  note?: string;
  profile: Profile;
  capabilities?: Capabilities;
  daily_last_30d: DailyPoint[];
  top_media_by_views: TopMedia[];
  recent_media?: RecentMedia[];
  /** Likes + comments across posts published in the trailing 30 days. Computed at pull time. */
  engagement_30d?: {
    since: string;
    posts: number;
    likes: number;
    comments: number;
    total: number;
  };
  /** Follower movement against the newest snapshot from an earlier day. */
  follower_delta?: { since: string; value: number };
  carousels?: { date: string; views: number; shares?: number; hook: string; note?: string }[];
  observed_dm_triggers?: string[];
  partial?: boolean;
  carried_from?: string | null;
  carried_fields?: string[];
  insights_error?: string;
  media_error?: string;
}

/** POST /api/refresh and the `lastOutcome` inside GET /api/status. */
export interface PullOutcome {
  at: string;
  ok: boolean;
  trigger: string;
  followers?: number;
  message: string;
}

/** A reel Jarvis has queued, waiting for a human to press publish. */
export interface PendingReel {
  id: string;
  stagedAt: string;
  videoName: string;
  caption: string;
  experiment: string | null;
  sourcePath: string | null;
  speed: number | null;
  sizeBytes: number | null;
  status: "pending" | "publishing" | "published" | "failed" | "discarded";
  publishedId?: string;
  error?: string;
}

/** GET /api/status - the backend's view of the refresh loop. */
export interface LiveStatus {
  running: boolean;
  nextRefreshInMs: number | null;
  refreshEveryMs: number;
  watching: boolean;
  lastOutcome: PullOutcome | null;
  snapshot: {
    pulledAt: string | null;
    pulledAtIso: string | null;
    ageMs: number | null;
    followers: number | null;
    capabilities: Capabilities | null;
    insightsError: string | null;
    partial: boolean;
    totalSnapshots: number;
  };
  /** How many reels are waiting on a human decision. Drives the queue tab's badge. */
  pendingPublishes?: number;
}
