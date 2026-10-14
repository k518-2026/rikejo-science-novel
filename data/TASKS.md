# 📋 分散ローカルLLM 自動作業リスト (`rikejo-science-novel`)

- **会話ID**: `03e1e31e-29c5-4db4-b211-06e49e17b8bd`
- **最終同期日時 (JST)**: `2026-10-14T20:57:25`
- **進捗サマリー**: 全 **47** 話 （完了: **47** / 挿絵待ち: **0** / **PC起動時実行キュー(`queued`)**: **0** / プロット作成済: **0** / 未着手待機: **0**）

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
| #47 | `ep47-lithium-ion-battery-intercalation-chemistry` | リチウムイオンが旅する結晶の隙間――充電池の化学とノーベル賞の物語 | `rtx5060lp` | 2026-10-14 | 未校閲 | 🎨 (kenomac-mini) |
| #46 | `ep46-transformer-attention-language-model-informatics` | 言葉の関係を見つめる『注意』のしくみ――Transformerと大規模言語モデルの情報学 | `rtx5060lp` | 2026-10-14 | 未校閲 | 🎨 (kenomac-mini) |
| #45 | `ep45-higgs-boson-standard-model-particle-physics` | 宇宙に質量を与えた見えない海――ヒッグス粒子と素粒子の標準模型 | `rtx5060lp` | 2026-10-14 | 未校閲 | 🎨 (kenomac-mini) |
| #44 | `ep44-p-vs-np-computational-complexity-math-informatics` | 解く難しさと確かめる優しさの狭間で――P対NP問題と計算量理論の地平 | `rtx5060lp` | 2026-10-13 | 未校閲 | 🎨 (kenomac-mini) |
| #43 | `ep43-synthetic-biology-minimal-cell-genome` | いのちの最小限レシピを求めて――合成生物学と人工ゲノムデザイン | `rtx5060lp` | 2026-10-13 | 未校閲 | 🎨 (kenomac-mini) |
| #42 | `ep42-paleoclimatology-milankovitch-cycles-earth-science` | 地球の鼓動が刻む氷河期の謎――ミランコビッチ・サイクルと古気候天文学 | `rtx5060lp` | 2026-10-13 | 未校閲 | 🎨 (kenomac-mini) |
| #41 | `ep41-quantum-teleportation-entanglement-photon-physics` | 二つの光子が織りなす見えない糸――量子もつれとテレポーテーションの物理 | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #40 | `ep40-explainable-ai-medical-imaging-informatics-teacher` | AIの『まなざし』を言葉に翻訳する――説明可能なAI（XAI）と信頼のアルゴリズム | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #39 | `ep39-metamaterials-acoustic-cloaking-wave-physics` | 光と音を曲げる透明マントの設計図――メタマテリアルと波動の幾何学 | `rtx5060lp` | 2026-10-12 | 未校閲 | 🎨 (kenomac-mini) |
| #38 | `ep38-causal-inference-natural-experiment-data-science` | アイスクリームが売れると水難事故が増える？――相関と因果を見抜く統計学 | `rtx5060lp` | 2026-10-11 | 未校閲 | 🎨 (kenomac-mini) |
