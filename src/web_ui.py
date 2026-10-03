import json
import logging
import subprocess
import webbrowser
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from src.config import get_config
from src.history_manager import HistoryManager
from src.dual_llm_generator import DualLLMStoryGenerator
from src.post_formatter import format_post_content
from src.mail_sender import WordPressMailSender
from src.main import extract_refs_from_markdown

JST = timezone(timedelta(hours=9))
logger = logging.getLogger("web-ui")

HTML_STUDIO_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>放課後サイエンス・キャンパス｜理系女子ライトノベル執筆スタジオ (Qwen 3.5 9B × Gemma 4 12B)</title>
  <style>
    :root {
      --bg: #fdf8fa;
      --card: #ffffff;
      --primary: #db2777;
      --primary-light: #fce7f3;
      --secondary: #0284c7;
      --secondary-light: #e0f2fe;
      --text: #1e293b;
      --muted: #64748b;
      --border: #e2e8f0;
      --success: #059669;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }
    header {
      background: linear-gradient(135deg, #be185d 0%, #db2777 45%, #0284c7 100%);
      color: #fff;
      padding: 18px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    }
    header h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 0.03em;
    }
    header .subtitle {
      font-size: 12.5px;
      opacity: 0.92;
      margin-top: 3px;
    }
    .status-badge {
      background: rgba(255,255,255,0.18);
      border: 1px solid rgba(255,255,255,0.35);
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 13px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: #fbbf24;
      display: inline-block;
    }
    .dot.online { background: #34d399; box-shadow: 0 0 8px #34d399; }
    .container {
      max-width: 1400px;
      margin: 20px auto;
      padding: 0 20px;
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 20px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.03);
      margin-bottom: 18px;
    }
    .card h2 {
      margin: 0 0 12px 0;
      font-size: 16px;
      color: var(--primary);
      border-bottom: 2px solid var(--primary-light);
      padding-bottom: 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 5px;
      color: #334155;
    }
    select, input[type="text"], textarea {
      width: 100%;
      padding: 9px 11px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      font-size: 13.5px;
      font-family: inherit;
      margin-bottom: 12px;
      background: #fff;
    }
    textarea {
      resize: vertical;
      line-height: 1.65;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 10px 16px;
      border: none;
      border-radius: 8px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn:disabled { opacity: 0.55; cursor: not-allowed; }
    .btn-director {
      background: var(--secondary);
      color: #fff;
    }
    .btn-director:hover:not(:disabled) { background: #0369a1; }
    .btn-writer {
      background: var(--primary);
      color: #fff;
    }
    .btn-writer:hover:not(:disabled) { background: #be185d; }
    .btn-success {
      background: var(--success);
      color: #fff;
    }
    .btn-success:hover:not(:disabled) { background: #047857; }
    .btn-outline {
      background: #f8fafc;
      color: #334155;
      border: 1px solid #cbd5e1;
    }
    .btn-outline:hover:not(:disabled) { background: #f1f5f9; }
    .btn-row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 8px;
    }
    .tabs {
      display: flex;
      gap: 8px;
      border-bottom: 2px solid var(--border);
      margin-bottom: 16px;
    }
    .tab-btn {
      padding: 9px 18px;
      border: none;
      background: transparent;
      font-size: 14px;
      font-weight: 600;
      color: var(--muted);
      cursor: pointer;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
    }
    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .info-pill {
      background: var(--secondary-light);
      color: #0369a1;
      padding: 10px 14px;
      border-radius: 8px;
      font-size: 13px;
      margin-bottom: 12px;
    }
    .char-card {
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 10px;
      background: #fffbfd;
    }
    .char-card h4 { margin: 0 0 6px 0; color: #9d174d; font-size: 14px; }
    .char-card p { margin: 3px 0; font-size: 12.5px; color: #475569; }
    #logBox {
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px 14px;
      border-radius: 8px;
      font-family: Consolas, monospace;
      font-size: 12.5px;
      max-height: 150px;
      overflow-y: auto;
      margin-bottom: 14px;
    }
    #previewFrame {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
      background: #fff;
      max-height: 720px;
      overflow-y: auto;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🌸 放課後サイエンス・キャンパス｜理系女子ライトノベル執筆スタジオ</h1>
      <div class="subtitle">構成作家 Qwen 3.5 (9B) × 執筆作家 Gemma 4 (12B) 分業システム ＋ Crossref 査読論文検証 ＋ Blogger / WordPress メール投稿</div>
    </div>
    <div class="status-badge" id="ollamaStatus">
      <span class="dot" id="statusDot"></span>
      <span id="statusText">Mac mini (192.168.128.59:11434) 接続確認中...</span>
    </div>
  </header>

  <div class="container">
    <!-- Left Column: Episode Selection & Lorebook -->
    <div>
      <div class="card">
        <h2>📚 1. エピソード＆科学テーマ選択</h2>
        <label for="episodeSelect">収録エピソード（全12話カタログ）</label>
        <select id="episodeSelect" onchange="onEpisodeChange()"></select>

        <div id="episodeMetaBox" class="info-pill"></div>

        <label for="customInstruction">追加オーダー・執筆指示（任意）</label>
        <textarea id="customInstruction" rows="3" placeholder="例：実験室のガラス器具の描写を多めに、先輩が紅茶を淹れてくれるシーンを入れてください"></textarea>

        <div class="btn-row">
          <button class="btn btn-director" id="btnGenPlot" onclick="generatePlotOnly()">
            🧠 ① 構成作家 (Qwen 2.5 14B) でプロット作成
          </button>
          <button class="btn btn-writer" id="btnGenFull" onclick="generateFullEpisode()">
            ✨ 一括生成 (Qwen構成 × Gemma執筆)
          </button>
        </div>
      </div>

      <div class="card">
        <h2>
          <span>👩‍🔬 2. ロアブック（キャラクター設定）</span>
          <button class="btn btn-outline" style="padding:4px 10px;font-size:12px;" onclick="saveLorebook()">保存</button>
        </h2>
        <div id="characterList"></div>
        <details style="margin-top:10px;">
          <summary style="cursor:pointer;font-size:13px;font-weight:600;color:var(--secondary);">＋ ロアブックJSONを直接編集する</summary>
          <textarea id="lorebookJsonEditor" rows="10" style="margin-top:8px;font-family:monospace;font-size:12px;"></textarea>
        </details>
      </div>
    </div>

    <!-- Right Column: Plot Studio, Manuscript Editor, HTML Preview & WP Dispatch -->
    <div>
      <div class="card">
        <div id="logBox">[System] 準備完了。エピソードを選択して「プロット作成」または「一括生成」をクリックしてください。</div>

        <div class="tabs">
          <button class="tab-btn active" onclick="switchTab('tabPlot', this)">📐 ① 構成作家プロット (Qwen 2.5 14B)</button>
          <button class="tab-btn" onclick="switchTab('tabManuscript', this)">🖋️ ② 小説原稿＆科学コラム (Gemma 2 9B)</button>
          <button class="tab-btn" onclick="switchTab('tabPreview', this)">🌐 ③ Blogger / WP 投稿プレビュー＆送信</button>
        </div>

        <!-- Tab 1: Plot Blueprint -->
        <div id="tabPlot" class="tab-panel active">
          <p style="margin-top:0;font-size:13px;color:var(--muted);">
            構成作家（<code>qwen2.5:14b</code>）が作成した4シーン構成プロットです。ここで自由に編集してから、執筆作家（<code>gemma2:9b</code>）に本文を書かせることができます。
          </p>
          <textarea id="plotEditor" rows="18" placeholder="「① 構成作家 (Qwen 2.5 14B) でプロット作成」を押すと、ここに緻密な4シーン構成プロットが出力されます。手動で書き換えることも可能です。"></textarea>
          <div class="btn-row">
            <button class="btn btn-writer" id="btnWriteFromPlot" onclick="generateFromPlot()">
              🖋️ このプロットをもとに執筆作家 (Gemma 2 9B) に小説本文を書かせる
            </button>
          </div>
        </div>

        <!-- Tab 2: Manuscript Markdown -->
        <div id="tabManuscript" class="tab-panel">
          <p style="margin-top:0;font-size:13px;color:var(--muted);">
            生成されたMarkdown原稿（YAMLフロントマター＋小説本文＋理系女子向け科学コラム＋Crossref検証済みDOI文献リスト）です。
          </p>
          <textarea id="manuscriptEditor" rows="22" placeholder="生成された小説原稿（Markdown）がここに表示されます。直接加筆・修正して保存できます。"></textarea>
          <div class="btn-row">
            <button class="btn btn-success" onclick="saveManuscript()">💾 原稿を content/ に保存</button>
            <button class="btn btn-outline" onclick="renderPreview()">🔍 HTMLプレビューを更新</button>
            <button class="btn btn-director" onclick="gitPushStock()">☁️ GitHubへコミット＆Push</button>
          </div>
        </div>

        <!-- Tab 3: Blogger / WordPress Preview & Email Send -->
        <div id="tabPreview" class="tab-panel">
          <div class="btn-row" style="margin-bottom: 14px; align-items: center;">
            <select id="wpStatusSelect" style="width:auto;margin-bottom:0;">
              <option value="publish">公開 (publish)</option>
              <option value="draft">下書き (draft)</option>
            </select>
            <button class="btn btn-outline" onclick="sendToWordPress(true)">🧪 Dry-Run（送信テスト）</button>
            <button class="btn btn-writer" onclick="sendToWordPress(false)">✉️ Blogger へメール投稿する</button>
            <button class="btn btn-director" onclick="gitPushStock()">☁️ GitHubへストックをPush</button>
          </div>
          <div id="previewFrame">ここに Blogger メール投稿用のHTMLプレビューが表示されます。</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let catalog = [];
    let lorebook = {};

    function logMsg(msg) {
      const box = document.getElementById('logBox');
      const now = new Date().toLocaleTimeString('ja-JP');
      box.innerHTML += `<div>[${now}] ${msg}</div>`;
      box.scrollTop = box.scrollHeight;
    }

    function switchTab(tabId, btnEl) {
      document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      if (btnEl) btnEl.classList.add('active');
    }

    async function fetchInitialData() {
      const res = await fetch('/api/init');
      const data = await res.json();
      catalog = data.catalog || [];
      lorebook = data.lorebook || {};

      // Update status badge
      const dot = document.getElementById('statusDot');
      const txt = document.getElementById('statusText');
      if (data.ollama && data.ollama.online) {
        dot.classList.add('online');
        txt.textContent = `Mac mini 接続OK (${data.ollama.host}) | 構成: ${data.director_model} × 執筆: ${data.writer_model}`;
      } else {
        dot.classList.remove('online');
        txt.textContent = `Mac mini 未接続 (${data.ollama ? data.ollama.host : ''})`;
      }

      // Populate select
      const sel = document.getElementById('episodeSelect');
      sel.innerHTML = '';
      catalog.forEach(ep => {
        const opt = document.createElement('option');
        opt.value = ep.id;
        const badge = ep.posted ? '【配信済】' : (ep.stocked ? '【ストック済】' : '【未執筆】');
        opt.textContent = `${badge} ${ep.title}（${ep.faculty}）`;
        sel.appendChild(opt);
      });

      renderLorebook();
      onEpisodeChange();
    }

    function renderLorebook() {
      document.getElementById('lorebookJsonEditor').value = JSON.stringify(lorebook, null, 2);
      const list = document.getElementById('characterList');
      list.innerHTML = '';
      (lorebook.characters || []).forEach(c => {
        const div = document.createElement('div');
        div.className = 'char-card';
        div.innerHTML = `
          <h4>${c.name} <span style="font-weight:normal;font-size:12px;color:#64748b;">（${c.role}）</span></h4>
          <p><strong>所属:</strong> ${c.affiliation}</p>
          <p><strong>性格:</strong> ${c.personality}</p>
          <p><strong>口調:</strong> ${c.speech_style}</p>
        `;
        list.appendChild(div);
      });
    }

    async function onEpisodeChange() {
      const wid = document.getElementById('episodeSelect').value;
      const ep = catalog.find(x => x.id === wid);
      if (!ep) return;
      document.getElementById('episodeMetaBox').innerHTML = `
        <div><strong>🏛️ 学部・研究室:</strong> ${ep.faculty}</div>
        <div><strong>🔬 科学テーマ:</strong> ${ep.theme}</div>
        <div><strong>👭 登場人物:</strong> ${ep.protagonist} ／ ${ep.mentor}</div>
        <div style="margin-top:6px;"><strong>📖 あらすじ:</strong> ${ep.summary}</div>
      `;

      // Load existing stock if available
      const res = await fetch(`/api/episode?work_id=${encodeURIComponent(wid)}`);
      const data = await res.json();
      if (data.content) {
        document.getElementById('manuscriptEditor').value = data.content;
        document.getElementById('previewFrame').innerHTML = data.html_preview || '';
        logMsg(`保存済み原稿（${data.file_path}）を読み込みました。`);
      } else {
        document.getElementById('manuscriptEditor').value = '';
        document.getElementById('previewFrame').innerHTML = '（まだ原稿が生成されていません）';
      }
    }

    async function saveLorebook() {
      try {
        const parsed = JSON.parse(document.getElementById('lorebookJsonEditor').value);
        const res = await fetch('/api/lorebook', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(parsed)
        });
        const out = await res.json();
        if (out.success) {
          lorebook = parsed;
          renderLorebook();
          logMsg('ロアブック（キャラクター設定）を保存しました！');
        }
      } catch (e) {
        alert('JSONの形式が正しくありません: ' + e.message);
      }
    }

    function setButtonsDisabled(disabled) {
      ['btnGenPlot', 'btnGenFull', 'btnWriteFromPlot'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = disabled;
      });
    }

    async function generatePlotOnly() {
      const wid = document.getElementById('episodeSelect').value;
      const custom = document.getElementById('customInstruction').value;
      setButtonsDisabled(true);
      logMsg('Crossref APIで実在論文を検証し、構成作家 (Qwen 2.5 14B) が4シーン構成プロットを作成しています（約20〜45秒）...');
      try {
        const res = await fetch('/api/generate_plot', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({work_id: wid, custom_instruction: custom})
        });
        const data = await res.json();
        if (data.success) {
          document.getElementById('plotEditor').value = data.plot;
          switchTab('tabPlot', document.querySelectorAll('.tab-btn')[0]);
          logMsg(`構成作家 (Qwen 2.5 14B) によるプロット作成が完了しました！（検証済み論文: ${data.papers_count}件）`);
        } else {
          logMsg('[Error] ' + (data.error || 'プロット生成に失敗しました'));
        }
      } catch (e) {
        logMsg('[Error] ' + e.message);
      } finally {
        setButtonsDisabled(false);
      }
    }

    async function generateFromPlot() {
      const wid = document.getElementById('episodeSelect').value;
      const plot = document.getElementById('plotEditor').value;
      const custom = document.getElementById('customInstruction').value;
      setButtonsDisabled(true);
      logMsg('執筆作家 (Gemma 2 9B) が前半・後半の小説本文を執筆し、構成作家 (Qwen 2.5 14B) が科学コラムを作成しています（約1〜3分）...');
      try {
        const res = await fetch('/api/generate_full', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({work_id: wid, plot_override: plot, custom_instruction: custom})
        });
        const data = await res.json();
        if (data.success) {
          document.getElementById('manuscriptEditor').value = data.markdown;
          document.getElementById('plotEditor').value = data.plot;
          document.getElementById('previewFrame').innerHTML = data.html_preview;
          switchTab('tabManuscript', document.querySelectorAll('.tab-btn')[1]);
          logMsg(`🎉 執筆完了！『${data.title}』を ${data.file_path} に保存しました！`);
          fetchInitialData();
        } else {
          logMsg('[Error] ' + (data.error || '執筆に失敗しました'));
        }
      } catch (e) {
        logMsg('[Error] ' + e.message);
      } finally {
        setButtonsDisabled(false);
      }
    }

    async function generateFullEpisode() {
      document.getElementById('plotEditor').value = '';
      await generateFromPlot();
    }

    async function saveManuscript() {
      const wid = document.getElementById('episodeSelect').value;
      const md = document.getElementById('manuscriptEditor').value;
      const res = await fetch('/api/save_manuscript', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({work_id: wid, markdown: md})
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('previewFrame').innerHTML = data.html_preview;
        logMsg(`原稿を ${data.file_path} に保存し、プレビューを更新しました。`);
      }
    }

    async function renderPreview() {
      await saveManuscript();
      switchTab('tabPreview', document.querySelectorAll('.tab-btn')[2]);
    }

    async function sendToWordPress(dryRun) {
      const wid = document.getElementById('episodeSelect').value;
      const status = document.getElementById('wpStatusSelect').value;
      await saveManuscript();
      logMsg(dryRun ? 'WordPress メール投稿の Dry-Run 検証を実行中...' : 'WordPress へメール投稿を実行中...');
      const res = await fetch('/api/send_wp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({work_id: wid, dry_run: dryRun, status: status})
      });
      const data = await res.json();
      if (data.success) {
        logMsg(`✅ ${data.message} (Title: ${data.title})`);
        fetchInitialData();
      } else {
        logMsg(`❌ 送信エラー: ${data.error}`);
      }
    }

    async function gitPushStock() {
      logMsg('GitHub リポジトリへ content/ と data/ を git commit & push しています...');
      const res = await fetch('/api/git_push', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        logMsg('☁️ GitHub リポジトリへの Push が完了しました！');
      } else {
        logMsg('⚠️ GitHub Push エラー: ' + data.error);
      }
    }

    window.addEventListener('DOMContentLoaded', fetchInitialData);
  </script>
</body>
</html>
"""


class StudioRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = HTML_STUDIO_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api/init":
            config = get_config()
            hm = HistoryManager()
            gen = DualLLMStoryGenerator(
                ollama_host=config.ollama_host,
                director_model=config.director_model,
                writer_model=config.writer_model,
            )
            posted_ids = hm.get_posted_ids()
            cat_out = []
            for w in hm.catalog:
                w_copy = dict(w)
                w_copy["posted"] = w["id"] in posted_ids
                w_copy["stocked"] = hm.find_stock_file_for_work(w["id"]) is not None
                cat_out.append(w_copy)

            self._send_json({
                "catalog": cat_out,
                "lorebook": gen.lorebook,
                "ollama": gen.check_connection(),
                "director_model": config.director_model,
                "writer_model": config.writer_model,
            })
            return

        if parsed.path == "/api/episode":
            qs = parse_qs(parsed.query)
            work_id = qs.get("work_id", [""])[0]
            hm = HistoryManager()
            stock_file = hm.find_stock_file_for_work(work_id)
            if stock_file and stock_file.exists():
                content = stock_file.read_text(encoding="utf-8")
                formatted = format_post_content(str(stock_file))
                self._send_json({
                    "content": content,
                    "file_path": str(stock_file),
                    "html_preview": formatted.content_html,
                })
            else:
                self._send_json({"content": "", "file_path": "", "html_preview": ""})
            return

        self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        config = get_config()
        hm = HistoryManager()
        gen = DualLLMStoryGenerator(
            ollama_host=config.ollama_host,
            director_model=config.director_model,
            writer_model=config.writer_model,
        )

        if parsed.path == "/api/lorebook":
            data = self._read_json()
            gen.save_lorebook(data)
            self._send_json({"success": True})
            return

        if parsed.path == "/api/generate_plot":
            data = self._read_json()
            work_id = data.get("work_id", "")
            custom_instruction = data.get("custom_instruction", "")
            work = next((w for w in hm.catalog if w["id"] == work_id), None)
            if not work:
                self._send_json({"success": False, "error": f"Work ID '{work_id}' not found"}, 400)
                return
            try:
                papers = gen.fetch_verified_references_for_work(work)
                plot = gen.generate_plot_with_director(
                    work=work,
                    verified_papers=papers,
                    custom_instruction=custom_instruction,
                )
                self._send_json({
                    "success": True,
                    "plot": plot,
                    "papers_count": len(papers),
                })
            except Exception as e:
                logger.error(f"Plot generation error: {e}", exc_info=True)
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        if parsed.path == "/api/generate_full":
            data = self._read_json()
            work_id = data.get("work_id", "")
            plot_override = data.get("plot_override", "")
            custom_instruction = data.get("custom_instruction", "")
            work = next((w for w in hm.catalog if w["id"] == work_id), None)
            if not work:
                self._send_json({"success": False, "error": f"Work ID '{work_id}' not found"}, 400)
                return
            try:
                full_md, ep_title, refs, plot_used = gen.generate_complete_episode(
                    work=work,
                    custom_plot_override=plot_override,
                    custom_instruction=custom_instruction,
                )
                today_str = datetime.now(JST).strftime("%Y-%m-%d")
                safe_id = work["id"].replace("-", "_")
                out_path = Path(f"content/{today_str}_{safe_id}.md")
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(full_md, encoding="utf-8")

                formatted = format_post_content(str(out_path))
                Path("preview_output.html").write_text(formatted.content_html, encoding="utf-8")

                self._send_json({
                    "success": True,
                    "title": ep_title,
                    "markdown": full_md,
                    "plot": plot_used,
                    "file_path": str(out_path),
                    "html_preview": formatted.content_html,
                })
            except Exception as e:
                logger.error(f"Full generation error: {e}", exc_info=True)
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        if parsed.path == "/api/save_manuscript":
            data = self._read_json()
            work_id = data.get("work_id", "")
            md_text = data.get("markdown", "")
            stock_file = hm.find_stock_file_for_work(work_id)
            if not stock_file:
                today_str = datetime.now(JST).strftime("%Y-%m-%d")
                safe_id = work_id.replace("-", "_")
                stock_file = Path(f"content/{today_str}_{safe_id}.md")
            stock_file.parent.mkdir(parents=True, exist_ok=True)
            stock_file.write_text(md_text, encoding="utf-8")
            formatted = format_post_content(str(stock_file))
            Path("preview_output.html").write_text(formatted.content_html, encoding="utf-8")
            self._send_json({
                "success": True,
                "file_path": str(stock_file),
                "html_preview": formatted.content_html,
            })
            return

        if parsed.path == "/api/send_wp":
            data = self._read_json()
            work_id = data.get("work_id", "")
            dry_run = bool(data.get("dry_run", True))
            status_override = data.get("status", "publish")
            work = next((w for w in hm.catalog if w["id"] == work_id), None)
            stock_file = hm.find_stock_file_for_work(work_id)
            if not stock_file or not stock_file.exists():
                self._send_json({"success": False, "error": "原稿ファイルが見つかりません。先に執筆または保存してください。"}, 400)
                return

            next_work = None
            if work:
                for idx, w in enumerate(hm.catalog):
                    if w["id"] == work["id"]:
                        next_work = hm.catalog[(idx + 1) % len(hm.catalog)]
                        break

            formatted = format_post_content(
                str(stock_file),
                status_override=status_override,
                include_jetpack_shortcodes=config.use_jetpack_shortcodes,
                next_work=next_work,
            )
            sender = WordPressMailSender(config)
            res = sender.send_post(formatted, dry_run=dry_run)
            if res.get("success") and not dry_run and work:
                refs = extract_refs_from_markdown(stock_file.read_text(encoding="utf-8", errors="ignore"))
                hm.record_post(
                    work=work,
                    episode_title=formatted.title,
                    file_path=str(stock_file),
                    references=refs,
                    status=formatted.status,
                )
            self._send_json(res)
            return

        if parsed.path == "/api/git_push":
            try:
                subprocess.run(["git", "add", "content/", "data/"], check=True)
                diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"])
                if diff_res.returncode != 0:
                    subprocess.run(
                        ["git", "commit", "-m", "feat(studio): Update Rikejo science novel content & lorebook [skip ci]"],
                        check=True,
                    )
                subprocess.run(["git", "push", "origin", "HEAD:main"], check=True)
                self._send_json({"success": True})
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        self.send_error(404)


def run_web_server(port: int = 8505, open_browser: bool = True):
    url = f"http://localhost:{port}"
    print("\n" + "=" * 72)
    print(" 🌸 放課後サイエンス・キャンパス｜理系女子ライトノベル執筆スタジオ (Web UI)")
    print(f" 🌐 URL: {url}")
    print(" 🤖 構成作家: qwen2.5:14b  ×  執筆作家: gemma2:9b (Mac mini: 192.168.128.59:11434)")
    print("=" * 72 + "\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    server = HTTPServer(("127.0.0.1", port), StudioRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Web UI Studio...")
        server.server_close()
