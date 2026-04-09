"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { buildCapabilitiesHoverText, type McpSettingsResponse } from "./SettingsPanel";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Session = {
  id: string;
  title: string;
  messages: ChatMessage[];
};

const backendBase = (
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://127.0.0.1:3501"
).replace(/\/$/, "");

/** Stable id so SSR and hydration match; random UUIDs per tab break activeId ↔ session. */
const DEFAULT_SESSION_ID = "default-session";

/** Remember last-opened thread after reload (server list must include this id). */
const ACTIVE_SESSION_STORAGE_KEY = "fs-deepagents-active-session";

type ApiSessionPayload = {
  session_id: string;
  title: string;
  messages: ChatMessage[];
};

function newSession(): Session {
  return {
    id: crypto.randomUUID(),
    title: "New chat",
    messages: [],
  };
}

function defaultSession(): Session {
  return {
    id: DEFAULT_SESSION_ID,
    title: "New chat",
    messages: [],
  };
}

function sessionsFromApi(rows: ApiSessionPayload[]): Session[] {
  return rows.map((p) => ({
    id: p.session_id,
    title: p.title?.trim() || "New chat",
    messages: (p.messages ?? []).map((m) => ({
      role: m.role,
      content: m.content,
    })),
  }));
}

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

export default function ChatShell() {
  const [sessions, setSessions] = useState<Session[]>(() => [defaultSession()]);
  const [activeId, setActiveId] = useState<string>(DEFAULT_SESSION_ID);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [mcpStatus, setMcpStatus] = useState<McpSettingsResponse | null>(null);
  const [mcpStatusError, setMcpStatusError] = useState<string | null>(null);

  const active = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? sessions[0],
    [sessions, activeId]
  );

  useEffect(() => {
    setActiveId((aid) => (sessions.some((s) => s.id === aid) ? aid : sessions[0]!.id));
  }, [sessions]);

  useEffect(() => {
    try {
      sessionStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, activeId);
    } catch {
      /* quota / private mode */
    }
  }, [activeId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${backendBase}/settings/mcp`);
        const resText = await res.text();
        let data: unknown = {};
        try {
          data = resText ? JSON.parse(resText) : {};
        } catch {
          if (!res.ok) {
            throw new Error(resText.slice(0, 120) || `HTTP ${res.status}`);
          }
        }
        if (!res.ok) {
          throw new Error(errorMessageFromResponseBody(data, res.status));
        }
        if (!cancelled) {
          setMcpStatus(data as McpSettingsResponse);
          setMcpStatusError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setMcpStatus(null);
          setMcpStatusError(e instanceof Error ? e.message : "MCP status unavailable");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${backendBase}/sessions`);
        const resText = await res.text();
        let data: { sessions?: ApiSessionPayload[] } = {};
        try {
          data = resText ? (JSON.parse(resText) as { sessions?: ApiSessionPayload[] }) : {};
        } catch {
          if (!res.ok) {
            throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
          }
        }
        if (!res.ok) {
          throw new Error(errorMessageFromResponseBody(data, res.status));
        }
        if (cancelled) return;
        const rows = data.sessions ?? [];
        if (rows.length === 0) {
          const d = defaultSession();
          setSessions([d]);
          setActiveId(d.id);
          setHistoryError(null);
          return;
        }
        const next = sessionsFromApi(rows);
        setSessions(next);
        let preferred: string | null = null;
        try {
          preferred = sessionStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
        } catch {
          preferred = null;
        }
        if (preferred && next.some((s) => s.id === preferred)) {
          setActiveId(preferred);
        } else {
          setActiveId(next[0]!.id);
        }
        setHistoryError(null);
      } catch (e) {
        if (!cancelled) {
          setHistoryError(e instanceof Error ? e.message : "Could not load conversation history");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeRef = useRef(active);
  const sendingRef = useRef(sending);
  activeRef.current = active;
  sendingRef.current = sending;

  const updateSession = useCallback((id: string, fn: (s: Session) => Session) => {
    setSessions((prev) => prev.map((s) => (s.id === id ? fn(s) : s)));
  }, []);

  const addSession = useCallback(() => {
    const s = newSession();
    setSessions((prev) => [...prev, s]);
    setActiveId(s.id);
    setInput("");
    setError(null);
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    try {
      const res = await fetch(`${backendBase}/sessions/${encodeURIComponent(id)}`, {
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
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
      return;
    }
    setError(null);
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      return next.length === 0 ? [defaultSession()] : next;
    });
  }, []);

  const submitMessage = useCallback(
    async (rawText: string) => {
      const text = rawText.trim();
      const sess = activeRef.current;
      if (!text || !sess || sendingRef.current) return;

      setError(null);
      setSending(true);
      setInput("");

      const sessionId = sess.id;

      updateSession(sessionId, (s) => {
        const nextTitle =
          s.title === "New chat" && s.messages.length === 0
            ? text.slice(0, 48) + (text.length > 48 ? "…" : "")
            : s.title;
        return {
          ...s,
          title: nextTitle,
          messages: [...s.messages, { role: "user", content: text }],
        };
      });

      try {
        const res = await fetch(`${backendBase}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            message: text,
          }),
        });
        const resText = await res.text();
        let data: { reply?: string } = {};
        try {
          data = resText ? (JSON.parse(resText) as { reply?: string }) : {};
        } catch {
          if (!res.ok) {
            throw new Error(resText.slice(0, 200) || `HTTP ${res.status}`);
          }
        }
        if (!res.ok) {
          throw new Error(errorMessageFromResponseBody(data, res.status));
        }
        const reply = data.reply ?? "";
        updateSession(sessionId, (s) => ({
          ...s,
          messages: [...s.messages, { role: "assistant", content: reply }],
        }));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Request failed");
        setInput(text);
        updateSession(sessionId, (s) => {
          const last = s.messages[s.messages.length - 1];
          if (last?.role !== "user" || last.content !== text) return s;
          const nextMessages = s.messages.slice(0, -1);
          return {
            ...s,
            messages: nextMessages,
            title: nextMessages.length === 0 ? "New chat" : s.title,
          };
        });
      } finally {
        setSending(false);
      }
    },
    [updateSession]
  );

  const trimmedInput = input.trim();
  const sendButtonStyle: CSSProperties = sending
    ? { backgroundColor: "rgba(30, 64, 175, 0.65)", color: "rgba(255,255,255,0.85)" }
    : trimmedInput
      ? { backgroundColor: "#2563eb", color: "#ffffff" }
      : {
          backgroundColor: "rgba(255,255,255,0.1)",
          color: "rgba(255,255,255,0.45)",
          border: "1px solid rgba(255,255,255,0.15)",
        };

  return (
    <div className="flex h-[100dvh] w-full bg-[#131314] text-[#e3e3e3]">
      <aside className="flex w-[260px] shrink-0 flex-col border-r border-white/10 bg-[#1b1b1c]">
        <div className="border-b border-white/10 p-3">
          <button
            type="button"
            onClick={addSession}
            className="w-full rounded-full border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-white/10"
          >
            New chat
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-2">
          <ul className="flex flex-col gap-1">
            {sessions.map((s) => (
              <li
                key={s.id}
                className="group flex items-stretch gap-0.5 rounded-xl transition hover:bg-white/[0.04]"
              >
                <button
                  type="button"
                  onClick={() => {
                    setActiveId(s.id);
                    setError(null);
                  }}
                  className={`min-w-0 flex-1 rounded-l-xl px-3 py-2.5 text-left text-sm transition ${
                    s.id === active?.id
                      ? "bg-[#2a2a2c] text-white"
                      : "text-white/80 group-hover:bg-white/5"
                  }`}
                >
                  <span className="line-clamp-2">{s.title}</span>
                </button>
                <button
                  type="button"
                  title="Delete"
                  aria-label={`Delete conversation: ${s.title}`}
                  className={`flex w-9 shrink-0 items-center justify-center rounded-r-xl text-white/50 transition hover:bg-red-500/20 hover:text-red-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-red-400/80 ${
                    s.id === active?.id ? "bg-[#2a2a2c]" : ""
                  } opacity-0 group-hover:opacity-100`}
                  onClick={(e) => {
                    e.stopPropagation();
                    void deleteSession(s.id);
                  }}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="h-4 w-4"
                    aria-hidden
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A1.75 1.75 0 0 0 7.596 19h4.807a1.75 1.75 0 0 0 1.742-1.96l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 1 0 1.5.06l.3-7.5Z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-white/10 px-4 md:px-6">
          <span className="min-w-0 truncate text-sm font-medium text-white/90">
            {active?.title ?? "Chat"}
          </span>
          <div className="flex shrink-0 items-center gap-2">
            {mcpStatus && !mcpStatusError && (
              <span
                className="inline-flex max-w-[16rem] cursor-help items-center gap-1 truncate rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-[11px] text-emerald-200/95 md:max-w-none"
                title={buildCapabilitiesHoverText(mcpStatus)}
              >
                <span>{(mcpStatus.skills ?? []).length} skills</span>
                <span className="text-emerald-200/40" aria-hidden>
                  ·
                </span>
                <span>
                  {mcpStatus.total_tools} tools · {mcpStatus.connected_servers}/
                  {mcpStatus.configured_servers} MCP
                </span>
              </span>
            )}
            {mcpStatusError && (
              <span
                className="max-w-[6rem] truncate text-[11px] text-amber-400/90"
                title={mcpStatusError}
              >
                MCP ?
              </span>
            )}
            <Link
              href="/settings"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-white/90 transition hover:bg-white/10"
            >
              Settings
            </Link>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-12">
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {historyError && (
              <p className="text-center text-sm text-amber-400/90">
                Could not load saved chats ({historyError}). Starting a fresh session; sends still
                work if the chat API is up.
              </p>
            )}
            {(active?.messages ?? []).length === 0 && (
              <p className="text-center text-sm text-white/45">
                Start a conversation. Threads are stored in SQLite on the AI server and reload here
                after you refresh or restart the stack. Hover a title to delete a thread from the
                server.
              </p>
            )}
            {(active?.messages ?? []).map((m, i) => (
              <div
                key={`${m.role}-${i}`}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-[#2f2f32] text-white"
                      : "bg-[#1e1f20] text-white/95"
                  }`}
                >
                  <span className="block whitespace-pre-wrap">{m.content}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="shrink-0 border-t border-white/10 p-4 md:px-12 md:pb-6">
          {error && (
            <p className="mx-auto mb-2 max-w-3xl text-center text-sm text-red-400">{error}</p>
          )}
          <form
            className="mx-auto flex max-w-3xl gap-2 rounded-3xl border border-white/10 bg-[#1e1f20] px-4 py-2"
            onSubmit={(e) => {
              e.preventDefault();
              if (sendingRef.current) return;
              const fd = new FormData(e.currentTarget);
              const msg = fd.get("message");
              const text = typeof msg === "string" ? msg : "";
              const trimmed = text.trim();
              if (!trimmed) return;
              void submitMessage(trimmed);
            }}
          >
            <textarea
              name="message"
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key !== "Enter" || e.shiftKey) return;
                if (e.nativeEvent.isComposing) return;
                e.preventDefault();
                const text = e.currentTarget.value.trim();
                if (!text || sendingRef.current) return;
                void submitMessage(text);
              }}
              placeholder="Message"
              className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent py-3 text-sm text-white outline-none placeholder:text-white/35"
              disabled={sending}
            />
            <button
              type="submit"
              aria-busy={sending}
              aria-disabled={sending || !trimmedInput}
              style={sendButtonStyle}
              className={`self-end shrink-0 rounded-full px-5 py-2 text-sm font-semibold shadow-sm transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#3b82f6] ${
                sending
                  ? "pointer-events-none cursor-wait"
                  : trimmedInput
                    ? "cursor-pointer hover:brightness-110 active:brightness-95"
                    : "cursor-default"
              }`}
            >
              {sending ? "…" : "Send"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}
