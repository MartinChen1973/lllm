"use client";

import type { CSSProperties } from "react";
import { useCallback, useMemo, useRef, useState } from "react";

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

  const active = useMemo(
    () => sessions.find((s) => s.id === activeId) ?? sessions[0],
    [sessions, activeId]
  );

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
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => {
                    setActiveId(s.id);
                    setError(null);
                  }}
                  className={`w-full rounded-xl px-3 py-2.5 text-left text-sm transition ${
                    s.id === active?.id
                      ? "bg-[#2a2a2c] text-white"
                      : "text-white/80 hover:bg-white/5"
                  }`}
                >
                  <span className="line-clamp-2">{s.title}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center border-b border-white/10 px-6 text-sm font-medium text-white/90">
          {active?.title ?? "Chat"}
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 md:px-12">
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {(active?.messages ?? []).length === 0 && (
              <p className="text-center text-sm text-white/45">
                Start a conversation. Messages are kept in this browser session only.
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
