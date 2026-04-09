import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "..", "..", ".env") });

const app = express();
app.use(express.json({ limit: "2mb" }));

const PORT = Number(process.env.PORT ?? 3501);
const AI_API_URL = (process.env.AI_API_URL ?? "http://127.0.0.1:8500").replace(/\/$/, "");

const corsOrigins = (
  process.env.CORS_ORIGINS ??
  "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3500,http://127.0.0.1:3500"
)
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

app.use(
  cors({
    origin: corsOrigins,
    credentials: true,
  })
);

const openApiSpec = {
  openapi: "3.1.0",
  info: {
    title: "Node chat proxy",
    version: "1.0.0",
    description: `Forwards POST /chat to the FastAPI AI service (${AI_API_URL}) with the same JSON body and status.`,
  },
  paths: {
    "/chat": {
      post: {
        summary: "Proxy chat to AI API",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["session_id", "message"],
                properties: {
                  session_id: { type: "string" },
                  message: { type: "string" },
                },
              },
            },
          },
        },
        responses: {
          "200": { description: "Forwarded response from AI API (e.g. { reply: string })" },
        },
      },
    },
    "/sessions": {
      get: {
        summary: "List saved conversations from AI API (checkpoint threads)",
        parameters: [
          {
            name: "limit",
            in: "query",
            required: false,
            schema: { type: "integer", default: 50 },
          },
        ],
        responses: {
          "200": {
            description: "Forwarded JSON with sessions array (session_id, title, messages)",
          },
        },
      },
    },
    "/sessions/{session_id}": {
      delete: {
        summary: "Delete conversation checkpoints on AI API",
        parameters: [
          {
            name: "session_id",
            in: "path",
            required: true,
            schema: { type: "string" },
          },
        ],
        responses: {
          "200": { description: "Forwarded response from AI API (e.g. { ok: true })" },
        },
      },
    },
    "/settings/mcp": {
      get: {
        summary: "MCP tool status and configuration source from AI API",
        responses: {
          "200": {
            description:
              "Forwarded JSON: source, servers (id, url, connected, tool_count, error, headers), totals",
          },
        },
      },
      put: {
        summary: "Persist MCP server list and rebuild the AI agent",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  servers: {
                    type: "array",
                    items: {
                      type: "object",
                      required: ["id", "url"],
                      properties: {
                        id: { type: "string" },
                        url: { type: "string" },
                        headers: { type: "object", additionalProperties: { type: "string" } },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        responses: {
          "200": { description: "Updated MCP settings and load outcome" },
        },
      },
    },
    "/settings/models": {
      get: {
        summary: "Chat model id and dropdown list from AI API (storage/model_settings.json)",
        responses: {
          "200": { description: "JSON { current_model, models }" },
        },
      },
      put: {
        summary: "Set active LangChain model id and list; rebuild agent",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["current_model"],
                properties: {
                  current_model: { type: "string" },
                  models: { type: "array", items: { type: "string" } },
                },
              },
            },
          },
        },
        responses: { "200": { description: "Updated model settings" } },
      },
    },
    "/settings/skills": {
      get: {
        summary: "List skill packages (SKILL.md under ai-api/skills/)",
        responses: { "200": { description: "Array of { id, skill_md_path }" } },
      },
      post: {
        summary: "Create a skill package and rebuild the AI agent",
        requestBody: {
          required: true,
          content: {
            "application/json": {
              schema: {
                type: "object",
                required: ["id", "content"],
                properties: { id: { type: "string" }, content: { type: "string" } },
              },
            },
          },
        },
        responses: { "200": { description: "Skill detail with content" } },
      },
    },
    "/settings/skills/{skill_id}": {
      get: {
        summary: "Get one skill package including SKILL.md body",
        parameters: [
          { name: "skill_id", in: "path", required: true, schema: { type: "string" } },
        ],
        responses: { "200": { description: "{ id, skill_md_path, content }" } },
      },
      put: {
        summary: "Update or rename a skill package and rebuild the AI agent",
        parameters: [
          { name: "skill_id", in: "path", required: true, schema: { type: "string" } },
        ],
        requestBody: {
          content: {
            "application/json": {
              schema: {
                type: "object",
                properties: {
                  content: { type: "string" },
                  new_id: { type: "string" },
                },
              },
            },
          },
        },
        responses: { "200": { description: "Updated skill detail" } },
      },
      delete: {
        summary: "Delete a skill package and rebuild the AI agent",
        parameters: [
          { name: "skill_id", in: "path", required: true, schema: { type: "string" } },
        ],
        responses: { "200": { description: "{ ok: true }" } },
      },
    },
  },
};

