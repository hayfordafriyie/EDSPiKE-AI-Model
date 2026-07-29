from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>EDSPiKE AI Agent</title>
<style>
:root{--bg:#0d1117;--surface:#161b22;--border:#30363d;--text:#c9d1d9;--text-muted:#8b949e;--primary:#58a6ff;--success:#238636;--danger:#da3633;--warning:#d29922}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column}
header{background:var(--surface);padding:12px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px;flex-shrink:0}
header h1{font-size:18px;color:var(--primary)}
header .badge{padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600}
.badge.build{background:var(--success);color:#fff}
.badge.plan{background:var(--warning);color:#000}
header .links{margin-left:auto;display:flex;gap:12px}
header .links a{color:var(--text-muted);text-decoration:none;font-size:13px}
header .links a:hover{color:var(--primary)}
#chat{flex:1;overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:16px}
.msg{max-width:80%;padding:12px 16px;border-radius:8px;line-height:1.6;font-size:14px}
.msg.user{background:#1f6feb;align-self:flex-end}
.msg.assistant{background:var(--surface);align-self:flex-start;border:1px solid var(--border)}
.msg pre{background:var(--bg);padding:12px;border-radius:6px;overflow-x:auto;margin:8px 0;border:1px solid var(--border)}
.msg code{font-family:'SF Mono','Fira Code',monospace;font-size:13px}
.msg p{margin:4px 0}
#input-area{padding:16px 24px;border-top:1px solid var(--border);background:var(--surface);display:flex;gap:8px;flex-shrink:0}
#input{flex:1;padding:10px 14px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);font-family:inherit;font-size:14px;resize:none;outline:none;transition:border-color .2s}
#input:focus{border-color:var(--primary)}
#send{padding:10px 24px;background:var(--success);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;transition:background .2s}
#send:hover{background:#2ea043}
#send:disabled{opacity:.5;cursor:not-allowed}
.status{color:var(--text-muted);font-size:13px;text-align:center;padding:8px;display:flex;align-items:center;justify-content:center;gap:8px}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--border);border-top-color:var(--primary);border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<header>
<h1>EDSPiKE</h1>
<span class="badge build" id="modeBadge">Build</span>
<div class="links">
<a href="#" id="modeToggle">Switch mode</a>
<a href="#" id="clearBtn">Clear</a>
</div>
</header>
<div id="chat"><div class="status">Ask me anything about your codebase.</div></div>
<div id="input-area">
<textarea id="input" rows="2" placeholder="Type a message... (Shift+Enter for new line)" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
<button id="send" onclick="send()">Send</button>
</div>
<script>
let mode='build',sessionId='sess_'+Date.now(),msgCount=0;
const chat=document.getElementById('chat'),input=document.getElementById('input'),sendBtn=document.getElementById('send');
function addMsg(role,content){
  const d=document.createElement('div');d.className='msg '+role;
  d.innerHTML=content.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/```(\w*)\n?([\s\S]*?)```/g,'<pre><code>$2</code></pre>').replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\n/g,'<br>');
  chat.appendChild(d);chat.scrollTop=chat.scrollHeight;
  if(role==='user')msgCount++;
}
function setStatus(msg,loading){
  const s=chat.querySelector('.status')||document.createElement('div');
  s.className='status';s.innerHTML=loading?('<span class="spinner"></span> '+msg):msg;
  if(!chat.contains(s))chat.appendChild(s);chat.scrollTop=chat.scrollHeight;
}
document.getElementById('modeToggle').onclick=function(e){
  e.preventDefault();
  mode=mode==='build'?'plan':'build';
  const b=document.getElementById('modeBadge');
  b.textContent=mode==='build'?'Build':'Plan';
  b.className='badge '+(mode==='build'?'build':'plan');
  setStatus('Switched to '+mode.charAt(0).toUpperCase()+mode.slice(1)+' mode');
};
document.getElementById('clearBtn').onclick=function(e){
  e.preventDefault();
  chat.innerHTML='<div class="status">Conversation cleared.</div>';
};
async function send(){
  const text=input.value.trim();if(!text)return;
  addMsg('user',text);input.value='';sendBtn.disabled=true;
  setStatus('Thinking...',true);
  try{
    const r=await fetch('/v1/generate',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({prompt:text,max_tokens:2048,session_id:sessionId,mode:mode})
    });
    const d=await r.json();
    chat.removeChild(chat.querySelector('.status'));
    addMsg('assistant',d.response||'*No response*');
  }catch(e){setStatus('Error: '+e.message);}
  finally{sendBtn.disabled=false;input.focus();}
}
</script>
</body>
</html>"""


def mount_web_ui(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def web_index():
        return PAGE
