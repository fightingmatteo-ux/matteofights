// D1 (binding DB) helpers: same table and JSON shape as tools/state.py (docs: kind, id, data JSON).
const NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%SZ','now')";

export async function all(env, kind) {
  const { results } = await env.DB.prepare("SELECT id, data, updated_at FROM docs WHERE kind = ? ORDER BY id").bind(kind).all();
  return results.map((r) => ({ ...JSON.parse(r.data), id: r.id, updated_at: r.updated_at }));
}

export async function get(env, kind, id) {
  const r = await env.DB.prepare("SELECT data FROM docs WHERE kind = ? AND id = ?").bind(kind, id).first();
  return r ? JSON.parse(r.data) : null;
}

export async function put(env, kind, id, data) {
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES (?, ?, ?) ON CONFLICT (kind, id) DO UPDATE SET data = excluded.data, updated_at = ${NOW_SQL}`,
  ).bind(kind, id, JSON.stringify(data)).run();
}

export async function patch(env, kind, id, fields) {
  const f = JSON.stringify(fields);
  await env.DB.prepare(
    `INSERT INTO docs (kind, id, data) VALUES (?, ?, json_patch('{}', ?)) ON CONFLICT (kind, id) DO UPDATE SET data = json_patch(docs.data, ?), updated_at = ${NOW_SQL}`,
  ).bind(kind, id, f, f).run();
}

export const now = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");
export const newId = () => now().slice(0, 10) + "-" + crypto.randomUUID().slice(0, 6);