const docsHtml = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Node proxy — OpenAPI</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css"/>
<style>body{margin:0}</style></head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
<script>
window.onload=function(){
  window.ui = SwaggerUIBundle({
    url: '/openapi.json',
    dom_id: '#swagger-ui',
    presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
    layout: 'StandaloneLayout'
  });
};
</script>
</body></html>`;

app.get("/openapi.json", (_req, res) => {
  res.json(openApiSpec);
});

app.get("/docs", (_req, res) => {
  res.type("text/html").send(docsHtml);
});

function preview(text, maxLen = 80) {
  if (text == null || typeof text !== "string") return "";
  const t = text.replace(/\s+/g, " ").trim();
  return t.length <= maxLen ? t : `${t.slice(0, maxLen)}…`;
}

/** Forward JSON to the FastAPI AI service (used for settings and skills; auth hooks go here later). */
async function proxyJsonToAi(req, res, method, upstreamPath, bodyObj) {
  const url = `${AI_API_URL}${upstreamPath}`;
  console.log(`[proxy] ${method} ${req.path} -> ${url}`);
  const t0 = Date.now();
  try {
    const init = { method };
    if (bodyObj !== undefined) {
      init.headers = { "Content-Type": "application/json" };
      init.body = JSON.stringify(bodyObj);
    }
    const r = await fetch(url, init);
    const text = await r.text();
    const ms = Date.now() - t0;
    console.log(
      `[proxy] upstream ${method} ${upstreamPath} status=${r.status} body_bytes=${text.length} elapsed_ms=${ms}`
    );
    res.status(r.status);
    try {
      res.json(JSON.parse(text));
    } catch {
      res.type("text/plain").send(text);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(
      `[proxy] ${method} ${upstreamPath} FAILED after ${Date.now() - t0}ms — cannot reach AI API:`,
      url,
      msg
    );
    res.status(502).json({
      detail: `Proxy could not reach AI API (${AI_API_URL}): ${msg}`,
    });
  }
}

app.get("/settings/mcp", async (req, res) => {
  await proxyJsonToAi(req, res, "GET", "/settings/mcp", undefined);
});

app.put("/settings/mcp", async (req, res) => {
  await proxyJsonToAi(req, res, "PUT", "/settings/mcp", req.body ?? {});
});

app.get("/settings/models", async (req, res) => {
  await proxyJsonToAi(req, res, "GET", "/settings/models", undefined);
});

app.put("/settings/models", async (req, res) => {
  await proxyJsonToAi(req, res, "PUT", "/settings/models", req.body ?? {});
});

app.get("/settings/skills", async (req, res) => {
  await proxyJsonToAi(req, res, "GET", "/settings/skills", undefined);
});

app.post("/settings/skills", async (req, res) => {
  await proxyJsonToAi(req, res, "POST", "/settings/skills", req.body ?? {});
});

app.get("/settings/skills/:skillId", async (req, res) => {
  const id = encodeURIComponent(req.params.skillId ?? "");
  await proxyJsonToAi(req, res, "GET", `/settings/skills/${id}`, undefined);
});

app.put("/settings/skills/:skillId", async (req, res) => {
  const id = encodeURIComponent(req.params.skillId ?? "");
  await proxyJsonToAi(req, res, "PUT", `/settings/skills/${id}`, req.body ?? {});
});

app.delete("/settings/skills/:skillId", async (req, res) => {
  const id = encodeURIComponent(req.params.skillId ?? "");
  await proxyJsonToAi(req, res, "DELETE", `/settings/skills/${id}`, undefined);
});

app.get("/sessions", async (req, res) => {
  const base = new URL(`${AI_API_URL}/sessions`);
  const lim = req.query?.limit;
  if (lim != null && lim !== "") {
    base.searchParams.set("limit", String(lim));
  }
  const url = base.toString();
  console.log(`[proxy] GET /sessions -> ${url}`);
  const t0 = Date.now();
  try {
    const r = await fetch(url, { method: "GET" });
    const text = await r.text();
    const ms = Date.now() - t0;
    console.log(
      `[proxy] upstream GET /sessions status=${r.status} body_bytes=${text.length} elapsed_ms=${ms}`
    );
    res.status(r.status);
    try {
      res.json(JSON.parse(text));
    } catch {
      res.type("text/plain").send(text);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(
      `[proxy] GET /sessions FAILED after ${Date.now() - t0}ms — cannot reach AI API:`,
      url,
      msg
    );
    res.status(502).json({
      detail: `Proxy could not reach AI API (${AI_API_URL}): ${msg}`,
    });
  }
});

app.delete("/sessions/:sessionId", async (req, res) => {
  const raw = req.params.sessionId ?? "";
  const sessionId = decodeURIComponent(raw);
  const url = `${AI_API_URL}/sessions/${encodeURIComponent(sessionId)}`;
  console.log(`[proxy] DELETE /sessions -> ${url}`);
  const t0 = Date.now();
  try {
    const r = await fetch(url, { method: "DELETE" });
    const text = await r.text();
    const ms = Date.now() - t0;
    console.log(
      `[proxy] upstream DELETE status=${r.status} body_bytes=${text.length} elapsed_ms=${ms}`
    );
    res.status(r.status);
    try {
      res.json(JSON.parse(text));
    } catch {
      res.type("text/plain").send(text);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(
      `[proxy] DELETE /sessions FAILED after ${Date.now() - t0}ms — cannot reach AI API:`,
      url,
      msg
    );
    res.status(502).json({
      detail: `Proxy could not reach AI API (${AI_API_URL}): ${msg}`,
    });
  }
});

app.post("/chat", async (req, res) => {
  const url = `${AI_API_URL}/chat`;
  const body = req.body ?? {};
  const sessionId = typeof body.session_id === "string" ? body.session_id : "";
  const message = typeof body.message === "string" ? body.message : "";
  console.log(
    `[proxy] POST /chat -> ${url} session_id=${preview(sessionId, 36)} msg_len=${message.length} preview="${preview(message)}"`
  );
  const t0 = Date.now();
  try {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    const ms = Date.now() - t0;
    console.log(
      `[proxy] upstream response status=${r.status} body_bytes=${text.length} elapsed_ms=${ms}`
    );
    res.status(r.status);
    try {
      res.json(JSON.parse(text));
    } catch {
      res.type("text/plain").send(text);
    }
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(
      `[proxy] POST /chat FAILED after ${Date.now() - t0}ms — cannot reach AI API:`,
      url,
      msg
    );
    res.status(502).json({
      detail: `Proxy could not reach AI API (${AI_API_URL}): ${msg}`,
    });
  }
});

const server = app.listen(PORT, () => {
  console.log(`Proxy listening on http://127.0.0.1:${PORT} -> ${AI_API_URL}`);
});
server.on("error", (err) => {
  if (err && err.code === "EADDRINUSE") {
    console.error(
      `\nPort ${PORT} is already in use (EADDRINUSE). Another "Node backend" from a previous run may still be open.`
    );
    console.error(
      `Close that console or stop the process, then run npm start again. (PowerShell: Get-NetTCPConnection -LocalPort ${PORT} -State Listen)`
    );
    process.exit(1);
  }
  throw err;
});
