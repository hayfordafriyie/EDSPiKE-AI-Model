from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


WEB_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EDSPiKE AI Agent</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; height: 100vh; display: flex; flex-direction: column; }
header { background: #161b22; padding: 12px 24px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 12px; }
header h1 { font-size: 18px; color: #58a6ff; }
header .mode-badge { background: #238636; color: #fff; padding: 2px 10px; border-radius: 12px; font-size: 12px; }
#chat { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.msg { max-width: 80%; padding: 12px 16px; border-radius: 8px; line-height: 1.5; }
.msg.user { background: #1f6feb; align-self: flex-end; }
.msg.assistant { background: #21262d; align-self: flex-start; border: 1px solid #30363d; }
.msg pre { background: #0d1117; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 8px 0; }
.msg code { font-family: 'SF Mono', monospace; font-size: 13px; }
#input-area { padding: 16px 24px; border-top: 1px solid #30363d; background: #161b22; display: flex; gap: 8px; }
#input-area textarea { flex: 1; padding: 10px; border: 1px solid #30363d; border-radius: 6px; background: #0d1117; color: #c9d1d9; font-family: inherit; font-size: 14px; resize: none; }
#input-area textarea:focus { outline: none; border-color: #58a6ff; }
#input-area button { padding: 10px 20px; background: #238636; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
#input-area button:hover { background: #2ea043; }
.status { color: #8b949e; font-size: 13px; text-align: center; padding: 8px; }
</style>
</head>
<body>
<header><h1>EDSPiKE AI Agent</h1><span class="mode-badge">Build</span></header>
<div id="chat">
<div class="status">Ask me anything about your codebase.</div>
</div>
<div id="input-area">
<textarea id="input" rows="2" placeholder="Type your message..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}"></textarea>
<button onclick="send()">Send</button>
</div>
<script>
const chat = document.getElementById('chat');
const input = document.getElementById('input');
function addMsg(role, content) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.innerHTML = content.replace(/\\n/g, '<br>').replace(/```(\\w*)\\n([\\s\\S]*?)```/g, '<pre><code>$2</code></pre>');
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}
async function send() {
  const text = input.value.trim();
  if (!text) return;
  addMsg('user', text);
  input.value = '';
  const status = document.createElement('div');
  status.className = 'status';
  status.textContent = 'Thinking...';
  chat.appendChild(status);
  try {
    const resp = await fetch('/v1/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt: text, max_tokens: 2048})
    });
    const data = await resp.json();
    status.remove();
    addMsg('assistant', data.response || 'No response');
  } catch(e) {
    status.textContent = 'Error: ' + e.message;
  }
}
</script>
</body>
</html>"""


def mount_web_ui(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def web_index():
        return WEB_UI_HTML
