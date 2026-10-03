# rikejo-science-novel ―― 『放課後サイエンス・キャンパス』理系女子ライトノベル × Mac mini ローカルLLM分業執筆 ＆ WordPress メール自動投稿システム

女子中高生（理系女子）が**「大学の研究室に行ってみたい！」「最先端の科学ってこんなに美しくてワクワクするんだ！」**と胸を躍らせるような、最新科学を正しくやさしく学べる学園・キャンパス科学ライトノベル『**放課後サイエンス・キャンパス**』を、**Mac mini (`http://192.168.128.59:11434/`) 上の2つのローカルLLMの分業体制**で自動執筆し、WordPress へメール投稿（Post via Email）するシステムです。

---

## 🌟 1. システムの3大特徴

### ① 「構成作家（Qwen 2.5 14B）」×「執筆作家（Gemma 2 9B）」の分業アーキテクチャ
Mac mini 上の Ollama（`http://192.168.128.59:11434/`）に搭載された2つのローカルLLMの長所を最大限に活かした協調パイプラインを採用しています：

| 役割 | 担当モデル | 担当工程 | 強み・特徴 |
|:---|:---|:---|:---|
| **🧠 構成作家 (Director)** | `qwen2.5:14b` | 1. 4シーン構成プロット設計図の作成<br>2. キャラクター設定（ロアブック）の整合性管理<br>3. 『理系女子のためのやさしい最新科学コラム＆大学研究室ガイド』の執筆 | 指示への忠実さ、論理的構成力、ストーリーの破綻のなさ、正確な科学解説に優れる |
| **🖋️ 執筆作家 (Writer)** | `gemma2:9b` | 1. 前半パート（第1・第2シーン）の小説本文執筆<br>2. 後半パート（第3・第4シーン）の小説本文執筆 | 小説らしい瑞々しい五感・情景描写、自然な会話劇、高速な文章生成に優れる |

### ② 査読付き科学論文（Crossref REST API + DOI実在検証）によるハルシネーションゼロ設計
- 執筆前に **Crossref REST API** から *Nature*, *Science*, *Cell*, *PNAS* 等の実在する査読付き論文3本を自動検索し、`https://doi.org/api/handles/` で **DOIの疎通（実在）を100%検証**してからプロット作成・本文執筆に渡します。
- そのため、架空の論文やリンク切れDOIが混入することは物理的にありません。

### ③ ブラウザで使える専用執筆ツール（Web UI スタジオ）搭載
- Windows PC 上で `.\run_studio.ps1`（または `python -m src.main --web`）を実行すると、ブラウザ（`http://localhost:8505`）で専用の**「理系女子ライトノベル執筆スタジオ」**が起動します。
- **ロアブック（キャラクター設定・口調）の編集**、**Qwen 2.5 14B によるプロット生成＆手動調整**、**Gemma 2 9B による本文執筆**、**WordPress メール投稿プレビュー＆ワンクリック送信**、**GitHub へのストック自動Push**までをすべてブラウザ画面上で操作できます。

---

## 📚 2. 収録エピソード・カタログ（全12話）

[`data/science_catalog.json`](data/science_catalog.json) に、高校の生物・化学・物理・数学・情報と大学の最先端研究室をつなぐ全12話を収録しています（自由に追加・編集可能）：

1. **第1話『夜の温室と光るペチュニアの秘密』**（農学部・応用生命科学科／合成生物学：自律発光植物・カフェ酸サイクル）
2. **第2話『モルフォ蝶の青い翅と、色素のない絵の具』**（理学部・生物科学科／フォトニクス材料：構造色とCRISPRゲノム編集）
3. **第3話『シャボン玉の郵便配達員――ナノ粒子の旅路』**（薬学部・創薬科学科／DDS研究室：脂質ナノ粒子 LNP と mRNA 医薬）
4. **第4話『百光年先の夕焼けを、プリズムで読む方法』**（理学部・地球惑星物理学科：JWST 宇宙望遠鏡と系外惑星大気透過スペクトル）
5. **第5話『折り紙でつくる、まだ地球にないタンパク質』**（情報理工学部・バイオインフォマティクス専攻：AlphaFold と De novo タンパク質設計）
6. **第6話『鋼鉄より強く、風より軽いドレスを編む』**（工学部・高分子材料工学科：人工クモ糸スパイダーシルクとバイオマテリアル）
7. **第7話『お腹の中の小さな銀河と、心の処方箋』**（農学部・食品生命科学科／神経免疫学：腸脳相関 Gut-Brain Axis とマイクロバイオーム）
8. **第8話『雨上がりのステンドグラスは太陽を醸す』**（理工学部・応用化学科：ペロブスカイト太陽電池と塗布型結晶成膜）
9. **第9話『眠る脳の図書館と、真夜中の水洗い』**（医学部・脳神経科学専攻／睡眠医科学：グリンパティック系と記憶の固定化）
10. **第10話『コップ一杯の海水から、クジラの歌を聴く』**（海洋生命科学部：環境DNA［eDNA］メタバーコーディング）
11. **第11話『アリスとボブの絶対に盗み見られない手紙』**（理学部・物理学科／量子情報科学：量子もつれと量子暗号通信）
12. **第12話『シャーレの中で、小さな心臓が鼓動をはじめる日』**（医学部・再生医療学／医工学：iPS細胞心筋シートと温度応答性培養皿）

