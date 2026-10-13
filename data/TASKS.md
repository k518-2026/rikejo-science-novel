# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-13T09:00:00`
- **進捗サマリー**: 全 **44** 話 （完了: **43** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **1** / プロット作成済: **0** / 未着手待機: **0**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| #44 | `ep44-p-vs-np-computational-complexity-math-informatics` | 解く難しさと確かめる優しさの狭間で――P対NP問題と計算量理論の地平 | 情報理工学部・数理情報学科 ／ 理学部・情報科学科（計算量理論・アルゴリズム幾何学研究室） | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #43 | `ep43-synthetic-biology-minimal-cell-genome` | いのちの最小限レシピを求めて――合成生物学と人工ゲノムデザイン | `rtx5060lp` | 2026-10-13 | 未校閲 | 🎨 (kenomac-mini) |
| #42 | `ep42-paleoclimatology-milankovitch-cycles-earth-science` | 地球の鼓動が刻む氷河期の謎――ミランコビッチ・サイクルと古気候天文学 | `rtx5060lp` | 2026-10-13 | 未校閲 | 🎨 (kenomac-mini) |
| #41 | `ep41-quantum-teleportation-entanglement-photon-physics` | 二つの光子が織りなす見えない糸――量子もつれとテレポーテーションの物理 | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #40 | `ep40-explainable-ai-medical-imaging-informatics-teacher` | AIの『まなざし』を言葉に翻訳する――説明可能なAI（XAI）と信頼のアルゴリズム | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #39 | `ep39-metamaterials-acoustic-cloaking-wave-physics` | 光と音を曲げる透明マントの設計図――メタマテリアルと波動の幾何学 | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #38 | `ep38-causal-inference-natural-experiment-data-science` | アイスクリームが売れると水難事故が増える？――相関と因果を見抜く統計学 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
| #37 | `ep37-circadian-rhythm-clock-genes-chronobiology` | 朝顔が咲く時刻を刻む細胞の振り子――時計遺伝子と体内時計の生物学 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
| #36 | `ep36-superconductivity-meissner-quantum-levitation` | 液体窒素の白い霧と空中に浮かぶ磁石――超伝導と量子ピン止め効果の物理 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
| #35 | `ep35-error-correcting-codes-reed-solomon-space-probe` | 傷ついたQRコードと深宇宙からの手紙――誤り訂正符号の代数幾何学 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
| #34 | `ep34-bioluminescence-gfp-live-cell-imaging` | オワンクラゲの緑の灯火――GFPが照らし出す生きた細胞の小宇宙 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
