# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-26T17:23:45`
- **進捗サマリー**: 全 **90** 話 （完了: **89** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **1** / プロット作成済: **0** / 未着手待機: **0**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| #90 | `ep90-crispr-base-editing-precision-genome-medicine` | 二重らせんを傷つけずに書き換える魔法のペン――CRISPR塩基編集（Base Editing）と精密遺伝子医療 | 理学部・生物学科 ／ ゲノム工学・分子遺伝治療研究室 | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #89 | `ep89-quantum-computing-shors-algorithm-number-theory` | 量子の波がほどく素因数分解――ショアのアルゴリズムと量子超越性の数理 | `rtx5060lp` | 2026-10-25 | 未校閲 | 🎨 (kenomac-mini) |
| #88 | `ep88-cosmic-microwave-background-big-bang-radiometry` | 二点七ケルビンの静寂が語るビッグバン――宇宙マイクロ波背景放射（CMB）と電波天文学の原点 | `rtx5060lp` | 2026-10-25 | 未校閲 | 🎨 (kenomac-mini) |
| #87 | `ep87-differential-privacy-laplace-mechanism-cryptography` | 雑音のヴェールが守る個人の秘密――差分プライバシーと数理統計の防壁 | `rtx5060lp` | 2026-10-23 | 未校閲 | 🎨 (kenomac-mini) |
| #86 | `ep86-radiocarbon-dating-accelerator-mass-spectrometry` | 炭素十四が刻んだ五万年の鼓動――放射性炭素年代測定と加速器質量分析の地球化学 | `rtx5060lp` | 2026-10-23 | 未校閲 | 🎨 (kenomac-mini) |
| #85 | `ep85-optogenetics-neural-circuits-light-control` | 青い閃光が灯す記憶のシナプス――光遺伝学（オプトジェネティクス）と神経回路の生体制御 | `rtx5060lp` | 2026-10-23 | 未校閲 | 🎨 (kenomac-mini) |
| #84 | `ep84-polynomial-time-primality-aks-algorithm-number-theory` | 素数の扉を開く多項式の鍵――AKS素数判定法と計算複雑性の奇跡 | `rtx5060lp` | 2026-10-21 | 未校閲 | 🎨 (kenomac-mini) |
| #83 | `ep83-convolutional-neural-networks-visual-cortex-ai` | 視覚の受容野を畳み込むレンズ――畳み込みニューラルネットワーク（CNN）と画像認識の幾何学 | `rtx5060lp` | 2026-10-21 | 未校閲 | 🎨 (kenomac-mini) |
| #82 | `ep82-quantum-hall-effect-topology-metrology` | 二次元の電子が刻む不変の階段――量子ホール効果とトポロジカル抵抗標準 | `rtx5060lp` | 2026-10-21 | 未校閲 | 🎨 (kenomac-mini) |
| #81 | `ep81-poincare-conjecture-ricci-flow-geometric-surgery` | 宇宙の形を丸める熱の方程式――リッチフローとポアンカレ予想の解決 | `rtx5060lp` | 2026-10-21 | 未校閲 | 🎨 (kenomac-mini) |
| #80 | `ep80-ribozyme-rna-world-origin-of-life` | 酵素の帽子を脱いだ核酸――リボザイムと太古のRNAワールド | `rtx5060lp` | 2026-10-21 | 未校閲 | 🎨 (kenomac-mini) |
