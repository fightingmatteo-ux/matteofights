import { test } from "node:test";
import assert from "node:assert/strict";
import { slotDue, queueDue } from "./due.js";

// 2026-10-20 is EDT (UTC-4): 12:31 NY = 16:31Z
const t = (iso) => Date.parse(iso);

test("slot window is [slot, slot+5min)", () => {
  assert.equal(slotDue(t("2026-10-20T16:31:00Z"), "12:31,18:31"), true);
  assert.equal(slotDue(t("2026-10-20T16:35:59Z"), "12:31,18:31"), true);
  assert.equal(slotDue(t("2026-10-20T16:36:00Z"), "12:31,18:31"), false);
  assert.equal(slotDue(t("2026-10-20T16:30:59Z"), "12:31"), false);
});

test("DST: 2026-11-01 is EST (UTC-5), 12:31 NY = 17:31Z", () => {
  assert.equal(slotDue(t("2026-11-01T17:31:00Z"), "12:31"), true);
  assert.equal(slotDue(t("2026-11-01T16:31:00Z"), "12:31"), false);
});

const item = (o = {}) => ({ id: "x", approved: true, status: "queued", not_before: "2026-10-20T16:00:00Z", ...o });

test("queueDue: newly due item fires right away", () => {
  assert.equal(queueDue(t("2026-10-20T16:02:00Z"), [item()]), true);
});

test("queueDue: skips unapproved, posting, posted, failed, manual audio, pending sound, not yet due", () => {
  const now = t("2026-10-20T16:02:00Z");
  for (const o of [{ approved: false }, { status: "posting" }, { status: "posted" }, { status: "failed" },
                   { audio_status: "manual" }, { sound_pending: true }, { not_before: "2026-10-20T17:00:00Z" }])
    assert.equal(queueDue(now, [item(o)]), false, JSON.stringify(o));
});

test("queueDue: an item due for a while retries only at :00-:04 and :30-:34", () => {
  assert.equal(queueDue(t("2026-10-20T17:12:00Z"), [item()]), false);
  assert.equal(queueDue(t("2026-10-20T17:31:00Z"), [item()]), true);
  assert.equal(queueDue(t("2026-10-20T18:03:00Z"), [item()]), true);
});
