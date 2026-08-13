# 结月ゆかり · Live2D 语音对话助手

一个网页端虚拟歌姬：Live2D 立绘 + 语音识别(中文) + 智普 GLM 大模型 + Edge 免费神经语音(TTS)。
打开网页即可**直接对话**：默认走服务端大模型代理，**无需填写任何 Key**；想用自己的 Key 或换服务商，点页面右下角 ⚙ 设置即可。

> 语音来自微软 Edge 神经语音（免费），大模型默认走智普 GLM。立绘模型为 Live2D Cubism 2（结月ゆかり / Yuzuki Yukari）。

## 目录结构
- `yukari_standalone.html` —— 自包含主页（模型/引擎内联，单文件即可运行），**左上角可自由切换模型**
- `view_yukari.html` —— 纯 Live2D 多模型展示页（无需对话，也同样可切换模型）
- `js/live2d.js` —— Live2D Cubism 2 引擎
- `js/switcher.js` —— 多模型切换器（下拉 / 上一个 / 下一个，含自动发现与离线兜底）
- `serve.py` —— 综合服务器：托管页面 + `/models`(模型自动发现) + `/tts`(Edge 语音) + `/llm`(智普代理)
- `start.sh` —— 一键启动
- `model_manifest.json` —— 模型清单（离线 / `file://` 打开时兜底用，可不选）
- `model/` —— Live2D 模型文件夹（已内置 14 个，来自 live2d-master 仓库）
- `render.yaml` / `requirements.txt` —— 云端部署配置

## 切换 / 新增模型
- **切换**：打开页面后，左上角会出现「模型切换」面板 —— 下拉直接选、或用 `‹` `›` 逐个换；有皮肤的模型（如「春」）会多出一个「皮肤」下拉。当前选择会记在浏览器（localStorage），下次打开自动恢复。
- **新增模型（零代码）**：把任意 Live2D Cubism 2 模型文件夹整目录丢进 `model/`，刷新页面即自动出现在列表里。`serve.py` 的 `/models` 接口会扫描 `model/` 目录；`model_manifest.json` 仅作离线兜底，一般无需手动维护。
- **内置模型**：结月ゆかり、琪亚娜、雷电芽衣、布洛妮娅、雷姆、樱、春、初音未来、Unity娘、姬子、希儿、德丽莎、辛、狐娘。

## 本地运行
```bash
# 1) 安装依赖（只需 edge-tts）
pip install -r requirements.txt

# 2) （可选）放一份 .env 写入你的智普 Key，本地免填 Key
#    cp .env.example .env  # 然后编辑填入 ZHIPU_API_KEY
#    不填也行：浏览器里打开后点 ⚙ 手动粘贴 Key

# 3) 启动
bash start.sh            # 默认 8123 端口
# 或： python serve.py 8123

# 4) 浏览器打开
http://localhost:8123/
```
点 🎤 说中文即可；角色会用语音回复并开口。（语音需要本服务运行，直接双击 html 文件无语音。）

## 部署到云端（打开即用）
把整个仓库推到 GitHub，然后在 **Render**（或 Railway）一键部署：

1. Render 新建 **Web Service**，关联本仓库。
2. 运行环境选 **Python**，`Build Command` = `pip install -r requirements.txt`，`Start Command` = `python serve.py`（仓库已带 `render.yaml`，可自动识别）。
3. 在 Render 的 **Environment** 里添加变量 `ZHIPU_API_KEY` = 你的智普 Key（仓库已设为不自动同步，需手动填）。
4. 部署完成后，打开分配的 `https://xxx.onrender.com/` —— **任何人打开即聊，无需 Key**。

> 为什么需要服务端代理：Edge TTS 与大模型都不能从纯静态页面直连（CORS / 密钥安全）。`serve.py` 的 `/llm` 把智普 Key 留在服务端，前端只发对话内容，因此公开部署也不会泄露 Key。

## 安全提示
- 不要把真实 `ZHIPU_API_KEY` 写进代码或提交到仓库，只用环境变量 / `.env`（已加入 `.gitignore`）。
- 公开部署时，建议用 Render 等平台的环境变量注入 Key。

## 自定义
- 换音色：设置面板里的「嗓音」下拉（晓晓/御姐预设等）。
- 换模型/服务商：设置面板切到 DeepSeek / Moonshot / 通义 / OpenAI 兼容，并填入对应 Key。
- 改角色人设：设置面板里的「系统提示词」。
