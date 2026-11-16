# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-11-16T09:10:26`
- **進捗サマリー**: 全 **119** 話 （完了: **119** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **0** / プロット作成済: **0** / 未着手待機: **0**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| - | - | （全エピソード完了済み・次回起動時に新規テーマ自動生成） | - | Completed | `sff7020` / `rtx5060lp` |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #119 | `ep119-perovskite-solar-cells-halide-photovoltaics-energy` | 結晶の奇跡が紡ぐ次世代の光――ペロブスカイト太陽電池とハロゲン化光電変換 | `rtx5060lp` | 2026-11-15 | 未校閲 | 🎨 (kenomac-mini) |
| #118 | `ep118-metamaterials-negative-index-refraction-invisibility-cloak` | 光を曲げて世界を消す人工格子――メタマテリアルと負の屈折率物理学 | `rtx5060lp` | 2026-11-15 | 未校閲 | 🎨 (kenomac-mini) |
| #117 | `ep117-optogenetics-channelrhodopsin-neural-circuits` | 光のスイッチが拓く意識の回廊――光遺伝学（オプトジェネティクス）と神経回路制御 | `rtx5060lp` | 2026-11-15 | 未校閲 | 🎨 (kenomac-mini) |
| #116 | `ep116-social-physics-opinion-dynamics-bounded-confidence-consensus` | 孤立した島を架橋するエージェント――社会物理学と合意形成の数理モデル | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #115 | `ep115-cosmic-inflation-scalar-field-vacuum-energy-big-bang` | 偽りの真空が引き裂いた瞬間――宇宙インフレーションと指数関数的急膨張 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #114 | `ep114-black-scholes-merton-option-pricing-stochastic-calculus` | 不確実な未来に価格をつける方程式――ブラック・ショールズ方程式と確率微積分の幾何学 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #113 | `ep113-molecular-machines-nanomotors-rotaxane-supramolecular-chemistry` | 光で回転する分子の歯車――超分子機械とナノローターの有機化学 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #112 | `ep112-topological-insulator-quantum-spin-hall-effect-condensed-matter` | 縁を駆ける乱れなきスピン――トポロジカル絶縁体と量子スピンホール効果 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #111 | `ep111-memristor-neuromorphic-computing-analog-ai` | 記憶する抵抗器とシナプスの夢――メムリスタと脳型アナログ計算 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #110 | `ep110-sanger-dna-sequencing-dideoxy-chain-termination-genomics` | 鎖を止める四色の鍵――サンガー法とDNA配列解読の分子生物学 | `rtx5060lp` | 2026-11-12 | 未校閲 | 🎨 (kenomac-mini) |
