"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

export type SkillInfoOut = {
  id: string;
  skill_md_path: string;
};

export type ModelSettingsOut = {
  current_model: string;
  models: string[];
};

export type McpSettingsResponse = {
  source: "file" | "environment";
  servers: Array<{
    id: string;
    url: string;
    connected: boolean;
    tool_count: number;
    tool_names: string[];
    error: string | null;
    headers: Record<string, string>;
    status?: "active" | "deleted";
  }>;
  total_tools: number;
  configured_servers: number;
  connected_servers: number;
  mcp_tool_names: string[];
  skills: SkillInfoOut[];
};

/** Multi-line hint for native `title` tooltips: every skill and each MCP server with its tools. */
export function buildCapabilitiesHoverText(s: McpSettingsResponse): string {
  const lines: string[] = [];
  lines.push(`⚙️ Configuration source: ${s.source}`);
  lines.push("");
  lines.push("📚 Skills:");
  const skills = s.skills ?? [];
  if (skills.length === 0) {
    lines.push("  📭 (none discovered under skills/)");
  } else {
    for (const sk of skills) {
      lines.push(`  📌 ${sk.id} — ${sk.skill_md_path}`);
    }
  }
  lines.push("");
  lines.push("🔌 MCP servers and tools:");
  const srvs = s.servers ?? [];
  if (srvs.length === 0) {
    lines.push("  📭 (none configured)");
  } else {
    for (const srv of srvs) {
      const removed = srv.status === "deleted";
      const st = removed ? "removed (inactive)" : srv.connected ? "connected" : "not connected";
      lines.push(`  🖥️ ${srv.id}`);
      lines.push(`    🔗 URL: ${srv.url}`);
      lines.push(`    📡 Status: ${st}`);
      if (removed) {
        lines.push("    ⏸️ Tools: —");
      } else if (!srv.connected && srv.error) {
        lines.push(`    ⚠️ Error: ${srv.error}`);
        lines.push("    🛠️ Tools: (unavailable)");
      } else {
        const tn = srv.tool_names ?? [];
        lines.push(
          tn.length > 0
            ? `    🛠️ Tools: ${tn.map((t) => `🔧 ${t}`).join(", ")}`
            : "    🛠️ Tools: (none)"
        );
      }
    }
  }
  return lines.join("\n");
}

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
  return {
    ...data,
    mcp_tool_names: data.mcp_tool_names ?? [],
    skills: data.skills ?? [],
    servers: (data.servers ?? []).map((row) => ({
      ...row,
      tool_names: row.tool_names ?? [],
    })),
  };
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
  const [activeSection, setActiveSection] = useState<"mcp" | "models" | "skills">("mcp");
  const [modelCurrent, setModelCurrent] = useState("");
  const [modelList, setModelList] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [modelsSaving, setModelsSaving] = useState(false);
  const [newModelInput, setNewModelInput] = useState("");
  const [skillsList, setSkillsList] = useState<SkillInfoOut[]>([]);
  const [skillsLoading, setSkillsLoading] = useState(false);
  const [skillsError, setSkillsError] = useState<string | null>(null);
  const [skillSaving, setSkillSaving] = useState(false);
  const [newSkillId, setNewSkillId] = useState("");
  const [newSkillContent, setNewSkillContent] = useState(
    "# Skill\n\nDescribe when this skill applies and the steps to follow.\n"
  );
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [renameSkillId, setRenameSkillId] = useState("");
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

  const loadModels = useCallback(async () => {
    setModelsLoading(true);
    setModelsError(null);
    try {
      const res = await fetch(`${backendBase}/settings/models`);
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
      const m = data as ModelSettingsOut;
      setModelCurrent(m.current_model ?? "");
      setModelList(Array.isArray(m.models) ? m.models : []);
    } catch (e) {
      setModelsError(e instanceof Error ? e.message : "Could not load model settings");
    } finally {
      setModelsLoading(false);
    }
  }, []);

  const loadSkills = useCallback(async () => {
    setSkillsLoading(true);
    setSkillsError(null);
    try {
      const res = await fetch(`${backendBase}/settings/skills`);
      const resText = await res.text();
      let data: unknown = [];
      try {
        data = resText ? JSON.parse(resText) : [];
      } catch {
        if (!res.ok) {
          throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
        }
      }
      if (!res.ok) {
        throw new Error(errorMessageFromResponseBody(data, res.status));
      }
      setSkillsList(Array.isArray(data) ? (data as SkillInfoOut[]) : []);
    } catch (e) {
      setSkillsError(e instanceof Error ? e.message : "Could not load skills");
    } finally {
      setSkillsLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (activeSection === "skills") {
      void loadSkills();
    }
  }, [activeSection, loadSkills]);

  useEffect(() => {
    if (activeSection === "models") {
      void loadModels();
    }
  }, [activeSection, loadModels]);

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

  const refreshAfterSkillMutation = useCallback(async () => {
    await Promise.all([loadSkills(), load()]);
  }, [loadSkills, load]);

  const openSkillEditor = useCallback(async (id: string) => {
    setSkillsError(null);
    setSkillSaving(true);
    try {
      const res = await fetch(`${backendBase}/settings/skills/${encodeURIComponent(id)}`);
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
      const d = data as { content: string; id: string };
      setEditingId(d.id);
      setEditContent(d.content);
      setRenameSkillId("");
    } catch (e) {
      setSkillsError(e instanceof Error ? e.message : "Could not load skill");
    } finally {
      setSkillSaving(false);
    }
  }, []);

  const closeSkillEditor = useCallback(() => {
    setEditingId(null);
    setEditContent("");
    setRenameSkillId("");
  }, []);

  const saveEditedSkill = useCallback(async () => {
    if (!editingId) return;
    setSkillSaving(true);
    setSkillsError(null);
    try {
      const body: { content: string; new_id?: string } = { content: editContent };
      const r = renameSkillId.trim();
      if (r && r !== editingId) {
        body.new_id = r;
      }
      const res = await fetch(`${backendBase}/settings/skills/${encodeURIComponent(editingId)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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
      const d = data as { id: string };
      setEditingId(d.id);
      setRenameSkillId("");
      await refreshAfterSkillMutation();
    } catch (e) {
      setSkillsError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSkillSaving(false);
    }
  }, [editingId, editContent, renameSkillId, refreshAfterSkillMutation]);

  const createSkill = useCallback(async () => {
    const id = newSkillId.trim();
    if (!id) {
      setSkillsError("Skill id is required.");
      return;
    }
    setSkillSaving(true);
    setSkillsError(null);
    try {
      const res = await fetch(`${backendBase}/settings/skills`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, content: newSkillContent }),
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
      await refreshAfterSkillMutation();
      setNewSkillId("");
    } catch (e) {
      setSkillsError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setSkillSaving(false);
    }
  }, [newSkillId, newSkillContent, refreshAfterSkillMutation]);

  const deleteSkill = useCallback(
    async (id: string) => {
      if (!window.confirm(`Delete skill "${id}" and its files on the API host?`)) {
        return;
      }
      setSkillSaving(true);
      setSkillsError(null);
      try {
        const res = await fetch(`${backendBase}/settings/skills/${encodeURIComponent(id)}`, {
          method: "DELETE",
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
        if (editingId === id) {
          closeSkillEditor();
        }
        await refreshAfterSkillMutation();
      } catch (e) {
        setSkillsError(e instanceof Error ? e.message : "Delete failed");
      } finally {
        setSkillSaving(false);
      }
    },
    [editingId, closeSkillEditor, refreshAfterSkillMutation]
  );

  const saveModels = useCallback(async () => {
    setModelsSaving(true);
    setModelsError(null);
    try {
      const res = await fetch(`${backendBase}/settings/models`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_model: modelCurrent, models: modelList }),
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
      const m = data as ModelSettingsOut;
      setModelCurrent(m.current_model ?? "");
      setModelList(Array.isArray(m.models) ? m.models : []);
    } catch (e) {
      setModelsError(e instanceof Error ? e.message : "Could not save model settings");
    } finally {
      setModelsSaving(false);
    }
  }, [modelCurrent, modelList]);

  const addModelToList = useCallback(() => {
    const t = newModelInput.trim();
    if (!t) return;
    setModelList((prev) => (prev.includes(t) ? prev : [...prev, t]));
    setModelCurrent((cur) => (cur.trim() ? cur : t));
    setNewModelInput("");
  }, [newModelInput]);

  const removeModelFromList = useCallback((m: string) => {
    setModelList((prev) => {
      const next = prev.filter((x) => x !== m);
      if (modelCurrent === m) {
        setModelCurrent(next[0] ?? "");
      }
      return next;
    });
  }, [modelCurrent]);

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
            title={status && !loading ? buildCapabilitiesHoverText(status) : undefined}
            className={`w-full cursor-help rounded-lg px-3 py-2 text-left text-sm transition ${
              activeSection === "mcp"
                ? "bg-white/10 text-white"
                : "text-white/65 hover:bg-white/[0.06]"
            }`}
          >
            MCP tools
          </button>
          <button
            type="button"
            onClick={() => setActiveSection("models")}
            title="LangChain chat model id (stored in ai-api/storage/model_settings.json)"
            className={`mt-1 w-full rounded-lg px-3 py-2 text-left text-sm transition ${
              activeSection === "models"
                ? "bg-white/10 text-white"
                : "text-white/65 hover:bg-white/[0.06]"
            }`}
          >
            Models
          </button>
          <button
            type="button"
            onClick={() => setActiveSection("skills")}
            title="Manage agent SKILL.md packages (stored on the API host; requests go through the Node backend)"
            className={`mt-1 w-full rounded-lg px-3 py-2 text-left text-sm transition ${
              activeSection === "skills"
                ? "bg-white/10 text-white"
                : "text-white/65 hover:bg-white/[0.06]"
            }`}
          >
            Skills
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
                <div
                  className="cursor-help rounded-xl border border-white/10 bg-black/25 px-4 py-3 text-sm"
                  title={buildCapabilitiesHoverText(status)}
                >
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
                  {(status.mcp_tool_names?.length ?? 0) > 0 && (
                    <div className="mt-3 border-t border-white/10 pt-3">
                      <h3
                        className="cursor-help text-xs font-medium uppercase tracking-wide text-white/50"
                        title={buildCapabilitiesHoverText(status)}
                      >
                        MCP tool names
                      </h3>
                      <ul className="mt-2 flex flex-wrap gap-1.5">
                        {status.mcp_tool_names.map((name) => (
                          <li key={name}>
                            <code className="rounded-md border border-white/10 bg-black/35 px-2 py-0.5 text-[11px] text-emerald-200/95">
                              {name}
                            </code>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {(status.skills?.length ?? 0) > 0 && (
                    <div className="mt-3 border-t border-white/10 pt-3">
                      <h3
                        className="cursor-help text-xs font-medium uppercase tracking-wide text-white/50"
                        title={buildCapabilitiesHoverText(status)}
                      >
                        Skills found
                      </h3>
                      <ul className="mt-2 flex flex-col gap-1.5">
                        {status.skills.map((s) => (
                          <li
                            key={s.id}
                            className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[11px] text-white/80"
                          >
                            <code className="rounded-md border border-violet-500/20 bg-violet-500/10 px-2 py-0.5 text-violet-200/95">
                              {s.id}
                            </code>
                            <span className="text-white/40">{s.skill_md_path}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
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

          {activeSection === "models" && (
            <div className="flex max-w-3xl flex-col gap-4">
              <div>
                <h2 className="text-sm font-medium text-white">Models</h2>
                <p className="mt-1 text-xs leading-relaxed text-white/45">
                  Active chat model for the Deep Agents API (
                  <code className="text-white/55">init_chat_model</code> string). Defaults include{" "}
                  <code className="text-white/55">openai:gpt-5.1-mini</code>,{" "}
                  <code className="text-white/55">openai:gpt-5.1</code>, and{" "}
                  <code className="text-white/55">openai:gpt-5-nano</code>. Add custom ids to the list,
                  then choose one and save. Settings are stored in{" "}
                  <code className="text-white/55">ai-api/storage/model_settings.json</code>.
                </p>
              </div>

              {modelsLoading && <p className="text-sm text-white/50">Loading…</p>}
              {modelsError && <p className="text-sm text-red-400">{modelsError}</p>}

              {!modelsLoading && (
                <>
                  <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#131314]">
                    <table className="w-full min-w-[20rem] border-collapse text-left text-sm">
                      <thead>
                        <tr className="border-b border-white/10 text-[11px] font-medium uppercase tracking-wide text-white/45">
                          <th className="px-4 py-3">Setting</th>
                          <th className="px-4 py-3">Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b border-white/5">
                          <td className="align-middle px-4 py-3 text-white/70">Active model</td>
                          <td className="px-4 py-3">
                            <select
                              value={
                                modelList.includes(modelCurrent)
                                  ? modelCurrent
                                  : (modelList[0] ?? "")
                              }
                              onChange={(e) => setModelCurrent(e.target.value)}
                              disabled={modelsSaving}
                              className="w-full max-w-xl rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-xs text-white outline-none focus:border-sky-500/50 disabled:opacity-45"
                            >
                              {modelList.length === 0 ? (
                                <option value="">—</option>
                              ) : (
                                modelList.map((m) => (
                                  <option key={m} value={m}>
                                    {m}
                                  </option>
                                ))
                              )}
                            </select>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-white/10 bg-[#131314]">
                    <table className="w-full min-w-[20rem] border-collapse text-left text-sm">
                      <thead>
                        <tr className="border-b border-white/10 text-[11px] font-medium uppercase tracking-wide text-white/45">
                          <th className="px-4 py-3">Model id</th>
                          <th className="w-28 px-4 py-3 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelList.map((m) => (
                          <tr key={m} className="border-b border-white/5 last:border-b-0">
                            <td className="px-4 py-2 font-mono text-xs text-white/90">{m}</td>
                            <td className="px-4 py-2 text-right">
                              <button
                                type="button"
                                onClick={() => removeModelFromList(m)}
                                disabled={modelsSaving}
                                className="text-xs text-red-400/90 hover:text-red-300 disabled:opacity-45"
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-black/20 p-4 sm:flex-row sm:items-end sm:gap-3">
                    <div className="min-w-0 flex-1">
                      <label className="text-[10px] font-medium uppercase text-white/40">
                        Add model id
                      </label>
                      <input
                        value={newModelInput}
                        onChange={(e) => setNewModelInput(e.target.value)}
                        placeholder="openai:gpt-5.1-mini"
                        className="mt-1 w-full rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-sm text-white outline-none placeholder:text-white/25 focus:border-sky-500/50"
                        disabled={modelsSaving}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addModelToList();
                          }
                        }}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={addModelToList}
                      disabled={modelsSaving || !newModelInput.trim()}
                      className="shrink-0 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10 disabled:opacity-45"
                    >
                      Add to list
                    </button>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => void saveModels()}
                      disabled={modelsSaving || modelsLoading}
                      className="rounded-full bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 disabled:opacity-45"
                    >
                      {modelsSaving ? "Saving…" : "Save and apply"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void loadModels()}
                      disabled={modelsSaving || modelsLoading}
                      className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10 disabled:opacity-45"
                    >
                      Reload from API
                    </button>
                  </div>
                </>
              )}
            </div>
          )}

          {activeSection === "skills" && (
            <div className="flex max-w-3xl flex-col gap-4">
              <div>
                <h2 className="text-sm font-medium text-white">Agent skills</h2>
                <p className="mt-1 text-xs leading-relaxed text-white/45">
                  Each skill is a folder under <code className="text-white/55">ai-api/skills/&lt;id&gt;/</code>{" "}
                  with a <code className="text-white/55">SKILL.md</code> file. The browser calls the Node
                  backend (port 3501 by default), which forwards to the FastAPI AI service. Authorization
                  and per-role rules can be enforced on that backend later.
                </p>
              </div>

              {skillsLoading && <p className="text-sm text-white/50">Loading skills…</p>}
              {skillsError && <p className="text-sm text-red-400">{skillsError}</p>}

              {!skillsLoading && (
                <div className="rounded-xl border border-white/10 bg-black/25 px-4 py-3 text-sm">
                  <p className="text-white/80">
                    <span className="text-white/50">Packages on disk:</span>{" "}
                    <span className="font-medium text-violet-300/95">{skillsList.length}</span>
                  </p>
                  {skillsList.length > 0 && (
                    <ul className="mt-3 flex flex-col gap-2 border-t border-white/10 pt-3">
                      {skillsList.map((s) => (
                        <li
                          key={s.id}
                          className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/5 bg-[#131314] px-3 py-2"
                        >
                          <div className="min-w-0 flex-1">
                            <code className="text-[12px] text-violet-200/95">{s.id}</code>
                            <span className="ml-2 text-[11px] text-white/35">{s.skill_md_path}</span>
                          </div>
                          <div className="flex shrink-0 gap-2">
                            <button
                              type="button"
                              onClick={() => void openSkillEditor(s.id)}
                              disabled={skillSaving}
                              className="rounded-md border border-white/15 bg-white/5 px-2 py-1 text-xs text-white/85 hover:bg-white/10 disabled:opacity-45"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => void deleteSkill(s.id)}
                              disabled={skillSaving}
                              className="rounded-md border border-red-500/30 bg-red-500/10 px-2 py-1 text-xs text-red-300/95 hover:bg-red-500/15 disabled:opacity-45"
                            >
                              Delete
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {editingId && (
                <div className="flex flex-col gap-3 rounded-xl border border-violet-500/25 bg-violet-500/5 p-4">
                  <h3 className="text-xs font-medium uppercase tracking-wide text-white/55">
                    Edit <code className="text-violet-200/95">{editingId}</code>
                  </h3>
                  <label className="text-[10px] font-medium uppercase text-white/40">
                    Rename (optional)
                  </label>
                  <input
                    value={renameSkillId}
                    onChange={(e) => setRenameSkillId(e.target.value)}
                    placeholder={`New id (letters, digits, hyphen, underscore; was ${editingId})`}
                    className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-sm text-white outline-none placeholder:text-white/25 focus:border-violet-500/40"
                    disabled={skillSaving}
                  />
                  <label className="text-[10px] font-medium uppercase text-white/40">SKILL.md</label>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    rows={16}
                    className="min-h-[12rem] rounded-lg border border-white/10 bg-black/35 px-3 py-2 font-mono text-xs text-white/90 outline-none focus:border-violet-500/40"
                    disabled={skillSaving}
                  />
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => void saveEditedSkill()}
                      disabled={skillSaving}
                      className="rounded-full bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-45"
                    >
                      {skillSaving ? "Saving…" : "Save skill"}
                    </button>
                    <button
                      type="button"
                      onClick={closeSkillEditor}
                      disabled={skillSaving}
                      className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/85 hover:bg-white/10 disabled:opacity-45"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-2 rounded-xl border border-white/10 bg-[#131314] p-4">
                <h3 className="text-xs font-medium uppercase tracking-wide text-white/50">Add skill</h3>
                <label className="text-[10px] font-medium uppercase text-white/40">Skill id</label>
                <input
                  value={newSkillId}
                  onChange={(e) => setNewSkillId(e.target.value)}
                  placeholder="mySkill"
                  className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 font-mono text-sm text-white outline-none placeholder:text-white/30 focus:border-violet-500/40"
                  disabled={skillSaving}
                />
                <label className="text-[10px] font-medium uppercase text-white/40">SKILL.md content</label>
                <textarea
                  value={newSkillContent}
                  onChange={(e) => setNewSkillContent(e.target.value)}
                  rows={10}
                  className="min-h-[8rem] rounded-lg border border-white/10 bg-black/35 px-3 py-2 font-mono text-xs text-white/90 outline-none focus:border-violet-500/40"
                  disabled={skillSaving}
                />
                <div className="flex flex-wrap gap-2 pt-1">
                  <button
                    type="button"
                    onClick={() => void createSkill()}
                    disabled={skillSaving}
                    className="rounded-full bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500 disabled:opacity-45"
                  >
                    {skillSaving ? "Working…" : "Create skill"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void loadSkills()}
                    disabled={skillSaving}
                    className="rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-white/90 hover:bg-white/10 disabled:opacity-45"
                  >
                    Reload list
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
