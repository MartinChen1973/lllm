"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

export type McpSettingsResponse = {
  source: "file" | "environment";
  servers: Array<{
    id: string;
    url: string;
    connected: boolean;
    tool_count: number;
    error: string | null;
    headers: Record<string, string>;
    status?: "active" | "deleted";
  }>;
  total_tools: number;
  configured_servers: number;
  connected_servers: number;
};

type FormRow = {
  /** Stable React list key; must not change when the user edits Server id (that would remount inputs and drop focus). */
  rowKey: string;
  id: string;
  url: string;
  headersText: string;
  // ⬇️ Soft-removed rows stay in API storage until restored or .env reset
  deleted: boolean;
};

function newRowKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `row_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

const backendBase = (
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:3501"
).replace(/\/$/, "");

function errorMessageFromResponseBody(data: unknown, status: number): string {
  if (data && typeof data === "object" && data !== null && "detail" in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    return JSON.stringify(d);
  }
  if (data && typeof data === "object" && data !== null) {
    return JSON.stringify(data);
  }
  return `HTTP ${status}`;
}

function statusFromResponse(data: McpSettingsResponse): McpSettingsResponse {
  return data;
}

function rowsFromStatus(s: McpSettingsResponse): FormRow[] {
  return s.servers.map((row) => ({
    rowKey: row.id,
    id: row.id,
    url: row.url,
    headersText:
      Object.keys(row.headers ?? {}).length > 0 ? JSON.stringify(row.headers, null, 0) : "",
    deleted: row.status === "deleted",
  }));
}

type BuildServersResult =
  | { ok: true; servers: { id: string; url: string; headers: Record<string, string>; deleted: boolean }[] }
  | { ok: false; message: string };

function validateAndBuildServers(rows: FormRow[]): BuildServersResult {
  const servers: {
    id: string;
    url: string;
    headers: Record<string, string>;
    deleted: boolean;
  }[] = [];
  for (const row of rows) {
    const id = row.id.trim();
    const url = row.url.trim();
    if (!id || !url) {
      return { ok: false, message: "Each row needs a server id and URL." };
    }
    let headers: Record<string, string> = {};
    const ht = row.headersText.trim();
    if (ht) {
      try {
        const parsed = JSON.parse(ht) as unknown;
        if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
          return {
            ok: false,
            message: "Headers must be a JSON object, e.g. {\"Authorization\": \"Bearer …\"}.",
          };
        }
        headers = Object.fromEntries(
          Object.entries(parsed as Record<string, unknown>).map(([k, v]) => [k, String(v)])
        );
      } catch {
        return { ok: false, message: "Invalid JSON in Headers for one of the rows." };
      }
    }
    servers.push({ id, url, headers, deleted: row.deleted });
  }
  return { ok: true, servers };
}

// ⬇️ Full-page user settings (opened in a new browser tab from chat to avoid modal scroll/layout issues)
export default function UserSettingsPage() {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<McpSettingsResponse | null>(null);
  const [rows, setRows] = useState<FormRow[]>([]);
  const [activeSection, setActiveSection] = useState<"mcp">("mcp");
  // ⬇️ Serialize PUT /settings/mcp so rapid Remove/Restore cannot race and drop updates
  const mcpSyncChainRef = useRef(Promise.resolve());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${backendBase}/settings/mcp`);
      const resText = await res.text();
      let data: unknown = {};
      try {
        data = resText ? JSON.parse(resText) : {};
      } catch {
        if (!res.ok) {
          throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
        }
      }
      if (!res.ok) {
        throw new Error(errorMessageFromResponseBody(data, res.status));
      }
      const s = statusFromResponse(data as McpSettingsResponse);
      setStatus(s);
      setRows(rowsFromStatus(s));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load MCP settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const syncRowsToBackend = useCallback(async (nextRows: FormRow[]) => {
    const built = validateAndBuildServers(nextRows);
    if (!built.ok) {
      setError(built.message);
      return;
    }
    const op = async () => {
      setSaving(true);
      setError(null);
      try {
        const res = await fetch(`${backendBase}/settings/mcp`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ servers: built.servers }),
        });
        const resText = await res.text();
        let data: unknown = {};
        try {
          data = resText ? JSON.parse(resText) : {};
        } catch {
          if (!res.ok) {
            throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
          }
        }
        if (!res.ok) {
          throw new Error(errorMessageFromResponseBody(data, res.status));
        }
        const s = statusFromResponse(data as McpSettingsResponse);
        setStatus(s);
        setRows(rowsFromStatus(s));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Sync failed");
        await load();
      } finally {
        setSaving(false);
      }
    };
    mcpSyncChainRef.current = mcpSyncChainRef.current.then(op).catch(() => undefined);
    await mcpSyncChainRef.current;
  }, [load]);

  const addRow = useCallback(() => {
    setRows((r) => [
      ...r,
      {
        rowKey: newRowKey(),
        id: `server_${r.filter((x) => !x.deleted).length + 1}`,
        url: "http://127.0.0.1:8501/mcp",
        headersText: "",
        deleted: false,
      },
    ]);
  }, []);

  const removeRow = useCallback(
    async (index: number) => {
      let snapshot: FormRow[] | null = null;
      setRows((prev) => {
        const row = prev[index];
        if (!row || row.deleted) return prev;
        snapshot = prev.map((x, i) => (i === index ? { ...x, deleted: true } : x));
        return snapshot;
      });
      if (snapshot) await syncRowsToBackend(snapshot);
    },
    [syncRowsToBackend]
  );

  const recoverRow = useCallback(
    async (index: number) => {
      let snapshot: FormRow[] | null = null;
      setRows((prev) => {
        const row = prev[index];
        if (!row || !row.deleted) return prev;
        snapshot = prev.map((x, i) => (i === index ? { ...x, deleted: false } : x));
        return snapshot;
      });
      if (snapshot) await syncRowsToBackend(snapshot);
    },
    [syncRowsToBackend]
  );

  const updateRow = useCallback((index: number, patch: Partial<FormRow>) => {
    setRows((r) => r.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }, []);

  const save = useCallback(async () => {
    await syncRowsToBackend(rows);
  }, [rows, syncRowsToBackend]);

  const clearCustom = useCallback(async () => {
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${backendBase}/settings/mcp`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ servers: [] }),
      });
      const resText = await res.text();
      let data: unknown = {};
      try {
        data = resText ? JSON.parse(resText) : {};
      } catch {
        if (!res.ok) {
          throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
        }
      }
      if (!res.ok) {
        throw new Error(errorMessageFromResponseBody(data, res.status));
      }
      const s = statusFromResponse(data as McpSettingsResponse);
      setStatus(s);
      setRows(rowsFromStatus(s));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not reset MCP settings");
    } finally {
      setSaving(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#131314] text-[#e3e3e3]">
      <header className="border-b border-white/10 bg-[#1b1b1c] px-4 py-4 md:px-8">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3">
          <h1 id="settings-title" className="text-base font-semibold text-white">
            User settings
          </h1>
          <Link
            href="/"
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-sm text-white/85 transition hover:bg-white/10"
          >
            Back to chat
          </Link>
        </div>
      </header>

      <div className="mx-auto flex max-w-5xl flex-col gap-0 md:flex-row">
        <nav
          className="shrink-0 border-b border-white/10 bg-[#1b1b1c]/80 p-3 md:w-44 md:border-b-0 md:border-r md:border-white/10"
          aria-label="Settings sections"
        >
          <button
            type="button"
            onClick={() => setActiveSection("mcp")}
            className={`w-full rounded-lg px-3 py-2 text-left text-sm transition ${
              activeSection === "mcp"
                ? "bg-white/10 text-white"
                : "text-white/65 hover:bg-white/[0.06]"
            }`}
          >
            MCP tools
          </button>
        </nav>

        <main className="min-w-0 flex-1 p-4 md:p-6">
          {activeSection === "mcp" && (
            <div className="flex max-w-3xl flex-col gap-4">
              <div>
                <h2 className="text-sm font-medium text-white">MCP tools</h2>
                <p className="mt-1 text-xs leading-relaxed text-white/45">
                  Configure Streamable HTTP MCP endpoints. When you save a non-empty list, it is
                  stored on the AI API host and overrides environment defaults until you clear it.
                  Removing a server deactivates it on the API (soft delete); restore it from the
                  removed list below. Optional headers are sent as HTTP headers (JSON object per
                  server).
                </p>
              </div>

              {loading && <p className="text-sm text-white/50">Loading…</p>}

              {status && !loading && (
                <div className="rounded-xl border border-white/10 bg-black/25 px-4 py-3 text-sm">
                  <p className="text-white/90">
                    <span className="text-white/50">Configuration source:</span>{" "}
                    {status.source === "file" ? "Saved file on API" : "Environment (.env)"}
                  </p>
                  <p className="mt-2 text-white/85">
                    <span className="font-medium text-emerald-400/95">{status.total_tools}</span>
                    <span className="text-white/50"> tools loaded · </span>
                    <span className="text-white/80">
                      {status.connected_servers}/{status.configured_servers}
                    </span>
                    <span className="text-white/50"> servers connected</span>
                  </p>
                </div>
              )}

              {error && <p className="text-sm text-red-400">{error}</p>}

              {!loading && (
                <div className="flex flex-col gap-6">
                  <div className="flex flex-col gap-2">
                    <h3 className="text-xs font-medium uppercase tracking-wide text-white/50">
                      Active servers
                    </h3>
                    <div className="hidden gap-2 text-[11px] font-medium uppercase tracking-wide text-white/40 md:grid md:grid-cols-[1fr_2fr_1fr_auto]">
                      <span>Server id</span>
                      <span>URL</span>
                      <span className="col-span-2">Headers (JSON)</span>
                    </div>
                    {rows.filter((r) => !r.deleted).length === 0 && (
                      <p className="py-3 text-center text-sm text-white/40">
                        No active servers — add one, reload from the API, or restore a removed entry
                        below.
                      </p>
                    )}
                    {rows.map((row, i) =>
                      !row.deleted ? (
                        <div
                          key={row.rowKey}
                          className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#131314] p-3 md:grid md:grid-cols-[1fr_2fr_1fr_auto]"
                        >
                          <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                            Server id
                          </label>
                          <input
                            value={row.id}
                            onChange={(e) => updateRow(i, { id: e.target.value })}
                            placeholder="oa"
                            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none placeholder:text-white/30 focus:border-blue-500/50"
                            disabled={saving}
                          />
                          <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                            URL
                          </label>
                          <input
                            value={row.url}
                            onChange={(e) => updateRow(i, { url: e.target.value })}
                            placeholder="http://127.0.0.1:8501/mcp"
                            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none placeholder:text-white/30 focus:border-blue-500/50"
                            disabled={saving}
                          />
                          <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                            Headers (JSON)
                          </label>
                          <input
                            value={row.headersText}
                            onChange={(e) => updateRow(i, { headersText: e.target.value })}
                            placeholder='{"Authorization": "Bearer …"}'
                            className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-xs text-white/90 outline-none placeholder:text-white/25 focus:border-blue-500/50 md:col-span-1"
                            disabled={saving}
                          />
                          <div className="flex items-center justify-end md:justify-center">
                            <button
                              type="button"
                              onClick={() => void removeRow(i)}
                              className="text-xs text-red-400/90 hover:text-red-300"
                              disabled={saving}
                            >
                              Remove
                            </button>
                          </div>
                          {status?.servers.find((s) => s.id === row.id)?.status !== "deleted" && (
                            <div className="text-xs text-white/45 md:col-span-4">
                              Last status:{" "}
                              {status?.servers.find((s) => s.id === row.id)?.connected ? (
                                <span className="text-emerald-400/90">
                                  connected ·{" "}
                                  {status?.servers.find((s) => s.id === row.id)?.tool_count} tools
                                </span>
                              ) : (
                                <span className="text-amber-400/90">
                                  not connected
                                  {status?.servers.find((s) => s.id === row.id)?.error
                                    ? ` — ${status?.servers.find((s) => s.id === row.id)?.error}`
                                    : ""}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ) : null
                    )}
                  </div>

                  {rows.some((r) => r.deleted) && (
                    <div className="flex flex-col gap-2">
                      <h3 className="text-xs font-medium uppercase tracking-wide text-white/50">
                        Removed (stored on API, not connected)
                      </h3>
                      <p className="text-[11px] leading-relaxed text-white/35">
                        These entries remain in{" "}
                        <code className="text-white/50">mcp_config.json</code> until you restore
                        them or use &quot;Use .env defaults&quot; to drop the saved file.
                      </p>
                      {rows.map((row, i) =>
                        row.deleted ? (
                          <div
                            key={row.rowKey}
                            className="flex flex-col gap-2 rounded-xl border border-white/5 bg-black/20 p-3 opacity-90 md:grid md:grid-cols-[1fr_2fr_1fr_auto]"
                          >
                            <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                              Server id
                            </label>
                            <input
                              value={row.id}
                              onChange={(e) => updateRow(i, { id: e.target.value })}
                              placeholder="oa"
                              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none placeholder:text-white/30 focus:border-blue-500/50"
                              disabled={saving}
                            />
                            <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                              URL
                            </label>
                            <input
                              value={row.url}
                              onChange={(e) => updateRow(i, { url: e.target.value })}
                              placeholder="http://127.0.0.1:8501/mcp"
                              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-sm text-white outline-none placeholder:text-white/30 focus:border-blue-500/50"
                              disabled={saving}
                            />
                            <label className="text-[10px] font-medium uppercase text-white/40 md:hidden">
                              Headers (JSON)
                            </label>
                            <input
                              value={row.headersText}
                              onChange={(e) => updateRow(i, { headersText: e.target.value })}
                              placeholder='{"Authorization": "Bearer …"}'
                              className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-xs text-white/90 outline-none placeholder:text-white/25 focus:border-blue-500/50 md:col-span-1"
                              disabled={saving}
                            />
                            <div className="flex items-center justify-end md:justify-center">
                              <button
                                type="button"
                                onClick={() => void recoverRow(i)}
                                className="text-xs text-emerald-400/90 hover:text-emerald-300"
                                disabled={saving}
                              >
                                Restore
                              </button>
                            </div>
                            <div className="text-xs text-white/40 md:col-span-4">
                              Not loaded for the agent. Click Restore to sync and reconnect, or edit
                              fields then Save and apply.
                            </div>
                          </div>
                        ) : null
                      )}
                    </div>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                <button
                  type="button"
                  onClick={addRow}
                  disabled={saving || loading}
                  className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10 disabled:opacity-45"
                >
                  Add server
                </button>
                <button
                  type="button"
                  onClick={() => void load()}
                  disabled={saving || loading}
                  className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10 disabled:opacity-45"
                >
                  Reload from API
                </button>
                <button
                  type="button"
                  onClick={() => void clearCustom()}
                  disabled={saving || loading}
                  className="rounded-full border border-amber-500/35 bg-amber-500/10 px-4 py-2 text-sm text-amber-200/90 hover:bg-amber-500/15 disabled:opacity-45"
                >
                  Use .env defaults
                </button>
                <button
                  type="button"
                  onClick={() => void save()}
                  disabled={saving || loading}
                  className="rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-45"
                >
                  {saving ? "Saving…" : "Save and apply"}
                </button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