---

## 🗂️ 3. ディレクトリ構成

```
rikejo-science-novel/
├── .github/
│   └── workflows/
│       └── publish.yml            # GitHub Actions 自動メール配信ワークフロー
├── content/                       # 生成されたライトノベル原稿ストック (*.md)
├── data/
│   ├── science_catalog.json       # 全12話のエピソード・大学学部・Crossref検索クエリ定義
│   ├── lorebook.json              # キャラクター設定（ロアブック）＆世界観ルール
│   ├── history.json               # WordPress投稿済み履歴データ
│   └── POSTED_STORIES.md          # 投稿済みエピソード一覧テーブル
├── src/
│   ├── __init__.py
│   ├── config.py                  # 環境変数・Mac mini Ollamaホスト・SMTP設定管理
│   ├── doi_verifier.py            # Crossref DOI実在検証モジュール
│   ├── dual_llm_generator.py      # Qwen 2.5 (14B) × Gemma 2 (9B) 分業執筆エンジン
│   ├── history_manager.py         # ストック＆投稿履歴管理
│   ├── post_formatter.py          # WordPressメール投稿用HTML/ショートコード変換
│   ├── mail_sender.py             # WordPress / Blogger メール送信エンジン
│   ├── web_ui.py                  # ブラウザで使える小説執筆ツール（Web UI スタジオ）
│   └── main.py                    # CLIエントリーポイント
├── tests/
│   └── test_system.py             # 単体テストスイート
├── run_studio.ps1                 # Web UI スタジオ起動スクリプト (Windows PowerShell)
├── run_local_stock.ps1            # Mac mini ローカルLLM一括書き溜め＆GitHub Pushスクリプト
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 4. 使い方（Windows PC ＋ Mac mini 連携）

### 4.1 ブラウザ執筆スタジオ（Web UI）を起動する

```powershell
cd e:\GoogleAntigravity\rikejo-science-novel
.\run_studio.ps1
```
ブラウザで `http://localhost:8505` が自動的に開き、以下が行えます：
1. **エピソード選択** ＆ **ロアブック（キャラクター設定）の編集**
2. **「① 構成作家 (Qwen 2.5 14B) でプロット作成」**をクリックし、生成されたプロットを確認・微調整
3. **「🖋️ このプロットをもとに執筆作家 (Gemma 2 9B) に小説本文を書かせる」**をクリックして小説本編と科学コラムを完成
4. **WordPress プレビュー確認 ＆ メール送信**、または **GitHub へのストックPush**

### 4.2 コマンドラインから一括書き溜め＆GitHubへPushする

```powershell
# 現在のストック＆配信状況を確認
python -m src.main --status-report

# 未生成のエピソードを2話分、Mac mini (Qwen2.5×Gemma2) で執筆してGitHubへ自動Push
.\run_local_stock.ps1 -Count 2

# 特定のエピソード（第1話）を生成してHTMLプレビュー出力（Dry-Run）
python -m src.main --work-id ep01-bioluminescence-plant --dry-run --preview-html

# WordPressへ実際にメール投稿する
python -m src.main --work-id ep01-bioluminescence-plant --send
```

---

## ⚙️ 5. GitHub Actions での自動メール投稿設定

GitHub リポジトリの **Settings > Secrets and variables > Actions** に以下の Secret を登録すると、毎日自動的に `content/` にストックされた小説が WordPress へメール投稿されます：

| Secret名 | 必須 | 内容 | 設定例 |
|---|:---:|---|---|
| `SMTP_HOST` | **必須** | SMTPサーバーのホスト名 | `smtp.gmail.com` |
| `SMTP_PORT` | **必須** | SMTPポート番号 | `587` |
| `SMTP_USER` | **必須** | 送信用メールアドレス | `your_email@gmail.com` |
| `SMTP_PASSWORD` | **必須** | Gmailアプリパスワード | `xxxx xxxx xxxx xxxx` |
| `WP_POST_EMAIL` | **必須** | WordPressメール投稿受信用アドレス | `secret_xxxx@post.wordpress.com` |
| `BLOGGER_POST_EMAIL` | 任意 | Bloggerメール投稿アドレス（同時配信する場合） | `user.secret@blogger.com` |
