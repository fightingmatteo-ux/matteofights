// What the ticker should start this tick. Pure functions, tested by due.test.js (node --test tools/ticker/).
const WINDOW_MS = 5 * 60 * 1000; // the cron runs every 5 minutes

const nyHM = (ms, tz) =>
  new Intl.DateTimeFormat("en-GB", { timeZone: tz, hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(ms));
const mins = (hm) => { const [h, m] = hm.split(":").map(Number); return h * 60 + m; };

// true when now is within [slot, slot + 5 min) of any "HH:MM" New York slot in the comma list
export function slotDue(nowMs, slots, tz = "America/New_York") {
  const now = mins(nyHM(nowMs, tz));
  return (slots || "").split(",").filter(Boolean).some((s) => { const d = now - mins(s.trim()); return d >= 0 && d < 5; });
}

// Same rule as tools/instagram/run_queue.py picks from.
const ready = (i, nowMs) => i.approved === true && i.status === "queued" && i.audio_status !== "manual" &&
  !i.sound_pending && Date.parse(i.not_before) <= nowMs;

// true when an approved item just became due (fire now), or one has been due a while (run_queue may be waiting
// out min_gap_hours): then retry only at :00-:04 and :30-:34 so a waiting item can't start a run every 5 minutes.
export function queueDue(nowMs, items) {
  const due = (items || []).filter((i) => ready(i, nowMs));
  if (!due.length) return false;
  if (due.some((i) => nowMs - Date.parse(i.not_before) < WINDOW_MS)) return true;
  return new Date(nowMs).getUTCMinutes() % 30 < 5;
}
