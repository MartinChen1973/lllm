import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "..", ".env") });

const app = express();
app.use(express.json({ limit: "1mb" }));

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

app.listen(PORT, () => {
  console.log(`Proxy listening on http://127.0.0.1:${PORT} -> ${AI_API_URL}`);
});
