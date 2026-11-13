# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-11-13T20:03:32`
- **進捗サマリー**: 全 **116** 話 （完了: **113** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **3** / プロット作成済: **0** / 未着手待機: **0**）

## 🖥️ 各ローカルLLMサーバーの役割分担（メインPC電源オフ時も各ノード単体で自律実行）

| 優先順 / 担当 | サーバー名 (IP) | 使用モデル / API | 担当エピソード・単体自律動作 |
|:---|:---|:---|:---|
| **プライマリ執筆 (`rtx5060lp`)** | `http://rtx5060lp:11434` (`192.168.128.62`) | Ollama `qwen3.5:9b` × `shosetsu` (`think: false`) | **偶数話メイン**（繊細で叙情的な青春科学ノベル調・単体起動時にGitHubから偶数話または停止中ノード分を取得して執筆） |
| **セカンダリ執筆 (`sff7020`)** | `http://sff7020:1234` (`192.168.128.16`) | LM Studio `google/gemma-4-26b-a4b-qat` (`reasoning_effort: none`) | **奇数話メイン**（知的スリルと煽りの効いたドラマチック展開・単体起動時にGitHubから奇数話または停止中ノード分を取得して執筆） |
| **挿絵＆Web公開 (`kenomac-mini`)** | `http://kenomac-mini:7860` (`192.168.128.59`) | Draw Things `FLUX.2 [klein] 4B` + Ollama `gemma4:12b` | **全話の挿絵生成**（単体起動時にGitHub上の `pending_illustration` 原稿を検出して挿絵生成＆GitHub Pages更新） |

## 🚀 GitHubから読み取って実行するタスクキュー (`queued` / 未完了タスク一覧)

| 話数 | タスクID | タイトル | 学部・研究室 | 状態 (`status`) | 次回担当ライター (交互割当) |
|:---:|:---|:---|:---|:---:|:---|
| #114 | `ep114-black-scholes-merton-option-pricing-stochastic-calculus` | 不確実な未来に価格をつける方程式――ブラック・ショールズ方程式と確率微積分の幾何学 | 理学部・数学科 ／ 数理ファイナンス・確率解析モデリング研究室 | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #115 | `ep115-cosmic-inflation-scalar-field-vacuum-energy-big-bang` | 偽りの真空が引き裂いた瞬間――宇宙インフレーションと指数関数的急膨張 | 理学部・天文学科 ／ 宇宙物理学・初期宇宙インフレーション理論研究室 | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |
| #116 | `ep116-social-physics-opinion-dynamics-bounded-confidence-consensus` | 孤立した島を架橋するエージェント――社会物理学と合意形成の数理モデル | 情報理工学部・知能情報学科 ／ 計算社会科学・複雑系ネットワーク研究室 | `queued` | ✨ **プライマリ `rtx5060lp`** (`shosetsu` 叙情ノベル調) |

## ✅ 完了済みエピソード（最新10件）

| 話数 | タスクID | タイトル | 執筆担当ノード | 執筆日 | 校閲 (`sff7020`) | 挿絵 (`kenomac-mini`) |
|:---:|:---|:---|:---:|:---:|:---:|:---:|
| #113 | `ep113-molecular-machines-nanomotors-rotaxane-supramolecular-chemistry` | 光で回転する分子の歯車――超分子機械とナノローターの有機化学 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #112 | `ep112-topological-insulator-quantum-spin-hall-effect-condensed-matter` | 縁を駆ける乱れなきスピン――トポロジカル絶縁体と量子スピンホール効果 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #111 | `ep111-memristor-neuromorphic-computing-analog-ai` | 記憶する抵抗器とシナプスの夢――メムリスタと脳型アナログ計算 | `rtx5060lp` | 2026-11-13 | 未校閲 | 🎨 (kenomac-mini) |
| #110 | `ep110-sanger-dna-sequencing-dideoxy-chain-termination-genomics` | 鎖を止める四色の鍵――サンガー法とDNA配列解読の分子生物学 | `rtx5060lp` | 2026-11-12 | 未校閲 | 🎨 (kenomac-mini) |
| #109 | `ep109-pagerank-random-walk-markov-chain-web-search-math` | 蜘蛛の巣をさまよう旅人の足跡――ページランクとマルコフ連鎖の情報数理 | `rtx5060lp` | 2026-11-12 | 未校閲 | 🎨 (kenomac-mini) |
| #108 | `ep108-bcs-theory-superconductivity-cooper-pairs` | 極低温の海に手を取り合う電子――BCS理論と超伝導クーパー対の量子凝縮 | `rtx5060lp` | 2026-11-12 | 未校閲 | 🎨 (kenomac-mini) |
| #107 | `ep107-green-fluorescent-protein-gfp-molecular-tagging-biochemistry` | 海月が灯す生きた細胞の道標――緑色蛍光タンパク質（GFP）と生体分子追跡 | `rtx5060lp` | 2026-11-07 | 未校閲 | 🎨 (kenomac-mini) |
| #106 | `ep106-chaos-butterfly-effect-strange-attractor-lorenz-math` | 蝶の羽ばたきが描く無限の軌道――決定論的カオスとローレンツ・アトラクターの幾何学 | `rtx5060lp` | 2026-11-07 | 未校閲 | 🎨 (kenomac-mini) |
| #105 | `ep105-stimulated-emission-laser-ruby-quantum-optics` | 紅玉に宿る光の行進――誘導放出とレーザーの量子光学 | `rtx5060lp` | 2026-11-07 | 未校閲 | 🎨 (kenomac-mini) |
| #104 | `ep104-evolutionary-game-theory-hawk-dove-cooperation-math` | 利己的な遺伝子が選ぶ譲り合い――進化ゲーム理論とESS（進化的に安定な戦略）の生態数理 | `rtx5060lp` | 2026-11-03 | 未校閲 | 🎨 (kenomac-mini) |
