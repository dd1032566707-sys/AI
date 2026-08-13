#!/usr/bin/env python3
# 综合服务器：托管 live2d 语音对话页 + /tts (Edge 免费神经语音) + /llm (智普大模型代理)
# 本地: python3 serve.py [port]   (默认 8123)
# 云端(Render/Railway 等): 读取环境变量 PORT 与 ZHIPU_API_KEY, 直接 python serve.py
import json, os, sys, asyncio, urllib.request, urllib.error
try:
    import edge_tts
    _HAS_TTS = True
except Exception:
    edge_tts = None
    _HAS_TTS = False
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------- 加载 .env(若存在, 仅当环境变量尚未设置时补全) ----------
def _load_dotenv():
    p = os.path.join(ROOT, '.env')
    if not os.path.exists(p):
        return
    try:
        with open(p, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass

_load_dotenv()

API_KEY = os.environ.get('ZHIPU_API_KEY', '')
ZHIPU_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'
ZHIPU_MODEL = os.environ.get('ZHIPU_MODEL', 'glm-4-flash')

# 模型文件夹 -> 中文显示名（未列出的文件夹回退为文件夹原名）
MODEL_FRIENDLY = {
    'yukari_model': '结月ゆかり',
    'kiana': '琪亚娜·卡斯兰娜',
    'mei': '雷电芽衣',
    'bronya': '布洛妮娅',
    'rem': '雷姆',
    'sakura': '樱',
    'haru': '春',
    'miku': '初音未来',
    'unitychan': 'Unity娘',
    'himeko': '姬子',
    'seele': '希儿',
    'theresa': '德丽莎',
    'sin': '辛',
    'fox': '狐娘',
}

def _discover_models():
    """扫描 model/ 目录，自动列出所有可用 Live2D 模型（丢新模型进目录即生效）。"""
    root_model = os.path.join(ROOT, 'model')
    if not os.path.isdir(root_model):
        return []
    pats = ('.model.json', 'model.json', 'model.default.json', 'index.json')
    out = []
    for folder in sorted(os.listdir(root_model)):
        fd = os.path.join(root_model, folder)
        if not os.path.isdir(fd) or folder.startswith('.'):
            continue
        defs = []
        for mr, _, files in os.walk(fd):
            for f in files:
                lf = f.lower()
                if lf.endswith(pats) or (lf.endswith('.json') and 'model' in lf):
                    defs.append(os.path.relpath(os.path.join(mr, f), fd).replace(os.sep, '/'))
        if not defs:
            continue
        defs.sort()
        out.append({'name': MODEL_FRIENDLY.get(folder, folder), 'folder': folder, 'defs': defs})
    return out


class Handler(SimpleHTTPRequestHandler):
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def end_headers(self):
        self._cors()
        super().end_headers()

    def do_GET(self):
        # 模型列表自动发现接口（供前端切换器使用）
        path = self.path.split('?', 1)[0]
        if path in ('/models', '/models/'):
            self._models()
            return
        # 根路径直接返回语音对话主页(便于"打开即用" + 通过健康检查)
        if self.path in ('/', '/index.html'):
            self.path = '/yukari_standalone.html'
        return super().do_GET()

    def _models(self):
        data = json.dumps(_discover_models(), ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _read_json(self):
        n = int(self.headers.get('Content-Length', 0) or 0)
        raw = self.rfile.read(n) if n else b'{}'
        try:
            return json.loads(raw.decode('utf-8') or '{}')
        except Exception:
            return {}

    def do_POST(self):
        path = self.path.rstrip('/')
        if path == '/tts':
            self._tts()
        elif path == '/llm':
            self._llm()
        else:
            self.send_error(404, 'not found')

    # ---------- Edge TTS (免费神经语音) ----------
    def _tts(self):
        try:
            import edge_tts as _tts
        except Exception:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': '服务端未安装 edge_tts，请运行: pip install edge_tts'}).encode('utf-8'))
            return
        try:
            data = self._read_json()
            text = (data.get('text') or '').strip()
            voice = data.get('voice') or 'zh-CN-XiaoxiaoNeural'
            pitch = data.get('pitch') or None
            rate = data.get('rate') or None
            if not text:
                self.send_error(400, 'empty text')
                return

            async def synth():
                kwargs = {}
                if pitch: kwargs['pitch'] = pitch
                if rate: kwargs['rate'] = rate
                comm = _tts.Communicate(text, voice, **kwargs)
                chunks = []
                async for ev in comm.stream():
                    if ev.get('type') == 'audio':
                        chunks.append(ev['data'])
                return b''.join(chunks)

            audio = asyncio.run(synth())
            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Content-Length', str(len(audio)))
            self._cors()
            self.end_headers()
            self.wfile.write(audio)
        except Exception as e:
            try:
                self.send_error(500, 'tts error: %s' % e)
            except Exception:
                pass

    # ---------- 智普大模型代理 (密钥仅存于服务端) ----------
    def _llm(self):
        if not API_KEY:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({'error': '服务端未配置 ZHIPU_API_KEY'}).encode('utf-8'))
            return
        try:
            data = self._read_json()
            payload = {
                'model': data.get('model') or ZHIPU_MODEL,
                'messages': data.get('messages') or [],
                'stream': True,
                'temperature': data.get('temperature', 0.85),
            }
            req = urllib.request.Request(
                ZHIPU_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + API_KEY,
                    'Accept': 'text/event-stream',
                },
                method='POST',
            )
            try:
                upstream = urllib.request.urlopen(req, timeout=120)
                self.send_response(upstream.getcode())
                self.send_header('Content-Type', upstream.headers.get('Content-Type', 'text/event-stream'))
                self.send_header('Cache-Control', 'no-cache')
                self._cors()
                self.end_headers()
                while True:
                    chunk = upstream.read(4096)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except urllib.error.HTTPError as e:
                body = e.read().decode('utf-8', 'replace')
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self._cors()
                self.end_headers()
                self.wfile.write(body.encode('utf-8'))
        except Exception as e:
            try:
                self.send_error(500, 'llm error: %s' % e)
            except Exception:
                pass

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT') or (sys.argv[1] if len(sys.argv) > 1 else 8123))
    os.chdir(ROOT)
    srv = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print('Serving %s on http://0.0.0.0:%d  (LLM proxy: %s)' % (ROOT, port, 'ON' if API_KEY else 'NO KEY'))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
